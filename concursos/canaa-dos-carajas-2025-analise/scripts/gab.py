import re,sys,json,unicodedata
def norm(t):
    t=unicodedata.normalize("NFKD",t).encode("ascii","ignore").decode().upper()
    t=t.replace("PROVA","").replace("TIPO","")
    m=re.search(r"(\d)\s*$",t); tipo=m.group(1) if m else "1"
    t=re.sub(r"[-–]\s*\d\s*$","",t); t=re.sub(r"\d\s*$","",t)
    t=re.sub(r"[^A-Z ]"," ",t); t=re.sub(r"\bE\b"," ",t); t=re.sub(r"\s+"," ",t).strip()
    return f"{t}|{tipo}"
SKIP=("CONCURSO","GABARITO","VAGAS","MUNICIPAL DE","QUESTAO ANULADA","PAGINA","WWW","PCIMARK","DE VAGAS","APLICADA","CARAJAS/PA","13/04","06/04","30/03","23/03")
def parse(path):
    blocks={}; cur=None; nums=None
    for raw in open(path,encoding="utf-8"):
        s=raw.strip()
        if not s: continue
        toks=s.split()
        if all(t.isdigit() for t in toks): nums=[int(t) for t in toks]; continue
        if nums and all(re.fullmatch(r"[A-Ea-e*]",t) for t in toks) and len(toks)==len(nums):
            for n,a in zip(nums,toks): blocks[cur][n]=a.upper()
            nums=None; continue
        a=unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().upper()
        if any(k in a for k in SKIP) or len(re.findall(r"[A-Za-z]{3,}",s))<2: continue
        cur=norm(s); blocks.setdefault(cur,{})
    return blocks
pre=parse(sys.argv[1]); de=parse(sys.argv[2])
res=[]
for k in de:
    if k not in pre: print("sem par:",k); continue
    an=[n for n,a in de[k].items() if a=="*"]
    alt=[(n,pre[k].get(n),a) for n,a in de[k].items() if a!="*" and pre[k].get(n)!=a]
    res.append(dict(prova=k,questoes=len(de[k]),anuladas=sorted(an),alteradas=sorted(alt)))
json.dump(res,open(sys.argv[3],"w"),ensure_ascii=False)
for r in res: 
    if r["anuladas"] or r["alteradas"]: print(r["prova"],"| Q:",r["questoes"],"| anuladas:",r["anuladas"],"| alteradas:",r["alteradas"])
print("provas:",len(res),"| total anuladas:",sum(len(r["anuladas"]) for r in res),"| total alteradas:",sum(len(r["alteradas"]) for r in res))
