"""
Governança hierárquica das xApps sob a RDL (doc 09 §2.6 e doc 11).

Nível 1 — plataforma: registro de xApps (identidade pela origem RMR), descritores e NetworkPolicy
          (``deploy/helm/ric-governance``) tornam a RDL o único caminho de RIC Control.
Nível 2 — interceptação: RIC Control (12040) de xApps de terceiros, roteado para a RDL, vira
          proposta; a RDL responde ACK ou FAILURE (``interception``).
Nível 3 — conflito implícito: KPM incoerente com a ação confirmada vira ``ConflictType.IMPLICIT``
          (``src/core/implicit_conflict.py``).
Nível 4 — Non-RT/SMO: o rApp de governança (``rapps/governance_rapp.py``) lê o relatório da RDL e
          ajusta modos e tetos de prioridade por política A1, ou recomenda retirar a xApp.
"""
