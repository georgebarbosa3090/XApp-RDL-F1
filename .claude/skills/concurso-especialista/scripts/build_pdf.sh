#!/usr/bin/env bash
# Uso: build_pdf.sh <pasta_com_md | arquivo1.md arquivo2.md ...> <saida.pdf> "<Título>"
# Converte Markdown -> HTML (pandoc) -> PDF (Chromium via Playwright).
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
args=("$@"); n=${#args[@]}
[ "$n" -ge 3 ] || { echo "uso: $0 <pasta|md...> <saida.pdf> <titulo>"; exit 1; }
TITLE="${args[$((n-1))]}"; OUT="${args[$((n-2))]}"; INPUTS=("${args[@]:0:$((n-2))}")
FILES=()
for i in "${INPUTS[@]}"; do
  if [ -d "$i" ]; then while IFS= read -r f; do FILES+=("$f"); done < <(ls "$i"/*.md | sort); else FILES+=("$i"); fi
done
HTML="${OUT%.pdf}.html"
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
