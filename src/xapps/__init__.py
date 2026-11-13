"""
Núcleos de decisão das xApps do projeto, todos guiados por KPM (decisão do autor de 2026-11-13: toda xApp
lê KPM e emite controle RC pela RDL). Cada classe herda de ``src.greenran.common.GreenRanXApp``: recebe
amostras KPM por célula (``observe``), lê a própria política A1 e propõe à RDL por RMR 30000.

- ``derivadas``: as reimplementações em Python inspiradas em xApps publicadas (xSlice, Energy Saving,
  Traffic Steering) e a Rogue (teste de segurança).
- ``proprias``: as xApps próprias que fazem os papéis sem original público (decisão D2 do docs/16):
  load balancer, beamformer, ISAC e eMBB.
"""
