#!/usr/bin/env python3
"""Ajuda a baixar recibos 99 do Gmail com o mínimo de downloads.

Os e-mails "Recibo(s) de corrida 99" (voude99@99app.com) costumam vir em lotes
e repetir os mesmos PDFs em vários e-mails. Este script:

  plan     lê o JSON salvo de get_thread (ou vários) e gera a lista mínima de
           (messageId, attachmentIndex, filename) para baixar, pulando nomes
           que já existem na pasta de PDFs.
  collect  pega os PDFs baixados por download_gmail_attachment (arquivos
           mcp-Gmail-blob-*.pdf), identifica cada um PELO CONTEÚDO (data +
           valor + categoria) e copia para a pasta de PDFs com o nome original.

Uso:
  python3 -I gmail_tools.py plan    <pasta_pdfs> <plan.json> <thread1.json> [thread2.json ...]
  python3 -I gmail_tools.py collect <pasta_pdfs> <plan.json> <blob1.pdf> [blob2.pdf ...]
"""
import json
import os
import re
import shutil
import subprocess
import sys

MON = {'jan': 'Jan', 'fev': 'Feb', 'mar': 'Mar', 'abr': 'Apr', 'mai': 'May', 'jun': 'Jun',
       'jul': 'Jul', 'ago': 'Aug', 'set': 'Sep', 'out': 'Oct', 'nov': 'Nov', 'dez': 'Dec'}

def norm(n):
    return n.replace('Bel_m', 'Belém').replace('Belem', 'Belém')

def load_messages(paths):
    msgs = []
    for p in paths:
        t = json.load(open(p))
        if isinstance(t, dict) and 'messages' in t:
            msgs += t['messages']
        elif isinstance(t, dict) and 'threads' in t:
            for th in t['threads']:
                msgs += th.get('messages', [])
    return msgs

def plan(pdf_dir, out, threads):
    os.makedirs(pdf_dir, exist_ok=True)
    have = {norm(f) for f in os.listdir(pdf_dir)}
    msgs = [(m['id'], [a['filename'] for a in m.get('attachments', [])]) for m in load_messages(threads)]
    names = {norm(f) for _, fs in msgs for f in fs if f.lower().endswith('.pdf')}
    todo = names - have
    print(f'emails={len(msgs)} anexos={sum(len(fs) for _, fs in msgs)} recibos_unicos={len(names)} '
          f'ja_tenho={len(names & have)} a_baixar={len(todo)}')
    items = []
    while todo:  # cobertura gulosa: poucos e-mails cobrindo todos os nomes
        mid, fs = max(msgs, key=lambda x: len({norm(f) for f in x[1]} & todo))
        for i, f in enumerate(fs):
            if norm(f) in todo:
                items.append({'messageId': mid, 'attachmentIndex': i, 'filename': norm(f)})
                todo.discard(norm(f))
    json.dump(items, open(out, 'w'), ensure_ascii=False, indent=0)
    print(f'plano salvo em {out} ({len(items)} downloads)')

def key_from_pdf(path):
    txt = subprocess.run(['pdftotext', '-layout', path, '-'], capture_output=True, text=True).stdout
    m = re.search(r'\w{3}, (\d+) (\w{3}), (\d{4})', txt)
    tot = re.search(r'Total\s+R\$([\d.,]+)', txt)
    cat = re.search(r'escolher\s*\n?\s*o\s+(.+)', txt)
    if not (m and tot):
        return None, None
    return f"{int(m.group(1)):02d}{MON.get(m.group(2).lower(), m.group(2))}{m.group(3)} - R${tot.group(1)}", \
        (cat.group(1).strip() if cat else None)

def collect(pdf_dir, plan_path, blobs):
    items = json.load(open(plan_path))
    pending = [it['filename'] for it in items if not os.path.exists(os.path.join(pdf_dir, it['filename']))]
    ok = miss = 0
    for b in blobs:
        k, cat = key_from_pdf(b)
        cands = [n for n in pending if f' - {k} - ' in n] if k else []
        if len(cands) > 1 and cat:
            cands = [n for n in cands if f' - {cat} - ' in n] or cands
        if len(cands) == 1:
            shutil.copy(b, os.path.join(pdf_dir, cands[0]))
            pending.remove(cands[0]); ok += 1
        else:
            miss += 1; print('NAO IDENTIFICADO:', b, k, cat, cands[:3])
    print(f'copiados={ok} nao_identificados={miss} ainda_faltando={len(pending)}')
    for n in pending:
        print('  falta:', n)

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'plan':
        plan(sys.argv[2], sys.argv[3], sys.argv[4:])
    elif cmd == 'collect':
        collect(sys.argv[2], sys.argv[3], sys.argv[4:])
    else:
        sys.exit(__doc__)
