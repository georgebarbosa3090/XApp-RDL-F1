#!/usr/bin/env bash
# Uso: build_pdf.sh <pasta_com_md | arquivo1.md arquivo2.md ...> <saida.pdf> "<Título>"
# Converte Markdown -> HTML (pandoc) -> PDF (Chromium via Playwright).
set -euo pipefail
export LANG=C.UTF-8 LC_ALL=C.UTF-8
DIR="$(cd "$(dirname "$0")" && pwd)"
args=("$@"); n=${#args[@]}
[ "$n" -ge 3 ] || { echo "uso: $0 <pasta|md...> <saida.pdf> <titulo>"; exit 1; }
TITLE="${args[$((n-1))]}"; OUT="${args[$((n-2))]}"; INPUTS=("${args[@]:0:$((n-2))}")
FILES=()
for i in "${INPUTS[@]}"; do
  if [ -d "$i" ]; then while IFS= read -r f; do FILES+=("$f"); done < <(ls "$i"/*.md | sort); else FILES+=("$i"); fi
done
HTML="${OUT%.pdf}.html"
# Pré-processamento: linha em branco após blockquote seguido de texto/lista (evita "lazy continuation" do pandoc)
TMPD="$(mktemp -d)"; FIXED=()
for f in "${FILES[@]}"; do
  g="$TMPD/$(basename "$f")"
  python3 -I -c 'import sys
L=open(sys.argv[1],encoding="utf-8").read().split("\n"); o=[]
for i,l in enumerate(L):
    o.append(l)
    if l.startswith(">") and i+1<len(L) and L[i+1].strip() and not L[i+1].startswith(">"): o.append("")
open(sys.argv[2],"w",encoding="utf-8").write("\n".join(o))' "$f" "$g"
  FIXED+=("$g")
done
FILES=("${FIXED[@]}")
pandoc "${FILES[@]}" -f markdown+emoji+pipe_tables -t html5 -s --toc --toc-depth=2 \
  --metadata title="$TITLE" --metadata lang=pt-BR -c "file://$DIR/style.css" --embed-resources -o "$HTML" 2>/dev/null \
|| pandoc "${FILES[@]}" -f markdown+pipe_tables -t html5 -s --toc --toc-depth=2 \
  --metadata title="$TITLE" --metadata lang=pt-BR --css "$DIR/style.css" --self-contained -o "$HTML"
node -e '
const { chromium } = require("playwright");
(async () => {
  const b = await chromium.launch(); const p = await b.newPage();
  await p.goto("file://" + process.argv[1], { waitUntil: "load" });
  await p.pdf({ path: process.argv[2], format: "A4", printBackground: true,
    margin: { top: "16mm", bottom: "16mm", left: "14mm", right: "14mm" },
    displayHeaderFooter: true, headerTemplate: "<span></span>",
    footerTemplate: "<div style=\"font-size:8px;width:100%;text-align:center;color:#666\">" + process.argv[3] + " — <span class=pageNumber></span>/<span class=totalPages></span></div>" });
  await b.close();
})();' "$(realpath "$HTML")" "$(realpath -m "$OUT")" "$TITLE"
echo "PDF gerado: $OUT"
