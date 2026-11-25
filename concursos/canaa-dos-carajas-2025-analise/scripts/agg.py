import json,sys,collections
S=sys.argv[1]; res=json.load(open(f"{S}/stats.json"))
lv=collections.defaultdict(lambda: dict(ins=0,apr=0,vag=0,cargos=0,disc=collections.defaultdict(lambda:[0,0,0,0,0])))
# disc acc: [soma acerto*apr, apr, soma acerto_borda*nb, nb, soma perda_share*apr]
for c,x in res.items():
    L=lv[x["nivel"]]; L["ins"]+=x["inscritos"]; L["apr"]+=x["aprovados"]; L["vag"]+=x["vagas"]; L["cargos"]+=1
    for d,v in x["disc"].items():
        a=L["disc"][d]; a[0]+=v["acerto"]*x["aprovados"]; a[1]+=x["aprovados"]
        if v["acerto_borda"] is not None: a[2]+=v["acerto_borda"]*x["n_borda"]; a[3]+=x["n_borda"]
        a[4]+=v["perda_share"]*x["aprovados"]
out={}
tot_ins=sum(L["ins"] for L in lv.values()); tot_apr=sum(L["apr"] for L in lv.values())
print(f"TOTAL: inscritos {tot_ins} aprovados {tot_apr} ({100*tot_apr/tot_ins:.1f}%)\n")
for n,L in lv.items():
    print(f"== {n}: cargos {L['cargos']} vagas {L['vag']} inscritos {L['ins']} aprovados {L['apr']} taxa {100*L['apr']/L['ins']:.1f}%")
    ds={d:dict(acerto=round(a[0]/a[1],1),borda=round(a[2]/a[3],1) if a[3] else None,perda_share=round(a[4]/a[1],1)) for d,a in L["disc"].items()}
    for d,v in sorted(ds.items(),key=lambda kv:kv[1]["acerto"]): print(f"   {d:52s} acerto {v['acerto']:5.1f}% | faixa do corte {v['borda']}% | {v['perda_share']}% dos pontos perdidos")
    out[n]=dict(cargos=L["cargos"],vagas=L["vag"],inscritos=L["ins"],aprovados=L["apr"],taxa=round(100*L["apr"]/L["ins"],1),disc=ds)
# overall per discipline family
fam=collections.defaultdict(lambda:[0,0,0,0])
for c,x in res.items():
    for d,v in x["disc"].items():
        f=d if not d.startswith("Dir") and d!="Direito Civil" and not d.startswith("Direito") else "Direito (Procurador)"
        fam[f][0]+=v["acerto"]*x["aprovados"]; fam[f][1]+=x["aprovados"]
        if v["acerto_borda"] is not None: fam[f][2]+=v["acerto_borda"]*x["n_borda"]; fam[f][3]+=x["n_borda"]
print("\n== GERAL por disciplina (todos os aprovados)")
for f,a in sorted(fam.items(),key=lambda kv:kv[1][0]/kv[1][1]): print(f"   {f:40s} {a[0]/a[1]:5.1f}% (n={a[1]}) | faixa do corte {a[2]/a[3] if a[3] else float('nan'):5.1f}% (n={a[3]})")
out["_familias"]={f:dict(acerto=round(a[0]/a[1],1),n=a[1],borda=round(a[2]/a[3],1) if a[3] else None,nb=a[3]) for f,a in fam.items()}
out["_total"]=dict(inscritos=tot_ins,aprovados=tot_apr,taxa=round(100*tot_apr/tot_ins,1))
json.dump(out,open(f"{S}/niveis.json","w"),ensure_ascii=False,indent=1)
