"""Integração com Gmail - Ler, enviar e gerenciar emails"""
import os
import pickle
import base64
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class GmailTool:
    """Ferramenta para gerenciar Gmail"""

    def __init__(self, credentials_path="config/credentials.json", token_path="config/token_gmail.json"):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.autenticado = False

    def autenticar(self):
        """Autentica com OAuth2 do Google"""
        creds = None

        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    return False
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('gmail', 'v1', credentials=creds)
        self.autenticado = True
        return True

    def listar_emails(self, query="is:inbox", max_results=10):
        """Lista emails com filtro opcional"""
        if not self.autenticado:
            if not self.autenticar():
                return "Não foi possível autenticar com Gmail."

        try:
            resultados = self.service.users().messages().list(
                userId='me', q=query, maxResults=max_results
            ).execute()

            mensagens = resultados.get('messages', [])
            if not mensagens:
                return "Nenhum email encontrado."

            output = f"📧 Emails (filtro: {query}):\n\n"

            for msg in mensagens:
                msg_data = self.service.users().messages().get(
                    userId='me', id=msg['id'], format='metadata',
                    metadataHeaders=['Subject', 'From', 'Date']
                ).execute()

                headers = msg_data['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sem assunto')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Desconhecido')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

                # Marca como lido visualmente
                is_unread = 'UNREAD' in msg_data.get('labelIds', [])
                prefix = "🔴" if is_unread else "✉️"

                output += f"{prefix} **{subject}**\n"
                output += f"   De: {sender}\n"
                output += f"   Data: {date[:16]}\n"
                output += f"   ID: {msg['id'][:12]}...\n\n"

            return output

        except HttpError as e:
            return f"Erro ao acessar Gmail: {e}"

    def ler_email(self, msg_id):
        """Lê conteúdo completo de um email"""
        if not self.autenticado:
            if not self.autenticar():
                return "Não autenticado."

        try:
            msg = self.service.users().messages().get(userId='me', id=msg_id).execute()

            headers = msg['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Sem assunto')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Desconhecido')

            # Extrai corpo do email
            body = ""
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body'].get('data', '')
                        if data:
                            body = base64.urlsafe_b64decode(data).decode('utf-8')
                            break
            else:
                data = msg['payload']['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')

            # Marca como lido
            self.service.users().messages().modify(
                userId='me', id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()

            return f"📧 **{subject}**\nDe: {sender}\n\n{body[:1000]}"

        except Exception as e:
            return f"Erro ao ler email: {e}"

    def enviar_email(self, para, assunto, corpo, cc=None):
        """Envia um novo email"""
        if not self.autenticado:
            if not self.autenticar():
                return "Não autenticado."

        try:
            message = MIMEMultipart()
            message['to'] = para
            message['subject'] = assunto
            if cc:
                message['cc'] = cc

            msg = MIMEText(corpo)
            message.attach(msg)

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            sent = self.service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()

            return f"✅ Email enviado! ID: {sent['id'][:12]}..."

        except Exception as e:
            return f"Erro ao enviar: {e}"

    def marcar_lido(self, msg_id):
        """Marca email como lido"""
        if not self.autenticado:
            return "Não autenticado."

        try:
            self.service.users().messages().modify(
                userId='me', id=msg_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return "✅ Marcado como lido."
        except Exception as e:
            return f"Erro: {e}"

    def deletar_email(self, msg_id):
        """Move email para lixeira"""
        if not self.autenticado:
            return "Não autenticado."

        try:
            self.service.users().messages().trash(userId='me', id=msg_id).execute()
            return "🗑️ Email movido para lixeira."
        except Exception as e:
            return f"Erro: {e}"


# ── Funções de módulo usadas em coordenador.py ────────────────────────────────

_gmail: GmailTool | None = None

def _get_gmail() -> GmailTool:
    global _gmail
    if _gmail is None:
        _gmail = GmailTool()
        _gmail.autenticar()
    return _gmail

def listar_emails_gmail(max_results: int = 10, apenas_nao_lidos: bool = False) -> str:
    try:
        g = _get_gmail()
        query = "is:unread" if apenas_nao_lidos else "is:inbox"
        return g.listar_emails(query=query, max_results=max_results)
    except Exception as e:
        return f"Não foi possível conectar ao Gmail. Verifique suas credenciais. Erro: {e}"

def enviar_email_gmail(destinatario: str, assunto: str, corpo: str) -> str:
    try:
        return _get_gmail().enviar_email(destinatario, assunto, corpo)
    except Exception as e:
        return f"Erro ao enviar email Gmail: {e}"

def enviar_analise_para_crm(subject: str, sender: str, email_summary: str,
                             category: str = "geral", priority: str = "normal",
                             suggested_action: str = "revisar") -> str:
    return "OK"
