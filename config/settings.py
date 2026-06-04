"""Configurações centralizadas do Agente Pessoal v3.0"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.2"))

    # Agente
    AGENT_NAME = os.getenv("AGENT_NAME", "MeuAgente")
    USER_NAME = os.getenv("USER_NAME", "Usuario")

    # Memória
    MEMORY_DIR = os.path.join(os.path.dirname(__file__), "..", "memory", "chroma_db")

    # Google (Calendar + Gmail)
    GOOGLE_CALENDAR_ENABLED = os.getenv("GOOGLE_CALENDAR_ENABLED", "false").lower() == "true"
    GMAIL_ENABLED = os.getenv("GMAIL_ENABLED", "false").lower() == "true"
    GOOGLE_CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "credentials.json")
    GOOGLE_TOKEN_PATH = os.path.join(os.path.dirname(__file__), "token.json")

    # Notion
    NOTION_ENABLED = os.getenv("NOTION_ENABLED", "false").lower() == "true"
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

    # WhatsApp
    WHATSAPP_ENABLED = os.getenv("WHATSAPP_ENABLED", "false").lower() == "true"
    WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
    WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
    WHATSAPP_WEBHOOK_URL = os.getenv("WHATSAPP_WEBHOOK_URL")

    # Telegram
    TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    # Web Search
    SERPAPI_KEY = os.getenv("SERPAPI_KEY")

    # Agendamento
    AUTO_SCHEDULE_ENABLED = os.getenv("AUTO_SCHEDULE_ENABLED", "true").lower() == "true"

    # Voz/Áudio
    VOICE_ENABLED = os.getenv("VOICE_ENABLED", "true").lower() == "true"
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

    # Banco de Dados
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///memory/agente.db")

    # API REST
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_DEBUG = os.getenv("API_DEBUG", "false").lower() == "true"

    # Outlook / Microsoft 365
    OUTLOOK_ENABLED = os.getenv("OUTLOOK_ENABLED", "false").lower() == "true"
    OUTLOOK_CLIENT_ID = os.getenv("OUTLOOK_CLIENT_ID")
    OUTLOOK_CLIENT_SECRET = os.getenv("OUTLOOK_CLIENT_SECRET")
    OUTLOOK_TENANT_ID = os.getenv("OUTLOOK_TENANT_ID")
    OUTLOOK_ACCESS_TOKEN = os.getenv("OUTLOOK_ACCESS_TOKEN")

    # Yahoo Mail
    YAHOO_MAIL_ENABLED = os.getenv("YAHOO_MAIL_ENABLED", "false").lower() == "true"
    YAHOO_EMAIL = os.getenv("YAHOO_EMAIL")
    YAHOO_APP_PASSWORD = os.getenv("YAHOO_APP_PASSWORD")

    # ProtonMail
    PROTONMAIL_ENABLED = os.getenv("PROTONMAIL_ENABLED", "false").lower() == "true"
    PROTONMAIL_API_TOKEN = os.getenv("PROTONMAIL_API_TOKEN")
    PROTONMAIL_USERNAME = os.getenv("PROTONMAIL_USERNAME")

    @classmethod
    def validate(cls):
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY não configurada!")
        return True


# Aliases de módulo para imports diretos em coordenador.py e outros módulos
OPENAI_API_KEY    = Config.OPENAI_API_KEY
MODEL_NAME        = Config.MODEL_NAME
TEMPERATURE       = Config.TEMPERATURE
AGENT_NAME        = Config.AGENT_NAME
USER_NAME         = Config.USER_NAME
GMAIL_ENABLED     = Config.GMAIL_ENABLED
OUTLOOK_ENABLED   = Config.OUTLOOK_ENABLED
YAHOO_MAIL_ENABLED = Config.YAHOO_MAIL_ENABLED
PROTONMAIL_ENABLED = Config.PROTONMAIL_ENABLED
