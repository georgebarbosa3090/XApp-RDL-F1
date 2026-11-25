import json,re,sys,statistics as st,unicodedata,collections
S,D=sys.argv[1],sys.argv[2]
rows=json.load(open(f"{S}/definitivo.json"))
def key(s): return re.sub(r"\s+"," ",unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().upper().replace("\\"," ").replace("-"," ")).strip()
# demanda
dem={}
for l in open(f"{D}/506-prefeitura-municipal-de-canaa-dos-carajaspa-demanda_por_vaga.txt",encoding="utf-8"):
    m=re.match(r"\s*(.+?)\s{2,}(\d+)\s+(\d+)\s+([\d,]+)\s*$",l)
    if m and not m.group(1).startswith("Total"): dem[key(m.group(1))]=(int(m.group(2)),int(m.group(3)))
LP,MAT,RLM,INF,ATU,SUS,LEG,CE="Língua Portuguesa","Matemática","Raciocínio Lógico Matemático","Noções de Informática","Atualidades","Legislação do SUS","Legislação Específica","Conhecimentos Específicos"
IPE,LED,FP="Informática p/ Práticas Educativas","Legislação Educacional","Fundamentos Pedagógicos"
G={
 "Fundamental Incompleto":(dict([(LP,15),(MAT,15)]),12,["AGENTE DE SERVICOS GERAIS","AGENTE DE SERVICOS DE SEGURANCA PATRIMONIAL"]),
 "Fundamental Completo":(dict([(LP,15),(MAT,15),(CE,10)]),16,["AGENTE DE SERVICOS DE CULINARIA","AGENTE DE SERVICOS ELETRICOS","AGENTE DE SERVICOS DE COZINHEIRO ESCOLAR","AGENTE DE SERVICOS DE MONITORIA SOCIAL","AGENTE DE SERVICOS DE MECANICA"]),
 "Médio":(dict([(LP,10),(RLM,10),(INF,10),(CE,20)]),25,["AGENTE DE SERVICOS ADMINISTRATIVOS","AGENTE DE SERVICOS DE CONSULTORIO ODONTOLOGICO","AGENTE DE SERVICOS DE INFORMATICA","AGENTE DE SERVICOS DE AUXILIAR DE SALA","AGENTE DE SERVICOS DE BIBLIOTECA ESCOLAR","AGENTE DE SERVICOS DE VIGILANCIA EPIDEMIOLOGICA","AGENTE DE SERVICOS DE VIGILANCIA SANITARIA","AGENTE DE SERVICOS SOCIAIS","AGENTE DE SERVICOS DE OPERACAO DE TRANSITO E TRANSPORTE","AGENTE DE TRANSITO, TRANSPORTE E RODOVIARIO"]),
 "Técnico":(dict([(LP,10),(RLM,10),(INF,10),(CE,20)]),25,["AGENTE DE SERVICOS TECNICOS AGROPECUARIOS","AGENTE DE SERVICOS TECNICOS AMBIENTAIS","AGENTE DE SERVICOS TECNICOS DE ANALISES CLINICAS","AGENTE DE SERVICOS TECNICOS EM ENFERMAGEM","AGENTE DE SERVICOS TECNICOS EM RADIOLOGIA","AGENTE DE SERVICOS TECNICOS EM OBRAS PUBLICAS"]),
 "Superior – Diversos":(dict([(LP,10),(RLM,10),(ATU,10),(CE,30)]),30,["ANALISTA DE CONTROLE INTERNO","ARQUITETO","AUDITOR AMBIENTAL","EDUCADOR DE TRANSITO","EDUCADOR FISICO","EDUCADOR SOCIAL","ENGENHEIRO AGRONOMO","ENGENHEIRO CIVIL","PEDAGOGO","PSICOLOGO"]),
 "Superior – Saúde":(dict([(LP,10),(RLM,10),(INF,10),(SUS,5),(CE,25)]),30,["ENFERMEIRO","FARMACEUTICO","FISIOTERAPEUTA","MEDICO VETERINARIO","NUTRICIONISTA","NUTRICIONISTA CLINICO","ODONTOLOGO","ODONTOLOGO PSF","BIOMEDICO","PSICOLOGO CLINICO"]),
 "Superior – Assistente Social":(dict([(LP,10),(RLM,10),(INF,10),(LEG,5),(CE,25)]),30,["ASSISTENTE SOCIAL"]),
 "Superior – Educação":(dict([(LP,10),(RLM,6),(IPE,6),(LED,8),(FP,10),(CE,20)]),30,["PROFESSOR DE EDUCACAO INFANTIL","PROFESSOR DE EDUCACAO BASICA","PROFESSOR DE EDUCACAO ESPECIAL","PROFESSOR DE ARTES","PROFESSOR DE CIENCIAS NATURAIS FISICA BIOLOGICA E QUIMICA","PROFESSOR DE EDUCACAO FISICA","PROFESSOR DE GEOGRAFIA","PROFESSOR DE HISTORIA","PROFESSOR DE INGLES","PROFESSOR DE LINGUA PORTUGUESA","PROFESSOR DE MATEMATICA"]),
 "Superior – Procurador":({"Língua Portuguesa":10,"Dir. Administrativo/Urbanístico/Ambiental":12,"Dir. Constitucional/Direitos Humanos":10,"Direito Civil":6,"Direito Processual Civil":6,"Direito Tributário":6,"Dir. Trabalho/Processo do Trabalho/Previdenciário":10},30,["PROCURADOR MUNICIPAL"]),
}
c2g={}
for g,(q,corte,cs) in G.items():
    for c in cs: c2g[key(c)]=g
by=collections.defaultdict(list)
for r in rows: by[key(r["cargo"])].append(r)
res={}; problems=[]
for ck,rs in by.items():
    g=c2g.get(ck); 
    if not g: problems.append(ck); continue
    q,corte,_=G[g]; vag,ins=dem.get(ck,(None,None))
    for r in rs:
        if MAT in q and RLM in r["disc"] and MAT not in r["disc"]:
            r["disc"][MAT]=r["disc"].pop(RLM)
    notas=sorted([r["nota"] for r in rs],reverse=True); tot=sum(q.values())
    for r in rs:
        for d,v in r["disc"].items():
            if d not in q or v>q[d]: problems.append((ck,d,v))
    def pct(sub,d): return 100*st.mean(r["disc"].get(d,0) for r in sub)/q[d]
    border=[r for r in rs if r["nota"]<=corte+2]
    disc={}
    for d,nq in q.items():
        vals=[r["disc"].get(d,0) for r in rs]
        disc[d]=dict(q=nq,acerto=round(pct(rs,d),1),acerto_borda=round(pct(border,d),1) if border else None,
                     abaixo50=round(100*sum(v<nq/2 for v in vals)/len(vals),1),zeros=sum(v==0 for v in vals),
                     notamax=sum(v==nq for v in vals),perda=round(nq-st.mean(vals),2))
    perda_tot=sum(x["perda"] for x in disc.values())
    for x in disc.values(): x["perda_share"]=round(100*x["perda"]/perda_tot,1) if perda_tot else 0
    res[rs[0]["cargo"]]=dict(nivel=g,questoes=tot,corte=corte,vagas=vag,inscritos=ins,aprovados=len(rs),
        pcd=sum(r["sit"]=="Aprovado PcD" for r in rs),
        taxa=round(100*len(rs)/ins,1) if ins else None, aprov_vaga=round(len(rs)/vag,1) if vag else None,
        media=round(st.mean(notas),2),mediana=st.median(notas),max=notas[0],min=notas[-1],dp=round(st.pstdev(notas),2),
        media_pct=round(100*st.mean(notas)/tot,1),
        corte_vagas=notas[vag-1] if vag and len(notas)>=vag else None, n_borda=len(border),disc=disc)
json.dump(res,open(f"{S}/stats.json","w"),ensure_ascii=False,indent=1)
print("problemas:",problems[:10])
print(f"{'cargo':52s} niv  ins  apr  taxa% vag corteV med%  pior disc (acerto%)")
for c,x in sorted(res.items(),key=lambda kv:kv[1]["taxa"] or 0):
    pior=min(x["disc"].items(),key=lambda kv:kv[1]["acerto"])
    print(f"{c[:52]:52s} {x['nivel'][:6]:6s} {x['inscritos']:5d} {x['aprovados']:5d} {x['taxa']:5.1f} {x['vagas']:3d} {str(x['corte_vagas']):>5s} {x['media_pct']:5.1f}  {pior[0][:28]} ({pior[1]['acerto']})")
