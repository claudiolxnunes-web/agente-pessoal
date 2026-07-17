#!/usr/bin/env python3
"""
fechamento_comercial.py
=======================
Envia resumo diario das interacoes registradas no Agro RC CRM.
Roda todo dia util as 17h30 UTC (14h30 Brasilia).
"""
import os
import sys
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.agro_rc_crm import crm_get

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

TIPO_EMOJI = {
    "cotacao":  "💰",
    "visita":   "🚗",
    "ligacao":  "📞",
    "email":    "📧",
    "proposta": "📋",
    "outros":   "📝",
}


def buscar_interacoes_hoje() -> list:
    result = crm_get("/interactions", {"limit": 100})
    if not result.get("success"):
        return []

    # Filtra apenas as de hoje (UTC-3)
    tz_br = timezone(timedelta(hours=-3))
    hoje = datetime.now(tz_br).date()

    interacoes = []
    for i in result.get("data", []):
        data_str = i.get("created_at", "")
        try:
            data = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
            data_br = data.astimezone(tz_br).date()
            if data_br == hoje:
                interacoes.append(i)
        except Exception:
            continue
    return interacoes


def montar_resumo(interacoes: list) -> str:
    hoje = datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y")
    L = [f"<b>Fechamento Comercial — {hoje}</b>", ""]

    if not interacoes:
        L.append("Nenhuma interacao registrada hoje.")
        return "\n".join(L)

    L.append(f"Total de interacoes: <b>{len(interacoes)}</b>")
    L.append("")

    # Agrupa por tipo
    por_tipo = {}
    for i in interacoes:
        tipo = i.get("tipo", "outros")
        por_tipo.setdefault(tipo, []).append(i)

    for tipo, items in sorted(por_tipo.items()):
        emoji = TIPO_EMOJI.get(tipo, "📝")
        L.append(f"{emoji} <b>{tipo.upper()} ({len(items)})</b>")
        for i in items:
            cliente = i.get("cliente_nome", "?")
            obs = i.get("observacao", "")[:80]
            proximo = i.get("proximo_passo", "")
            linha = f"  • {cliente}: {obs}"
            if proximo:
                linha += f"\n    ➡ {proximo}"
            L.append(linha)
        L.append("")

    # Proximos passos do dia
    proximos = [i for i in interacoes if i.get("proxima_data")]
    if proximos:
        L.append("📅 <b>Proximos passos agendados:</b>")
        for i in proximos:
            L.append(f"  • {i.get('cliente_nome','?')} — {i.get('proximo_passo','')} ({i.get('proxima_data','')})")

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
        print("Fechamento enviado.")
        return True
    except Exception as e:
        print(f"Erro: {e}")
        return False


if __name__ == "__main__":
    interacoes = buscar_interacoes_hoje()
    mensagem = montar_resumo(interacoes)
    enviar_telegram(mensagem)
