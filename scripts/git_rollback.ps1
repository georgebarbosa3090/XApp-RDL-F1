<#
.SYNOPSIS
    Script de Rollback Seguro (PowerShell)
    Projeto: xApp RDL - Fase 1
#>

param(
    [string]$Commit = "",
    [int]$Steps = 1,
    [switch]$Push,
    [switch]$Clean,
    [switch]$List,
    [string]$Branch = "main",
    [string]$Remote = "origin"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  xApp RDL: Ferramenta de Rollback e Restauracao Segura" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

if ($List) {
    Write-Host "[i] Historico dos ultimos 10 commits:" -ForegroundColor Yellow
    git log -n 10 --graph --pretty=format:'%C(yellow)%h%Creset -%C(auto)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset'
    Write-Host "`n[i] Tags de seguranca disponiveis:" -ForegroundColor Yellow
    git tag -l "backup/*" | Select-Object -Last 10
    exit 0
}

if ($Clean) {
    Write-Host "[!] Descartando alteracoes nao commitadas locais..." -ForegroundColor Yellow
    git restore . 2>$null
    git clean -fd
    Write-Host "[OK] Diretorio de trabalho limpo." -ForegroundColor Green
    exit 0
}

$currentShort = git rev-parse --short HEAD
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupTag = "backup/rollback_${timestamp}_${currentShort}"

Write-Host "[+] Criando ponto de seguranca: $backupTag..." -ForegroundColor Cyan
git tag $backupTag HEAD

$destCommit = if (-not [string]::IsNullOrWhiteSpace($Commit)) { $Commit } else { "HEAD~$Steps" }

Write-Host "[+] Executando rollback para: $destCommit..." -ForegroundColor Yellow
git reset --hard $destCommit

$newShort = git rev-parse --short HEAD
Write-Host "[OK] Rollback local concluido com sucesso!" -ForegroundColor Green
Write-Host "     Commit anterior: $currentShort" -ForegroundColor Green
Write-Host "     Commit atual:    $newShort" -ForegroundColor Green
Write-Host "     Tag de seguranca criada: $backupTag" -ForegroundColor Green

if ($Push) {
    Write-Host "[!] Propagando rollback para o GitHub ($Remote/$Branch)..." -ForegroundColor Yellow
    git push --force-with-lease $Remote $Branch
    Write-Host "[OK] Rollback sincronizado com o GitHub!" -ForegroundColor Green
} else {
    Write-Host "`n[Dica] Para propagar para o GitHub remoto execute: `n       git push --force-with-lease origin main`nou use o parametro -Push" -ForegroundColor Gray
}
