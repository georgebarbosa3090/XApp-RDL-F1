#!/usr/bin/env bash
# Uso: extrair_prova.sh prova.pdf > prova.txt  — extrai PDF em duas colunas, coluna esquerda e depois direita.
set -euo pipefail
f="$1"; n=$(pdfinfo "$f" | awk '/Pages/{print $2}')
W=$(pdfinfo "$f" | awk '/Page size/{print int($3)}'); H=$(pdfinfo "$f" | awk '/Page size/{print int($5)}'); h=$((W/2))
for p in $(seq 1 "$n"); do
  pdftotext -f "$p" -l "$p" -x 0 -y 0 -W "$h" -H "$H" "$f" -
  pdftotext -f "$p" -l "$p" -x "$h" -y 0 -W "$h" -H "$H" "$f" -
done
