"""Ferramentas disponíveis para o agente — imports opcionais para dependências externas"""

def _try_import(module_path, class_name):
    try:
        import importlib
        mod = importlib.import_module(module_path, package="tools")
        return getattr(mod, class_name, None)
    except (ImportError, ModuleNotFoundError):
        return None


GoogleCalendarTool = _try_import(".google_calendar_tool", "GoogleCalendarTool")
GmailTool          = _try_import(".gmail_tool", "GmailTool")
NotionTool         = _try_import(".notion_tool", "NotionTool")
WhatsAppTool       = _try_import(".whatsapp_tool", "WhatsAppTool")
TelegramTool       = _try_import(".telegram_tool", "TelegramTool")
OutlookTool        = _try_import(".outlook_tool", "OutlookTool")
YahooMailTool      = _try_import(".yahoo_mail_tool", "YahooMailTool")
ProtonMailTool     = _try_import(".protonmail_tool", "ProtonMailTool")
TitanTool          = _try_import(".titan_tool", "TitanTool")

# Ferramentas que não dependem de libs externas específicas
try:
    from .web_search_tool import WebSearchTool
except (ImportError, ModuleNotFoundError):
    WebSearchTool = None

try:
    from .document_tool import DocumentTool
except (ImportError, ModuleNotFoundError):
    DocumentTool = None

try:
    from .scheduler_tool import SchedulerTool
except (ImportError, ModuleNotFoundError):
    SchedulerTool = None

try:
    from .voice_tool import VoiceTool
except (ImportError, ModuleNotFoundError):
    VoiceTool = None

__all__ = [
    "GoogleCalendarTool", "NotionTool", "WebSearchTool",
    "GmailTool", "WhatsAppTool", "TelegramTool",
    "DocumentTool", "SchedulerTool", "VoiceTool",
    "OutlookTool", "YahooMailTool", "ProtonMailTool", "TitanTool"
]
