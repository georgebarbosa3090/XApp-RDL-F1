import json,sys,re,unicodedata,collections
S=sys.argv[1]
def k(s):
    s=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().upper()
    s=re.sub(r"[^A-Z ]"," ",s); s=re.sub(r"\bE\b"," ",s); return re.sub(r"\s+"," ",s).strip()
res=json.load(open(f"{S}/stats.json"))
lvl={k(c):x["nivel"] for c,x in res.items()}
B={"Médio":[(10,"Língua Portuguesa"),(20,"Raciocínio Lógico Matemático"),(30,"Noções de Informática"),(50,"Conhecimentos Específicos")],
   "Técnico":[(10,"Língua Portuguesa"),(20,"Raciocínio Lógico Matemático"),(30,"Noções de Informática"),(50,"Conhecimentos Específicos")],
   "Fundamental Incompleto":[(15,"Língua Portuguesa"),(30,"Matemática")],
   "Fundamental Completo":[(15,"Língua Portuguesa"),(30,"Matemática"),(40,"Conhecimentos Específicos")],
   "Superior – Diversos":[(10,"Língua Portuguesa"),(20,"Raciocínio Lógico Matemático"),(30,"Atualidades"),(60,"Conhecimentos Específicos")],
   "Superior – Saúde":[(10,"Língua Portuguesa"),(20,"Raciocínio Lógico Matemático"),(30,"Noções de Informática"),(35,"Legislação do SUS"),(60,"Conhecimentos Específicos")],
   "Superior – Assistente Social":[(10,"Língua Portuguesa"),(20,"Raciocínio Lógico Matemático"),(30,"Noções de Informática"),(35,"Legislação Específica"),(60,"Conhecimentos Específicos")],
   "Superior – Educação":[(10,"Língua Portuguesa"),(16,"Raciocínio Lógico Matemático"),(22,"Informática p/ Práticas Educativas"),(30,"Legislação Educacional"),(40,"Fundamentos Pedagógicos"),(60,"Conhecimentos Específicos")],
   "Superior – Procurador":[(10,"Língua Portuguesa"),(22,"Dir. Administrativo"),(32,"Dir. Constitucional"),(38,"Direito Civil"),(44,"Proc. Civil"),(50,"Tributário"),(60,"Trabalho/Previdenciário")]}
def disc(level,n):
    for lim,name in B[level]:
        if n<=lim: return name
out=[]; dias={"d1":"23/03","d2":"30/03","d3":"06/04","d4":"13/04"}
for d,data in dias.items():
    for r in json.load(open(f"{S}/gab_{d}.json")):
        cargo,tipo=r["prova"].split("|")
        L=lvl.get(cargo)
        if not L: print("sem nível:",cargo); continue
        for n in r["anuladas"]: out.append(dict(dia=data,cargo=cargo,tipo=tipo,nivel=L,q=n,tipo_mud="anulada",disc=disc(L,n)))
        for n,a,b in r["alteradas"]: out.append(dict(dia=data,cargo=cargo,tipo=tipo,nivel=L,q=n,tipo_mud=f"alterada {a}→{b}",disc=disc(L,n)))
json.dump(out,open(f"{S}/mudancas.json","w"),ensure_ascii=False,indent=0)
t1=[o for o in out if o["tipo"]=="1"]
print("ocorrências (só tipo 1, evita duplicar tipo 2):",len(t1),"| anuladas",sum(o["tipo_mud"]=="anulada" for o in t1),"| alteradas",sum(o["tipo_mud"]!="anulada" for o in t1))
c=collections.Counter(o["disc"] for o in t1); print(c.most_common())
print("cargos com alguma mudança (tipo 1):",len({o['cargo'] for o in t1}))
