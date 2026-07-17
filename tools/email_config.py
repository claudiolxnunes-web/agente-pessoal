"""Validação centralizada de configuração de e-mail."""
import os

from config.settings import Config


def verificar_gmail() -> str | None:
    if not Config.GMAIL_ENABLED:
        return "⚠️ Gmail desabilitado. Configure GMAIL_ENABLED=true no .env"
    if not os.path.exists(Config.GOOGLE_CREDENTIALS_PATH):
        return (
            "❌ Falta config/credentials.json (OAuth Google).\n"
            "   1. Google Cloud Console → Credentials → OAuth Desktop\n"
            "   2. Baixe o JSON e salve como config/credentials.json\n"
            "   3. Rode o agente uma vez para autorizar no navegador"
        )
    return None


def verificar_yahoo() -> str | None:
    if not Config.YAHOO_MAIL_ENABLED:
        return "⚠️ Yahoo Mail desabilitado. Configure YAHOO_MAIL_ENABLED=true no .env"
    if not Config.YAHOO_EMAIL:
        return "❌ YAHOO_EMAIL não configurado no .env"
    if not Config.YAHOO_APP_PASSWORD:
        return (
            "❌ YAHOO_APP_PASSWORD não configurado no .env.\n"
            "   Use senha de aplicativo (Account Security → Generate app password), "
            "não a senha normal da conta."
        )
    return None


def verificar_outlook() -> str | None:
    if not Config.OUTLOOK_ENABLED:
        return "⚠️ Outlook desabilitado. Configure OUTLOOK_ENABLED=true no .env"
    if not Config.OUTLOOK_CLIENT_ID:
        return "❌ OUTLOOK_CLIENT_ID não configurado no .env"
    token_file = os.path.join(Config.PROJECT_ROOT, "config", "outlook_token.json")
    if not Config.OUTLOOK_ACCESS_TOKEN and not os.path.exists(token_file):
        return (
            "❌ Token Outlook ausente. Configure OUTLOOK_ACCESS_TOKEN no .env "
            "ou execute o fluxo OAuth (gerar_url_autorizacao → trocar_code_por_token)."
        )
    return None


def verificar_proton() -> str | None:
    if not Config.PROTONMAIL_ENABLED:
        return "⚠️ ProtonMail desabilitado. Configure PROTONMAIL_ENABLED=true no .env"
    if not Config.PROTONMAIL_API_TOKEN:
        return "❌ PROTONMAIL_API_TOKEN não configurado no .env"
    if not Config.PROTONMAIL_USERNAME:
        return "❌ PROTONMAIL_USERNAME não configurado no .env"
    return None


def normalizar_senha_app(senha: str | None) -> str:
    """Remove espaços comuns em senhas de app copiadas do provedor."""
    return (senha or "").replace(" ", "")
