@echo off
REM ==============================================================================
REM Abre 2 Terminais no Windows com 3 Janelas Cada no WSL Ubuntu (Total 6 Janelas)
REM ==============================================================================
echo [INFO] Abrindo Terminal 1 (Rede ^& Telemetria E2: 3 Janelas)...
echo [INFO] Abrindo Terminal 2 (Cognicao ^& Acao E2SM-RC: 3 Janelas)...

where wt.exe >nul 2>&1
if %ERRORLEVEL% equ 0 (
    start "" wt.exe -w new --title "Terminal 1: Rede & Telemetria E2 (3 Janelas)" wsl.exe -d Ubuntu-20.04 -u root bash -c "launch_terminal1_ran_telemetry.sh"
    start "" wt.exe -w new --title "Terminal 2: Cognicao & Acao E2SM-RC (3 Janelas)" wsl.exe -d Ubuntu-20.04 -u root bash -c "launch_terminal2_cognitive_action.sh"
) else (
    start "Terminal 1: Rede & Telemetria E2 (3 Janelas)" wsl.exe -d Ubuntu-20.04 -u root bash -c "launch_terminal1_ran_telemetry.sh"
    start "Terminal 2: Cognicao & Acao E2SM-RC (3 Janelas)" wsl.exe -d Ubuntu-20.04 -u root bash -c "launch_terminal2_cognitive_action.sh"
)
echo [OK] 2 Terminais abertos com 3 janelas cada!
