"""Tool de integracao com a plataforma WorkDev (VPS1) via /api/ai/voz."""
import os
import requests

WORKDEV_URL = os.getenv(
    "WORKDEV_API_URL",
    "https://workdev.bpfconsult.com.br/api/ai/voz",
)
WORKDEV_KEY = os.getenv("WORKDEV_API_KEY", "")


def executar_comando_workdev(texto: str) -> str:
    """Envia comando em texto livre para o Fable executar no WorkDev."""
    if not WORKDEV_KEY:
        return "WORKDEV_API_KEY nao configurada no .env do agente."
    try:
        r = requests.post(
            WORKDEV_URL,
            json={"texto": texto},
            headers={"X-API-Key": WORKDEV_KEY},
            timeout=90,
        )
        r.raise_for_status()
        data = r.json()
        return data.get("reply", "Sem resposta do WorkDev.")
    except requests.Timeout:
        return "WorkDev demorou demais para responder."
    except Exception as e:
        return f"Erro ao falar com o WorkDev: {type(e).__name__} - {e}"
