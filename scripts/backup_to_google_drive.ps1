# PowerShell wrapper for automated Google Drive backup of XApp-RDL-F2
Write-Host "Iniciando processo de backup automatizado para o Google Drive..." -ForegroundColor Cyan

$uvPath = "C:\Users\george.barbosa\.local\bin\uv.exe"
if (Test-Path $uvPath) {
    & $uvPath run --with google-api-python-client --with google-auth-httplib2 --with google-auth-oauthlib python scripts/backup_to_google_drive.py
} else {
    python scripts/backup_to_google_drive.py
}
