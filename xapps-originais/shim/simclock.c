/*
 * Autor: George Barbosa
 * Relógio simulado do libe42_shim (docs/16, E2).
 *
 * As xApps originais do FlexRIC esperam com sleep()/usleep() e medem prazos com time(). Para que
 * rodem sem alteração em passo travado com o ns-3, esta unidade sobrepõe essas funções da libc
 * (a biblioteca é ligada antes da libc, então as chamadas da xApp resolvem para cá):
 *   - time() devolve um instante fixo de referência mais o tempo simulado;
 *   - sleep()/usleep()/nanosleep() bloqueiam até o tempo simulado alcançar o prazo.
 * O tempo simulado só avança quando o shim recebe uma janela do orquestrador (simclock_advance).
 * A barreira (simclock_wait_idle) espera todas as threads da xApp voltarem a um sleep com prazo
 * futuro: nesse ponto a xApp terminou de reagir ao KPM da janela e o controle emitido é enviado.
 * Funções de relógio de parede (clock_gettime, gettimeofday) não são sobrepostas: a xApp as usa só
 * para medir latência nos próprios logs.
 */
#define _GNU_SOURCE
#include "simclock.h"

#include <errno.h>
#include <pthread.h>
#include <time.h>
#include <unistd.h>

#define MAX_THREADS 32
static const time_t kEpoch0 = 1767225600; /* 2026-01-01T00:00:00Z: referência fixa, reprodutível */

typedef struct {
  int used;
  int blocked;
  double deadline;
} slot_t;

static pthread_mutex_t mu = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t cv_time = PTHREAD_COND_INITIALIZER;
static pthread_cond_t cv_idle = PTHREAD_COND_INITIALIZER;
static slot_t slots[MAX_THREADS];
static double g_now = 0.0;
static int g_shutdown = 0;
static __thread int my_slot = -1;

static int ensure_slot_locked(void)
{
  if (my_slot >= 0) return my_slot;
  for (int i = 0; i < MAX_THREADS; ++i)
    if (!slots[i].used) {
      slots[i] = (slot_t){.used = 1, .blocked = 0, .deadline = 0.0};
      my_slot = i;
      return i;
    }
  return -1;
}

void simclock_register_app_thread(void)
{
  pthread_mutex_lock(&mu);
  ensure_slot_locked();
  pthread_mutex_unlock(&mu);
}

double simclock_now(void)
{
  pthread_mutex_lock(&mu);
  double t = g_now;
  pthread_mutex_unlock(&mu);
  return t;
}

void simclock_advance(double t_s)
{
  pthread_mutex_lock(&mu);
  if (t_s > g_now) g_now = t_s;
  pthread_cond_broadcast(&cv_time);
  pthread_mutex_unlock(&mu);
}

static int all_idle_locked(void)
{
  for (int i = 0; i < MAX_THREADS; ++i)
    if (slots[i].used && !(slots[i].blocked && slots[i].deadline > g_now + 1e-9)) return 0;
  return 1;
}

void simclock_wait_idle(void)
{
  pthread_mutex_lock(&mu);
  while (!g_shutdown && !all_idle_locked()) pthread_cond_wait(&cv_idle, &mu);
  pthread_mutex_unlock(&mu);
}

void simclock_shutdown(void)
{
  pthread_mutex_lock(&mu);
  g_shutdown = 1;
  pthread_cond_broadcast(&cv_time);
  pthread_cond_broadcast(&cv_idle);
  pthread_mutex_unlock(&mu);
}

static void sim_sleep(double seconds)
{
  pthread_mutex_lock(&mu);
  int s = ensure_slot_locked();
  double deadline = g_now + seconds;
  if (s >= 0) {
    slots[s].blocked = 1;
    slots[s].deadline = deadline;
  }
  pthread_cond_broadcast(&cv_idle);
  while (!g_shutdown && g_now + 1e-9 < deadline) pthread_cond_wait(&cv_time, &mu);
  if (s >= 0) slots[s].blocked = 0;
  pthread_mutex_unlock(&mu);
}

/* ------------------------------------------------------------- sobreposições da libc (xApp) */
unsigned int sleep(unsigned int seconds)
{
  sim_sleep((double)seconds);
  return 0;
}

int usleep(useconds_t usec)
{
  sim_sleep((double)usec / 1e6);
  return 0;
}

int nanosleep(const struct timespec* req, struct timespec* rem)
{
  if (req == NULL) {
    errno = EFAULT;
    return -1;
  }
  sim_sleep((double)req->tv_sec + (double)req->tv_nsec / 1e9);
  if (rem) rem->tv_sec = rem->tv_nsec = 0;
  return 0;
}

time_t time(time_t* tloc)
{
  pthread_mutex_lock(&mu);
  time_t v = kEpoch0 + (time_t)g_now;
  pthread_mutex_unlock(&mu);
  if (tloc) *tloc = v;
  return v;
}
