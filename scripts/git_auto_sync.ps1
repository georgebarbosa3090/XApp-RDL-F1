<#
.SYNOPSIS
    Script de Monitoramento e Auto-Sync para GitHub (PowerShell)
    Projeto: xApp RDL - Fase 1
#>

param(
    [int]$Interval = 5
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  xApp RDL: Monitor de Atualizacao Automatica (PowerShell)" -ForegroundColor Cyan
Write-Host "  Intervalo de varredura: $Interval segundos" -ForegroundColor Cyan
Write-Host "  Pressione Ctrl+C para encerrar." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

while ($true) {
    $status = git status --porcelain 2>$null
    if ($status) {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Write-Host "`n[*] [$timestamp] Alteracoes detectadas no repositorio:" -ForegroundColor Yellow
        git status -s
        
        Start-Sleep -Seconds 3
        Write-Host "[*] Executando sincronizacao automatica..." -ForegroundColor Cyan
        & "$PSScriptRoot\git_sync.ps1" -Message "auto(sync): auto-update changes on $timestamp"
        Write-Host "[*] Aguardando novas alteracoes..." -ForegroundColor Gray
    }
    Start-Sleep -Seconds $Interval
}
