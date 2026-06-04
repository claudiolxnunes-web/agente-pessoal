"""Webhook WhatsApp para o Agente Pessoal"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import uvicorn
from config.settings import Config
from agents.coordenador import conversar
from tools import WhatsAppTool

app = FastAPI(title="Agente Pessoal - WhatsApp Webhook")

# Inicializa ferramenta WhatsApp
whatsapp = None
if Config.WHATSAPP_ENABLED:
    whatsapp = WhatsAppTool(
        Config.WHATSAPP_PHONE_NUMBER_ID,
        Config.WHATSAPP_ACCESS_TOKEN,
        Config.WHATSAPP_VERIFY_TOKEN
    )

@app.get("/webhook")
async def verify_webhook(request: Request):
    """Verificação do webhook pelo Meta"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if whatsapp and whatsapp.verificar_webhook(mode, token, challenge):
        return Response(content=challenge, media_type="text/plain")

    return JSONResponse(content={"error": "Verificação falhou"}, status_code=403)

@app.post("/webhook")
async def receive_message(request: Request):
    """Recebe mensagens do WhatsApp"""
    data = await request.json()

    if not whatsapp:
        return JSONResponse(content={"status": "WhatsApp não configurado"})

    # Processa mensagem
    msg = whatsapp.processar_webhook(data)

    if msg:
        numero = msg["de"]
        texto = msg["texto"]

        # Processa via agente
        resposta = conversar(texto, thread_id=f"whatsapp_{numero}")

        # Envia resposta de volta
        whatsapp.enviar_mensagem(numero, resposta)

        # Marca como lida
        whatsapp.marcar_lida(msg["id"])

    return JSONResponse(content={"status": "ok"})

@app.get("/")
async def root():
    return {
        "status": "online",
        "agente": Config.AGENT_NAME,
        "whatsapp": Config.WHATSAPP_ENABLED
    }

if __name__ == "__main__":
    if not Config.WHATSAPP_ENABLED:
        print("❌ WhatsApp não configurado. Verifique .env")
        print("WHATSAPP_ENABLED=true")
        sys.exit(1)

    print("🚀 WhatsApp Webhook iniciado!")
    print(f"🌐 URL: {Config.WHATSAPP_WEBHOOK_URL}")
    print("Configure esta URL no Facebook Developers
")

    uvicorn.run(app, host="0.0.0.0", port=8000)
