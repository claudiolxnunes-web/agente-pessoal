#!/usr/bin/env python3
"""
lembrete_precos_minerais.py
===========================
Envia lembrete semanal (segunda-feira) via Telegram para atualizar
precos manuais de minerais e insumos de nutricao animal.
"""
import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.precos_manuais_store import carregar_precos

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

# Insumos que voce quer monitorar — adicione ou remova conforme necessario
INSUMOS_MONITORADOS = [
    "fosfato bicalcico",
    "enxofre ventilado",
    "enxofre 70% lavado",
    "ureia pecuaria",
    "farelo de soja",
    "farelo de trigo",
    "DDGS 30%",
    "DDGS 32%",
    "DDGS 42%",
    "farelo de algodao",
    "sulfato de cobre",
    "sulfato de zinco",
    "sulfato de manganes",
    "selenito de sodio",
    "sulfato de cobalto",
    "iodato de calcio",
    "oxido de magnesio",
    "oxido de zinco",
    "sal mineral bovinos",
]


def montar_lembrete() -> str:
    precos = carregar_precos()
    hoje = datetime.now().strftime("%d/%m/%Y")
    L = [
        "<b>Lembrete semanal - Precos de Minerais e Insumos</b>",
        f"Data: {hoje}",
        "",
        "Atualize os precos abaixo enviando mensagens no formato:",
        "<code>atualiza preco INGREDIENTE R$X/ton</code>",
        "",
    ]

    # Separa em: cadastrados (com data) e nao cadastrados
    cadastrados = []
    nao_cadastrados = []

    for insumo in INSUMOS_MONITORADOS:
        chave = insumo.lower().strip()
        if chave in precos:
            item = precos[chave]
            cadastrados.append(
                f"• {item['ingrediente']}: {item['valor']} "
                f"(ref. {item['atualizado_em']})"
            )
        else:
            nao_cadastrados.append(f"• {insumo} — <i>sem registro</i>")

    if cadastrados:
        L.append("<b>Precos cadastrados:</b>")
        L.extend(cadastrados)
        L.append("")

    if nao_cadastrados:
        L.append("<b>Sem registro ainda:</b>")
        L.extend(nao_cadastrados)
        L.append("")

    L.append("Envie <code>listar precos manuais</code> para ver todos os precos cadastrados.")
    return "\n".join(L)


def enviar_telegram(mensagem: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Token ou chat_id nao configurados.")
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": mensagem,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=15
        )
        r.raise_for_status()
        print("Lembrete enviado.")
        return True
    except Exception as e:
        print(f"Erro ao enviar: {e}")
        return False


if __name__ == "__main__":
    mensagem = montar_lembrete()
    enviar_telegram(mensagem)
