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
- Para E2 real: Near-RT RIC Release I implantado com `bash scripts/deploy_ric_i_release.sh` ([guia operacional, seção 7.2](../../../docs/02_guia_operacional_deploy_e_simulacao.md#72-near-rt-ric-o-ran-sc-release-i)), com o E2Term SCTP em `service-ricplt-e2term-sctp-alpha.ricplt:36422` (valor padrão de `ric.e2termAddress`).

## Uso

```bash
helm upgrade --install nori-ns3 deploy/helm/nori-ns3 -n ricsim --create-namespace \
  --set ric.e2termAddress=<servico-e2term-sctp>.<namespace>

# Acompanhar a preparação e a compilação ao vivo (a primeira vez leva horas)
kubectl -n ricsim logs -f deploy/nori-ns3

# Executar um cenário AO VIVO (saída em tempo real no terminal)
kubectl -n ricsim exec -it deploy/nori-ns3 -- \
  bash /scripts/run.sh nori-rc-slicing-demo nori_rc_demo_seed1 --seed 1 -- --simTime=10

# Trazer a evidência para o repositório e certificar
POD=$(kubectl -n ricsim get pod -l app.kubernetes.io/name=nori-ns3 -o jsonpath='{.items[0].metadata.name}')
kubectl -n ricsim cp "$POD:/workspace/runs/nori_rc_demo_seed1" experiments/runs/nori_rc_demo_seed1
python scripts/certification/certify_chain.py --run nori_rc_demo_seed1
```

`run.sh` grava em `/workspace/runs/<run_id>/`: `execution_manifest.json` (backend `NORI_NS3`, commits reais lidos de `BUILD_INFO.json`, comando, horários, código de saída), `logs/stdout.log`, saídas do ns-3 em `raw/` e `raw/e2_sctp.pcap` com o tráfego SCTP/E2 capturado por `tcpdump`, além de `hashes.sha256`. Ele não sobrescreve execuções existentes.

## Limites

- Primeira implantação em 2026-11-08 (k3s v1.26.5, WSL com 5 GB): preparo + compilação em ~32 min com `build.jobs: 2`; reinício do pod sem recompilar em ~6 min. Correções feitas nessa implantação:
  - o git do root recusava os checkouts do usuário `developer` ("dubious ownership"): `ns3_commit` e `nr_commit` saíam vazios no `BUILD_INFO.json` e um reinício abortaria em `pin()`; o entrypoint marca os repositórios como seguros;
  - um reinício refazia checkout e extração do NORI, mudando os horários dos fontes e levando o próximo `./ns3` a recompilar tudo com todos os núcleos; agora os fontes só são tocados quando a compilação vai acontecer, e `run.sh` usa `./ns3 run --no-build`;
  - os exemplos do NORI esperam um IP em `--ipE2TermRic`; `run.sh` resolve o nome do serviço do E2Term para o ClusterIP e registra `e2term_ip` no manifesto.
- O PCAP comprova tráfego SCTP real, mas a separação das mensagens E2 por tipo (Setup, Indication, Control, ACK) ainda depende de dissecação (`tshark`), sem a qual o certificador não aprova G1/G3.
- Sem RIC acessível, o NORI não completa o E2 Setup: a execução só gera FlowMonitor.
