<#
.SYNOPSIS
    Script de Sincronizacao Rapida e Segura com o GitHub (PowerShell)
    Projeto: xApp RDL - Fase 1
#>

param(
    [string]$Message = "",
    [string]$Branch = "main",
    [string]$Remote = "origin"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Sincronizacao do Repositorio xApp RDL -> GitHub ($Branch)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Fetch remoto
git fetch $Remote $Branch --quiet 2>$null

$status = git status --porcelain
if ($status) {
    Write-Host "[+] Alteracoes locais detectadas:" -ForegroundColor Yellow
    git status -s

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    git tag -f "backup/pre-sync-latest" HEAD 2>$null

    if ([string]::IsNullOrWhiteSpace($Message)) {
        $summary = (git status -s | Select-Object -First 3 | ForEach-Object { ($_ -split '\s+')[1] }) -join ' '
        $Message = "chore(sync): update repository ($summary) [$timestamp]"
    }

    Write-Host "[+] Commitando alteracoes: `"$Message`"" -ForegroundColor Green
    git add -A
    git commit -m "$Message"
} else {
    Write-Host "[i] Nenhuma alteracao pendente para commit." -ForegroundColor Gray
}

Write-Host "[+] Sincronizando com $Remote/$Branch (pull --rebase)..." -ForegroundColor Cyan
git pull --rebase $Remote $Branch

Write-Host "[+] Enviando commits para o GitHub..." -ForegroundColor Cyan
git push $Remote $Branch

$latestHash = git rev-parse --short HEAD
Write-Host "============================================================" -ForegroundColor Green
Write-Host " [OK] Repositorio sincronizado com sucesso no GitHub!" -ForegroundColor Green
Write-Host "      Commit atual: $latestHash" -ForegroundColor Green
Write-Host "      Branch:       $Branch" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
