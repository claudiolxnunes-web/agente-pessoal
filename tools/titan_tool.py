"""
Integração com Titan Mail / GoDaddy (contato@bpfconsult.com.br)
Usa IMAP para leitura e SMTP para envio.
"""
import os, sys, imaplib, smtplib, email, logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

TITAN_EMAIL    = os.getenv("TITAN_EMAIL", "contato@bpfconsult.com.br")
TITAN_PASSWORD = os.getenv("TITAN_PASSWORD", "")
TITAN_IMAP     = os.getenv("TITAN_IMAP_HOST", "imap.titan.email")
TITAN_SMTP     = os.getenv("TITAN_SMTP_HOST", "smtp.titan.email")
TITAN_IMAP_PORT = int(os.getenv("TITAN_IMAP_PORT", "993"))
TITAN_SMTP_PORT = int(os.getenv("TITAN_SMTP_PORT", "587"))
TITAN_ENABLED  = os.getenv("TITAN_ENABLED", "false").lower() == "true"


def _decode_header_str(value: str) -> str:
    parts = decode_header(value or "")
    result = []
    for part, charset in parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def list_emails(max_results: int = 10, apenas_nao_lidos: bool = False) -> list:
    """Lista e-mails do Titan via IMAP. Retorna lista de dicts."""
    if not TITAN_ENABLED:
        return [{"de": "—", "assunto": "⚠️ Titan não habilitado. Configure TITAN_ENABLED=true no .env", "data": "—"}]
    if not TITAN_PASSWORD:
        return [{"de": "—", "assunto": "❌ TITAN_PASSWORD não configurado no .env", "data": "—"}]

    try:
        mail = imaplib.IMAP4_SSL(TITAN_IMAP, TITAN_IMAP_PORT)
        mail.login(TITAN_EMAIL, TITAN_PASSWORD)
        mail.select("inbox")

        criterio = "UNSEEN" if apenas_nao_lidos else "ALL"
        _, ids = mail.search(None, criterio)
        id_list = ids[0].split()[-max_results:]

        mensagens = []
        for mid in reversed(id_list):
            _, dados = mail.fetch(mid, "(RFC822)")
            msg = email.message_from_bytes(dados[0][1])
            remetente = _decode_header_str(msg.get("From", "?"))
            assunto   = _decode_header_str(msg.get("Subject", "Sem assunto"))
            data      = msg.get("Date", "?")[:16]
            mensagens.append({"de": remetente, "assunto": assunto, "data": data})

        mail.logout()
        return mensagens

    except Exception as e:
        logger.error(f"Erro IMAP Titan: {e}")
        return [{"de": "—", "assunto": f"❌ Erro ao listar e-mails: {e}", "data": "—"}]


def send_email(destinatario: str, assunto: str, corpo: str) -> str:
    """Envia e-mail pelo Titan via SMTP."""
    if not TITAN_ENABLED:
        return "⚠️ Titan não habilitado. Configure TITAN_ENABLED=true no .env"
    if not TITAN_PASSWORD:
        return "❌ TITAN_PASSWORD não configurado no .env"

    try:
        msg = MIMEMultipart()
        msg["From"]    = TITAN_EMAIL
        msg["To"]      = destinatario
        msg["Subject"] = assunto
        msg.attach(MIMEText(corpo, "plain", "utf-8"))

        with smtplib.SMTP(TITAN_SMTP, TITAN_SMTP_PORT) as servidor:
            servidor.ehlo()
            servidor.starttls()
            servidor.login(TITAN_EMAIL, TITAN_PASSWORD)
            servidor.sendmail(TITAN_EMAIL, destinatario, msg.as_string())

        return f"✅ E-mail enviado via Titan para {destinatario}"

    except Exception as e:
        logger.error(f"Erro SMTP Titan: {e}")
        return f"❌ Erro ao enviar e-mail Titan: {e}"


class TitanTool:
    """Wrapper orientado a objeto para o Titan Mail."""

    def list_emails(self, max_results: int = 10, apenas_nao_lidos: bool = False) -> list:
        return list_emails(max_results, apenas_nao_lidos)

    def send_email(self, destinatario: str, assunto: str, corpo: str) -> str:
        return send_email(destinatario, assunto, corpo)
