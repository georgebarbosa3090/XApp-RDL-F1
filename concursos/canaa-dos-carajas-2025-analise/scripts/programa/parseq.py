import sys, re, json
src, out = sys.argv[1], sys.argv[2]
noise = re.compile(r'^(AGENTE ADMINISTRATIVO – MANHÃ|FGV CONHECIMENTO|TIPO .*PÁGINA \d+|PREFEITURA DE CARAGUATATUBA|MUNICÍPIO DE SÃO JOSÉ DOS CAMPOS|Assistente em Gestão Municipal – TARDE|Realiz|zação)$')
sections = ['Língua Portuguesa','Raciocínio Lógico Matemático','Noções de Informática','Aspectos Locais de Caraguatatuba','Conhecimentos Específicos','Atualidades','Conhecimentos Gerais']
L = [l.rstrip() for l in open(src, encoding='utf-8')]
# start at first section
i = next(k for k,l in enumerate(L) if l.strip() in ('Língua Portuguesa','Conhecimentos Gerais'))
qs = {}; cur = None; nxt = 1; sec = None
newpara = re.compile(r'^(I{1,3}V?\.|IV\.|V\.|\( \)|\d+\.\s|Está correto|Estão corret|As afirmativas são|Assinale|Avalie|Com base|Diante|Nessa|Nesse|Sobre|Com relação|Acerca|Disponível)')
for l in L[i:]:
    s = l.strip().replace(' ',' ')
    s = re.sub(r'^[•]\s*', '', s)
    if not s or noise.match(s): continue
    if s in sections or s.startswith('Conhecimentos Específicos'):
        sec = s; continue
    if re.fullmatch(r'\d{1,2}', s) and int(s) == nxt:
        cur = {'n': nxt, 'sec': sec, 'stem': [], 'opts': {}, 'last': None}; qs[nxt] = cur; nxt += 1; continue
    if cur is None: continue
    m = re.match(r'^\(([A-E])\)\s*(.*)', s)
    if m:
        cur['opts'][m.group(1)] = m.group(2); cur['last'] = m.group(1); continue
    if cur['last']:
        cur['opts'][cur['last']] += ' ' + s; continue
    if cur['stem'] and not newpara.match(s) and not re.search(r'[.?:;]$', cur['stem'][-1]):
        cur['stem'][-1] += ' ' + s
    else:
        cur['stem'].append(s)
for q in qs.values(): q.pop('last')
json.dump(qs, open(out,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(qs), 'questões')
