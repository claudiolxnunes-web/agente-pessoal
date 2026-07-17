"""Integração com Yahoo Mail via IMAP/SMTP"""
import os
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

class YahooMailTool:
    """Ferramenta para gerenciar Yahoo Mail via IMAP/SMTP"""

    def __init__(self, email: str = None, senha_app: str = None):
        """
        Para Yahoo, use 'senha de app' (não a senha normal):
        1. Acesse Account Info > Account Security
        2. Gere 'App Password'
        """
        self.email = email or os.getenv("YAHOO_EMAIL")
        self.senha = senha_app or os.getenv("YAHOO_APP_PASSWORD")
        self.imap_server = "imap.mail.yahoo.com"
        self.smtp_server = "smtp.mail.yahoo.com"
        self.imap_port = 993
        self.smtp_port = 587
        self.autenticado = False

    def _conectar_imap(self) -> imaplib.IMAP4_SSL:
        """Conecta ao servidor IMAP"""
        mail = imaplib.IMAP4_SSL(self.imap_server)
        mail.login(self.email, self.senha)
        return mail

    def _conectar_smtp(self) -> smtplib.SMTP:
        """Conecta ao servidor SMTP"""
        server = smtplib.SMTP(self.smtp_server, self.smtp_port)
        server.starttls()
        server.login(self.email, self.senha)
        return server

    def listar_emails(self, pasta: str = "inbox", max_results: int = 10,
                     nao_lidos: bool = False) -> str:
        """Lista emails do Yahoo"""
        try:
            mail = self._conectar_imap()
            mail.select(pasta)

            # Busca emails
            if nao_lidos:
                status, messages = mail.search(None, "UNSEEN")
            else:
                status, messages = mail.search(None, "ALL")

            if status != "OK" or not messages[0]:
                return "📧 Nenhum email encontrado."

            ids = messages[0].split()[-max_results:]

            output = f"📧 Emails Yahoo ({'não lidos' if nao_lidos else 'todos'}):\n\n"

            for msg_id in reversed(ids):
                status, msg_data = mail.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue

                msg = email.message_from_bytes(msg_data[0][1])
                assunto = email.header.decode_header(msg["Subject"])[0][0]
                if isinstance(assunto, bytes):
                    assunto = assunto.decode("utf-8", errors="replace")

                remetente = msg["From"]
                data = msg["Date"]

                # Verifica se está lido
                status, flags = mail.fetch(msg_id, "(FLAGS)")
                is_unread = b"\\Seen" not in flags[0]
                prefix = "🔴" if is_unread else "✉️"

                output += f"{prefix} **{assunto}**\n"
                output += f"   De: {remetente}\n"
                output += f"   Data: {data}\n\n"

            mail.close()
            mail.logout()
            return output

        except Exception as e:
            return f"❌ Erro Yahoo Mail: {e}"

    def ler_email(self, msg_id: str) -> str:
        """Lê conteúdo de um email"""
        try:
            mail = self._conectar_imap()
            mail.select("inbox")

            status, msg_data = mail.fetch(msg_id.encode(), "(RFC822)")
            if status != "OK":
                return "Email não encontrado."

            msg = email.message_from_bytes(msg_data[0][1])
            assunto = email.header.decode_header(msg["Subject"])[0][0]
            if isinstance(assunto, bytes):
                assunto = assunto.decode("utf-8", errors="replace")

            remetente = msg["From"]

            # Extrai corpo
            corpo = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        corpo = part.get_payload(decode=True).decode("utf-8", errors="replace")
                        break
            else:
                corpo = msg.get_payload(decode=True).decode("utf-8", errors="replace")

            # Marca como lido
            mail.store(msg_id.encode(), "+FLAGS", "\\Seen")

            mail.close()
            mail.logout()

            return f"📧 **{assunto}**\nDe: {remetente}\n\n{corpo[:2000]}"

        except Exception as e:
            return f"❌ Erro: {e}"

    def enviar_email(self, para: str, assunto: str, corpo: str,
                     html: bool = False) -> str:
        """Envia email via Yahoo SMTP"""
        try:
            server = self._conectar_smtp()

            msg = MIMEMultipart()
            msg["From"] = self.email
            msg["To"] = para
            msg["Subject"] = assunto

            content_type = "html" if html else "plain"
            msg.attach(MIMEText(corpo, content_type, "utf-8"))

            server.send_message(msg)
            server.quit()

            return f"✅ Email enviado para {para} via Yahoo"

        except Exception as e:
            return f"❌ Erro ao enviar: {e}"

    def deletar_email(self, msg_id: str) -> str:
        """Move email para lixeira"""
        try:
            mail = self._conectar_imap()
            mail.select("inbox")
            mail.store(msg_id.encode(), "+FLAGS", "\\Deleted")
            mail.expunge()
            mail.close()
            mail.logout()
            return "🗑️ Email movido para lixeira."
        except Exception as e:
            return f"❌ Erro: {e}"

    def info(self) -> str:
        """Retorna informações da conta"""
        if not self.email:
            return "❌ Yahoo Mail não configurado."
        return f"📧 Yahoo Mail: {self.email}"


# ── Funções de módulo ─────────────────────────────────────────────────────────
def listar_emails_yahoo(max_results: int = 10, apenas_nao_lidos: bool = False) -> str:
    try:
        tool = YahooMailTool()
        return tool.listar_emails(max_results=max_results, nao_lidos=apenas_nao_lidos)
    except Exception as e:
        return f"Erro Yahoo Mail: {e}"

def enviar_email_yahoo(destinatario: str, assunto: str, corpo: str) -> str:
    try:
        return YahooMailTool().enviar_email(destinatario, assunto, corpo)
    except Exception as e:
        return f"Erro ao enviar Yahoo: {e}"
