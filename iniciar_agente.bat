@echo off
cd /d "c:\Users\clxn2\OneDrive\Área de Trabalho\Agente_Pessoal"

:loop
echo %DATE% %TIME% - Iniciando Agente Pessoal...
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
echo %DATE% %TIME% - Servidor parou. Reiniciando em 5 segundos...
timeout /t 5 /nobreak
goto loop
