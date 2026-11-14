#!/usr/bin/env python3
"""Gera o relatório em PDF (A4 paisagem) a partir do CSV de parse_receipts.py.

Uso:
    python3 -I build_report.py <corridas.csv> <saida.pdf> [--card 4251]
        [--fatura fatura.json] [--marca AUREA] [--csv-saida conferido.csv]
        [--fonte "62 e-mails do Gmail em 14/11/2026"]

fatura.json (opcional) = lista dos lançamentos de CORRIDA da 99 lidos da fatura
ou das capturas do app do cartão (ignore 99Food e outras lojas):
    {"cobertura": "01/11 21:51 a 13/11 21:19",
     "lancamentos": [{"data": "12/11/2026", "hora": "08:59",
                      "descricao": "PG *99 L2L 99 RIDE", "valor": "5,70"}, ...]}
Cada lançamento é casado com uma corrida de mesma data e mesmo valor; as
casadas recebem a marca (padrão "AUREA ✓", fundo dourado). Lançamentos sem
recibo e recibos do período coberto sem lançamento são sinalizados.
"""
import argparse
import collections
import csv
import datetime
import json

from reportlab.lib import colors
from reportlab.lib.fonts import addMapping
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

FONT_DIR = '/usr/share/fonts/truetype/dejavu/'
try:
    pdfmetrics.registerFont(TTFont('DV', FONT_DIR + 'DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DVB', FONT_DIR + 'DejaVuSans-Bold.ttf'))
    addMapping('DV', 0, 0, 'DV'); addMapping('DV', 1, 0, 'DVB')
    F, FB = 'DV', 'DVB'
except Exception:  # noqa: BLE001 — sem DejaVu, cai para Helvetica (sem ✓/→)
    F, FB = 'Helvetica', 'Helvetica-Bold'

INK = colors.HexColor('#1f2937'); MUT = colors.HexColor('#6b7280'); ACC = colors.HexColor('#1d4ed8')
GRID = colors.HexColor('#d1d5db'); HBG = colors.HexColor('#eef2ff')
RBG = colors.HexColor('#fee2e2'); RED = colors.HexColor('#b91c1c')
GBG = colors.HexColor('#fef3c7'); GOLD = colors.HexColor('#fcd34d'); GINK = colors.HexColor('#78350f')
MN = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out',
      11: 'Nov', 12: 'Dez'}

def v(r): return float(r['Valor (R$)'].replace('.', '').replace(',', '.'))
def brl(x): return 'R$ ' + f'{x:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
def dt(r): return datetime.datetime.strptime(r['Data'] + ' ' + (r['Início'] or '00:00'), '%d/%m/%Y %H:%M')

H1 = ParagraphStyle('h1', fontName=FB, fontSize=17, leading=21, textColor=INK, spaceAfter=2)
SUB = ParagraphStyle('sub', fontName=F, fontSize=9, leading=12, textColor=MUT, spaceAfter=10)
H2 = ParagraphStyle('h2', fontName=FB, fontSize=12, leading=15, textColor=INK, spaceBefore=10, spaceAfter=5)
B = ParagraphStyle('b', fontName=F, fontSize=9, leading=12.5, textColor=INK)
RB = ParagraphStyle('rb', parent=B, textColor=colors.HexColor('#7f1d1d'))
C = ParagraphStyle('c', fontName=F, fontSize=7, leading=8.6, textColor=INK)

def tbl(data, widths, right=(), fs=8.5, total=False, red=(), gold=()):
    t = Table(data, colWidths=widths, repeatRows=1)
    st = [('FONT', (0, 0), (-1, -1), F, fs), ('TEXTCOLOR', (0, 0), (-1, -1), INK),
          ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), ('LINEBELOW', (0, 0), (-1, -1), 0.4, GRID),
          ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
          ('FONT', (0, 0), (-1, 0), FB, fs), ('BACKGROUND', (0, 0), (-1, 0), HBG),
          ('LINEBELOW', (0, 0), (-1, 0), 0.8, ACC)]
    st += [('ALIGN', (c, 0), (c, -1), 'RIGHT') for c in right]
    st += [('BACKGROUND', (0, r), (-1, r), RBG) for r in red]
    for r in gold:
        st += [('BACKGROUND', (0, r), (-1, r), GBG), ('LINEBEFORE', (0, r), (0, r), 3, GOLD)]
    if total:
        st += [('FONT', (0, -1), (-1, -1), FB, fs), ('LINEABOVE', (0, -1), (-1, -1), 0.8, INK)]
    t.setStyle(TableStyle(st)); return t

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv'); ap.add_argument('pdf')
    ap.add_argument('--card', default=''); ap.add_argument('--fatura'); ap.add_argument('--marca', default='AUREA')
    ap.add_argument('--csv-saida'); ap.add_argument('--fonte', default='')
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.csv, encoding='utf-8-sig'), delimiter=';'))
    rows.sort(key=dt)
    card = f' final {a.card}' if a.card else ''
    main_ = [r for r in rows if not r['Alerta']]
    other = [r for r in rows if r['Alerta']]
    MK = f'{a.marca} ✓'

    # ---- conferência com fatura
    fat, conf, semrec, cob = [], {}, [], ''
    if a.fatura:
        fj = json.load(open(a.fatura))
        fat = fj['lancamentos'] if isinstance(fj, dict) else fj
        cob = fj.get('cobertura', '') if isinstance(fj, dict) else ''
        for l in fat:
            m = [r for r in rows if r['Data'] == l['data'] and r['Valor (R$)'] == l['valor'] and r['#'] not in conf]
            if m:
                conf[m[0]['#']] = l
            else:
                semrec.append(l)
    aur = [r for r in rows if r['#'] in conf]
    nolanc = []
    if fat:
        lo = min(datetime.datetime.strptime(l['data'] + ' ' + l['hora'], '%d/%m/%Y %H:%M') for l in fat)
        hi = max(datetime.datetime.strptime(l['data'] + ' ' + l['hora'], '%d/%m/%Y %H:%M') for l in fat)
        nolanc = [r for r in main_ if r['#'] not in conf and lo - datetime.timedelta(minutes=40) <= dt(r) <= hi]

    if a.csv_saida:
        with open(a.csv_saida, 'w', newline='', encoding='utf-8-sig') as fh:
            w = csv.writer(fh, delimiter=';'); hd = list(rows[0].keys()) + [f'Conferência fatura{card}']
            w.writerow(hd)
            for r in rows:
                l = conf.get(r['#'])
                w.writerow(list(r.values()) + [f"{MK} confirmado – lançamento {l['data'][:5]} {l['hora']} {l['descricao']}" if l else
                                               ('SEM LANÇAMENTO NA FATURA' if r in nolanc else '')])
            for l in semrec:
                w.writerow([''] * len(rows[0]) + [f"LANÇAMENTO SEM RECIBO: {l['data']} {l['hora']} {l['descricao']} R$ {l['valor']}"])

    doc = SimpleDocTemplate(a.pdf, pagesize=landscape(A4), leftMargin=14 * mm, rightMargin=14 * mm,
                            topMargin=10 * mm, bottomMargin=13 * mm, title=f'Relatório de corridas 99 – cartão{card}')
    W = doc.width; s = []
    s.append(Paragraph(f'Relatório de corridas 99 – Cartão de crédito{card}', H1))
    s.append(Paragraph(f'Período: {rows[0]["Data"]} a {rows[-1]["Data"]} · {len(rows)} recibos únicos' +
                       (f' · Fonte: {a.fonte}' if a.fonte else ''), SUB))
    hdr = ['Corridas', 'Valor total', f'No cartão principal{card}', 'Outro meio / outro cartão']
    val = [str(len(rows)), brl(sum(map(v, rows))), f'{len(main_)}  ·  {brl(sum(map(v, main_)))}',
           f'{len(other)}  ·  {brl(sum(map(v, other)))}']
    if fat:
        hdr.append(f'{MK} confirmadas'); val.append(f'{len(aur)}  ·  {brl(sum(map(v, aur)))}')
    ws = [0.12, 0.18, 0.25, 0.22, 0.23] if len(hdr) == 5 else [0.15, 0.22, 0.33, 0.30]
    kt = Table([hdr, val], colWidths=[W * x for x in ws])
    ks = [('FONT', (0, 0), (-1, 0), F, 8), ('TEXTCOLOR', (0, 0), (-1, 0), MUT), ('FONT', (0, 1), (-1, 1), FB, 14),
          ('TEXTCOLOR', (3, 1), (3, 1), RED if other else INK), ('BOX', (0, 0), (-1, -1), 0.6, GRID),
          ('LINEAFTER', (0, 0), (-2, 1), 0.6, GRID), ('TOPPADDING', (0, 0), (-1, -1), 6),
          ('BOTTOMPADDING', (0, 1), (-1, 1), 9), ('LEFTPADDING', (0, 0), (-1, -1), 9)]
    if fat:
        ks += [('BACKGROUND', (4, 0), (4, 1), GBG), ('TEXTCOLOR', (4, 1), (4, 1), GINK)]
    kt.setStyle(TableStyle(ks)); s += [kt, Spacer(1, 8)]
    brands = {h for r in main_ for h in r['Logo'].split()}
    note = ('<b>Importante:</b> os recibos da 99 não mostram os dígitos do cartão, só “Cartão de Crédito/Débito” e o '
            f'logo da bandeira. Os {len(main_)} recibos no cartão principal têm '
            + ('o <b>mesmo logo</b> (imagem idêntica), compatível com um único cartão.' if len(brands) == 1 else
               f'<b>{len(brands)} logos diferentes</b> – pode haver mais de um cartão.'))
    if fat:
        note += f' <b>Conferência com a fatura:</b> {len(aur)} corridas confirmadas no cartão{card}, marcadas como <b>{MK}</b>.'
    else:
        note += f' Para confirmar o cartão{card}, envie a fatura ou capturas do app do cartão.'
    nt = Table([[Paragraph(note, RB)]], colWidths=[W])
    nt.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), RBG), ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#f87171')),
                            ('LEFTPADDING', (0, 0), (-1, -1), 8), ('TOPPADDING', (0, 0), (-1, -1), 6),
                            ('BOTTOMPADDING', (0, 0), (-1, -1), 6)]))
    s.append(nt)

    if other:
        s.append(Paragraph(f'⚠ Corridas pagas com outro meio ou outro cartão (não o cartão{card})', H2))
        d = [['Data', 'Hora', 'Categoria', 'Cidade', 'Origem → Destino', 'Pagamento', 'Valor']]
        d += [[r['Data'], r['Início'], r['Categoria'], r['Cidade'], Paragraph(f"{r['Origem']} → {r['Destino']}", C),
               Paragraph(r['Pagamento'], C), brl(v(r))] for r in other]
        d += [['', '', '', '', '', 'Total', brl(sum(map(v, other)))]]
        s.append(tbl(d, [20 * mm, 14 * mm, 20 * mm, 22 * mm, W - 158 * mm, 46 * mm, 24 * mm], right=(6,), total=True,
                     red=range(1, len(other) + 1)))
        s += [Spacer(1, 4), Paragraph(f'Janela do outro meio: <b>{other[0]["Data"]} {other[0]["Início"]}</b> a '
                                      f'<b>{other[-1]["Data"]} {other[-1]["Início"]}</b>.', B)]
    else:
        s.append(Paragraph('✓ Nenhuma corrida paga com outro meio: todas usaram o mesmo cartão.', H2))

    if fat:
        s.append(Paragraph(f'★ Conferência com a fatura{card} – marcação {a.marca}', H2))
        s.append(Paragraph(f'Lançamentos de corrida 99 lidos da fatura{(" (" + cob + ")") if cob else ""}, comparados com os recibos pela data e pelo valor.', B))
        s.append(Spacer(1, 4))
        fd = [['Fatura (data/hora)', 'Descrição', 'Valor', 'Corrida (recibo)', 'Trajeto', 'Status']]; gr = []; rr = []
        for l in fat:
            m = [r for r in aur if conf[r['#']] is l]
            if m:
                r = m[0]; fd.append([f"{l['data'][:5]} {l['hora']}", l['descricao'], 'R$ ' + l['valor'],
                                     f"#{r['#']} · {r['Início']}–{r['Fim']}", Paragraph(f"{r['Origem']} → {r['Destino']}", C),
                                     f'{MK} confirmado']); gr.append(len(fd) - 1)
            else:
                fd.append([f"{l['data'][:5]} {l['hora']}", l['descricao'], 'R$ ' + l['valor'], '—',
                           Paragraph('Nenhum recibo 99 com essa data e valor', C), '⚠ SEM RECIBO']); rr.append(len(fd) - 1)
        fd.append(['', '', '', '', f'Confirmado {a.marca}', brl(sum(map(v, aur)))])
        s.append(tbl(fd, [35 * mm, 36 * mm, 20 * mm, 34 * mm, W - 165 * mm, 40 * mm], right=(2,), total=True, gold=gr, red=rr))
        msg = f'<b>Resultado:</b> {len(aur)} de {len(fat)} lançamentos batem com recibos.'
        if semrec:
            msg += ' <b>Lançamentos sem recibo:</b> ' + '; '.join(f"{l['data'][:5]} {l['hora']} {l['descricao']} R$ {l['valor']}" for l in semrec) + \
                   ' – confira no app da 99 (Histórico de corridas); pode ser corrida cujo recibo não veio por e-mail.'
        if nolanc:
            msg += ' <b>Recibos no período sem lançamento na fatura:</b> ' + '; '.join(f"#{r['#']} {r['Data'][:5]} R$ {r['Valor (R$)']}" for r in nolanc) + '.'
        s += [Spacer(1, 4), Paragraph(msg, B)]

    bm = collections.OrderedDict()
    for r in main_:
        d = dt(r); bm.setdefault((d.year, d.month), []).append(r)
    md = [['Mês', 'Período', 'Corridas', 'Valor']] + [[f'{MN[m]}/{y}', f"{g[0]['Data'][:5]} a {g[-1]['Data'][:5]}", str(len(g)),
                                                     brl(sum(map(v, g)))] for (y, m), g in bm.items()]
    md += [['Total', '', str(len(main_)), brl(sum(map(v, main_)))]]
    bc = collections.defaultdict(list)
    for r in rows: bc[r['Cidade']].append(r)
    cd = [['Cidade', 'Corridas', 'Valor']] + [[c, str(len(g)), brl(sum(map(v, g)))] for c, g in sorted(bc.items(), key=lambda x: -len(x[1]))]
    side = Table([[[Paragraph(f'Cartão principal{card} por mês', H2), tbl(md, [22 * mm, 32 * mm, 20 * mm, 28 * mm], right=(2, 3), total=True)],
                   [Paragraph('Todas as corridas por cidade', H2), tbl(cd, [34 * mm, 20 * mm, 28 * mm], right=(1, 2))]]],
                 colWidths=[W * 0.52, W * 0.48])
    side.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LEFTPADDING', (0, 0), (-1, -1), 0)]))
    s.append(side)

    pts = []
    pre = [r for r in rows if 'pré-autorização' in r['Pagamento']]
    if pre:
        pts.append('<b>Pré-autorizações:</b> ' + '; '.join(f"{r['Data'][:5]} corrida R$ {r['Valor (R$)']} – {r['Pagamento'].split('(', 1)[1].rstrip(')')}" for r in pre) +
                   '. Na fatura pode aparecer o valor retido e um estorno separado.')
    top = sorted(rows, key=lambda r: -v(r))[:4]
    pts.append('<b>Maiores valores:</b> ' + '; '.join(f"{r['Data'][:5]} {r['Início']} {brl(v(r))} ({r['Origem']} → {r['Destino']}, {r['Distância/Tempo']})" for r in top) + '.')
    ds = sorted({dt(r).date() for r in rows})
    gaps = [(x, y) for x, y in zip(ds, ds[1:]) if (y - x).days > 10]
    if gaps:
        pts.append('<b>Sem corridas:</b> ' + '; '.join(f"{(x + datetime.timedelta(1)).strftime('%d/%m')} a {(y - datetime.timedelta(1)).strftime('%d/%m')}" for x, y in gaps) + '.')
    dup = [k for k, c in collections.Counter((r['Data'], r['Valor (R$)']) for r in rows).items() if c > 1]
    pts.append('<b>Mesmo dia e mesmo valor:</b> ' + (', '.join(f'{d} R$ {x}' for d, x in dup) + ' – conferir se não é cobrança dupla.' if dup else 'nenhum caso.'))
    blk = [Paragraph('Pontos de atenção', H2)]
    for p in pts: blk += [Paragraph('• ' + p, B), Spacer(1, 2)]
    s.append(KeepTogether(blk))

    s.append(PageBreak())
    s.append(Paragraph(f'Detalhamento – {len(rows)} corridas', H2))
    leg = 'Legenda: fundo vermelho = outro meio/outro cartão'
    if fat: leg = f'Legenda: fundo dourado = <b>{MK}</b> (confirmada na fatura{card}) · ' + leg.split(': ')[1]
    s += [Paragraph(leg, B), Spacer(1, 3)]
    d = [['#', 'Data', 'Início', 'Fim', 'Categoria', 'Cidade', 'Origem', 'Destino', 'Dist./tempo', 'Pagamento', 'Valor']]
    red, gold = [], []
    for i, r in enumerate(rows, 1):
        pg = (r['Pagamento'].split(' (')[0][:22] + ' ⚠') if r['Alerta'] else (f'{MK} ' + ('VISA' if 'VISA' in r['Pagamento'] else 'cartão') if r['#'] in conf else
                                                                         ('VISA (pré-aut.)' if 'pré' in r['Pagamento'] else ('VISA' if 'VISA' in r['Pagamento'] else r['Pagamento'][:22])))
        d.append([str(i), r['Data'], r['Início'], r['Fim'], r['Categoria'], r['Cidade'], Paragraph(r['Origem'], C),
                  Paragraph(r['Destino'], C), r['Distância/Tempo'], Paragraph(pg, C), brl(v(r))])
        if r['Alerta']: red.append(i)
        if r['#'] in conf: gold.append(i)
    d.append([''] * 9 + ['Total', brl(sum(map(v, rows)))])
    s.append(tbl(d, [9 * mm, 18 * mm, 11 * mm, 11 * mm, 19 * mm, 19 * mm, (W - 174 * mm) / 2, (W - 174 * mm) / 2,
                     25 * mm, 27 * mm, 21 * mm], right=(0, 10), fs=7, total=True, red=red, gold=gold))

    def foot(cv, dc):
        cv.saveState(); cv.setFont(F, 7); cv.setFillColor(MUT)
        cv.drawString(dc.leftMargin, 8 * mm, f'Relatório de corridas 99 · cartão{card}' + (f' · conferência {a.marca}' if fat else '') +
                      f' · gerado em {datetime.date.today().strftime("%d/%m/%Y")}')
        cv.drawRightString(dc.pagesize[0] - dc.rightMargin, 8 * mm, f'Página {dc.page}'); cv.restoreState()
    doc.build(s, onFirstPage=foot, onLaterPages=foot)
    print(f'PDF: {a.pdf} · corridas={len(rows)} principal={len(main_)} outro={len(other)} confirmadas={len(aur)} '
          f'sem_recibo={len(semrec)} sem_lancamento={len(nolanc)}')

if __name__ == '__main__':
    main()
