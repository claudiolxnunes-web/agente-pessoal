import sys, json, requests, threading, webbrowser
from urllib.parse import unquote, urlparse, parse_qs
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
sys.path.insert(0, '.')
from config.settings import OUTLOOK_CLIENT_ID, OUTLOOK_CLIENT_SECRET

code_recebido = None

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global code_recebido
        parsed = parse_qs(urlparse(self.path).query)
        if 'code' in parsed:
            code_recebido = unquote(parsed['code'][0])
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<h1>Autenticado! Pode fechar esta aba.</h1>")
        else:
            self.send_response(400)
            self.end_headers()
    def log_message(self, *args):
        pass

print("Acesse a URL abaixo no navegador:")
base = "https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize"
url = (f"{base}?client_id={OUTLOOK_CLIENT_ID}&response_type=code"
       f"&redirect_uri=https://imaging-quarrel-fabulous.ngrok-free.dev"
       f"&scope=https://graph.microsoft.com/Mail.ReadWrite "
       f"https://graph.microsoft.com/Mail.Send "
       f"https://graph.microsoft.com/Calendars.ReadWrite offline_access"
       f"&response_mode=query")
print(url)
print("\nAguardando autenticacao...")

server = HTTPServer(('localhost', 8080), Handler)
server.timeout = 120
while not code_recebido:
    server.handle_request()

print("Code capturado automaticamente!")

resp = requests.post(
    "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
    data={
        "client_id": OUTLOOK_CLIENT_ID,
        "client_secret": OUTLOOK_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code_recebido,
        "redirect_uri": "https://imaging-quarrel-fabulous.ngrok-free.dev",
        "scope": "https://graph.microsoft.com/Mail.ReadWrite https://graph.microsoft.com/Mail.Send https://graph.microsoft.com/Calendars.ReadWrite offline_access",
    }
)
dados = resp.json()
if "access_token" in dados:
    token_info = {
        "access_token": dados["access_token"],
        "refresh_token": dados.get("refresh_token", ""),
        "expires_at": (datetime.utcnow() + timedelta(seconds=dados.get("expires_in", 3600))).isoformat(),
    }
    with open('config/outlook_token.json', 'w') as f:
        json.dump(token_info, f, indent=2)
    print("Token Outlook salvo com sucesso!")
else:
    print("Erro:", dados.get("error_description", dados))
