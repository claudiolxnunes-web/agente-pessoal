import sys, json, requests
from urllib.parse import unquote, urlparse, parse_qs
from datetime import datetime, timedelta
sys.path.insert(0, '.')
from config.settings import OUTLOOK_CLIENT_ID, OUTLOOK_CLIENT_SECRET

with open('/tmp/outlook_code.txt', 'r') as f:
    raw = f.read().strip()

# Extrai o code da URL ou usa direto
if 'code=' in raw:
    parsed = parse_qs(urlparse(raw).query)
    code = unquote(parsed.get('code', [raw])[0])
else:
    code = unquote(raw)

print("Code:", code[:30], "...")

resp = requests.post(
    "https://login.microsoftonline.com/consumers/oauth2/v2.0/token",
    data={
        "client_id": OUTLOOK_CLIENT_ID,
        "client_secret": OUTLOOK_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://localhost:8080",
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
    print("✅ Token Outlook salvo com sucesso!")
else:
    print("Erro:", dados.get("error_description", dados))
