# ==============================================================================
# Script: scripts/start_auto_sync.ps1
# Inicia o daemon auto_git_sync.py em background (processo independente)
# ==============================================================================

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$syncScript = Join-Path $scriptDir "auto_git_sync.py"
$logFile = Join-Path $repoRoot "auto_git_sync.log"
$errFile = Join-Path $repoRoot "auto_git_sync.err.log"

$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    $pythonExe = $venvPython
} else {
    $pythonExe = "python"
}

$existing = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    try {
        $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        $cmd -like "*auto_git_sync.py*"
    } catch {
        $false
    }
}

if ($existing) {
    Write-Host "[INFO] O processo Auto Git Sync já está em execução (PID: $($existing.Id))." -ForegroundColor Yellow
    exit 0
}

Write-Host "Iniciando Auto Git Sync em segundo plano usando: $pythonExe" -ForegroundColor Cyan
Write-Host "Logs serão gravados em: $logFile" -ForegroundColor Cyan

$process = Start-Process -FilePath $pythonExe `
    -ArgumentList "`"$syncScript`"" `
    -WorkingDirectory $repoRoot `
    -RedirectStandardOutput $logFile `
    -RedirectStandardError $errFile `
    -WindowStyle Hidden `
    -PassThru

Write-Host "[OK] Auto Git Sync iniciado com sucesso com PID $($process.Id)!" -ForegroundColor Green
