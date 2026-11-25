import re, sys, json
GEN = [("Port.","Língua Portuguesa"),("Matemática","Matemática"),("Lóg. Mat.","Raciocínio Lógico Matemático"),
       ("de Info.","Noções de Informática"),("Atualidades","Atualidades"),("do SUS","Legislação do SUS"),
       ("Específica","Legislação Específica"),("Educativas","Informática p/ Práticas Educativas"),
       ("Educacional","Legislação Educacional"),("Pedagógicos","Fundamentos Pedagógicos"),
       ("do Cargo","Conhecimentos Específicos"),("Objetiva","NOTA")]
PROC = [("Portuguesa","Língua Portuguesa"),("Urban/ Ambiental","Dir. Administrativo/Urbanístico/Ambiental"),
        ("Direitos Humanos","Dir. Constitucional/Direitos Humanos"),("Civil","Direito Civil"),
        ("Processual Civil","Direito Processual Civil"),("Tributário","Direito Tributário"),
        ("Trabalho/Direito Previdenciário","Dir. Trabalho/Processo do Trabalho/Previdenciário"),("Objetiva","NOTA")]
def cols(line, spec):
    out=[]; pos=0
    for lab,name in spec:
        i=line.find(lab,pos)
        if i<0: return None
        out.append((i+len(lab)/2, name)); pos=i+len(lab)
    return out
rows=[]; cargo=None; colmap=None; bad=0
rx=re.compile(r"^(\d{9})\s+(.*?)\s+(\d{2}/\d{2}/\d{4})(.*)$")
for raw in open(sys.argv[1],encoding="utf-8"):
    line=raw.rstrip("\n")
    s=line.strip()
    if s and re.fullmatch(r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇ ,/()\\–-]{6,}",s) and not s.startswith("CONCURSO") and "RESULTADO" not in s and "EDITAL" not in s:
        cargo=s; continue
    if s.startswith("Inscrição"):
        colmap = cols(line,PROC) if "Previdenciário" in line else cols(line,GEN)
        continue
    m=rx.match(line)
    if not m or not colmap: continue
    insc,nome,nasc,rest=m.groups()
    off=len(line)-len(rest)
    sit = "Aprovado PcD" if "PcD" in rest else ("Aprovado" if "Aprovado" in rest else "?")
    vals={}
    for t in re.finditer(r"\d+",rest):
        c=off+t.start()+len(t.group())/2
        name=min(colmap,key=lambda x:abs(x[0]-c))[1]
        if name in vals: bad+=1
        vals[name]=int(t.group())
    nota=vals.pop("NOTA",None)
    ok = nota is not None and sum(vals.values())==nota
    if not ok: bad+=1
    rows.append(dict(cargo=cargo,insc=insc,nasc=nasc,sit=sit,nota=nota,disc=vals,ok=ok))
json.dump(rows,open(sys.argv[2],"w",encoding="utf-8"),ensure_ascii=False)
print("linhas:",len(rows),"inconsistentes:",sum(not r["ok"] for r in rows),"colisões:",bad)
for r in rows:
    if not r["ok"]: print("X",r); break
