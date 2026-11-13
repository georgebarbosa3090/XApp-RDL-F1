#!/usr/bin/env bash
# Autor: George Barbosa
# Compila o libe42_shim e as xApps originais ligadas a ele (docs/16, E2), depois de conferir que as
# fontes das xApps são as do SOURCE.md (sha256). Uso (Ubuntu do WSL): bash xapps-originais/shim/build.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
SRCS="${XAPPS_ORIGINAIS:-$HOME/xapps-originais}"
check() {  # arquivo sha256
  local got; got=$(sha256sum "$1" | cut -d' ' -f1)
  [ "$got" = "$2" ] || { echo "sha256 diverge: $1" >&2; exit 65; }
}
sha_of() {  # SOURCE.md caminho
  grep -F "\`$2\`" "$1" | grep -oE '[0-9a-f]{64}' | head -1
}
check "$SRCS/xslice-oran/examples/xApp/c/ctrl/xapp_xslice.c" \
      "$(sha_of "$REPO/third_party/xapps/xslice-oran/SOURCE.md" examples/xApp/c/ctrl/xapp_xslice.c)"
check "$SRCS/flexric-orange/examples/xApp/c/orange/xapp_es_with_cell_util.c" \
      "$(sha_of "$REPO/third_party/xapps/flexric-orange-es/SOURCE.md" examples/xApp/c/orange/xapp_es_with_cell_util.c)"
echo "fontes originais conferidas (sha256 do SOURCE.md)"
BUILD="${SHIM_BUILD:-$HOME/xapps-originais/shim-build}"
cmake -S "$HERE" -B "$BUILD" -DCMAKE_BUILD_TYPE=Release > "$BUILD.cmake.log" 2>&1 || { tail -30 "$BUILD.cmake.log"; exit 1; }
nice -n 10 cmake --build "$BUILD" -j2 2>&1 | grep -E "error|Error|undefined reference|Built target" | head -60
ls -la "$BUILD"/libe42_shim.so "$BUILD"/*_rdl 2>/dev/null
