# xApp RDL (Resource and Decision Layer) - Fase 1 (H-RDL)

## 1. Visão Geral
A **xApp RDL** é um orquestrador determinístico para o O-RAN Near-RT RIC. Sua principal função é arbitrar intenções de controle concorrentes provenientes de múltiplas xApps em uma rede, decidindo a alocação ótima de recursos utilizando regras de negócio rígidas e uma **função de utilidade multiobjetivo heurística** (H-RDL).

## 2. Contribuição (Fase 1)
Este projeto visa resolver o problema crítico de **Conflitos de Ação** no O-RAN, onde xApps independentes podem tentar modificar os mesmos parâmetros de rádio de forma divergente (ex: QoS vs. Energy Savings). A contribuição científica central desta primeira fase é demonstrar que a delegação da ação final para a RDL consegue reduzir conflitos utilizando *detecção + regras + restrições de segurança*, sem depender inicialmente de aprendizado de máquina (MARL). Isso compõe o Baseline formal (H0).

## 3. Arquitetura
A arquitetura foi desenhada utilizando Domain-Driven Design (DDD) e Clean Architecture, dividindo o software em:
* gents/: Motores de percepção (análise combinatória em lote na Decision Window de 200ms), raciocínio (Heurísticas Determinísticas TVS/EEVS) e *Safety Guards*.
* coordination/: Despachante de controle e correlacionador de ACKs.
* domain/: Classes imutáveis (Proposals, Conflicts, Decisions).
* e2/: Decodificadores e Encoders específicos de KPM e RC (isolamento de ASN.1).
* infrastructure/: Clientes RMR, SDL (Redis), Subscription Manager e Config Manager.
* observability/: Métricas no padrão Prometheus (ex: dl_kpm_indications_total), health e logs em JSON (Structlog).

**Fluxo Decisório (H-RDL):**
`mermaid
flowchart TD
    A[xApps] -->|ActionProposal| B(Decision Window 200ms)
    B --> C(PerceptionAgent)
    C -->|ConflictEvent| D(Rule Resolver / Heurístico)
    D --> E(Safety Guard)
    E -->|Validação Física| F(E2SM-RC Encoder)
`

## 4. Requisitos
* Linux / Ubuntu 20.04+ (Bare-metal ou WSL2)
* Python 3.10+ (ou ambiente via `uv` / `venv`)
* Docker CE 20.10+
* Kubernetes v1.22+ (k3s, k3d, RKE2 ou kubeadm)
* Helm 3.x
* Ferramentas de build: `make`, `build-essential`
* Plataforma Near-RT RIC da OSC (O-RAN Software Community) ou ambiente simulado.

## 5. Instalação e Execução Rápida

### Passo a passo completo para instalação, validação e execução:

```bash
# 1. Instalar o make e dependências essenciais no Ubuntu
sudo apt update && sudo apt install -y make build-essential git python3-pip

# 2. Clonar e entrar no diretório do projeto
git clone https://github.com/georgebarbosa3090/XApp-RDL-F1.git
cd XApp-RDL-F1

# 3. Construir a imagem Docker da xApp RDL
make build
# (ou para build forçado sem cache):
make build-no-cache

# 4. Teste Rápido de Execução (Smoke Test standalone via Docker)
docker rm -f xapp-rdl-test 2>/dev/null || true
docker run -d --name xapp-rdl-test -p 8090:8080 -p 8091:8081 -e USE_FAKE_SDL=true iqos-xapp-rdl:1.1.0
sleep 3
curl -i http://localhost:8090/health
curl http://localhost:8091/metrics | grep -E "rdl_|dl_"
docker logs xapp-rdl-test
docker rm -f xapp-rdl-test

# 5. Executar a suíte de testes unitários
make test

# 6. Aplicar os manifestos no Kubernetes (Namespace ricxapp)
kubectl create namespace ricxapp --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f deploy/kubernetes/deployment.yaml
kubectl apply -f deploy/kubernetes/service.yaml

# 7. Acompanhar os pods e logs estruturados em tempo real
kubectl get pods -n ricxapp -w
kubectl logs -l app=ricxapp-iqos-xapp-rdl -n ricxapp -f
```

---

## 6. Configuração
Toda a configuração é estrita e centralizada. Modifique o arquivo [configs/config-file.json](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase1/configs/config-file.json) para alterar credenciais do SDL, portas RMR e timers de controle. O [configs/schema.json](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase1/configs/schema.json) blinda a configuração contra erros.

---

## 7. Execução Local para Desenvolvimento (Standalone)
A RDL pode ser inicializada localmente com mocks de SDL e RMR:
```bash
export USE_FAKE_SDL=true
export RMR_SEED_RT=configs/routes.rt
python src/main.py
```
A saúde do app pode ser verificada em `http://localhost:8080/health` e as métricas em `http://localhost:8081/metrics`.

---

## 8. Implantação e Validação no OSC Near-RT RIC

Para o guia detalhado e completo de instalação da plataforma OSC, consulte o documento:
📖 [Guia de Instalação e Validação no OSC Near-RT RIC (docs/08_guia_instalacao_osc_near_rt_ric.md)](file:///c:/Users/george.barbosa/.gemini/antigravity/scratch/iqos-xapp-rdl-phase1/docs/08_guia_instalacao_osc_near_rt_ric.md)

### Resumo dos passos para o Near-RT RIC:

1. **Garantir o banco de dados SDL (Redis):**
   ```bash
   kubectl apply -n ricplt -f - <<EOF
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: deployment-ricplt-dbaas-redis
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: ricplt-dbaas
     template:
       metadata:
         labels:
           app: ricplt-dbaas
       spec:
         containers:
         - name: redis
           image: redis:6.2-alpine
           ports:
           - containerPort: 6379
   ---
   apiVersion: v1
   kind: Service
   metadata:
     name: service-ricplt-dbaas-tcp
   spec:
     selector:
       app: ricplt-dbaas
     ports:
     - port: 6379
       targetPort: 6379
   EOF
   ```

2. **Onboarding via `dms_cli` / AppMgr (Opcional):**
   ```bash
   make onboard
   make install
   ```

3. **Validação e Testes:**
   ```bash
   # Rodar suíte de testes unitários com pytest
   make test

   # Coletar evidências da bateria de testes
   ./scripts/collect_evidence.sh EXPERIMENTO_H0_BASELINE
   ```

---

## 9. Troubleshooting & Problemas Conhecidos

### 1. Erro de carregamento da biblioteca RMR (`librmr_si.so: cannot open shared object file`)
* **Sintoma:** Ao iniciar a xApp, o Python lança `OSError: librmr_si.so: cannot open shared object file: No such file or directory` durante o `import ricxappframe`.
* **Causa:** O `ricxappframe` busca exatamente o arquivo `librmr_si.so` (sem sufixo de versão) via `ctypes`. O pacote binário padrão `rmr_4.9.0_amd64.deb` instala `librmr_si.so.4`, enquanto o link simbólico `librmr_si.so` vem no pacote de desenvolvimento `rmr-dev_4.9.0_amd64.deb`.
* **Solução:** O `docker/Dockerfile` instala tanto `rmr` quanto `rmr-dev`, executa `ldconfig` e define `ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/local/lib64:${LD_LIBRARY_PATH}`.

### 2. Falha de compilação no Docker (`error: command 'gcc' failed` para `hiredis`)
* **Sintoma:** O build do Docker falha na etapa de instalação com erro de compilação C para `hiredis` ou extensões nativas.
* **Causa:** Tentativa de compilação direta na imagem enxuta de runtime (`python:3.10-slim`) que não possui compiladores C por padrão de segurança.
* **Solução:** O Dockerfile utiliza abordagem *Multi-Stage Build*: o estágio `builder` compila todos os `.whl` com `gcc` e `python3-dev`, e o estágio de runtime apenas instala os binários estritamente offline (`--no-index --find-links=/tmp/wheels`).

### 3. Conflito de portas no host (`Bind for 0.0.0.0:8080 failed: port is already allocated`)
* **Sintoma:** Ao rodar `docker run`, o Docker acusa que a porta `8080` já está alocada.
* **Causa:** A porta `8080` é amplamente utilizada por serviços do Near-RT RIC (AppMgr, Ingress, etc.) ou outros containers locais.
* **Solução:** Em testes manuais/standalone, mapeie para portas alternativas no host:
  ```bash
  docker run -d --name xapp-rdl-test -p 8090:8080 -p 8091:8081 -e USE_FAKE_SDL=true iqos-xapp-rdl:1.1.0
  curl http://localhost:8090/health
  curl http://localhost:8091/metrics
  ```

### 4. Falha de comunicação com o SDL (Redis) ou comandos não chegam à rádio-base
* **Verificação 1:** Em produção, garanta que a variável de ambiente `USE_FAKE_SDL` esteja definida como `"false"`.
* **Verificação 2:** Certifique-se de que o pod do Redis (`service-ricplt-dbaas-tcp`) no namespace `ricplt` esteja ativo e respondendo na porta `6379`.
* **Verificação 3:** Inspecione as métricas de indicações e decisões:
  ```bash
  curl http://localhost:8081/metrics | grep -E "rdl_|dl_"
  ```
* **Verificação 4:** Acompanhe os logs filtrando por erros:
  ```bash
  kubectl logs -l app=ricxapp-iqos-xapp-rdl -n ricxapp -f | grep '"level":"error"'
  ```

---

## 10. Limitações
- O decodificador KPM atualmente opera uma validação binária leve devido à necessidade de bibliotecas C para a tradução APER estrita.

---

## 11. Roadmap
- [x] Concluir testes de laboratório do baseline (H0).
- [ ] Evoluir para a Fase 2 (CA-RDL - Context-Aware).
- [ ] Reinserir MAPPO (RDL-C) para resolução de domínios complexos/indiretos.
