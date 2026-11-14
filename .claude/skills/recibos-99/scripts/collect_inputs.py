#!/usr/bin/env python3
"""Junta recibos 99 (PDFs soltos e/ou .zip) numa pasta única, sem duplicatas.

Uso:
    python3 -I collect_inputs.py <pasta_saida> <arquivo1.zip|pdf> [<arquivo2> ...]

- Lê os .zip com o módulo zipfile do Python (o `unzip` costuma recusar os zips
  da 99 com "overlapped components" por causa da codificação dos nomes).
- Normaliza o nome (Bel#U00e9m / Bel_m / Belem -> Belém) e remove caracteres
  inseguros; o mesmo recibo vindo de vários zips fica uma vez só.
- Também aceita uma pasta: copia os PDFs que houver nela.
"""
import os
import re
import sys
import zipfile

def norm(name: str) -> str:
    name = os.path.basename(name)
    name = name.replace('#U00e9', 'é').replace('Bel_m', 'Belém').replace('Belem', 'Belém')
    name = re.sub(r'^[0-9a-f]{8}[-_]+', '', name)          # prefixo de upload
    name = re.sub(r'^99Receipt_-_(\d{2}\w{3}\d{4})_-_R(\d+)', r'99Receipt - \1 - R\2', name)
    name = re.sub(r'[^\w.,$ ()-]', '_', name)
    return name

def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    added = dup = 0
    def put(name, data):
        nonlocal added, dup
        n = norm(name)
        if not n.lower().endswith('.pdf'):
            return
        p = os.path.join(out, n)
        if os.path.exists(p):
            dup += 1
            return
        with open(p, 'wb') as fh:
            fh.write(data)
        added += 1
    for src in sys.argv[2:]:
        if os.path.isdir(src):
            for f in sorted(os.listdir(src)):
                if f.lower().endswith('.pdf'):
                    put(f, open(os.path.join(src, f), 'rb').read())
        elif src.lower().endswith('.zip'):
            with zipfile.ZipFile(src) as z:
                for i in z.infolist():
                    if not i.is_dir():
                        put(i.filename, z.read(i))
        elif src.lower().endswith('.pdf'):
            put(src, open(src, 'rb').read())
    print(f'adicionados={added} duplicados_ignorados={dup} total_na_pasta={len(os.listdir(out))}')

if __name__ == '__main__':
    main()
