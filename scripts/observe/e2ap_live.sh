#!/usr/bin/env bash
# Aba Protocolo E2AP: tcpdump no pod do NORI passado direto ao tshark local, decodificando ao vivo
# E2 Setup, Subscription, Indication, Control e ACK, com RICrequestID e RAN function.
# Uso: bash scripts/observe/e2ap_live.sh            (TSHARK=/caminho/tshark para outro executável)
export KUBECONFIG="${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}"
TSHARK="${TSHARK:-$(command -v tshark || echo "$HOME/.local/tshark-4.2.2/root/usr/bin/tshark")}"
[ -x "$TSHARK" ] || { echo "tshark não encontrado (docs/04, seção 7.5)" >&2; exit 3; }
echo "capturando SCTP/E2 no pod do NORI; decodificação pelo $("$TSHARK" --version | head -1)"
printf '%-12s %-14s %-20s %-26s %-13s %s\n' "hora" "sentido" "PDU" "procedimento" "RICrequestID" "RAN function"
kubectl -n ricsim exec -i deploy/nori-ns3 -- tcpdump -i any -U -s 0 -w - sctp 2>/dev/null \
  | "$TSHARK" -l -n -r - -o sctp.reassembly:TRUE -d sctp.port==36422,e2ap -Y e2ap -T fields \
      -E separator=';' -E occurrence=f -e frame.time -e sctp.dstport -e e2ap.E2AP_PDU -e e2ap.procedureCode \
      -e e2ap.ricRequestorID -e e2ap.ricInstanceID -e e2ap.RANfunctionID 2>/dev/null \
  | awk -F';' '
    BEGIN {
      pdu[0]="initiatingMessage"; pdu[1]="successfulOutcome"; pdu[2]="unsuccessfulOutcome"
      p[1]="E2 Setup"; p[2]="Error Indication"; p[3]="Reset"; p[4]="RIC Control"; p[5]="RIC Indication"
      p[7]="RIC Service Update"; p[8]="RIC Subscription"; p[9]="RIC Subscription Delete"; p[10]="E2 Node Config Update"
      p[12]="Subscription Delete Required"; p[13]="E2 Removal"
    }
    {
      split($1, tm, " "); hora = substr(tm[4], 1, 12)
      sent = ($2 == "36422") ? "nó -> RIC" : "RIC -> nó"
      nome = (p[$4] != "") ? p[$4] : "procedimento " $4
      req = ($5 != "") ? $5 "/" $6 : "-"
      fn = ($7 != "") ? $7 : "-"
      printf "%-12s %-14s %-20s %-26s %-13s %s\n", hora, sent, pdu[$3], nome, req, fn; fflush()
    }'
