#!/usr/bin/env python3
"""
planejar_dia_diario.py
=======================
Dispara o planejamento diário (agenda Calendar + tarefas Notion), já
existente em agents/coordenador.py, e envia o resultado pro Telegram.

Pensado pra rodar via cron, de manhã, dentro do venv do agente_pessoal.
"""

import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [planejar_dia] %(levelname)s: %(message)s"
)
logger = logging.getLogger("planejar_dia")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.coordenador import planejar_dia
from tools.telegram_tool import enviar_mensagem_telegram

TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def main():
    logger.info("Gerando planejamento do dia...")
    if not TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_CHAT_ID não configurado no .env")
        return

    try:
        plano = planejar_dia()
    except Exception as e:
        logger.error("Falha ao gerar planejamento: %s", e)
        plano = f"Não consegui montar o planejamento de hoje (erro: {e})"

    mensagem = f"🗓️ Planejamento do dia\n\n{plano}"

    try:
        resultado = enviar_mensagem_telegram(TELEGRAM_CHAT_ID, mensagem)
        logger.info("Enviado: %s", resultado)
    except Exception as e:
        logger.error("Falha ao enviar mensagem: %s", e)


if __name__ == "__main__":
    main()
