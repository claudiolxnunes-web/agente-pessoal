"""Integração com Google Calendar"""
import os
import pickle
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarTool:
    """Ferramenta para gerenciar Google Calendar"""

    def __init__(self, credentials_path="config/credentials.json", token_path="config/token.json"):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None
        self.autenticado = False

    def autenticar(self):
        """Autentica com OAuth2 do Google"""
        creds = None

        # Carrega token existente
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)

        # Se não existir ou estiver expirado, recria
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    print("⚠️  Arquivo credentials.json não encontrado!")
                    print("   Vá em https://console.cloud.google.com/ para criar.")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)

            # Salva token para próximas execuções
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('calendar', 'v3', credentials=creds)
        self.autenticado = True
        return True

    def listar_eventos(self, dias=7, max_resultados=10):
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

def _get_calendar() -> GoogleCalendarTool:
    global _calendar
    if _calendar is None:
        _calendar = GoogleCalendarTool()
        _calendar.autenticar()
    return _calendar

def criar_evento_calendar(titulo: str, data_hora: str, duracao_horas: int = 1,
                           descricao: str = "", local: str = "") -> str:
    try:
        from datetime import datetime, timedelta
        dt = datetime.strptime(data_hora, "%d/%m/%Y %H:%M")
        inicio = dt.isoformat()
        fim = (dt + timedelta(hours=duracao_horas)).isoformat()
        return _get_calendar().criar_evento(titulo, inicio, fim, descricao, local)
    except Exception as e:
        return f"Erro ao criar evento: {e}"

def listar_eventos_calendar(dias: int = 7) -> str:
    try:
        return _get_calendar().listar_eventos(dias=dias)
    except Exception as e:
        return f"Erro ao listar eventos: {e}"
