# Guia de Implantação e Execução

O projeto xApp RDL foi refatorado para ter empacotamento determinístico, sem rodar como usuário root.

## 1. O Dockerfile (Multi-stage Build)
O container é construído em duas etapas (*Multi-stage*) para reduzir a imagem final.
1. Na primeira etapa, compilamos as dependências pesadas (`wheels`) num ambiente que contém o GCC.
2. Na segunda etapa, jogamos fora o lixo de compilação. Criamos um usuário Linux chamado `xapp` (ID 1000, não-root) que rodará a aplicação de forma segura e sem permissões de administrador. A aplicação recebe o `PYTHONPATH=/app`.

Para construí-lo:
```bash
make build
```

## 2. Variáveis de Ambiente e Healthchecks
A RDL usa as seguintes variáveis inseridas no arquivo `deployment.yaml`:
- `USE_FAKE_SDL`: Se verdadeiro, mocka o Redis. Se for para a rede real, deve ser `false`.
- `RMR_SEED_RT`: Caminho injetado apontando para as rotas RMR geradas.

**Kubernetes Probes:**
Nós expomos a porta `8080` (HTTP) para testes vitais do Kubernetes Kubelet:
- **LivenessProbe** pinga o `/health`. Se não responder UP, o Kubernetes mata o pod.
- **ReadinessProbe** pinga o `/ready`. Ele só responde UP se a configuração centralizada for válida, RMR estiver iniciado e o SDL estiver conectado. Senão, ele barra a entrada de requisições E2.

## 3. Implantação via dms_cli
Você não usa o `kubectl apply` diretamente para enviar a xApp para a OSC. O fluxo oficial de produção é:

```bash
# 1. Enviar o pacote descriptor para validação do AppMgr
make onboard

# 2. Requerer que o RIC busque a imagem e crie o Deploy/SVC
make install

# 3. Observar status
make status
```

Se desejar subir de forma avulsa para testar rede (bypassing the AppMgr temporariamente), temos os manifestos de base presentes em `deploy/kubernetes/`.
