import json, sys, re
sys.path.insert(0, '.')
from coments import CARAG, SJC, CARAG_KEY, SJC_KEY
OUT = sys.argv[1]
c = json.load(open('carag.json', encoding='utf-8')); s = json.load(open('sjc.json', encoding='utf-8'))
def clean(t): return re.sub(r'\s+', ' ', t.replace('', '')).strip()
s['25']['opts'] = {'A': '1/6.', 'B': '1/5.', 'C': '1/4.', 'D': '1/3.', 'E': '1/2.'}
s['20']['stem'] = [s['20']['stem'][0], '\n| Linha | Letras | Algarismos |\n|:-:|:-:|:-:|\n| (início) | PRESJC | 2025 |\n| 1) | RESJCP | 0252 |\n| 2) | ESJCPR | 2520 |\n| 3) | SJCPRE | 5202 |\n| 4) | … | … |\n', s['20']['stem'][2]]
st = c['13']['stem']; c['13']['stem'] = [st[0], '\n- ' + st[1] + '\n- ' + st[2] + ' ' + st[3] + '\n- ' + st[4] + '\n', st[5]]
c['21']['stem'] = ['(questão com figura — excluída)']
def render(q, n):
    out = [f'**{n}.** ' + '  \n'.join(clean(x) if not x.startswith('\n') else x for x in q['stem'])]
    # parágrafos com tabela/lista precisam de linha em branco
    body = out[0].replace('  \n\n', '\n\n').replace('\n  \n', '\n\n')
    opts = '  \n'.join(f'({k}) {clean(v)}' for k, v in sorted(q['opts'].items()))
    return body + '\n\n' + opts + '\n'
def simulado(title, intro, data, key, com, blocos, orig):
    md = [f'# {title}\n', intro, '\n']
    n = 0; mapa = []
    for nome, nums in blocos:
        md.append(f'\n## {nome}\n')
        for q in nums:
            n += 1; mapa.append((n, q, nome))
            md.append(render(data[str(q)], n)); md.append('')
    md.append('\n## Folha de respostas\n')
    rows = []
    for i in range(0, n, 10):
        rows.append('| ' + ' | '.join(str(k) for k in range(i+1, min(i+11, n+1))) + ' |')
        rows.append('|' + ':-:|' * (min(i+11, n+1) - (i+1)))
        rows.append('| ' + ' | '.join('&nbsp;' for _ in range(i+1, min(i+11, n+1))) + ' |\n')
    md.append('\n'.join(rows))
    md.append(f'\n## Gabarito comentado — {title}\n')
    md.append('| Nº | ' + orig + ' | Tema | Gab. | Resolução |\n|-:|:-:|---------|:-:|------------------------------|')
    for (k, q, nome) in mapa:
        t, txt = com[q]
        md.append(f'| {k} | {q} | {t} | **{key[q-1]}** | {txt} |')
    # desempenho por bloco
    md.append('\n### Anote seu desempenho\n')
    md.append('| Disciplina | Questões | Acertos | % | Meta |\n|---|:-:|:-:|:-:|:-:|')
    k0 = 1
    for nome, nums in blocos:
        md.append(f'| {nome} | {k0}–{k0+len(nums)-1} | | | ≥ 70% |'); k0 += len(nums)
    md.append(f'| **Total** | **{n}** | | | **≥ 70%** |')
    return '\n'.join(md) + '\n', n
intro1 = ('> **Prova real da FGV**: Prefeitura de Caraguatatuba (SP), Edital 03/2023, cargo **Agente Administrativo**, nível médio, aplicada em 14/01/2024 (caderno tipo 4, azul). Gabarito **definitivo** da FGV.\n'
          '> Excluídas: a Q21 (Excel com figura, que não sai legível no texto extraído) e as Q27–30 (Aspectos Locais de Caraguatatuba). Restam **45 questões** → faça em **2 h 40 min** (≈ 3,5 min por questão), sem consulta.\n'
          '> A numeração original aparece na coluna "Orig." do gabarito.')
intro2 = ('> **Prova real da FGV**: Município de São José dos Campos (SP), cargo **Assistente em Gestão Municipal**, nível médio, aplicada em 31/08/2025 (caderno tipo 1, branca). Gabarito **definitivo** da FGV (a Q47 foi anulada e ficou de fora).\n'
          '> Montado no **formato da prova de Canaã** (≈ 10 LP + 10 RLM + 10 Info + 20 CE): **50 questões** → faça em **3 h**. Saíram as questões de Atualidades (31–35) e 4 de Português (9, 11, 12 e 14), que estão como exercícios no módulo de Português.\n'
          '> As questões de informática que a prova original trazia nos Específicos (46, 48–50) foram agrupadas em Informática.')
b1 = [('Língua Portuguesa', list(range(1, 11))), ('Raciocínio Lógico Matemático', list(range(11, 19))),
      ('Noções de Informática', [19, 20, 22, 23, 24, 25, 26]), ('Conhecimentos Específicos', list(range(31, 51)))]
b2 = [('Língua Portuguesa', [1, 2, 3, 4, 5, 6, 7, 8, 10, 13, 15]), ('Raciocínio Lógico Matemático', list(range(16, 26))),
      ('Noções de Informática', [26, 27, 28, 29, 30, 46, 48, 49, 50]), ('Conhecimentos Específicos', list(range(36, 46)) + list(range(51, 61)))]
m1, n1 = simulado('Simulado 1 — FGV Caraguatatuba 2024 (Agente Administrativo)', intro1, c, CARAG_KEY, CARAG, b1, 'Orig.')
m2, n2 = simulado('Simulado 2 — FGV São José dos Campos 2025 (Assistente em Gestão Municipal)', intro2, s, SJC_KEY, SJC, b2, 'Orig.')
open(OUT + '/05-simulado-1-caraguatatuba.md', 'w', encoding='utf-8').write(m1)
open(OUT + '/06-simulado-2-sao-jose-dos-campos.md', 'w', encoding='utf-8').write(m2)
# extras de português (SJC 9, 11, 12, 14)
ex = ['\n### Questões extras FGV (SJC 2025) — treine agora\n']
for i, q in enumerate([9, 11, 12, 14], 1):
    ex.append(render(s[str(q)], f'E{i}'))
ex.append('\n**Gabarito:** ' + '; '.join(f'E{i} – **{SJC_KEY[q-1]}** ({SJC[q][1]})' for i, q in enumerate([9, 11, 12, 14], 1)) + '\n')
open(OUT + '/_extras_lp.md', 'w', encoding='utf-8').write('\n'.join(ex))
print(n1, n2)
