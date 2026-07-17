"""
Integração com Outlook / Microsoft 365 via Microsoft Graph API
Suporta contas pessoais (Hotmail/Outlook.com) com refresh token automático.
"""
import os, sys, json, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from datetime import datetime, timedelta
from config.settings import (
    OUTLOOK_ENABLED, OUTLOOK_CLIENT_ID, OUTLOOK_CLIENT_SECRET,
    OUTLOOK_TENANT_ID, OUTLOOK_ACCESS_TOKEN
)

logger = logging.getLogger(__name__)

GRAPH_BASE    = "https://graph.microsoft.com/v1.0"
TOKEN_URL     = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
TOKEN_FILE    = "config/outlook_token.json"  # salva access + refresh token


# ══════════════════════════════════════════════════════════════════════════════
# Gerenciamento de Token com Refresh Automático
# ══════════════════════════════════════════════════════════════════════════════

def _carregar_token() -> dict:
    """Carrega token salvo em disco (access + refresh + expiry)."""
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    # Fallback: token estático do .env (sem refresh)
    return {"access_token": OUTLOOK_ACCESS_TOKEN, "refresh_token": "", "expires_at": 0}


def _salvar_token(dados: dict):
    """Salva token atualizado em disco."""
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump(dados, f, indent=2)


def _renovar_token(refresh_token: str) -> dict | None:
    """Usa o refresh_token para obter um novo access_token."""
    if not refresh_token:
        return None
    try:
        resp = requests.post(TOKEN_URL, data={
            "client_id":     OUTLOOK_CLIENT_ID,
            "client_secret": OUTLOOK_CLIENT_SECRET,
            "grant_type":    "refresh_token",
            "refresh_token": refresh_token,
            "scope":         "https://graph.microsoft.com/Mail.ReadWrite "
                             "https://graph.microsoft.com/Mail.Send "
                             "https://graph.microsoft.com/Calendars.ReadWrite "
                             "offline_access",
        }, timeout=10)
        resp.raise_for_status()
        dados = resp.json()
        token_info = {
            "access_token":  dados["access_token"],
            "refresh_token": dados.get("refresh_token", refresh_token),
            "expires_at":    (datetime.utcnow() + timedelta(seconds=dados.get("expires_in", 3600))).isoformat(),
        }
        _salvar_token(token_info)
        logger.info("🔄 Token Outlook renovado com sucesso.")
        return token_info
    except Exception as e:
        logger.error(f"❌ Falha ao renovar token Outlook: {e}")
        return None


def _get_access_token() -> str | None:
    """Retorna um access_token válido, renovando automaticamente se necessário."""
    token_info = _carregar_token()
    access_token  = token_info.get("access_token", "")
    refresh_token = token_info.get("refresh_token", "")
    expires_at    = token_info.get("expires_at", 0)

    # Verifica se o token está próximo de expirar (margem de 5 min)
    try:
        expiry = datetime.fromisoformat(str(expires_at))
        if datetime.utcnow() >= expiry - timedelta(minutes=5):
            novo = _renovar_token(refresh_token)
            if novo:
                return novo["access_token"]
    except Exception:
        pass  # expires_at inválido ou ausente — tenta usar o token atual

    return access_token


def _headers() -> dict:
    token = _get_access_token()
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _check() -> str | None:
    if not OUTLOOK_ENABLED:
        return "⚠️ Outlook não está habilitado. Configure OUTLOOK_ENABLED=true no .env"
    if not OUTLOOK_CLIENT_ID:
        return "❌ OUTLOOK_CLIENT_ID não configurado no .env"
    token = _get_access_token()
    if not token:
        return "❌ Token do Outlook inválido ou expirado. Execute o fluxo de autenticação novamente."
    return None


# ══════════════════════════════════════════════════════════════════════════════
# Autenticação inicial (gera o token pela primeira vez)
# ══════════════════════════════════════════════════════════════════════════════

def gerar_url_autorizacao() -> str:
    """
    Retorna a URL para o usuário autorizar o app na Microsoft.
    Após autorizar, o usuário recebe um 'code' na URL de redirect.
    Use trocar_code_por_token(code) em seguida.
    """
    base = "https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize"
    params = (
        f"?client_id={OUTLOOK_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri=http://localhost:8080"
        f"&scope=https://graph.microsoft.com/Mail.ReadWrite "
        f"https://graph.microsoft.com/Mail.Send "
        f"https://graph.microsoft.com/Calendars.ReadWrite offline_access"
        f"&response_mode=query"
    )
    return base + params


def trocar_code_por_token(code: str) -> str:
    """
    Troca o 'code' recebido após autorização pelo access_token + refresh_token.
    Salva automaticamente em config/outlook_token.json.
    """
    try:
        resp = requests.post(TOKEN_URL, data={
            "client_id":     OUTLOOK_CLIENT_ID,
            "client_secret": OUTLOOK_CLIENT_SECRET,
            "grant_type":    "authorization_code",
            "code":          code,
            "redirect_uri":  "http://localhost:8080",
            "scope":         "https://graph.microsoft.com/Mail.ReadWrite "
                             "https://graph.microsoft.com/Mail.Send "
                             "https://graph.microsoft.com/Calendars.ReadWrite offline_access",
        }, timeout=10)
        resp.raise_for_status()
        dados = resp.json()
        token_info = {
            "access_token":  dados["access_token"],
            "refresh_token": dados.get("refresh_token", ""),
            "expires_at":    (datetime.utcnow() + timedelta(seconds=dados.get("expires_in", 3600))).isoformat(),
        }
        _salvar_token(token_info)
        return "✅ Token Outlook salvo com sucesso! O agente vai renovar automaticamente."
    except Exception as e:
        return f"❌ Erro ao trocar code por token: {e}"


# ══════════════════════════════════════════════════════════════════════════════
# Funções principais
# ══════════════════════════════════════════════════════════════════════════════

def listar_emails_outlook(max_results: int = 10, apenas_nao_lidos: bool = False) -> str:
    """Lista e-mails do Outlook."""
    err = _check()
    if err:
        return err

    try:
        params = {
            "$top": max_results,
            "$orderby": "receivedDateTime desc",
            "$select": "id,subject,from,receivedDateTime,isRead,bodyPreview",
        }
        if apenas_nao_lidos:
            params["$filter"] = "isRead eq false"

        resp = requests.get(f"{GRAPH_BASE}/me/messages", headers=_headers(), params=params, timeout=10)
        resp.raise_for_status()
        msgs = resp.json().get("value", [])

        if not msgs:
            return "📭 Nenhum e-mail encontrado no Outlook."

        linhas = ["📧 E-mails do Outlook:"]
        for m in msgs:
            lido = "✉️" if m.get("isRead") else "🔵"
            remetente = m.get("from", {}).get("emailAddress", {}).get("address", "?")[:40]
            assunto   = m.get("subject", "Sem assunto")[:60]
            data      = m.get("receivedDateTime", "")[:10]
            mid       = m.get("id", "")[:8]
            linhas.append(f"  {lido} [{mid}] {data} | {remetente} | {assunto}")

        return "\n".join(linhas)

    except requests.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Token expirado. Tente novamente — o agente vai renovar automaticamente."
        return f"❌ Erro ao listar e-mails do Outlook: {e}"
    except requests.RequestException as e:
        return f"❌ Erro ao listar e-mails do Outlook: {e}"


def enviar_email_outlook(destinatario: str, assunto: str, corpo: str) -> str:
    """Envia e-mail pelo Outlook."""
    err = _check()
    if err:
        return err

    try:
        payload = {
            "message": {
                "subject": assunto,
                "body": {"contentType": "Text", "content": corpo},
                "toRecipients": [{"emailAddress": {"address": destinatario}}],
            }
        }
        resp = requests.post(f"{GRAPH_BASE}/me/sendMail",
                             headers=_headers(), json=payload, timeout=10)
        resp.raise_for_status()
        return f"✅ E-mail enviado via Outlook para {destinatario}"
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            return "❌ Token expirado. Tente novamente — o agente vai renovar automaticamente."
        return f"❌ Erro ao enviar e-mail pelo Outlook: {e}"
    except requests.RequestException as e:
        return f"❌ Erro ao enviar e-mail pelo Outlook: {e}"


def listar_eventos_outlook(dias: int = 7) -> str:
    """Lista eventos do calendário Outlook."""
    err = _check()
    if err:
        return err

    try:
        agora = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        fim   = (datetime.utcnow() + timedelta(days=dias)).strftime("%Y-%m-%dT%H:%M:%SZ")

        params = {
            "$top": 10,
            "$filter": f"start/dateTime ge '{agora}' and start/dateTime le '{fim}'",
            "$orderby": "start/dateTime",
            "$select": "id,subject,start,end,location",
        }
        resp = requests.get(f"{GRAPH_BASE}/me/events", headers=_headers(), params=params, timeout=10)
        resp.raise_for_status()
        eventos = resp.json().get("value", [])

        if not eventos:
            return f"📅 Nenhum evento Outlook nos próximos {dias} dias."

        linhas = [f"📅 Eventos Outlook — próximos {dias} dias:"]
        for ev in eventos:
            inicio    = ev.get("start", {}).get("dateTime", "")[:16].replace("T", " ")
            local     = ev.get("location", {}).get("displayName", "")
            local_str = f" @ {local}" if local else ""
            linhas.append(f"  • {inicio} — {ev.get('subject', '?')}{local_str}")

        return "\n".join(linhas)

    except requests.RequestException as e:
        return f"❌ Erro ao listar eventos do Outlook: {e}"


def deletar_email_outlook(msg_id: str) -> str:
    """Deleta um e-mail do Outlook."""
    err = _check()
    if err:
        return err

    try:
        resp = requests.delete(f"{GRAPH_BASE}/me/messages/{msg_id}",
                               headers=_headers(), timeout=10)
        resp.raise_for_status()
        return f"🗑️ E-mail {msg_id[:8]} deletado do Outlook."
    except requests.RequestException as e:
        return f"❌ Erro ao deletar e-mail do Outlook: {e}"
