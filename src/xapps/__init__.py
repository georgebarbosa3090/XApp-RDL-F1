"""
Núcleos de decisão das xApps do projeto, todos guiados por KPM (decisão do autor de 2026-11-13: toda xApp
lê KPM e emite controle RC pela RDL). Cada classe herda de ``src.greenran.common.GreenRanXApp``: recebe
amostras KPM por célula (``observe``), lê a própria política A1 e propõe à RDL por RMR 30000.

- ``derivadas``: as reimplementações em Python inspiradas em xApps publicadas (Energy Saving, Traffic
  Steering) e a Rogue (teste de segurança).
- ``proprias``: as xApps próprias (decisão D2 do docs/16): load balancer, beamformer, ISAC, eMBB e a URLLC
  Slice Guard, que faz o papel do xSlice (até 2026-11-21, a derivada ``XSliceDerivada``).
"""
