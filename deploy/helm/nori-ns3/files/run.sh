#!/usr/bin/env bash
# Executa um cenário NORI AO VIVO (saída no terminal em tempo real) e grava a evidência:
#   /workspace/runs/<run_id>/execution_manifest.json, logs/stdout.log,
#   raw/ (saídas do ns-3, ex. FlowMonitor) e raw/e2_sctp.pcap (tráfego SCTP/E2 real),
#   hashes.sha256 (integridade; não prova execução).
# Uso: bash /scripts/run.sh <exemplo|scratch/cenario> <run_id> [--seed N] [-- args do cenário]
set -uo pipefail

W=/workspace
NS3="$W/ns-3-dev"
[ -f "$W/READY" ] || { echo "Bancada ainda não está pronta (veja os logs do pod)." >&2; exit 69; }
[ $# -ge 2 ] || { echo "Uso: run.sh <exemplo> <run_id> [--seed N] [-- args]" >&2; exit 64; }
EXAMPLE="$1"; RUN_ID="$2"; shift 2
SEED=1
if [ "${1:-}" = "--seed" ]; then SEED="$2"; shift 2; fi
[ "${1:-}" = "--" ] && shift
[[ "$SEED" =~ ^[0-9]+$ ]] || { echo "--seed deve ser inteiro" >&2; exit 64; }
[[ "$RUN_ID" =~ ^[A-Za-z0-9_.-]+$ ]] || { echo "run_id inválido" >&2; exit 64; }

OUT="$W/runs/$RUN_ID"
[ -e "$OUT" ] && { echo "Execução já existe: $OUT (não sobrescrevo evidência)" >&2; exit 73; }
mkdir -p "$OUT/raw" "$OUT/logs"
chown -R developer: "$OUT"

ARGS="--RngRun=${SEED} --ipE2TermRic=${E2TERM_ADDRESS}"
for a in "$@"; do ARGS+=" $(printf '%q' "$a")"; done
CMD="cd '$NS3' && ./ns3 run '${EXAMPLE} ${ARGS}' --cwd '$OUT/raw'"

STARTED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
tcpdump -i any -U -s 0 -w "$OUT/raw/e2_sctp.pcap" "sctp or port ${E2TERM_PORT}" 2>"$OUT/logs/tcpdump.log" &
TCPDUMP_PID=$!
sleep 1
echo "=== [$STARTED] ${EXAMPLE} seed=${SEED} run_id=${RUN_ID} (saída ao vivo) ==="
su developer -c "$CMD" 2>&1 | tee "$OUT/logs/stdout.log"
EXIT_CODE=${PIPESTATUS[0]}
FINISHED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
sleep 1
kill -INT "$TCPDUMP_PID" 2>/dev/null; wait "$TCPDUMP_PID" 2>/dev/null

python3 - "$OUT" <<PY
import glob, json, os, sys
out = sys.argv[1]
info = json.load(open("$W/BUILD_INFO.json"))
pcap = os.path.join(out, "raw", "e2_sctp.pcap")
pcap_has_packets = os.path.exists(pcap) and os.path.getsize(pcap) > 24   # 24 B = só o cabeçalho
xmls = glob.glob(os.path.join(out, "raw", "*.xml"))
sources = []
if xmls:
    sources.append("NS3_FLOWMONITOR")
if pcap_has_packets:
    sources += ["NORI_E2", "E2_PCAP"]
status = "SUCCESS" if int("$EXIT_CODE") == 0 else "FAILED"
manifest = {
    "run_id": "$RUN_ID",
    "source": sources,
    "backend": "NORI_NS3",
    "scenario": "$EXAMPLE",
    "seed": int("$SEED"),
    "command": """$CMD""",
    "run_status": status,
    "exit_code": int("$EXIT_CODE"),
    "started_at_utc": "$STARTED",
    "finished_at_utc": "$FINISHED",
    "ns3_version": info.get("ns3_version"),
    "ns3_commit": info.get("ns3_commit"),
    "fiveg_lena_version": info.get("fiveg_lena_version"),
    "nr_commit": info.get("nr_commit"),
    "nori_commit": info.get("nori_commit"),
    "e2sim_commit": info.get("e2sim_commit"),
    "e2ap": info.get("e2ap"), "e2sm_kpm": info.get("e2sm_kpm"), "e2sm_rc": info.get("e2sm_rc"),
    "e2term": "${E2TERM_ADDRESS}:${E2TERM_PORT}",
    "pcap_has_packets": pcap_has_packets,
    "environment": {"os": info.get("os"), "compiler": info.get("compiler"), "runtime": "kubernetes (k3s) pod"},
    "publication_eligible": status == "SUCCESS" and bool(sources),
}
json.dump(manifest, open(os.path.join(out, "execution_manifest.json"), "w"), indent=2)
PY

( cd "$OUT" && find . -type f ! -name hashes.sha256 -printf '%P\n' | sort | xargs -r sha256sum > hashes.sha256 )
echo "=== [$FINISHED] fim: exit=${EXIT_CODE} evidência em ${OUT} ==="
echo "Copie para o repositório com: kubectl cp <ns>/<pod>:${OUT} experiments/runs/${RUN_ID}"
exit "$EXIT_CODE"
