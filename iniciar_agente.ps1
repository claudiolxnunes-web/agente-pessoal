# Script para iniciar o Agente Pessoal como servidor 24/7
Set-Location "c:\Users\clxn2\OneDrive\Área de Trabalho\Agente_Pessoal"

# Aguarda rede estar disponível (útil no boot)
Start-Sleep -Seconds 10

# Inicia o servidor uvicorn com auto-restart em caso de falha
while ($true) {
    Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Iniciando Agente Pessoal..." -ForegroundColor Green
    python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
    Write-Host "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') - Servidor parou. Reiniciando em 5 segundos..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}
