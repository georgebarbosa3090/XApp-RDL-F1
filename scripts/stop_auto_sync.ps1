# ==============================================================================
# Script: scripts/stop_auto_sync.ps1
# Interrompe o processo de background auto_git_sync.py
# ==============================================================================

$stopped = 0
Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        if ($cmd -like "*auto_git_sync.py*") {
            Write-Host "Encerrando processo Auto Git Sync (PID: $($_.Id))..." -ForegroundColor Yellow
            Stop-Process -Id $_.Id -Force
            $stopped++
        }
    } catch {
        # Ignora processos sem permissão de consulta WMI
    }
}

if ($stopped -gt 0) {
    Write-Host "[OK] $stopped processo(s) do Auto Git Sync encerrado(s)." -ForegroundColor Green
} else {
    Write-Host "[INFO] Nenhum processo ativo do Auto Git Sync foi encontrado." -ForegroundColor Cyan
}
