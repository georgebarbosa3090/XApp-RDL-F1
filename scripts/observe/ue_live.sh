#!/usr/bin/env bash
# Aba Registro de UEs: só as linhas [RDL-UE] da execução NORI em andamento (traces RRC do 5G-LENA:
# novo contexto no gNB, seleção de célula, conexão RRC no gNB e no UE, e UE -> IMSI, IP e fatia).
exec bash "$(dirname "$0")/nori_live.sh" '\[RDL-UE\]|^=== \['
