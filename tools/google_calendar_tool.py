"""Integração com Google Calendar"""
import os
import logging
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar']

logger = logging.getLogger(__name__)

class GoogleCalendarTool:
    """Ferramenta para gerenciar Google Calendar"""

    def __init__(self, credentials_path="config/credentials.json", token_path="config/token.json"):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.autenticado = False

    def autenticar(self):
        """Autentica com OAuth2 do Google.

        Em servidor (sem navegador), o token deve ser gerado uma vez na
        máquina local (com OAUTH_FLUXO_LOCAL=true) e o arquivo
        config/token.json copiado para o servidor — aqui só fazemos a
        renovação automática via refresh_token.
        """
        creds = None

        # Carrega token existente em JSON
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        if creds and not creds.valid and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                logger.error(f"Falha ao renovar token Google Calendar: {e}")
                creds = None

        # Se ainda não temos credenciais válidas, decide como obter
        if not creds or not creds.valid:
            if os.getenv("OAUTH_FLUXO_LOCAL", "false").lower() == "true":
                if not os.path.exists(self.credentials_path):
                    logger.error("config/credentials.json não encontrado para autorizar o Calendar.")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            else:
                logger.error(
                    "Token do Google Calendar ausente ou expirado sem refresh_token. "
                    "Gere o token localmente (rode com OAUTH_FLUXO_LOCAL=true em uma "
                    "máquina com navegador) e copie config/token.json para o servidor."
                )
                return False

            # Salva token para próximas execuções
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('calendar', 'v3', credentials=creds)
        self.autenticado = True
        return True

    def listar_eventos(self, dias=7, max_resultados=50):
        """Lista eventos dos próximos N dias"""
        if not self.autenticado:
            if not self.autenticar():
                return "Não foi possível autenticar com Google Calendar."

        try:
            agora = datetime.utcnow().isoformat() + 'Z'
            futuro = (datetime.utcnow() + timedelta(days=dias)).isoformat() + 'Z'

            eventos_result = self.service.events().list(
                calendarId='primary',
                timeMin=agora,
                timeMax=futuro,
                maxResults=max_resultados,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            eventos = eventos_result.get('items', [])

            if not eventos:
                return f"Nenhum evento encontrado nos próximos {dias} dias."

            resultado = f"📅 Eventos nos próximos {dias} dias:\n\n"
            for evento in eventos:
                inicio = evento['start'].get('dateTime', evento['start'].get('date'))
                fim = evento['end'].get('dateTime', evento['end'].get('date'))
                titulo = evento.get('summary', 'Sem título')

                # Formata data
                try:
                    dt = datetime.fromisoformat(inicio.replace('Z', '+00:00'))
                    inicio_fmt = dt.strftime("%d/%m %H:%M")
                except:
                    inicio_fmt = inicio

                resultado += f"• {inicio_fmt} - {titulo}\n"
                if 'location' in evento:
                    resultado += f"  📍 {evento['location']}\n"
                if 'description' in evento:
                    desc = evento['description'][:100]
                    resultado += f"  📝 {desc}\n"
                resultado += "\n"

            return resultado

        except HttpError as e:
            return f"Erro ao acessar Google Calendar: {e}"

    def criar_evento(self, titulo, data_inicio, data_fim=None, descricao="", local=""):
        """Cria um novo evento no calendário"""
        if not self.autenticado:
            if not self.autenticar():
                return "Não foi possível autenticar com Google Calendar."

        try:
            # Se data_fim não fornecida, assume 1 hora de duração
            if data_fim is None:
                dt_inicio = datetime.fromisoformat(data_inicio)
                dt_fim = dt_inicio + timedelta(hours=1)
                data_fim = dt_fim.isoformat()

            evento = {
                'summary': titulo,
                'description': descricao,
                'location': local,
                'start': {
                    'dateTime': data_inicio,
                    'timeZone': 'America/Sao_Paulo',
                },
                'end': {
                    'dateTime': data_fim,
                    'timeZone': 'America/Sao_Paulo',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},
                        {'method': 'popup', 'minutes': 30},
                    ],
                },
            }

            evento_criado = self.service.events().insert(
                calendarId='primary', 
                body=evento
            ).execute()

            return f"✅ Evento criado: {evento_criado.get('htmlLink')}"

        except Exception as e:
            return f"Erro ao criar evento: {e}"

    def deletar_evento(self, evento_id):
        """Deleta um evento pelo ID"""
        if not self.autenticado:
            if not self.autenticar():
                return "Não foi possível autenticar."

        try:
            self.service.events().delete(calendarId='primary', eventId=evento_id).execute()
            return "✅ Evento deletado com sucesso."
        except Exception as e:
            return f"Erro ao deletar: {e}"


# ── Funções de módulo usadas em coordenador.py ────────────────────────────────

_calendar: GoogleCalendarTool | None = None

def _get_calendar() -> GoogleCalendarTool | None:
    global _calendar
    if _calendar is not None and _calendar.autenticado:
        return _calendar
    tool = GoogleCalendarTool()
    if not tool.autenticar():
        return None
    _calendar = tool
    return _calendar

def criar_evento_calendar(titulo: str, data_hora: str, duracao_horas: int = 1,
                           descricao: str = "", local: str = "") -> str:
    try:
        from datetime import datetime, timedelta
        cal = _get_calendar()
        if cal is None:
            return "❌ Não foi possível autenticar com o Google Calendar. Verifique config/credentials.json e config/token.json."
        dt = datetime.strptime(data_hora, "%d/%m/%Y %H:%M")
        inicio = dt.isoformat()
        fim = (dt + timedelta(hours=duracao_horas)).isoformat()
        return cal.criar_evento(titulo, inicio, fim, descricao, local)
    except Exception as e:
        return f"Erro ao criar evento: {e}"

def listar_eventos_calendar(dias: int = 7) -> str:
    try:
        cal = _get_calendar()
        if cal is None:
            return "❌ Não foi possível autenticar com o Google Calendar. Verifique config/credentials.json e config/token.json."
        return cal.listar_eventos(dias=dias)
    except Exception as e:
        return f"Erro ao listar eventos: {e}"
