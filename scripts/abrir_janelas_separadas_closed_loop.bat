@echo off
REM ==============================================================================
REM Abre 4 Janelas Separadas e Independentes no Windows para Monitoramento Live
REM Projeto: xApp RDL (Fase 1 H-RDL) - Demonstração Física Closed-Loop O-RAN
REM ==============================================================================
echo ==============================================================================
echo  INICIALIZANDO AS 4 JANELAS DEDICADAS DO CLOSED-LOOP EM TEMPO REAL
echo ==============================================================================
echo [INFO] Janela 1: Simulador RAN ns-3 / 5G-LENA (Registros de UEs & Enlaces)
echo [INFO] Janela 2: Sinalizacao E2 / SCTP (Handshake e E2Term no Near-RT RIC)
echo [INFO] Janela 3: xApp H-RDL (Percepcao, Raciocinio, Refinamento e Despacho)
echo [INFO] Janela 4: Injetor de Conflito & Telemetria Causal Prometheus
echo ==============================================================================

where wt.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [INFO] Utilizando Windows Terminal (wt.exe) para abrir janelas independentes...

    REM Janela 1: Simulador RAN ns-3
    start "" wt.exe -w new --title "JANELA 1: RAN ns-3 5G-LENA (Registros UE)" wsl.exe -d Ubuntu-20.04 -u root bash -c "echo '=== JANELA 1: SIMULADOR RAN ns-3 / 5G-LENA ==='; cd /root/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scenario_rdl_closed_loop_nori --seed=1001 --run=1 --simTime=60.0 --realtime=true --syncMode=BestEffort --enableE2=true --ricIp=127.0.0.1 --ricPort=36422 --gNbNum=2 --ueNumPerGnb=15'; echo ''; echo '[SIMULACAO FINALIZADA. Pressione Enter para sair]'; read line"

    REM Janela 2: Sinalização E2 / SCTP
    start "" wt.exe -w new --title "JANELA 2: SINALIZACAO E2 / SCTP (E2Term :36422)" wsl.exe -d Ubuntu-20.04 -u root bash -c "echo '=== JANELA 2: SINALIZACAO E2 / SCTP (E2Term :36422) ==='; kubectl logs -n ricplt -l app=ricplt-e2term-alpha -f; exec bash"

    REM Janela 3: xApp H-RDL
    start "" wt.exe -w new --title "JANELA 3: xApp H-RDL (Percepcao, Decisao & Refinamento)" wsl.exe -d Ubuntu-20.04 -u root bash -c "echo '=== JANELA 3: xApp H-RDL (PERCEPCAO, DECISAO & REFINAMENTO) ==='; kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl -c iqos-xapp-rdl -f; exec bash"

    REM Janela 4: Injetor de Conflito
    start "" wt.exe -w new --title "JANELA 4: INJETOR DE CONFLITO & PROMETHEUS" wsl.exe -d Ubuntu-20.04 -u root bash -c "echo '=== JANELA 4: INJECAO DE CONFLITO & TELEMETRIA ==='; echo 'Pressione ENTER para disparar propostas conflitantes (xSlice PRB=80% vs TrafficSteering PRB=40%)...'; read line; cd /root/XApp-RDL-F1 && bash scripts/inject_traffic.sh; echo ''; echo '--- Metricas Prometheus Live ---'; curl -s http://localhost:8081/metrics | grep -E '^rdl_'; exec bash"

) else (
    echo [INFO] Windows Terminal nao detectado. Abrindo janelas CMD padrao...

    start "JANELA 1: RAN ns-3 (Registros UE)" wsl.exe -d Ubuntu-20.04 -u root bash -c "cd /root/ns3-oran-workspace/ns-3-oran && ./ns3 run 'scenario_rdl_closed_loop_nori --seed=1001 --run=1 --simTime=60.0 --realtime=true --syncMode=BestEffort --enableE2=true --ricIp=127.0.0.1 --ricPort=36422'; exec bash"
    start "JANELA 2: SINALIZACAO E2 / SCTP" wsl.exe -d Ubuntu-20.04 -u root bash -c "kubectl logs -n ricplt -l app=ricplt-e2term-alpha -f; exec bash"
    start "JANELA 3: xApp H-RDL" wsl.exe -d Ubuntu-20.04 -u root bash -c "kubectl logs -n ricxapp -l app=ricxapp-iqos-xapp-rdl -c iqos-xapp-rdl -f; exec bash"
    start "JANELA 4: INJETOR DE CONFLITO" wsl.exe -d Ubuntu-20.04 -u root bash -c "cd /root/XApp-RDL-F1 && bash scripts/inject_traffic.sh; exec bash"
)

echo ==============================================================================
echo [OK] 4 Janelas independentes abertas com sucesso!
echo ==============================================================================
pause
