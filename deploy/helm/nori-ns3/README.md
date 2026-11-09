# Chart `nori-ns3` — bancada ns-3 + 5G-LENA + NORI via Helm (sem Docker)

Implanta no cluster Kubernetes (k3s) uma bancada que compila e executa o **NORI** (`github.com/lasseufpa/nori`), o módulo E2 do ns-3 para 5G-LENA. Esta é a única pilha do projeto que produz tráfego **E2 real** (E2 Setup, Subscription, Indication KPM e Control RC), necessário para os gates G1, G3 e G4.

## Por que um chart e não Docker

O NORI é distribuído com um Dockerfile. Como o projeto usa Helm em vez de Docker, o chart reproduz os mesmos passos dentro de um pod `ubuntu:20.04`:

1. dependências do sistema iguais às do Dockerfile, mais `tcpdump`;
2. Nokia `asn1c`;
3. `e2sim` com o ASN.1 v3.01 do NORI e o patch X.691 — o patch é **extraído do próprio Dockerfile do NORI** em tempo de execução, sem cópia manual;
4. ns-3, 5G-LENA e NORI (em `contrib/nori`) nos commits fixados pelo NORI;
5. `./ns3 configure -d optimized --enable-examples` e `./ns3 build -j2`.

As compilações ficam no volume persistente (`/workspace`); a cada reinício o pod só reinstala o que vive no sistema de arquivos efêmero.

## Versões fixadas (`values.yaml`)

| Componente | Commit | Observação |
| :-- | :-- | :-- |
| NORI | `8a30867` | HEAD em 2026-10-29 |
| ns-3 | `ab4cce0` | ns-3.42, fixado pelo NORI |
| 5G-LENA | `78b7179` | fixado pelo NORI |
| e2sim | `da6f82f` | fixado pelo NORI |
| asn1c (Nokia) | `8b8028a` | o NORI usa o HEAD; fixado aqui |

Se algum commit não existir, a preparação falha (sem fallback). O NORI implementa **E2AP v3.01 / E2SM-KPM v3.00 / E2SM-RC v3.01** e espera um **Near-RT RIC O-RAN SC Release I**. O codec E2 atual da xApp RDL (v02.03 / RC v01.03 local) não é compatível com esses formatos; a interoperabilidade E2 exige alinhá-lo.

## Pré-requisitos

- k3s ativo e kubeconfig legível: serviço systemd permanente instalado uma vez com `sudo bash scripts/install_k3s_service.sh` (alternativa sem mudança permanente: `sudo systemd-run --unit=k3s k3s server --write-kubeconfig-mode 644`, a refazer a cada reinício do WSL). Não use `sudo k3s server ... &`: em segundo plano o `sudo` não consegue pedir a senha e o processo fica parado.
  ```bash
  export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
  kubectl get nodes
  ```
- Memória livre: clusters k3d e o Rancher (Docker) disputam a memória do WSL com o RIC e o NORI. Pare-os antes (reversível com `sudo k3d cluster start <nome>` e `sudo docker start <container>`):
  ```bash
  sudo k3d cluster stop --all
  sudo docker ps --format '{{.Names}}\t{{.Image}}'   # localizar o container do Rancher
  sudo docker stop <container-do-rancher>
  ```
- WSL com 5 GB de memória (`%UserProfile%\.wslconfig`: `memory=5GB`). O limite do pod é 3,5 GiB com `build.jobs: 2`; não aumente os processos de compilação.
- ~25 GB livres no volume (`storage.size`).
- Para E2 real: Near-RT RIC Release I implantado com `bash scripts/deploy_ric_i_release.sh` ([guia operacional, seção 7.2](../../../docs/04_instalacao_e_operacao.md#72-near-rt-ric-o-ran-sc-release-i)), com o E2Term SCTP em `service-ricplt-e2term-sctp-alpha.ricplt:36422` (valor padrão de `ric.e2termAddress`).

## Uso

```bash
helm upgrade --install nori-ns3 deploy/helm/nori-ns3 -n ricsim --create-namespace \
  --set ric.e2termAddress=<servico-e2term-sctp>.<namespace>

# Acompanhar a preparação e a compilação ao vivo (a primeira vez leva horas)
kubectl -n ricsim logs -f deploy/nori-ns3

# Executar um cenário AO VIVO (saída em tempo real no terminal); variante com FlowMonitor
kubectl -n ricsim exec -it deploy/nori-ns3 -- \
  bash /scripts/run.sh nori-rc-slicing-flowmon nori_kpm_flowmon_seed1_p1s --seed 1 -- \
  --simTime=40 --ns3::E2Interface::E2Periodicity=1

# Trazer a evidência, recortar os eventos da xApp kpm-probe, dissecar o E2 e certificar
bash scripts/collect_nori_run.sh nori_kpm_flowmon_seed1_p1s
python scripts/certification/certify_chain.py
```

### Patches sobre o NORI

O NORI `8a30867` aplica o RIC Control E2SM-RC da função 300 (cotas de PRB por fatia no escalonador `NrRLMacSchedulerOfdma`), mas não responde com RIC Control Acknowledge: só a função 4 (E2SM-CCC) confirma. Sem ACK não há como correlacionar Control e desfecho (gate G3). O patch [`files/patches/0001-rc-control-ack.patch`](files/patches/0001-rc-control-ack.patch) faz a função 300 enviar `RICcontrolAcknowledge` com o RICrequestID e o RANfunctionID do pedido, reaproveitando o código que o próprio NORI usa na CCC, e só quando o Control foi decodificado com ao menos uma cota de PRB.

- O entrypoint aplica os patches de `files/patches/` de forma idempotente (`patch -R --dry-run` detecta o que já está aplicado) e recompila incrementalmente com `build.jobs` processos (~8 min na primeira vez); se um patch não se aplicar, aborta (código 7).
- `BUILD_INFO.json` e cada manifesto registram `nori_patches` (arquivo e sha256). O certificador (R6) só aceita patches listados em `reproducibility/versions.lock` com o mesmo sha256. Execuções com o NORI intacto continuam conferindo.
- O perfil `optimized` compila sem `NS_LOG`: os `NS_LOG_INFO` do NORI e do patch não aparecem no `stdout.log`; a evidência do Control e do ACK é o PCAP.

### Variante `nori-rc-slicing-flowmon`

O exemplo `nori-rc-slicing-demo` instala um FlowMonitor mas não o grava, e a política exige FlowMonitor para `NORI_NS3` (R9/R10). A cada início, o entrypoint gera `scratch/nori-rc-slicing-flowmon.cc` a partir do exemplo, inserindo após o único `Simulator::Run();`:

```cpp
monitor->CheckForLostPackets();
monitor->SerializeToXmlFile("flowmonitor.xml", true, true);
```

Desde a fase 4, a variante também grava `slice_series.csv` a cada 0,5 s simulado: contadores acumulados do FlowMonitor por UE/fatia (UE 0 = SST 1, UE 1 = SST 2), com o tempo simulado e o relógio de parede. É a medida de referência do efeito do Control, porque o KPM do NORI não mede vazão por UE.

A variante também imprime o registro dos UEs, que o build otimizado do ns-3 não mostra (os `NS_LOG` somem): callbacks nos traces RRC do 5G-LENA (`NrGnbRrc/NewUeContext`, `NrGnbRrc/ConnectionEstablished`, `NrUeRrc/InitialCellSelectionEndOk`, `NrUeRrc/ConnectionEstablished`) escrevem uma linha `[RDL-UE]` por evento, e um resumo a t = 0,3 s liga cada UE a IMSI, IP e fatia. No início, cada trace aparece como "conectado" ou "indisponível". `run.sh` registra no manifesto o cenário de conflito (`conflict_scenario`, de `RDL_SCENARIO`) e o baseline (`baseline`, de `RDL_BASELINE`) quando a execução vem de `scripts/run_nori_scenario.sh` ([docs/05](../../../docs/05_observabilidade_e_campanhas.md)).

Os fontes do NORI não são alterados. Se a variante mudar, o entrypoint reconfigura e compila só esse alvo (~20 s); se o ponto de inserção não for único, aborta (código 6). `run.sh` registra no manifesto o caminho e o sha256 do fonte compilado (`scenario_source`).

### Período dos relatórios KPM

O NORI ignora o *Event Trigger* da subscrição: envia duas Indications (nó e UE) a cada `E2Interface::E2Periodicity` de tempo simulado, padrão 0,01 s. Em 60 s isso dá ~12 mil Indications e um PCAP de ~16 MB; use `--ns3::E2Interface::E2Periodicity=1` para alinhar ao período de 1000 ms pedido pela xApp `kpm-probe`.

`run.sh` grava em `/workspace/runs/<run_id>/`: `execution_manifest.json` (backend `NORI_NS3`, commits reais lidos de `BUILD_INFO.json`, comando, horários, código de saída), `logs/stdout.log`, saídas do ns-3 em `raw/` e `raw/e2_sctp.pcap` com o tráfego SCTP/E2 capturado por `tcpdump`, além de `hashes.sha256`. Ele não sobrescreve execuções existentes.

## Limites

- Primeira implantação em 2026-11-08 (k3s v1.26.5, WSL com 5 GB): preparo + compilação em ~32 min com `build.jobs: 2`; reinício do pod sem recompilar em ~6 min. Correções feitas nessa implantação:
  - o git do root recusava os checkouts do usuário `developer` ("dubious ownership"): `ns3_commit` e `nr_commit` saíam vazios no `BUILD_INFO.json` e um reinício abortaria em `pin()`; o entrypoint marca os repositórios como seguros;
  - um reinício refazia checkout e extração do NORI, mudando os horários dos fontes e levando o próximo `./ns3` a recompilar tudo com todos os núcleos; agora os fontes só são tocados quando a compilação vai acontecer, e `run.sh` usa `./ns3 run --no-build`;
  - os exemplos do NORI esperam um IP em `--ipE2TermRic`; `run.sh` resolve o nome do serviço do E2Term para o ClusterIP e registra `e2term_ip` no manifesto.
- O PCAP é dissecado fora do pod ([`e2_pcap_dissect.py`](../../../scripts/certification/e2_pcap_dissect.py), com confirmação do tshark); o diretório da execução não é alterado.
- Em tempo real, a simulação fica mais lenta que o relógio: 60 s simulados levaram ~3 min com Indications a cada 10 ms.
- Sem RIC acessível, o NORI não completa o E2 Setup: a execução só gera FlowMonitor.
