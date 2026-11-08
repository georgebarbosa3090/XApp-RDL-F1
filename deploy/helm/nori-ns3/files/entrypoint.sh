#!/usr/bin/env bash
# Prepara a bancada ns-3 + 5G-LENA + NORI no volume /workspace (idempotente).
# Reproduz o Dockerfile oficial do NORI sem Docker: dependências, Nokia asn1c,
# e2sim com ASN.1 v3.01 do NORI e patch X.691, ns-3/nr fixados e NORI em contrib/nori.
# Compilações ficam no volume; a cada início só reinstala o que vive no FS efêmero.
set -euo pipefail

W=/workspace
SRC="$W/src"
NS3="$W/ns-3-dev"
JOBS="${BUILD_JOBS:-2}"
mkdir -p "$SRC" "$W/logs" "$W/runs"
rm -f "$W/READY"
export DEBIAN_FRONTEND=noninteractive

log() { echo "[$(date -u +%H:%M:%S)] $*"; }

pin() {  # pin <dir> <repo> <commit>: clona e fixa o commit; falha se não existir
  local dir="$1" repo="$2" commit="$3"
  [ -d "$dir/.git" ] || git clone -q "$repo" "$dir"
  if ! git -C "$dir" cat-file -e "${commit}^{commit}" 2>/dev/null; then
    git -C "$dir" fetch -q origin || true
  fi
  git -C "$dir" cat-file -e "${commit}^{commit}" || { log "ERRO: commit ${commit} não existe em ${repo}"; exit 3; }
  git -C "$dir" checkout -q --force "$commit"
}

log "Dependências do sistema (iguais ao Dockerfile do NORI + tcpdump)"
apt-get update -q
apt-get install -y -q build-essential cmake libsctp-dev autoconf automake libtool bison flex \
  libboost-all-dev sudo git python3 libc6-dev sqlite3 libsqlite3-dev libeigen3-dev \
  nlohmann-json3-dev software-properties-common wget tcpdump lksctp-tools >/dev/null
add-apt-repository -y ppa:ubuntu-toolchain-r/test >/dev/null
apt-get update -q
apt-get install -y -q gcc-11 g++-11 >/dev/null
update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 20
update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-11 20
id developer >/dev/null 2>&1 || useradd -m -u 1000 -s /bin/bash developer
# Os checkouts em /workspace pertencem ao usuário developer (chown abaixo); sem isto o git do root
# recusa ler os repositórios ("dubious ownership"): os commits sairiam vazios no BUILD_INFO.json
# e, num reinício do pod, pin() acusaria commit inexistente.
git config --global --replace-all safe.directory '*'

log "NORI ${NORI_COMMIT}"
pin "$SRC/nori" "$NORI_REPO" "$NORI_COMMIT"

log "Nokia asn1c ${ASN1C_COMMIT}"
STAMP_ASN1C="$W/.stamp-asn1c-${ASN1C_COMMIT}"
if [ ! -f "$STAMP_ASN1C" ]; then
  pin "$SRC/asn1c" "$ASN1C_REPO" "$ASN1C_COMMIT"
  ( cd "$SRC/asn1c" && autoreconf -iv >/dev/null && ./configure >/dev/null && make -j"$JOBS" >/dev/null )
  touch "$STAMP_ASN1C"
fi
make -C "$SRC/asn1c" install >/dev/null && ldconfig

log "e2sim ${E2SIM_COMMIT} com ASN.1 v3.01 do NORI"
E2SIM="$SRC/e2-interface"
STAMP_E2SIM="$W/.stamp-e2sim-${E2SIM_COMMIT}-${NORI_COMMIT}"
if [ ! -f "$STAMP_E2SIM" ]; then
  pin "$E2SIM" "$E2SIM_REPO" "$E2SIM_COMMIT"
  cd "$E2SIM/e2sim/asn1c"
  rm -f ./*.c ./*.h Makefile.am.libasncodec asn_constant.h
  mkdir -p asn/v03 && cp "$SRC/nori/asn/v03/"*.asn asn/v03/
  asn1c -fcompound-names -fno-include-deps -findirect-choice -no-gen-OER -no-gen-example \
    ./asn/v03/e2ap-common-v03.01.asn ./asn/v03/e2ap-constant-v03.01.asn ./asn/v03/e2ap-container-v03.01.asn \
    ./asn/v03/e2ap-epd-v03.01.asn ./asn/v03/e2ap-ied-v03.01.asn ./asn/v03/e2ap-pdu-v03.01.asn >/dev/null
  asn1c -fcompound-names -fno-include-deps -findirect-choice -no-gen-OER -no-gen-example \
    ./asn/v03/e2sm-v03.01.asn ./asn/v03/e2sm-kpm-v03.00.asn ./asn/v03/e2sm-rc-v03.01.asn >/dev/null
  # Patch X.691/10.6 extraído do próprio Dockerfile do NORI (fonte única, sem cópia manual)
  PATCH_CMD="$(grep -m1 '^RUN python3 -c' "$SRC/nori/Dockerfile" | sed 's/^RUN //; s#/tmp/e2-interface#'"$E2SIM"'#g')"
  [ -n "$PATCH_CMD" ] || { log "ERRO: patch constr_CHOICE não encontrado no Dockerfile do NORI"; exit 4; }
  bash -c "$PATCH_CMD"
  cd "$E2SIM/e2sim"
  python3 - <<'PY'
import re
path = "CMakeLists.txt"
s = open(path).read()
s = s.replace("$<TARGET_OBJECTS:def_objects>", "$<TARGET_OBJECTS:asn1_objects>;$<TARGET_OBJECTS:def_objects>")
marker = "unset( DEV_PKG  CACHE )"
block = "install(\n    FILES\n        src/messagerouting/e2ap_asn1c_codec.h\n    DESTINATION\n        ${install_inc}\n)\n"
assert marker in s, "marcador DEV_PKG ausente no CMakeLists do e2sim"
s = s.replace(marker, block + marker, 1)
open(path, "w").write(s)
PY
  mkdir -p build && cd build && cmake .. -DDEV_PKG=1 >/dev/null && make package -j"$JOBS" >/dev/null
  touch "$STAMP_E2SIM"
fi
dpkg --install "$E2SIM/e2sim/build/e2sim-dev_1.0.0_amd64.deb" >/dev/null && ldconfig

STAMP_NS3="$W/.stamp-ns3-${NS3_COMMIT}-${NR_COMMIT}-${NORI_COMMIT}-${BUILD_PROFILE}"
if [ ! -f "$STAMP_NS3" ]; then
  log "ns-3 ${NS3_COMMIT} + nr ${NR_COMMIT} + contrib/nori: preparo e compilação"
  pin "$NS3" "$NS3_REPO" "$NS3_COMMIT"
  pin "$NS3/contrib/nr" "$NR_REPO" "$NR_COMMIT"
  rm -rf "$NS3/contrib/nori" && mkdir -p "$NS3/contrib/nori"
  ( cd "$SRC/nori" && git archive "$NORI_COMMIT" ) | tar -x -C "$NS3/contrib/nori"
  chown -R developer: "$NS3"
  EX_FLAG=$([ "${ENABLE_EXAMPLES}" = "true" ] && echo --enable-examples || echo --disable-examples)
  set -o pipefail
  su developer -c "cd '$NS3' && ./ns3 configure -d '${BUILD_PROFILE}' ${EX_FLAG} && ./ns3 build -j${JOBS}" \
    2>&1 | tee "$W/logs/build_ns3_$(date -u +%Y%m%dT%H%M%SZ).log"
  touch "$STAMP_NS3"
else
  # Já compilado: não tocar nos fontes. Um checkout ou nova extração muda os horários dos
  # arquivos e faz o próximo ./ns3 recompilar tudo (com todos os núcleos, estourando a memória).
  log "ns-3 ${NS3_COMMIT} + nr ${NR_COMMIT} + contrib/nori: já compilado; conferindo commits"
  [ "$(git -C "$NS3" rev-parse HEAD)" = "$NS3_COMMIT" ] || { log "ERRO: ns-3 fora do commit fixado"; exit 5; }
  [ "$(git -C "$NS3/contrib/nr" rev-parse HEAD)" = "$NR_COMMIT" ] || { log "ERRO: nr fora do commit fixado"; exit 5; }
fi

# Patches do projeto sobre o NORI (deploy/helm/nori-ns3/files/patches, listados com sha256 no
# reproducibility/versions.lock). Idempotente: só aplica o que falta e então recompila (-j${JOBS}).
PATCHED=0
for pf in /scripts/*.patch; do
  [ -f "$pf" ] || continue
  name="$(basename "$pf")"
  if ( cd "$NS3/contrib/nori" && patch -p1 -R --dry-run -s -f < "$pf" ) >/dev/null 2>&1; then
    log "patch ${name}: já aplicado"
  elif ( cd "$NS3/contrib/nori" && patch -p1 --dry-run -s -f < "$pf" ) >/dev/null 2>&1; then
    ( cd "$NS3/contrib/nori" && patch -p1 -s -f --no-backup-if-mismatch < "$pf" )
    chown -R developer: "$NS3/contrib/nori"
    log "patch ${name}: aplicado (sha256 $(sha256sum "$pf" | cut -d' ' -f1))"
    PATCHED=1
  else
    log "ERRO: patch ${name} não se aplica ao NORI ${NORI_COMMIT}"; exit 7
  fi
done
if [ "$PATCHED" = 1 ]; then
  log "recompilação incremental após patches (-j${JOBS})"
  set -o pipefail
  su developer -c "cd '$NS3' && ./ns3 build -j${JOBS}" 2>&1 | tee "$W/logs/build_patches_$(date -u +%Y%m%dT%H%M%SZ).log"
fi

# Variante do projeto em scratch/ (os fontes do NORI ficam intactos), gerada do exemplo RC:
#  - grava flowmonitor.xml ao fim de Simulator::Run() (o exemplo instala o FlowMonitor mas não grava);
#  - grava slice_series.csv a cada 0,5 s simulado: contadores acumulados do FlowMonitor por UE/fatia
#    com o tempo simulado e o relógio de parede, para alinhar ao PCAP E2 e medir o efeito do Control
#    (o KPM do NORI não mede vazão por UE: DRB.UEThpDl sai sempre 0).
# Os arquivos vão para o --cwd da execução (raw/). Só recompila quando a variante muda.
VAR_DST="$NS3/scratch/nori-rc-slicing-flowmon.cc"
VAR_TMP="$(mktemp)"
python3 - "$NS3/contrib/nori/examples/nori-rc-slicing-demo.cc" "$VAR_TMP" <<'PY' || { log "ERRO: variante FlowMonitor não gerada"; exit 6; }
import sys
src, dst = sys.argv[1:3]
text = open(src).read()

def insert(text, anchor, new, before=False):
    if text.count(anchor) != 1:
        sys.exit(f"ponto de inserção não é único no exemplo do NORI: {anchor.strip()!r}")
    return text.replace(anchor, (new + anchor) if before else (anchor + new))

text = insert(text, "#include <vector>\n", "#include <chrono>\n#include <fstream>\n")
series_fn = r'''
// [xapp-rdl] Série temporal do FlowMonitor por UE/fatia (medida de referência da RAN), com tempo
// simulado e relógio de parede (simulação em tempo real) para alinhar ao PCAP E2.
static void
XappRdlSliceSeries(Ptr<FlowMonitor> monitor,
                   FlowMonitorHelper* helper,
                   std::map<Ipv4Address, uint32_t> ueIpToIndex,
                   double interval,
                   double simTime)
{
    static std::ofstream out;
    if (!out.is_open())
    {
        out.open("slice_series.csv");
        out << "sim_time_s,wall_epoch_s,ue_index,sst,tx_packets,rx_packets,rx_bytes,delay_sum_s\n";
    }
    Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(helper->GetClassifier());
    std::map<uint32_t, FlowMonitor::FlowStats> perUe;
    for (const auto& it : monitor->GetFlowStats())
    {
        Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(it.first);
        auto idx = ueIpToIndex.find(t.destinationAddress);
        if (idx == ueIpToIndex.end())
        {
            continue;
        }
        FlowMonitor::FlowStats& acc = perUe[idx->second];
        acc.txPackets += it.second.txPackets;
        acc.rxPackets += it.second.rxPackets;
        acc.rxBytes += it.second.rxBytes;
        acc.delaySum += it.second.delaySum;
    }
    double wall = std::chrono::duration<double>(std::chrono::system_clock::now().time_since_epoch()).count();
    double now = Simulator::Now().GetSeconds();
    for (uint32_t i = 0; i < ueIpToIndex.size(); ++i)
    {
        const FlowMonitor::FlowStats& s = perUe[i];
        int sst = (i == 0) ? 1 : 2; // mapeamento do exemplo: UE 0 eMBB (SST 1), UE 1 URLLC (SST 2)
        out << std::fixed << std::setprecision(6) << now << "," << wall << "," << i << "," << sst << ","
            << s.txPackets << "," << s.rxPackets << "," << s.rxBytes << "," << s.delaySum.GetSeconds() << "\n";
    }
    out.flush();
    if (simTime <= 0.0 || now + interval <= simTime)
    {
        Simulator::Schedule(Seconds(interval), &XappRdlSliceSeries, monitor, helper, ueIpToIndex, interval, simTime);
    }
}

'''
text = insert(text, "int\nmain(int argc, char* argv[])\n", series_fn, before=True)
text = insert(text, "\n    Simulator::Run();\n",
              "\n    // [xapp-rdl] série por fatia a cada 0,5 s simulado\n"
              "    Simulator::Schedule(Seconds(0.5), &XappRdlSliceSeries, monitor, &flowmonHelper, ueIpToIndex, 0.5, simTime);\n",
              before=True)
text = insert(text, "\n    Simulator::Run();\n",
              "\n    // [xapp-rdl] FlowMonitor gravado em XML para o certificador (R9/R10)\n"
              "    monitor->CheckForLostPackets();\n"
              "    monitor->SerializeToXmlFile(\"flowmonitor.xml\", true, true);\n")
open(dst, "w").write("// Gerado pelo chart nori-ns3 a partir de contrib/nori/examples/nori-rc-slicing-demo.cc\n" + text)
PY
if ! cmp -s "$VAR_TMP" "$VAR_DST"; then
  install -o developer -g developer -m 644 "$VAR_TMP" "$VAR_DST"
  log "scratch/nori-rc-slicing-flowmon.cc atualizado: reconfiguração e compilação incremental (-j${JOBS})"
  EX_FLAG=$([ "${ENABLE_EXAMPLES}" = "true" ] && echo --enable-examples || echo --disable-examples)
  set -o pipefail
  su developer -c "cd '$NS3' && ./ns3 configure -d '${BUILD_PROFILE}' ${EX_FLAG} >/dev/null && ./ns3 build -j${JOBS} nori-rc-slicing-flowmon" \
    2>&1 | tee "$W/logs/build_flowmon_$(date -u +%Y%m%dT%H%M%SZ).log"
fi
rm -f "$VAR_TMP"
chown -R developer: "$W/runs" "$W/logs"

python3 - <<PY
import json, subprocess
def rev(d):
    return subprocess.run(["git", "-C", d, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
def first(cmd):
    out = subprocess.run(cmd, capture_output=True, text=True).stdout.strip().splitlines()
    return out[0] if out else ""
info = {
    "backend": "NORI_NS3",
    "ns3_commit": rev("$NS3"),
    "ns3_version": open("$NS3/VERSION").read().strip() if __import__("os").path.exists("$NS3/VERSION") else first(["git", "-C", "$NS3", "describe", "--tags", "--always"]),
    "nr_commit": rev("$NS3/contrib/nr"),
    "fiveg_lena_version": first(["git", "-C", "$NS3/contrib/nr", "describe", "--tags", "--always"]),
    "nori_commit": rev("$SRC/nori"),
    "e2sim_commit": rev("$E2SIM"),
    "asn1c_commit": rev("$SRC/asn1c"),
    "e2ap": "v03.01", "e2sm_kpm": "v03.00", "e2sm_rc": "v03.01",
    "nori_patches": [{"file": __import__("os").path.basename(p),
                      "sha256": __import__("hashlib").sha256(open(p, "rb").read()).hexdigest()}
                     for p in sorted(__import__("glob").glob("/scripts/*.patch"))],
    "build_profile": "${BUILD_PROFILE}",
    "compiler": first(["g++", "--version"]),
    "os": first(["bash", "-c", ". /etc/os-release && echo \$PRETTY_NAME"]),
}
json.dump(info, open("/workspace/BUILD_INFO.json", "w"), indent=2)
print(json.dumps(info, indent=2))
PY

touch "$W/READY"
log "Bancada pronta. Execute cenários com: kubectl exec -it <pod> -- bash /scripts/run.sh <exemplo> <run_id> [args]"
exec sleep infinity
