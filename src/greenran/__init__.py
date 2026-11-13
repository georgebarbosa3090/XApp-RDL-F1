# Autor: George Barbosa
# Software próprio do projeto xApp RDL. Licença: Apache-2.0 (ver LICENSE e AUTHORS.md).
"""
xApps do GreenRAN (OpenRAN@Brasil, testbed UFPA), conforme a proposta GreenRAN (A1.5 e A1.6):

- ``ranslicer_greenran``: RANSlicer-GreenRAN — cota de PRB por fatia guiada por intenção (eMBB das câmeras de
  vigilância × mMTC dos sensores), com política aprendida opcional sob escudo de segurança.
- ``energysaver_greenran``: EnergySaver-GreenRAN — padrões sazonais de carga por célula, desligamento de
  RU em baixa demanda com evacuação prévia dos UEs para a vizinha (borda entre duas RUs) e religamento.

As duas propõem à xApp RDL (RMR 30000) e recebem o resultado (30001); a RDL coordena as duas na escala
Near-RT, e o rApp-ResourceOptimizer (``rapps/greenran_resource_optimizer.py``) as coordena na escala
Non-RT por A1 (tipos 21000 e 21001). Doc 12.
"""
