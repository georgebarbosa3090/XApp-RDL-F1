/*
 * Autor: George Barbosa
 * libe42_shim, backend ns-3 (docs/16 §7.1 e etapa E2).
 *
 * Implementa a API E42 do FlexRIC (src/xApp/e42_xapp_api.h) para que as xApps originais do FlexRIC
 * (xSlice, ES Orange) rodem sem alteração dentro da malha fechada: em vez de um Near-RT RIC, a API
 * conversa por um socket Unix (RDL_SHIM_SOCKET) com o driver da xApp no orquestrador
 * (scripts/closed_loop/flexric_driver.py), que entrega o KPM medido no ns-3 e recebe o controle.
 *
 * Protocolo de texto (uma mensagem por linha):
 *   orquestrador -> shim
 *     HELLO <n_gnbs> <janela_s> | GNB <idx> <cell_id> ... | ENDHELLO
 *     WIN <t_s> | UE <ue> <cell> <conectado> <vazao_mbps> <atraso_ms> <sinr_db> <n> (<cell> <rsrp_dbm>)xn
 *               | ENDWIN
 *     END
 *   shim -> orquestrador (depois de cada janela, quando a xApp terminou de reagir; ver simclock.c)
 *     CTRL <style> <action> <ran_ue_id> <n> (<caminho>=<valor>)xn
 *     DONE
 * O controle sai como as folhas da árvore de RAN Parameters do E2SM-RC (caminho de IDs, valor
 * inteiro, real ou octet string). O mapeamento para proposta da RDL fica no driver em Python.
 *
 * Perfil (RDL_SHIM_PROFILE): "es" monta a indicação KPM formato 3 como o agente do ns-O-RAN
 * (um item de dados por medida; SINR servidor e das vizinhas), "xslice" como o agente da OAI
 * (um item de dados por período, com as medidas DRB/RRU por UE).
 */
#define _GNU_SOURCE
#include <assert.h>
#include <math.h>
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>

#include "xApp/e42_xapp_api.h"
#include "xApp/e2_node_arr_xapp.h"
#include "sm/agent_if/read/sm_ag_if_rd.h"
#include "sm/rc_sm/ie/rc_data_ie.h"
#include "sm/rc_sm/ie/ir/ran_param_struct.h"
#include "sm/rc_sm/ie/ir/ran_param_list.h"
#include "sm/rc_sm/ie/ir/lst_ran_param.h"
#include "util/byte_array.h"

#include "simclock.h"

#define MAX_GNBS 16
#define MAX_UES 512
#define MAX_SUBS 128
#define MAX_NEIGH 16
#define LINE 65536

typedef struct {
  int ue;
  int cell;
  int connected;
  double thp_mbps;
  double delay_ms;
  double sinr_db;
  int n_neigh;
  int neigh_cell[MAX_NEIGH];
  double neigh_rsrp[MAX_NEIGH];
} ue_kpm_t;

typedef struct {
  int active;
  int node;  /* índice do gNB */
  uint32_t rf_id;
  sm_cb cb;
  uint32_t period_ms;
} sub_t;

static int g_fd = -1;
static FILE* g_in = NULL;
static pthread_mutex_t g_out_mu = PTHREAD_MUTEX_INITIALIZER;
static int g_n_gnbs = 0;
static int g_cell_of_gnb[MAX_GNBS];
static double g_window_s = 0.2;
static char g_profile[16] = "es";
static sub_t g_subs[MAX_SUBS];
static int g_n_subs = 0;
static pthread_mutex_t g_subs_mu = PTHREAD_MUTEX_INITIALIZER;
static char* g_ctrl_buf = NULL; /* linhas CTRL pendentes */
static size_t g_ctrl_len = 0;
static pthread_mutex_t g_ctrl_mu = PTHREAD_MUTEX_INITIALIZER;
static volatile int g_stop = 0;
static pthread_t g_reader;

/* ------------------------------------------------------------------------------------------ util */
static void send_line(const char* s)
{
  pthread_mutex_lock(&g_out_mu);
  size_t n = strlen(s), off = 0;
  while (off < n) {
    ssize_t w = write(g_fd, s + off, n - off);
    assert(w > 0 && "shim: falha ao escrever no socket");
    off += (size_t)w;
  }
  pthread_mutex_unlock(&g_out_mu);
}

static int read_line(char* buf, size_t sz)
{
  if (fgets(buf, (int)sz, g_in) == NULL) return 0;
  buf[strcspn(buf, "\r\n")] = '\0';
  return 1;
}

static void append_ctrl(const char* s)
{
  pthread_mutex_lock(&g_ctrl_mu);
  size_t n = strlen(s);
  g_ctrl_buf = realloc(g_ctrl_buf, g_ctrl_len + n + 1);
  memcpy(g_ctrl_buf + g_ctrl_len, s, n + 1);
  g_ctrl_len += n;
  pthread_mutex_unlock(&g_ctrl_mu);
}

static byte_array_t ba_of(const char* s) { return cp_str_to_ba(s); }

static int node_of_id(global_e2_node_id_t const* id)
{
  for (int g = 0; g < g_n_gnbs; ++g)
    if ((int)id->nb_id.nb_id == g_cell_of_gnb[g]) return g;
  return -1;
}

/* ------------------------------------------------------------------- nós e RAN Functions (E2 Setup) */
static const char* kMeasEs[] = {"L3servingSINR3gpp_cell_", "L3neighSINRListOf_UEID_"};
static const char* kMeasXslice[] = {"DRB.PdcpSduVolumeDL", "DRB.PdcpSduVolumeUL", "DRB.RlcSduDelayDl",
                                    "DRB.UEThpDl",         "DRB.UEThpUl",         "RRU.PrbTotDl",
                                    "RRU.PrbTotUl"};

static kpm_ran_function_def_t kpm_def(void)
{
  kpm_ran_function_def_t d = {0};
  d.sz_ric_event_trigger_style_list = 1;
  d.ric_event_trigger_style_list = calloc(1, sizeof(ric_event_trigger_style_item_t));
  d.ric_event_trigger_style_list[0].style_type = STYLE_1_RIC_EVENT_TRIGGER;
  d.ric_event_trigger_style_list[0].style_name = ba_of("Periodic Report");
  d.ric_event_trigger_style_list[0].format_type = FORMAT_1_RIC_EVENT_TRIGGER;

  int es = strcmp(g_profile, "es") == 0;
  const char** names = es ? kMeasEs : kMeasXslice;
  size_t n = es ? 2 : 7;
  d.sz_ric_report_style_list = 1;
  d.ric_report_style_list = calloc(1, sizeof(ric_report_style_item_t));
  ric_report_style_item_t* r = &d.ric_report_style_list[0];
  r->report_style_type = STYLE_4_RIC_SERVICE_REPORT;
  r->report_style_name = ba_of("Common Condition-based, UE-level Measurement");
  r->act_def_format_type = FORMAT_4_ACTION_DEFINITION;
  r->meas_info_for_action_lst_len = n;
  r->meas_info_for_action_lst = calloc(n, sizeof(meas_info_for_action_lst_t));
  for (size_t i = 0; i < n; ++i) r->meas_info_for_action_lst[i].name = ba_of(names[i]);
  r->ind_hdr_format_type = FORMAT_1_INDICATION_HEADER;
  r->ind_msg_format_type = FORMAT_3_INDICATION_MESSAGE;
  d.name.name = ba_of("ORAN-E2SM-KPM");
  d.name.oid = ba_of("1.3.6.1.4.1.53148.1.2.2.2");
  d.name.description = ba_of("KPM Monitor");
  return d;
}

e2_node_arr_xapp_t e2_nodes_xapp_api(void)
{
  e2_node_arr_xapp_t arr = {0};
  arr.len = (uint8_t)g_n_gnbs;
  arr.n = calloc((size_t)g_n_gnbs, sizeof(e2_node_connected_xapp_t));
  for (int g = 0; g < g_n_gnbs; ++g) {
    e2_node_connected_xapp_t* n = &arr.n[g];
    n->id.type = ngran_gNB;
    n->id.plmn.mcc = 1;
    n->id.plmn.mnc = 1;
    n->id.plmn.mnc_digit_len = 2;
    n->id.nb_id.nb_id = (uint32_t)g_cell_of_gnb[g];
    n->len_rf = 3;
    n->rf = calloc(3, sizeof(sm_ran_function_t));
    n->rf[0].id = 2; /* KPM */
    n->rf[0].rev = 1;
    n->rf[0].defn.type = KPM_RAN_FUNC_DEF_E;
    n->rf[0].defn.kpm = kpm_def();
    n->rf[0].oid = ba_of("1.3.6.1.4.1.53148.1.2.2.2");
    n->rf[1].id = 3; /* RC */
    n->rf[1].rev = 1;
    n->rf[1].defn.type = RC_RAN_FUNC_DEF_E;
    n->rf[1].defn.rc.name.name = ba_of("ORAN-E2SM-RC");
    n->rf[1].defn.rc.name.oid = ba_of("1.3.6.1.4.1.53148.1.1.2.3");
    n->rf[1].defn.rc.name.description = ba_of("RAN Control");
    n->rf[1].oid = ba_of("1.3.6.1.4.1.53148.1.1.2.3");
    n->rf[2].id = 142; /* MAC (estatísticas, xSlice) */
    n->rf[2].rev = 1;
    n->rf[2].defn.type = MAC_RAN_FUNC_DEF_E;
    n->rf[2].oid = ba_of("1.3.6.1.4.1.53148.1.1.2.142");
  }
  return arr;
}

/* ----------------------------------------------------------------------------- subscrição/controle */
sm_ans_xapp_t report_sm_xapp_api(global_e2_node_id_t* id, uint32_t rf_id, void* data, sm_cb handler)
{
  sm_ans_xapp_t ans = {0};
  int node = node_of_id(id);
  if (node < 0 || g_n_subs >= MAX_SUBS) {
    ans.success = false;
    ans.u.reason = "shim: nó ou limite de subscrições";
    return ans;
  }
  uint32_t period = 1000;
  if (rf_id == 2 && data != NULL) {
    kpm_sub_data_t const* s = (kpm_sub_data_t const*)data;
    period = s->ev_trg_def.kpm_ric_event_trigger_format_1.report_period_ms;
  } else if (data != NULL) {
    period = (uint32_t)atoi((char const*)data); /* "1_ms", "10_ms", ... */
  }
  if (period == 0) period = 1;
  pthread_mutex_lock(&g_subs_mu);
  int h = g_n_subs++;
  g_subs[h] = (sub_t){.active = 1, .node = node, .rf_id = rf_id, .cb = handler, .period_ms = period};
  pthread_mutex_unlock(&g_subs_mu);
  ans.success = true;
  ans.u.handle = h + 1;
  return ans;
}

void rm_report_sm_xapp_api(int const handle)
{
  pthread_mutex_lock(&g_subs_mu);
  if (handle >= 1 && handle <= g_n_subs) g_subs[handle - 1].active = 0;
  pthread_mutex_unlock(&g_subs_mu);
}

/* folhas da árvore de RAN Parameters: "id/id/...=valor" */
static void walk_param(seq_ran_param_t const* p, const char* prefix, char* out, size_t outsz, int* n);

static void walk_val(ran_param_val_type_t const* v, const char* path, char* out, size_t outsz, int* n)
{
  char buf[256];
  ran_parameter_value_t const* leaf = NULL;
  switch (v->type) {
    case ELEMENT_KEY_FLAG_TRUE_RAN_PARAMETER_VAL_TYPE: leaf = v->flag_true; break;
    case ELEMENT_KEY_FLAG_FALSE_RAN_PARAMETER_VAL_TYPE: leaf = v->flag_false; break;
    case STRUCTURE_RAN_PARAMETER_VAL_TYPE:
      if (v->strct)
        for (size_t i = 0; i < v->strct->sz_ran_param_struct; ++i)
          walk_param(&v->strct->ran_param_struct[i], path, out, outsz, n);
      return;
    case LIST_RAN_PARAMETER_VAL_TYPE:
      if (v->lst)
        for (size_t i = 0; i < v->lst->sz_lst_ran_param; ++i) {
          char p2[200];
          snprintf(p2, sizeof(p2), "%s[%zu]", path, i);
          ran_param_struct_t const* s = &v->lst->lst_ran_param[i].ran_param_struct;
          for (size_t j = 0; j < s->sz_ran_param_struct; ++j) walk_param(&s->ran_param_struct[j], p2, out, outsz, n);
        }
      return;
    default: return;
  }
  if (leaf == NULL) return;
  switch (leaf->type) {
    case INTEGER_RAN_PARAMETER_VALUE: snprintf(buf, sizeof(buf), " %s=i:%ld", path, (long)leaf->int_ran); break;
    case REAL_RAN_PARAMETER_VALUE: snprintf(buf, sizeof(buf), " %s=r:%g", path, leaf->real_ran); break;
    case BOOLEAN_RAN_PARAMETER_VALUE: snprintf(buf, sizeof(buf), " %s=b:%d", path, (int)leaf->bool_ran); break;
    case OCTET_STRING_RAN_PARAMETER_VALUE:
    case PRINTABLESTRING_RAN_PARAMETER_VALUE:
    case BIT_STRING_RAN_PARAMETER_VALUE: {
      byte_array_t ba = leaf->type == OCTET_STRING_RAN_PARAMETER_VALUE ? leaf->octet_str_ran
                        : leaf->type == BIT_STRING_RAN_PARAMETER_VALUE ? leaf->bit_str_ran
                                                                        : leaf->printable_str_ran;
      int k = snprintf(buf, sizeof(buf), " %s=s:", path);
      for (size_t i = 0; i < ba.len && k < (int)sizeof(buf) - 3; ++i) k += snprintf(buf + k, sizeof(buf) - k, "%02x", ba.buf[i]);
      break;
    }
    default: return;
  }
  strncat(out, buf, outsz - strlen(out) - 1);
  (*n)++;
}

static void walk_param(seq_ran_param_t const* p, const char* prefix, char* out, size_t outsz, int* n)
{
  char path[200];
  snprintf(path, sizeof(path), "%s%s%u", prefix, prefix[0] ? "/" : "", p->ran_param_id);
  walk_val(&p->ran_param_val, path, out, outsz, n);
}

sm_ans_xapp_t control_sm_xapp_api(global_e2_node_id_t* id, uint32_t rf_id, void* wr)
{
  sm_ans_xapp_t ans = {.success = true};
  (void)id;
  if (rf_id != 3 || wr == NULL) {
    ans.success = false;
    ans.u.reason = "shim: só RC (3) é encaminhado";
    return ans;
  }
  rc_ctrl_req_data_t const* c = (rc_ctrl_req_data_t const*)wr;
  long style = -1, act = -1, ue = -1;
  if (c->hdr.format == FORMAT_1_E2SM_RC_CTRL_HDR) {
    style = c->hdr.frmt_1.ric_style_type;
    act = c->hdr.frmt_1.ctrl_act_id;
    if (c->hdr.frmt_1.ue_id.type == GNB_UE_ID_E2SM && c->hdr.frmt_1.ue_id.gnb.ran_ue_id)
      ue = (long)*c->hdr.frmt_1.ue_id.gnb.ran_ue_id;
  }
  char* leaves = calloc(1, LINE);
  int n = 0;
  if (c->msg.format == FORMAT_1_E2SM_RC_CTRL_MSG)
    for (size_t i = 0; i < c->msg.frmt_1.sz_ran_param; ++i) walk_param(&c->msg.frmt_1.ran_param[i], "", leaves, LINE, &n);
  char* line = calloc(1, LINE + 128);
  snprintf(line, LINE + 128, "CTRL %ld %ld %ld %d%s\n", style, act, ue, n, leaves);
  append_ctrl(line);
  free(leaves);
  free(line);
  return ans;
}

/* --------------------------------------------------------------------------- indicações KPM e MAC */
static meas_record_lst_t rec_real(double v) { meas_record_lst_t r = {.value = REAL_MEAS_VALUE}; r.real_val = v; return r; }
static meas_record_lst_t rec_int(uint32_t v) { meas_record_lst_t r = {.value = INTEGER_MEAS_VALUE}; r.int_val = v; return r; }

static meas_info_format_1_lst_t info_named(const char* name)
{
  meas_info_format_1_lst_t m = {0};
  m.meas_type.type = NAME_MEAS_TYPE;
  m.meas_type.name = ba_of(name);
  m.label_info_lst_len = 1;
  m.label_info_lst = calloc(1, sizeof(label_info_lst_t));
  m.label_info_lst[0].noLabel = calloc(1, sizeof(enum_value_e));
  *m.label_info_lst[0].noLabel = TRUE_ENUM_VALUE;
  return m;
}

static ue_id_e2sm_t ue_id_of(int id)
{
  ue_id_e2sm_t u = {0};
  u.type = GNB_UE_ID_E2SM;
  u.gnb.ran_ue_id = calloc(1, sizeof(uint64_t));
  *u.gnb.ran_ue_id = (uint64_t)id;
  return u;
}

/* ES (ns-O-RAN): por UE, uma medida de SINR servidor e uma lista de pares (SINR da vizinha, ID) */
static void fill_es(meas_report_per_ue_t* r, ue_kpm_t const* u, int local_id)
{
  char name[128];
  kpm_ind_msg_format_1_t* f = &r->ind_msg_format_1;
  f->meas_info_lst_len = f->meas_data_lst_len = 2;
  f->meas_info_lst = calloc(2, sizeof(meas_info_format_1_lst_t));
  f->meas_data_lst = calloc(2, sizeof(meas_data_lst_t));
  snprintf(name, sizeof(name), "L3servingSINR3gpp_cell_%d_UEID_%d", u->cell, local_id);
  f->meas_info_lst[0] = info_named(name);
  f->meas_data_lst[0].meas_record_len = 1;
  f->meas_data_lst[0].meas_record_lst = calloc(1, sizeof(meas_record_lst_t));
  f->meas_data_lst[0].meas_record_lst[0] = rec_real(u->sinr_db);
  snprintf(name, sizeof(name), "L3neighSINRListOf_UEID_%d_of_Cell_%d", local_id, u->cell);
  f->meas_info_lst[1] = info_named(name);
  /* SINR da vizinha ~ SINR servidor + (RSRP vizinha - RSRP servidora): mesma interferência + ruído (docs/16) */
  double rsrp_serv = NAN;
  for (int k = 0; k < u->n_neigh; ++k)
    if (u->neigh_cell[k] == u->cell) rsrp_serv = u->neigh_rsrp[k];
  int nn = 0;
  for (int k = 0; k < u->n_neigh; ++k)
    if (u->neigh_cell[k] != u->cell) nn++;
  f->meas_data_lst[1].meas_record_len = (size_t)(2 * nn);
  f->meas_data_lst[1].meas_record_lst = calloc((size_t)(2 * nn) + 1, sizeof(meas_record_lst_t));
  int j = 0;
  for (int k = 0; k < u->n_neigh; ++k) {
    if (u->neigh_cell[k] == u->cell) continue;
    double s = isnan(rsrp_serv) ? NAN : u->sinr_db + (u->neigh_rsrp[k] - rsrp_serv);
    f->meas_data_lst[1].meas_record_lst[j++] = rec_real(s);
    f->meas_data_lst[1].meas_record_lst[j++] = rec_int((uint32_t)u->neigh_cell[k]);
  }
}

/* xSlice (OAI): um item de dados com as medidas DRB/RRU, na ordem da definição da RAN Function */
static void fill_xslice(meas_report_per_ue_t* r, ue_kpm_t const* u, double window_s, double cell_prb_per_ue)
{
  kpm_ind_msg_format_1_t* f = &r->ind_msg_format_1;
  f->meas_info_lst_len = 7;
  f->meas_info_lst = calloc(7, sizeof(meas_info_format_1_lst_t));
  for (int i = 0; i < 7; ++i) f->meas_info_lst[i] = info_named(kMeasXslice[i]);
  f->meas_data_lst_len = 1;
  f->meas_data_lst = calloc(1, sizeof(meas_data_lst_t));
  meas_data_lst_t* d = &f->meas_data_lst[0];
  d->meas_record_len = 7;
  d->meas_record_lst = calloc(7, sizeof(meas_record_lst_t));
  double kbits = u->thp_mbps * 1e3 * window_s;
  d->meas_record_lst[0] = rec_int((uint32_t)lround(kbits));                       /* PdcpSduVolumeDL [kb] */
  d->meas_record_lst[1] = rec_int(0);                                             /* sem tráfego UL */
  d->meas_record_lst[2] = rec_real(isnan(u->delay_ms) ? 0.0 : u->delay_ms * 1e3); /* RlcSduDelayDl [us] */
  d->meas_record_lst[3] = rec_real(u->thp_mbps * 1e3);                            /* UEThpDl [kbps] */
  d->meas_record_lst[4] = rec_real(0.0);
  d->meas_record_lst[5] = rec_int((uint32_t)lround(cell_prb_per_ue));            /* PrbTotDl */
  d->meas_record_lst[6] = rec_int(0);
}

static void deliver_kpm(sub_t const* s, ue_kpm_t const* ues, int n_ues, double t_s)
{
  int es = strcmp(g_profile, "es") == 0;
  int cell = g_cell_of_gnb[s->node];
  int idx[MAX_UES], m = 0;
  for (int i = 0; i < n_ues; ++i)
    if (ues[i].cell == cell && ues[i].connected) idx[m++] = i;
  if (es && m > 20) m = 20; /* limite do ES Orange: 20 UEs por célula (docs/16) */
  if (m == 0) return;
  sm_ag_if_rd_t rd = {0};
  rd.type = INDICATION_MSG_AGENT_IF_ANS_V0;
  rd.ind.type = KPM_STATS_V3_0;
  kpm_ind_data_t* ind = &rd.ind.kpm.ind;
  ind->hdr.type = FORMAT_1_INDICATION_HEADER;
  ind->hdr.kpm_ric_ind_hdr_format_1.collectStartTime = (uint64_t)llround(t_s * 1e6);
  ind->msg.type = FORMAT_3_INDICATION_MESSAGE;
  ind->msg.frm_3.ue_meas_report_lst_len = (size_t)m;
  ind->msg.frm_3.meas_report_per_ue = calloc((size_t)m, sizeof(meas_report_per_ue_t));
  for (int k = 0; k < m; ++k) {
    ue_kpm_t const* u = &ues[idx[k]];
    meas_report_per_ue_t* r = &ind->msg.frm_3.meas_report_per_ue[k];
    /* ES: ID local da célula (0..19), porque o ES indexa vetores de 20 posições pelo ID do UE */
    int ue_id = es ? k : u->ue;
    r->ue_meas_report_lst = ue_id_of(ue_id);
    if (es)
      fill_es(r, u, k);
    else
      fill_xslice(r, u, g_window_s, 0.0);
  }
  s->cb(&rd);
  free_kpm_ind_data(ind);
}

static void deliver_mac(sub_t const* s, double t_s)
{
  sm_ag_if_rd_t rd = {0};
  rd.type = INDICATION_MSG_AGENT_IF_ANS_V0;
  rd.ind.type = MAC_STATS_V0;
  rd.ind.mac.msg.tstamp = (int64_t)llround(t_s * 1e6);
  s->cb(&rd);
}

/* ------------------------------------------------------------------------------- laço de janelas */
static ue_kpm_t g_ues[MAX_UES];

static void parse_ue(const char* line, ue_kpm_t* u)
{
  char tok[64];
  const char* p = line + 3;
  int off = 0;
  memset(u, 0, sizeof(*u));
  sscanf(p, "%d %d %d %lf %lf %lf %d%n", &u->ue, &u->cell, &u->connected, &u->thp_mbps, &u->delay_ms, &u->sinr_db,
         &u->n_neigh, &off);
  p += off;
  if (u->n_neigh > MAX_NEIGH) u->n_neigh = MAX_NEIGH;
  for (int k = 0; k < u->n_neigh; ++k) {
    if (sscanf(p, "%d %63s%n", &u->neigh_cell[k], tok, &off) != 2) { u->n_neigh = k; break; }
    u->neigh_rsrp[k] = strtod(tok, NULL);
    p += off;
  }
}

static void* reader_main(void* arg)
{
  (void)arg;
  char* line = malloc(LINE);
  while (read_line(line, LINE)) {
    if (strcmp(line, "END") == 0) break;
    if (strncmp(line, "WIN ", 4) != 0) continue;
    double t = strtod(line + 4, NULL);
    int n_ues = 0;
    while (read_line(line, LINE) && strcmp(line, "ENDWIN") != 0)
      if (strncmp(line, "UE ", 3) == 0 && n_ues < MAX_UES) parse_ue(line, &g_ues[n_ues++]);
    /* 1) indicações da janela, no tempo da janela anterior (os dados foram coletados nela) */
    pthread_mutex_lock(&g_subs_mu);
    int n_subs = g_n_subs;
    sub_t subs[MAX_SUBS];
    memcpy(subs, g_subs, sizeof(sub_t) * (size_t)n_subs);
    pthread_mutex_unlock(&g_subs_mu);
    for (int h = 0; h < n_subs; ++h) {
      if (!subs[h].active) continue;
      if (subs[h].rf_id == 2) {
        int reps = (int)lround(g_window_s * 1000.0 / subs[h].period_ms);
        if (reps < 1) reps = 1;
        for (int r = 0; r < reps; ++r) deliver_kpm(&subs[h], g_ues, n_ues, t);
      } else if (subs[h].rf_id == 142) {
        deliver_mac(&subs[h], t); /* o xSlice só conta as indicações MAC (sm_cb_mac) */
      }
    }
    /* 2) o relógio avança: threads da xApp com prazo vencido acordam e reagem */
    simclock_advance(t);
    /* 3) barreira: todas as threads da xApp de volta a um sleep com prazo futuro */
    simclock_wait_idle();
    pthread_mutex_lock(&g_ctrl_mu);
    if (g_ctrl_len) send_line(g_ctrl_buf);
    g_ctrl_len = 0;
    if (g_ctrl_buf) g_ctrl_buf[0] = '\0';
    pthread_mutex_unlock(&g_ctrl_mu);
    send_line("DONE\n");
  }
  free(line);
  g_stop = 1;
  simclock_shutdown();
  return NULL;
}

void init_xapp_api(fr_args_t const* args)
{
  (void)args;
  const char* sock = getenv("RDL_SHIM_SOCKET");
  assert(sock != NULL && "shim: RDL_SHIM_SOCKET não definido");
  const char* prof = getenv("RDL_SHIM_PROFILE");
  if (prof) snprintf(g_profile, sizeof(g_profile), "%s", prof);
  g_fd = socket(AF_UNIX, SOCK_STREAM, 0);
  struct sockaddr_un a = {.sun_family = AF_UNIX};
  snprintf(a.sun_path, sizeof(a.sun_path), "%s", sock);
  int rc = connect(g_fd, (struct sockaddr*)&a, sizeof(a));
  assert(rc == 0 && "shim: connect falhou");
  g_in = fdopen(dup(g_fd), "r");
  char line[512];
  while (read_line(line, sizeof(line))) {
    if (strncmp(line, "HELLO ", 6) == 0) {
      sscanf(line + 6, "%d %lf", &g_n_gnbs, &g_window_s);
    } else if (strncmp(line, "GNB ", 4) == 0) {
      int g, c;
      if (sscanf(line + 4, "%d %d", &g, &c) == 2 && g < MAX_GNBS) g_cell_of_gnb[g] = c;
    } else if (strcmp(line, "ENDHELLO") == 0) {
      break;
    }
  }
  if (strcmp(g_profile, "es") == 0)
    for (int g = 0; g < g_n_gnbs; ++g)
      if (g_cell_of_gnb[g] < 1 || g_cell_of_gnb[g] > 9) {
        /* o ES Orange envia a célula como um caractere '1'..'9' (docs/16) */
        fprintf(stderr, "shim: perfil es aceita células 1..9; célula %d\n", g_cell_of_gnb[g]);
        exit(70);
      }
  simclock_register_app_thread(); /* a thread que chama a API é a principal da xApp */
  pthread_create(&g_reader, NULL, reader_main, NULL);
}

bool try_stop_xapp_api(void) { return g_stop != 0; }
