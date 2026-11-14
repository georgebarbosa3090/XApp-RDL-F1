#!/usr/bin/env python3
"""Extrai os dados dos recibos 99 (PDF) e identifica a forma de pagamento.

Uso:
    python3 -I parse_receipts.py <pasta_pdfs> <saida.csv> [--card 4251]

Saída: CSV (; separado, UTF-8 com BOM, abre direto no Excel) com uma linha por
corrida, já ordenado e sem duplicatas (mesma data + hora de início + valor).

Por que olhar o logo: o recibo da 99 NÃO mostra os dígitos do cartão, só o
texto "Cartão de Crédito/Débito" e um logo da bandeira. O logo é uma imagem
embutida; comparamos o hash dos pixels com logos conhecidos. Um logo de cartão
diferente do principal é o sinal de que outro cartão foi usado.
"""
import argparse
import collections
import csv
import datetime
import glob
import hashlib
import os
import re
import subprocess
import tempfile

from PIL import Image

# hash md5 (6 primeiros) dos pixels RGB -> rótulo. Medido nos recibos reais.
KNOWN_LOGOS = {
    '80x46:d83a61': 'VISA',
    '57x36:693411': 'Nubank (NuPay)',
}
MON_EN = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
          'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
MON_PT = {'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6, 'jul': 7, 'ago': 8,
          'set': 9, 'out': 10, 'nov': 11, 'dez': 12}

def logos(pdf):
    out = []
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(['pdfimages', '-png', pdf, os.path.join(td, 'i')], capture_output=True)
        for p in sorted(glob.glob(os.path.join(td, 'i-*.png'))):
            im = Image.open(p)
            if im.mode in ('L', '1', 'LA'):
                continue  # máscaras de transparência
            w, h = im.size
            if w <= 100 and h <= 60 and w > h:
                out.append(f'{w}x{h}:' + hashlib.md5(im.convert('RGB').tobytes()).hexdigest()[:6])
    return out

def money(s):
    return float(s.replace('.', '').replace(',', '.'))

def parse(pdf, card):
    txt = subprocess.run(['pdftotext', '-layout', pdf, '-'], capture_output=True, text=True).stdout
    L = [l.strip() for l in txt.splitlines() if l.strip()]
    base = os.path.basename(pdf)
    m = re.search(r'Receipt - (\d\d)(\w{3})(\d{4}) - R\$([\d.,]+) - (.+?) - (.+)\.pdf', base)
    if m:
        dd, mon, yy, val, cat, city = m.groups()
        date = datetime.date(int(yy), MON_EN[mon], int(dd))
    else:  # nome fora do padrão: tira do texto
        d = re.search(r'\w{3}, (\d+) (\w{3}), (\d{4})', txt)
        date = datetime.date(int(d.group(3)), MON_PT[d.group(2).lower()], int(d.group(1)))
        val = re.search(r'Total\s+R\$([\d.,]+)', txt).group(1)
        c = re.search(r'escolher\s*\n?\s*o\s+(.+)', txt)
        cat, city = (c.group(1).strip() if c else '?'), '?'
    times = [i for i, l in enumerate(L) if re.fullmatch(r'\d{1,2}:\d\d [AP]M', l)]
    t0 = datetime.datetime.strptime(L[times[0]], '%I:%M %p') if times else None
    t1 = datetime.datetime.strptime(L[times[1]], '%I:%M %p') if len(times) > 1 else None
    km = re.search(r'Detalhes\s+([\d,]+ km \| \d+ min)', txt)
    i = L.index('Método de pagamento') if 'Método de pagamento' in L else None
    pay_lines = [L[k] for k in range(i + 1, min(i + 4, len(L))) if 'R$' in L[k]] if i is not None else []
    pay_text = ' / '.join(re.sub(r'\s+[-+]R\$.*', '', p) for p in pay_lines) or 'N/D'
    lg = logos(pdf)
    brands = sorted({KNOWN_LOGOS.get(x, f'logo desconhecido {x}') for x in lg})
    brand = ', '.join(brands) or 'sem logo'
    alerta, meio = '', ''
    if 'NuPay' in pay_text or brand.startswith('Nubank'):
        meio, alerta = 'NuPay Débito (Nubank)', 'OUTRO MEIO'
    elif 'Dinheiro' in pay_text:
        meio, alerta = 'Dinheiro', 'OUTRO MEIO'
    elif 'Pix' in pay_text or 'PIX' in pay_text:
        meio, alerta = 'Pix', 'OUTRO MEIO'
    elif brand == 'VISA':
        meio = f'Cartão Crédito/Débito VISA'
    else:
        meio, alerta = f'Cartão – bandeira: {brand} ({pay_text})', 'OUTRO CARTÃO?'
    pre = re.search(r'pré-autorização temporária.*?R\$([\d.,]+)', txt.replace('\n', ' '))
    if pre:
        ref = [re.search(r'\+R\$([\d.,]+)', p) for p in pay_lines if 'Reembolso' in p]
        meio += f' (pré-autorização R${pre.group(1)}' + (f', reembolso R${ref[0].group(1)}' if ref and ref[0] else '') + ')'
    return dict(data=date, ini=t0.strftime('%H:%M') if t0 else '', fim=t1.strftime('%H:%M') if t1 else '',
                cat=cat, cidade=city, valor=val, v=money(val), meio=meio, alerta=alerta, logo=' '.join(lg),
                origem=L[times[0] + 1] if times else '', destino=L[times[1] + 1] if len(times) > 1 else '',
                dist=km.group(1) if km else '', arquivo=base)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf_dir'); ap.add_argument('out_csv'); ap.add_argument('--card', default='')
    a = ap.parse_args()
    rows, seen = [], set()
    for pdf in sorted(glob.glob(os.path.join(a.pdf_dir, '*.pdf'))):
        try:
            r = parse(pdf, a.card)
        except Exception as e:  # noqa: BLE001 — um recibo ruim não pode parar o lote
            print('ERRO lendo', os.path.basename(pdf), e); continue
        k = (r['data'], r['ini'], r['valor'])
        if k in seen:
            continue
        seen.add(k); rows.append(r)
    rows.sort(key=lambda r: (r['data'], r['ini']))
    with open(a.out_csv, 'w', newline='', encoding='utf-8-sig') as fh:
        w = csv.writer(fh, delimiter=';')
        w.writerow(['#', 'Data', 'Início', 'Fim', 'Categoria', 'Cidade', 'Valor (R$)', 'Pagamento', 'Alerta',
                    'Origem', 'Destino', 'Distância/Tempo', 'Logo', 'Arquivo'])
        for n, r in enumerate(rows, 1):
            w.writerow([n, r['data'].strftime('%d/%m/%Y'), r['ini'], r['fim'], r['cat'], r['cidade'], r['valor'],
                        r['meio'], r['alerta'], r['origem'], r['destino'], r['dist'], r['logo'], r['arquivo']])
    tot = sum(r['v'] for r in rows)
    print(f'corridas={len(rows)} total=R${tot:.2f} periodo={rows[0]["data"]}..{rows[-1]["data"]}' if rows else 'nenhum recibo')
    by = collections.Counter(r['meio'].split(' (pré')[0] for r in rows)
    for k, c in by.most_common():
        print(f'  {c:4d}  {k}')
    for r in rows:
        if r['alerta']:
            print(f"  ALERTA {r['alerta']}: {r['data']} {r['ini']} {r['cidade']} R${r['valor']} {r['meio']}")

if __name__ == '__main__':
    main()
