# PowerShell wrapper for automated Google Drive backup
Write-Host "Iniciando processo de backup automatizado para o Google Drive..." -ForegroundColor Cyan

$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
$userLocalUv = Join-Path $env:USERPROFILE ".local\bin\uv.exe"

if ($uvCmd) {
    & $uvCmd.Source run --with google-api-python-client --with google-auth-httplib2 --with google-auth-oauthlib python scripts/backup_to_google_drive.py
} elseif (Test-Path $userLocalUv) {
    & $userLocalUv run --with google-api-python-client --with google-auth-httplib2 --with google-auth-oauthlib python scripts/backup_to_google_drive.py
} else {
    python scripts/backup_to_google_drive.py
}
