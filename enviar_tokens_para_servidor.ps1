# Copia os tokens OAuth do Google (gerados localmente) para o servidor GCP
# Preencha os valores abaixo antes de rodar.
#
# Pré-requisito: gere os tokens localmente primeiro!
#   1. No .env, defina OAUTH_FLUXO_LOCAL=true
#   2. Rode o agente uma vez e autorize Gmail/Calendar no navegador
#      (isso cria config/credentials.json, config/token.json e config/token_gmail.json)
#   3. Depois rode este script para enviá-los ao servidor

# ── PREENCHER ─────────────────────────────────────────────────────────────────
$ServidorHost = "34.95.138.252"
$ServidorUser = "claudiolx_nunes"
$ChaveSSH     = "C:\Users\clxn2\.ssh\github_deploy"
$PastaRemota  = "~/agente_pessoal/config"
# ──────────────────────────────────────────────────────────────────────────────

$arquivos = @(
    "config\credentials.json",
    "config\token.json",
    "config\token_gmail.json"
)

foreach ($arquivo in $arquivos) {
    if (-not (Test-Path $arquivo)) {
        Write-Host "AVISO: $arquivo nao encontrado localmente - pulei." -ForegroundColor Yellow
        continue
    }
    Write-Host "Enviando $arquivo para ${ServidorUser}@${ServidorHost}:${PastaRemota}/ ..." -ForegroundColor Cyan
    scp -i $ChaveSSH $arquivo "${ServidorUser}@${ServidorHost}:${PastaRemota}/"
}

Write-Host ""
Write-Host "Pronto. Agora reinicie o servico no servidor:" -ForegroundColor Green
Write-Host "  ssh -i $ChaveSSH ${ServidorUser}@${ServidorHost} 'sudo systemctl restart agente-api'"
