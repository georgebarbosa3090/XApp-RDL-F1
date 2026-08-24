# Matriz de Conformidade Zero to Hero

| Requisito do artigo | Arquivo do projeto | Evidência | Estado |
| :--- | :--- | :--- | :--- |
| Descriptor | configs/xapp_descriptor.json | validação schema | CONFORME |
| RMR | src/rdl_xapp.py | rotas + testes | CONFORME |
| SDL | src/infrastructure/sdl_repository.py | persistência SDL | CONFORME |
| Subscrição | src/infrastructure/subscription_manager.py | SUB_REQ enviada | CONFORME |
| E2AP | src/e2/e2ap_decoder.py | APER via pycrate | CONFORME |
| KPM | src/e2/kpm_decoder.py | APER via pycrate | CONFORME |
| Controle | src/e2/rc_encoder.py | APER nativo E2SM-RC | CONFORME |
| Healthcheck | src/observability/health_server.py | /health + /ready | CONFORME |
| Métricas | src/observability/metrics.py | Nomenclatura exata | CONFORME |
| Segurança | src/agents/refinement_agent.py | Safety Guard PRB | CONFORME |
| Container | docker/Dockerfile | non-root + multi-stage | CONFORME |
| K8s | deploy/kubernetes/deployment.yaml | resources limits | CONFORME |
