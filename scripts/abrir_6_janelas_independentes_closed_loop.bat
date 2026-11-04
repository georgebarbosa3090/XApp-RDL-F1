@echo off
REM ==============================================================================
REM Abre 6 Janelas Independentes no Windows para Cada Estágio do Closed-Loop
REM Projeto: xApp RDL (Fase 1 H-RDL) - Demonstração Física O-RAN ao Vivo
REM ==============================================================================
echo ==============================================================================
echo  ABRINDO AS 6 JANELAS INDEPENDENTES DO CLOSED-LOOP EM TEMPO REAL
echo ==============================================================================

where wt.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [INFO] Abrindo 6 Janelas no Windows Terminal...

    REM Janela 1: Simulador RAN ns-3 (Registros de UEs & Tráfego)
    start "" wt.exe -w new --title "JANELA 1: RAN ns-3 5G-LENA (Registros UE)" wsl.exe -d Ubuntu-20.04 -u root bash -c "echo '=== JANELA 1: SIMULADOR RAN ns-3 / 5G-LENA ==='; cd /root/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scenario_rdl_closed_loop_nori --seed=1001 --run=1 --simTime=60.0 --realtime=true --syncMode=BestEffort --enableE2=true --ricIp=127.0.0.1 --ricPort=36422 --gNbNum=2 --ueNumPerGnb=15'; echo ''; echo '[SIMULACAO FINALIZADA. Pressione Enter para sair]'; read line"

    REM Janela 2: Sinalização E2 / SCTP (E2Term)
    start "" wt.exe -w new --title "JANELA 2: SINALIZACAO E2 / SCTP (:36422)" wsl.exe -d Ubuntu-20.04 -u root bash -c "echo '=== JANELA 2: SINALIZACAO E2 / SCTP (E2Term) ==='; kubectl logs -n ricplt -l app=ricplt-e2term-alpha -f; exec bash"

    REM Janela 3: xApp H-RDL (Percepção, Raciocínio, Refinamento & Despacho)
    start "" wt.exe -w new --title "JANELA 3: xApp H-RDL (Decisao & Refinamento)" wsl.exe -d Ubuntu-20.04 -u root bash -c "echo '=== JANELA 3: xApp H-RDL (PERCEPCAO, DECISAO & REFINAMENTO) ==='; kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl -c iqos-xapp-rdl -f; exec bash"

    REM Janela 4: Injetor de Conflito Concorrente
    start "" wt.exe -w new --title "JANELA 4: INJETOR DE CONFLITO (xSlice vs TS)" wsl.exe -d Ubuntu-20.04 -u root bash -c "echo '=== JANELA 4: INJETOR DE CONFLITO ==='; echo 'Pressione ENTER para disparar propostas conflitantes...'; read line; cd /root/XApp-RDL-F1 && bash scripts/inject_traffic.sh; exec bash"

    REM Janela 5: Monitor de Métricas Prometheus
    start "" wt.exe -w new --title "JANELA 5: PROMETHEUS LIVE METRICS" wsl.exe -d Ubuntu-20.04 -u root bash -c "echo '=== JANELA 5: METRICAS CAUSAIS PROMETHEUS ==='; while true; do clear; echo '=== RDL METRICS LIVE (Porta :8081) ==='; curl -s http://localhost:8081/metrics | grep -E '^rdl_'; sleep 2; done"

    REM Janela 6: Fechamento de Malha & Controle E2SM-RC
    start "" wt.exe -w new --title "JANELA 6: FECHAMENTO DE MALHA E2SM-RC" wsl.exe -d Ubuntu-20.04 -u root bash -c "echo '=== JANELA 6: FECHAMENTO DE MALHA & RC ACK ==='; cd /root/XApp-RDL-F1 && python3 -u scripts/wsl_pane_monitors.py pane6; exec bash"

) else (
    echo [INFO] Abrindo em janelas CMD padrao...
    start "JANELA 1: RAN ns-3 (Registros UE)" wsl.exe -d Ubuntu-20.04 -u root bash -c "cd /root/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scenario_rdl_closed_loop_nori --seed=1001 --run=1 --simTime=60.0 --realtime=true --syncMode=BestEffort --enableE2=true --ricIp=127.0.0.1 --ricPort=36422'; exec bash"
    start "JANELA 2: SINALIZACAO E2 / SCTP" wsl.exe -d Ubuntu-20.04 -u root bash -c "kubectl logs -n ricplt -l app=ricplt-e2term-alpha -f; exec bash"
    start "JANELA 3: xApp H-RDL" wsl.exe -d Ubuntu-20.04 -u root bash -c "kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl -c iqos-xapp-rdl -f; exec bash"
    start "JANELA 4: INJETOR DE CONFLITO" wsl.exe -d Ubuntu-20.04 -u root bash -c "cd /root/XApp-RDL-F1 && bash scripts/inject_traffic.sh; exec bash"
    start "JANELA 5: PROMETHEUS METRICS" wsl.exe -d Ubuntu-20.04 -u root bash -c "while true; do clear; curl -s http://localhost:8081/metrics | grep -E '^rdl_'; sleep 2; done"
    start "JANELA 6: FECHAMENTO DE MALHA" wsl.exe -d Ubuntu-20.04 -u root bash -c "cd /root/XApp-RDL-F1 && python3 -u scripts/wsl_pane_monitors.py pane6; exec bash"
)

echo ==============================================================================
echo [OK] 6 Janelas independentes abertas com sucesso!
echo ==============================================================================
pause
