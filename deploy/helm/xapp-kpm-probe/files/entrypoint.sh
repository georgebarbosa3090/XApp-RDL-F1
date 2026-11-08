#!/usr/bin/env bash
# Preparo da xApp kpm-probe sem Docker: RMR (.deb fixado por sha256), venv com ricxappframe
# e asn1tools no volume persistente e o ASN.1 E2SM do NORI no commit fixado (sha256 conferido).
set -euo pipefail
D=/data
mkdir -p "$D/cache" "$D/asn" "$D/logs"
log() { echo "[$(date -u +%H:%M:%S)] $*"; }

fetch() {  # fetch <url> <destino> <sha256>
  python3 - "$1" "$2" "$3" <<'PY'
import hashlib, sys, urllib.request
url, dest, expected = sys.argv[1:4]
data = urllib.request.urlopen(url, timeout=60).read()
got = hashlib.sha256(data).hexdigest()
if got != expected:
    sys.exit(f"sha256 divergente para {url}: {got} != {expected}")
open(dest, "wb").write(data)
PY
}

DEB="$D/cache/rmr_${RMR_VERSION}_amd64.deb"
if [ ! -f "$DEB" ] || [ "$(sha256sum "$DEB" | cut -d' ' -f1)" != "$RMR_SHA256" ]; then
  log "RMR ${RMR_VERSION}: download"
  fetch "$RMR_URL" "$DEB" "$RMR_SHA256"
fi
dpkg --install "$DEB" >/dev/null && ldconfig
log "RMR ${RMR_VERSION} instalado (sha256 ${RMR_SHA256})"

STAMP="$D/.stamp-venv-$(echo "ricxappframe${PIP_RICXAPPFRAME} asn1tools${PIP_ASN1TOOLS} ${PIP_HRDL_DEPS}" | sha256sum | cut -c1-16)"
if [ ! -f "$STAMP" ]; then
  log "venv: ricxappframe==${PIP_RICXAPPFRAME} (sem dependências) asn1tools==${PIP_ASN1TOOLS}"
  rm -rf "$D/venv" && python3 -m venv "$D/venv"
  # Só o módulo ricxappframe.rmr é usado, e ele depende apenas da biblioteca padrão (ctypes).
  # As dependências declaradas (ricsdl -> hiredis) exigiriam compilador C na imagem.
  "$D/venv/bin/pip" install -q --no-cache-dir --no-deps "ricxappframe==${PIP_RICXAPPFRAME}"
  "$D/venv/bin/pip" install -q --no-cache-dir "asn1tools==${PIP_ASN1TOOLS}" ${PIP_HRDL_DEPS}
  "$D/venv/bin/python" -c "from ricxappframe.rmr import rmr; import asn1tools, pydantic, numpy, pycrate_asn1rt, structlog"
  touch "$STAMP"
fi

for entry in $NORI_ASN_FILES; do
  f="${entry%%=*}"; h="${entry#*=}"
  if [ ! -f "$D/asn/$f" ] || [ "$(sha256sum "$D/asn/$f" | cut -d' ' -f1)" != "$h" ]; then
    fetch "$NORI_ASN_BASE_URL/$f" "$D/asn/$f" "$h"
  fi
  log "ASN.1 $f sha256 $h"
done

# Código do repositório (src/) do commit XAPP_RDL_SRC_COMMIT, entregue em base64 pelo chart
APP="$D/app/${XAPP_RDL_SRC_COMMIT}"
if [ ! -d "$APP/src" ]; then
  rm -rf "$D/app" && mkdir -p "$APP"
  base64 -d /scripts/src.tar.gz.b64 | tar -xz -C "$APP"
fi
log "src/ do commit ${XAPP_RDL_SRC_COMMIT} em $APP"

export ASN_DIR="$D/asn" EVENTS_FILE="$D/logs/kpm_probe_events.jsonl" XAPP_RDL_APP_DIR="$APP" XAPP_RDL_ASN1_DIR="$D/asn"
exec "$D/venv/bin/python" -u /scripts/kpm_probe.py
