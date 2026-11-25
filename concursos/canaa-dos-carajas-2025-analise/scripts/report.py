import json,sys,collections,statistics as st,csv
S,O=sys.argv[1],sys.argv[2]
res=json.load(open(f"{S}/stats.json")); niv=json.load(open(f"{S}/niveis.json"))
mud=json.load(open(f"{S}/mudancas.json")); disc=json.load(open(f"{S}/discursiva.json"))
rows=json.load(open(f"{S}/definitivo.json"))
def br(x,d=1): return (f"{x:,.{d}f}").replace(",","X").replace(".",",").replace("X",".")
def bi(x): return f"{x:,}".replace(",",".")
def tc(s): 
    small={"de","da","do","das","dos","e","em","para","p/"}
    return " ".join(w if (w.lower() in small and i) else w.capitalize() for i,w in enumerate(s.lower().split()))
RAMP=[(0,"#cce3fd"),(35,"#9dc8f7"),(45,"#6aabf1"),(52,"#338ced"),(60,"#2370cd"),(70,"#1757ac"),(85,"#0e3d7e")]
def cell(v):
    if v is None: return '<td class="hm na">—</td>'
    col=[c for t,c in RAMP if v>=t][-1]; fg="#fff" if v>=45 else "#191919"
    return f'<td class="hm" style="background:{col};color:{fg}">{br(v)}%</td>'
def bar(v,mx=100,color="#257de0",w=100):
    return f'<span class="bar"><span style="width:{max(0.5,w*v/mx):.1f}%;background:{color}"></span></span>'
L=[]; A=L.append
T=niv["_total"]
ORDER=["Fundamental Incompleto","Fundamental Completo","Médio","Técnico","Superior – Diversos","Superior – Saúde","Superior – Assistente Social","Superior – Educação","Superior – Procurador"]
# ---------- capa / resumo
A("# Resumo executivo")
A(f"""> **Concurso**: Prefeitura Municipal de Canaã dos Carajás/PA — Edital nº 01/2024 — banca **FGV** — provas objetivas em **23/03, 30/03, 06/04 e 13/04/2025**.
> **Base de dados**: resultado **definitivo** da prova objetiva publicado pela FGV (22/05/2025), com a **nota de cada aprovado em cada disciplina** — {bi(T['aprovados'])} candidatos, 56 cargos —, demanda de candidatos por vaga, gabaritos preliminares e definitivos dos 4 dias e resultados da prova discursiva. Todos os números deste relatório foram **calculados a partir desses arquivos oficiais**.
""")
lv=lambda n: niv[n]
worst=sorted(niv["_familias"].items(),key=lambda kv:kv[1]["acerto"])
A("## Principais conclusões")
A(f"""1. **{bi(T['inscritos'])} inscritos, 556 vagas, {bi(T['aprovados'])} aprovados na objetiva ({br(T['taxa'])}%)**. Ou seja, **{bi(T['inscritos']-T['aprovados'])} candidatos ({br(100-T['taxa'])}%) foram reprovados ou faltaram** — a FGV não publica a abstenção.
2. **Ninguém foi eliminado "por matéria"**: o edital **não tem nota mínima por disciplina** — elimina só pelo total (40% no fundamental, 50% nos demais). Por isso, "a matéria que mais desclassificou" é medida pelos **pontos perdidos** e pelo desempenho de quem passou **raspando o corte** (seção 3).
3. **Raciocínio Lógico/Matemática foi a matéria mais difícil do concurso**: {br(niv['_familias']['Raciocínio Lógico Matemático']['acerto'])}% de acerto médio entre os aprovados que fizeram RLM e só **{br(niv['_familias']['Raciocínio Lógico Matemático']['borda'])}%** entre os que passaram no limite; em **Matemática** (fundamental) quem passou raspando acertou só **{br(niv['_familias']['Matemática']['borda'])}%**. Foi a pior disciplina em **{sum(1 for c,x in res.items() if min(x['disc'],key=lambda d:x['disc'][d]['acerto']) in ('Raciocínio Lógico Matemático','Matemática'))} dos 56 cargos**.
4. **Nível Técnico foi o mais seletivo**: só **{br(lv('Técnico')['taxa'])}%** dos inscritos aprovados — **Técnico em Enfermagem: {res['AGENTE DE SERVIÇOS TÉCNICOS EM ENFERMAGEM']['aprovados']} aprovados para 30 vagas entre {bi(res['AGENTE DE SERVIÇOS TÉCNICOS EM ENFERMAGEM']['inscritos'])} inscritos ({br(res['AGENTE DE SERVIÇOS TÉCNICOS EM ENFERMAGEM']['taxa'])}%)**. O vilão foi **Noções de Informática** ({br(lv('Técnico')['disc']['Noções de Informática']['acerto'])}% de acerto entre os aprovados).
5. **Matérias mais fáceis**: Informática para Práticas Educativas (professores, {br(lv('Superior – Educação')['disc']['Informática p/ Práticas Educativas']['acerto'])}%), Legislação Específica do Assistente Social ({br(lv('Superior – Assistente Social')['disc']['Legislação Específica']['acerto'])}%) e Língua Portuguesa no nível superior (≈ 70%).
6. **Conhecimentos Específicos** é onde os aprovados dos níveis médio, técnico e superior **perdem mais pontos em valor absoluto** (por ter mais questões): de 29% a 45% de todos os pontos perdidos, conforme o nível. No fundamental, quem lidera as perdas é **Matemática** (51% a 60%).
7. **Gabarito**: {sum(1 for o in mud if o['tipo']=='1' and o['tipo_mud']=='anulada')} anulações e {sum(1 for o in mud if o['tipo']=='1' and o['tipo_mud']!='anulada')} alterações de resposta (contando cada prova tipo 1), afetando {len({o['cargo'] for o in mud})} cargos. Os recursos contra o **resultado** não mudaram nenhuma nota (preliminar = definitivo).
""")
# ---------- metodologia
A("# 1. Fontes, método e limitações")
A("""| Arquivo oficial (FGV) | Uso na análise |
|---|---|
| Resultado definitivo da prova objetiva (22/05/2025, 308 p.) | Nota de **cada aprovado por disciplina** — base de todas as estatísticas de acerto |
| Resultado preliminar da prova objetiva (13/05/2025) | Comparação: **nenhuma nota mudou** após os recursos |
| Demanda de candidatos por vaga (09/12/2024) | Inscritos e vagas por cargo → taxa de aprovação |
| Gabaritos preliminares e definitivos (4 dias de prova) | Questões **anuladas** e com **resposta alterada** |
| Habilitados e resultado definitivo da prova discursiva | Eliminação na redação (professores) e na peça (procurador) |
| Edital retificado e os 3 cadernos de prova enviados | Estrutura das provas, critérios de aprovação, ordem das disciplinas |

**Critérios de aprovação (edital, itens 8.2 e 8.3)**: Fundamental Incompleto ≥ 12/30; Fundamental Completo ≥ 16/40; Médio e Técnico ≥ 25/50; Superior ≥ 30/60. **Não há mínimo por disciplina.** Professores e Procurador fazem ainda prova discursiva eliminatória.

**Como ler os indicadores**
- **Acerto médio** (%): média de questões certas na disciplina ÷ nº de questões, **entre os aprovados**.
- **Faixa do corte**: aprovados com nota até **2 pontos acima do mínimo**. São os candidatos mais parecidos com os que foram eliminados — o melhor indicador disponível do que derrubou os reprovados.
- **Pontos perdidos**: questões erradas em média em cada disciplina; a "% dos pontos perdidos" mostra quanto cada matéria pesou na nota que faltou.
- **Taxa de aprovação** = aprovados ÷ inscritos (os inscritos incluem quem faltou, então a taxa real entre presentes é maior).
- **Questões anuladas** valem ponto para todos e já estão nas notas da FGV: elevam um pouco o acerto da disciplina atingida (ex.: 1 das 10 questões de Raciocínio Lógico do nível técnico).

> ⚠️ **Limitação importante**: a FGV publica as notas **apenas dos aprovados**; reprovados consultam o desempenho em link individual. Assim, os percentuais de acerto descrevem quem passou (são maiores que os de todos os candidatos). A comparação **entre disciplinas** e a análise da **faixa do corte** continuam válidas para identificar onde os candidatos erram mais.
""")
# ---------- visão geral por nível
A("# 2. Visão geral por nível")
A("| Nível | Cargos | Vagas | Inscritos | Aprovados | Taxa de aprovação | Reprovados ou ausentes |\n|---|---:|---:|---:|---:|---:|---:|")
for n in ORDER:
    x=niv[n]; A(f"| {n} | {x['cargos']} | {x['vagas']} | {bi(x['inscritos'])} | {bi(x['aprovados'])} | **{br(x['taxa'])}%** {bar(x['taxa'],60)} | {bi(x['inscritos']-x['aprovados'])} |")
A(f"| **Total** | **56** | **556** | **{bi(T['inscritos'])}** | **{bi(T['aprovados'])}** | **{br(T['taxa'])}%** | **{bi(T['inscritos']-T['aprovados'])}** |")
A("""
- O nível **Técnico** (4,0%) e o **Superior – Saúde** (10,8%) foram os mais seletivos; o **Fundamental Incompleto** (51,5%) o menos — corte de apenas 40% e provas só de Português e Matemática.
- Mesmo nos cargos com muitos aprovados, a disputa real é pela **nota de corte das vagas** (seção 4): no Fundamental Incompleto, 5.571 aprovados disputam 210 vagas.
""")
# ---------- disciplinas heatmap
A("# 3. Desempenho por disciplina — onde mais se erra e onde mais se acerta")
A("## 3.1 Mapa de calor: acerto médio dos aprovados (disciplina × nível)")
A("Quanto mais escuro, maior o acerto. Células claras = disciplinas em que os candidatos mais erraram.\n")
cols=["Língua Portuguesa","Matemática","Raciocínio Lógico Matemático","Noções de Informática","Atualidades","Legislação do SUS","Legislação Específica","Legislação Educacional","Informática p/ Práticas Educativas","Fundamentos Pedagógicos","Conhecimentos Específicos"]
short={"Língua Portuguesa":"Português","Matemática":"Matemática","Raciocínio Lógico Matemático":"Rac. Lógico","Noções de Informática":"Informática","Atualidades":"Atualidades","Legislação do SUS":"Leg. SUS","Legislação Específica":"Leg. Específica","Legislação Educacional":"Leg. Educacional","Informática p/ Práticas Educativas":"Info. Práticas Educ.","Fundamentos Pedagógicos":"Fund. Pedagógicos","Conhecimentos Específicos":"Conh. Específicos"}
h='<table class="heat"><thead><tr><th>Nível</th>'+"".join(f"<th>{short[c]}</th>" for c in cols)+"</tr></thead><tbody>"
for n in ORDER:
    if n=="Superior – Procurador": continue
    d=niv[n]["disc"]; h+=f"<tr><th>{n}</th>"+"".join(cell(d[c]["acerto"]) if c in d else '<td class="hm na">—</td>' for c in cols)+"</tr>"
h+="</tbody></table>"
A(h)
A('\n<p class="legend"><span class="sw" style="background:#cce3fd"></span>&lt; 35% <span class="sw" style="background:#9dc8f7"></span>35–45% <span class="sw" style="background:#6aabf1"></span>45–52% <span class="sw" style="background:#338ced"></span>52–60% <span class="sw" style="background:#2370cd"></span>60–70% <span class="sw" style="background:#1757ac"></span>70–85% <span class="sw" style="background:#0e3d7e"></span>≥ 85% · Procurador na seção 3.4.</p>\n')
A("## 3.2 Ranking geral das disciplinas")
A("Média ponderada pelo número de aprovados que fizeram cada disciplina. A coluna **faixa do corte** mostra o acerto de quem passou raspando — o perfil mais próximo de quem foi eliminado.\n")
A("| # | Disciplina | Acerto (todos os aprovados) | Acerto na faixa do corte | Diferença |\n|---:|---|---|---|---:|")
fam={k:v for k,v in niv["_familias"].items() if k!="Direito (Procurador)"}
for i,(f,v) in enumerate(sorted(fam.items(),key=lambda kv:kv[1]["acerto"]),1):
    A(f"| {i} | **{f}** | {br(v['acerto'])}% {bar(v['acerto'],100)} | {br(v['borda'])}% {bar(v['borda'],100,'#f47230')} | {br(v['acerto']-v['borda'])} p.p. |")
A('\n<p class="legend"><span class="sw" style="background:#257de0"></span>Todos os aprovados <span class="sw" style="background:#f47230"></span>Aprovados na faixa do corte (até 2 pontos acima do mínimo)</p>\n')
A(f"""**Leitura**
- **Mais erraram**: **Raciocínio Lógico Matemático** (45%) e, no fundamental, **Matemática** — onde a distância entre a média e a faixa do corte é a **maior de todas** ({br(fam['Matemática']['acerto']-fam['Matemática']['borda'])} pontos percentuais): quem não domina Matemática fica no limite ou é eliminado.
- Em seguida: **Legislação do SUS** (saúde), **Legislação Educacional** (professores) e **Atualidades** (superior diversos) — todas em torno de 50%.
- **Mais acertaram**: **Informática para Práticas Educativas** (97% — 864 dos 1.033 professores aprovados gabaritaram), **Legislação Específica** do Assistente Social (73%) e **Conhecimentos Específicos** em geral (63%).
""")
A("## 3.3 Qual matéria mais \"derrubou\" candidatos em cada nível")
A("Para cada nível: a disciplina com **pior acerto na faixa do corte** e a que concentra a **maior fatia dos pontos perdidos**.\n")
A("| Nível | Pior acerto na faixa do corte | Maior fatia dos pontos perdidos | Melhor desempenho |\n|---|---|---|---|")
for n in ORDER:
    d=niv[n]["disc"]
    pb=min(d.items(),key=lambda kv:kv[1]["borda"] if kv[1]["borda"] is not None else 999)
    pp=max(d.items(),key=lambda kv:kv[1]["perda_share"]); mb=max(d.items(),key=lambda kv:kv[1]["acerto"])
    A(f"| {n} | **{pb[0]}** ({br(pb[1]['borda'])}%) | {pp[0]} ({br(pp[1]['perda_share'])}%) | {mb[0]} ({br(mb[1]['acerto'])}%) |")
A("""
> 💡 **Interpretação**: Conhecimentos Específicos concentra mais pontos perdidos por ter **mais questões** (20 a 30), mas a **taxa de erro** é maior nas matérias básicas — sobretudo **Raciocínio Lógico/Matemática**. Para quem está no limite, ganhar 3 questões de RLM vale o mesmo que 3 de Específicos e costuma ser mais barato de estudar.
""")
A("## 3.4 Procurador Municipal (prova de Direito)")
d=niv["Superior – Procurador"]["disc"]
A("| Disciplina | Questões | Acerto dos aprovados | Faixa do corte | % dos pontos perdidos |\n|---|---:|---|---:|---:|")
qp={"Língua Portuguesa":10,"Dir. Administrativo/Urbanístico/Ambiental":12,"Dir. Constitucional/Direitos Humanos":10,"Direito Civil":6,"Direito Processual Civil":6,"Direito Tributário":6,"Dir. Trabalho/Processo do Trabalho/Previdenciário":10}
for k,v in sorted(d.items(),key=lambda kv:kv[1]["acerto"]):
    A(f"| {k} | {qp[k]} | {br(v['acerto'])}% {bar(v['acerto'])} | {br(v['borda'])}% | {br(v['perda_share'])}% |")
A("\nNo limite do corte, **Constitucional/Direitos Humanos** e **Tributário** (≈ 43%) foram as que mais derrubaram; **Direito Civil** foi a mais tranquila.\n")
# ---------- por cargo
A("# 4. Estatísticas por cargo")
A("## 4.1 Taxa de aprovação na objetiva (aprovados ÷ inscritos)")
mx=max(x["taxa"] for x in res.values())
h='<table class="bars"><tbody>'
for c,x in sorted(res.items(),key=lambda kv:kv[1]["taxa"]):
    h+=f'<tr><td class="lbl">{tc(c)}</td><td class="val">{br(x["taxa"])}%</td><td class="b">{bar(x["taxa"],mx)}</td></tr>'
A(h+"</tbody></table>\n")
A("## 4.2 Tabela completa por cargo")
A("**Corte das vagas** = nota objetiva do candidato na posição igual ao número de vagas (ampla concorrência e PcD juntos, só a objetiva — para professores e procurador a classificação final ainda soma discursiva e títulos).\n")
A("| Cargo | Nível | Vagas | Inscritos | Aprovados | Taxa | Mín. | Corte das vagas | Média | Máx. | Disciplina mais difícil | Disciplina mais fácil |\n|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|")
for n in ORDER:
    for c,x in sorted([(c,x) for c,x in res.items() if x["nivel"]==n],key=lambda kv:kv[1]["taxa"]):
        dd=x["disc"]; lo=min(dd.items(),key=lambda kv:kv[1]["acerto"]); hi=max(dd.items(),key=lambda kv:kv[1]["acerto"])
        A(f"| {tc(c)} | {n.replace('Superior – ','Sup. ')} | {x['vagas']} | {bi(x['inscritos'])} | {x['aprovados']} | {br(x['taxa'])}% | {x['corte']}/{x['questoes']} | **{x['corte_vagas']}** | {br(x['media'],1)} | {x['max']} | {short.get(lo[0],lo[0])} ({br(lo[1]['acerto'],0)}%) | {short.get(hi[0],hi[0])} ({br(hi[1]['acerto'],0)}%) |")
A("""
**Destaques**
- **Mais difíceis de passar**: Técnico em Enfermagem (2,2%), Técnico de Análises Clínicas (3,6%), Técnico Ambiental (3,9%), Biblioteca Escolar (5,2%) e Técnico em Obras Públicas (6,5%).
- **Mais fáceis de passar**: Segurança Patrimonial (54%), Serviços Gerais (48%) e Culinária (41%) — mas com centenas ou milhares de aprovados por vaga.
- **Cortes mais altos das vagas**: Procurador e Odontólogo PSF (52/60), Professor de História (52/60), Odontólogo e Educador Físico (51/60).
""")
# ---------- 3 cargos enviados
A("# 5. Análise detalhada dos 3 cargos das provas enviadas")
by=collections.defaultdict(list)
for r in rows: by[r["cargo"]].append(r)
def detalhe(c, dia, extra):
    x=res[c]; A(f"## {tc(c)}")
    A(f"Prova de **{dia}** · {x['questoes']} questões · aprovação com **{x['corte']} pontos** · **{x['vagas']} vagas** · **{bi(x['inscritos'])} inscritos** · **{x['aprovados']} aprovados** ({br(x['taxa'])}%; {x['pcd']} PcD) · nota média dos aprovados **{br(x['media'],1)}** ({br(x['media_pct'])}%) · máxima **{x['max']}** · **corte das vagas: {x['corte_vagas']}**.\n")
    A("| Disciplina | Questões | Acerto dos aprovados | Acerto na faixa do corte | Aprovados com menos de 50% na disciplina | Zeraram | Gabaritaram |\n|---|---:|---|---:|---:|---:|---:|")
    for k,v in sorted(x["disc"].items(),key=lambda kv:kv[1]["acerto"]):
        A(f"| {k} | {v['q']} | {br(v['acerto'])}% {bar(v['acerto'])} | {br(v['acerto_borda']) if v['acerto_borda'] is not None else '—'}% | {br(v['abaixo50'])}% | {v['zeros']} | {v['notamax']} |")
    cnt=collections.Counter(r["nota"] for r in by[c]); mxn=max(cnt.values())
    h='<table class="hist"><tbody><tr>'
    for nota in range(x["corte"],x["max"]+1):
        v=cnt.get(nota,0); h+=f'<td><div class="col" style="height:{max(1,90*v/mxn):.0f}px" title="{v}"></div><div class="n">{v}</div><div class="x">{nota}</div></td>'
    h+='</tr></tbody></table>'
    A("\n**Distribuição das notas dos aprovados** (eixo: nota; valor acima da barra: nº de candidatos)\n"); A(h)
    A(extra)
mm=[o for o in mud if o["tipo"]=="1"]
def mlist(c):
    k=c.upper()
    import unicodedata,re
    kk=re.sub(r"\s+"," ",re.sub(r"[^A-Z ]"," ",unicodedata.normalize("NFKD",c).encode("ascii","ignore").decode().upper())).replace(" E "," ").strip()
    xs=[o for o in mud if o["cargo"]==kk]
    return "; ".join(f"Q{o['q']} tipo {o['tipo']} ({o['disc']}) — {o['tipo_mud']}" for o in sorted(xs,key=lambda o:(o['tipo'],o['q']))) or "nenhuma"
x=res["AGENTE DE SERVIÇOS ADMINISTRATIVOS"]
detalhe("AGENTE DE SERVIÇOS ADMINISTRATIVOS","13/04/2025 (manhã)",f"""
**Leitura**: o cargo com **mais inscritos** do concurso (6.914; **98,8 candidatos por vaga**). Entre os aprovados, **Informática** ({br(x['disc']['Noções de Informática']['acerto'])}%) e **Raciocínio Lógico** ({br(x['disc']['Raciocínio Lógico Matemático']['acerto'])}%) tiveram o pior acerto, e na faixa do corte o RLM cai para {br(x['disc']['Raciocínio Lógico Matemático']['acerto_borda'])}%. Para ficar nas 70 vagas foi preciso **{x['corte_vagas']}/50** (70%).
**Mudanças de gabarito** (preliminar → definitivo): {mlist('AGENTE DE SERVIÇOS ADMINISTRATIVOS')}.
""")
x=res["AGENTE DE SERVIÇOS TÉCNICOS EM ENFERMAGEM"]
detalhe("AGENTE DE SERVIÇOS TÉCNICOS EM ENFERMAGEM","13/04/2025 (tarde)",f"""
**Leitura**: o cargo **mais seletivo do concurso**: só **{x['aprovados']}** de {bi(x['inscritos'])} inscritos passaram — **menos de 2,5 aprovados por vaga** (30 vagas). **Noções de Informática** foi a grande eliminadora ({br(x['disc']['Noções de Informática']['acerto'])}% de acerto entre os aprovados; **{br(x['disc']['Noções de Informática']['abaixo50'])}% dos aprovados acertaram menos da metade**). O corte das vagas ficou em **{x['corte_vagas']}/50**, colado no mínimo de 25: quase todo aprovado terá chance de convocação.
**Mudanças de gabarito**: {mlist('AGENTE DE SERVIÇOS TÉCNICOS EM ENFERMAGEM')} (a anulação vale ponto para todos).
""")
x=res["PROFESSOR DE EDUCAÇÃO ESPECIAL"]; dd=disc["PROFESSOR DE EDUCAÇÃO ESPECIAL"]
detalhe("PROFESSOR DE EDUCAÇÃO ESPECIAL","30/03/2025 (manhã) — objetiva + redação",f"""
**Leitura**: **Raciocínio Lógico** foi a disciplina mais difícil do cargo — o **3º pior acerto entre todas as combinações cargo × disciplina do concurso**: **{br(x['disc']['Raciocínio Lógico Matemático']['acerto'])}%** de acerto médio (6 questões; **{br(x['disc']['Raciocínio Lógico Matemático']['abaixo50'])}%** dos aprovados acertaram menos de 3 e {x['disc']['Raciocínio Lógico Matemático']['zeros']} zeraram). Em contraste, **Informática para Práticas Educativas** ficou em {br(x['disc']['Informática p/ Práticas Educativas']['acerto'])}%.
**Redação** (20 pontos, mínimo 8): {dd['habilitados']} habilitados à correção, **{dd['aprovados_disc']} aprovados**; nota média {br(dd['media'])}, mínima {br(dd['min'])}, máxima {br(dd['max'])} — a redação **não eliminou ninguém** neste cargo; a eliminação aconteceu na objetiva e no **limite de 30 correções** (só os 20 melhores da ampla concorrência + 10 PcD tiveram a redação corrigida).
**Mudanças de gabarito**: {mlist('PROFESSOR DE EDUCAÇÃO ESPECIAL')}.
""")
# ---------- gabaritos
A("# 6. Anulações e alterações de gabarito")
A("Comparação entre os gabaritos **preliminares** e **definitivos** publicados pela FGV (contando as provas tipo 1; o tipo 2 repete as mesmas questões em outra ordem). A anulação dá o ponto a todos os candidatos; a alteração troca a alternativa correta.\n")
dias=collections.OrderedDict((d,[o for o in mm if o["dia"]==d]) for d in ["23/03","30/03","06/04","13/04"])
A("| Dia | Provas afetadas | Anulações | Alterações | Disciplinas atingidas |\n|---|---:|---:|---:|---|")
for d,xs in dias.items():
    c=collections.Counter(o["disc"] for o in xs)
    A(f"| {d} | {len({o['cargo'] for o in xs})} | {sum(o['tipo_mud']=='anulada' for o in xs)} | {sum(o['tipo_mud']!='anulada' for o in xs)} | {', '.join(f'{k} ({v})' for k,v in c.most_common())} |")
A("""
**Questões comuns que mudaram para muitos cargos de uma vez**
- **23/03 (superior, exceto Educação)**: **Q9 de Língua Portuguesa** teve a resposta trocada de **D para E** em **19 cargos**; Biomédico e Médico Veterinário tiveram ainda a **Q41 anulada**.
- **30/03 (Educação e Pedagogo)**: **3 questões de Fundamentos Pedagógicos (Q31, Q35, Q36)** tiveram a resposta alterada em **todas as 11 provas de professor**.
- **06/04 (médio e Enfermeiro)**: **Q21 de Informática** alterada (E → A) e **Q27 de Informática anulada** nos **9 cargos de nível médio** aplicados nesse dia.
- **13/04 (técnico e Administrativo)**: **Q12 de Raciocínio Lógico anulada** em todos os 6 cargos técnicos; Administrativo teve 3 respostas alteradas (1 de Informática e 2 de Específicos).
> 💡 **Lição**: Informática e Fundamentos Pedagógicos concentraram as falhas de gabarito da FGV neste concurso — vale **sempre** conferir o gabarito preliminar e recorrer.
""")
# ---------- discursiva
A("# 7. Prova discursiva")
A("Professores: redação valendo 20 pontos (aprovação com 8). Procurador: peça prática valendo 40 pontos (aprovação com 20). Só têm a discursiva corrigida os mais bem classificados na objetiva, até o limite do edital.\n")
A("| Cargo | Corrigidas (habilitados) | Aprovados na discursiva | Eliminados | Nota média | Mínima | Máxima |\n|---|---:|---:|---:|---:|---:|---:|")
dd=dict(disc); cn=dd.pop("NATURAIS\\FÍSICA\\BIOLÓGICA E QUÍMICA",None)
if cn: dd["PROFESSOR DE CIÊNCIAS NATURAIS\\FÍSICA\\BIOLÓGICA E QUÍMICA"]["habilitados"]=cn["habilitados"]
for c,v in sorted(dd.items()):
    A(f"| {tc(c)} | {v['habilitados']} | {v['aprovados_disc']} | {v['habilitados']-v['aprovados_disc']} | {br(v['media'],2)} | {br(v['min'],2)} | {br(v['max'],2)} |")
th=sum(v["habilitados"] for v in dd.values()); ta=sum(v["aprovados_disc"] for v in dd.values())
A(f"\n**{th} redações/peças corrigidas, {ta} aprovadas ({br(100*ta/th)}%)**. A discursiva eliminou pouco entre professores; no **Procurador** eliminou **{dd['PROCURADOR MUNICIPAL']['habilitados']-dd['PROCURADOR MUNICIPAL']['aprovados_disc']} de {dd['PROCURADOR MUNICIPAL']['habilitados']}** — a peça prática foi a fase mais dura do cargo. O verdadeiro filtro foi a **objetiva + o limite de correções**.\n")
# ---------- recomendações
A("# 8. O que isso significa para quem vai prestar a próxima prova da FGV")
A("""| Perfil | Prioridade nº 1 | Prioridade nº 2 | Observação |
|---|---|---|---|
| Fundamental | **Matemática** (operações, porcentagem, problemas) | Português (interpretação) | Quem passou raspando acertou só ~31% de Matemática |
| Médio | **Raciocínio Lógico** | Português | Informática foi mais acessível no médio (64%), mas teve questões anuladas/alteradas |
| Técnico | **Noções de Informática** (37% de acerto!) | Português | Específicos foi a parte "fácil" (67%) |
| Superior – Saúde | **Informática** e **Legislação do SUS** | Raciocínio Lógico | Legislação do SUS ≈ 50%: 5 questões fáceis de recuperar com lei seca |
| Superior – Diversos | **Raciocínio Lógico** (39%) | Atualidades | Português foi forte (71%) |
| Professores | **Raciocínio Lógico** (34%) | **Legislação Educacional** (51%) | Informática ≈ 97%: não gaste tempo; treine a redação (mínimo 8/20) |
| Procurador | **Constitucional** e **Tributário** | Processual Civil | Peça prática eliminou 22% dos corrigidos |

**Estratégia FGV que os números confirmam**: (1) não há mínimo por disciplina — **nunca deixe questões em branco**; (2) cada ponto em RLM/Matemática vale o mesmo que em Específicos e é onde está a maior folga de ganho; (3) acompanhe o gabarito preliminar: 49 dos 56 cargos tiveram ao menos uma questão anulada ou alterada.
""")
open(f"{O}/relatorio.md","w",encoding="utf-8").write("\n".join(L)+"\n")
# CSV por cargo
with open(f"{O}/dados/estatisticas_por_cargo.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f,delimiter=";"); allD=sorted({d for x in res.values() for d in x["disc"]})
    w.writerow(["cargo","nivel","vagas","inscritos","aprovados","aprovados_pcd","taxa_aprovacao_%","nota_minima","total_questoes","corte_vagas","media","mediana","maxima","desvio_padrao"]+[f"acerto_%_{d}" for d in allD]+[f"acerto_faixa_corte_%_{d}" for d in allD])
    for c,x in sorted(res.items()):
        w.writerow([c,x["nivel"],x["vagas"],x["inscritos"],x["aprovados"],x["pcd"],x["taxa"],x["corte"],x["questoes"],x["corte_vagas"],x["media"],x["mediana"],x["max"],x["dp"]]+[x["disc"].get(d,{}).get("acerto","") for d in allD]+[x["disc"].get(d,{}).get("acerto_borda","") for d in allD])
with open(f"{O}/dados/mudancas_gabarito.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f,delimiter=";"); w.writerow(["dia","cargo","tipo","nivel","questao","disciplina","mudanca"])
    for o in mud: w.writerow([o["dia"],o["cargo"],o["tipo"],o["nivel"],o["q"],o["disc"],o["tipo_mud"]])
print("ok")
