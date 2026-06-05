"""Integração com ProtonMail via API REST"""
import os
import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any

class ProtonMailTool:
    """Ferramenta para gerenciar ProtonMail via API"""

    def __init__(self, api_token: str = None, username: str = None):
        """
        ProtonMail API Token:
        1. Acesse https://mail.proton.me
        2. Configurações > API > Crie token de acesso
        """
        self.api_token = api_token or os.getenv("PROTONMAIL_API_TOKEN")
        self.username = username or os.getenv("PROTONMAIL_USERNAME")
        self.base_url = "https://mail.proton.me/api"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        self.autenticado = bool(self.api_token)

    def _request(self, method: str, endpoint: str, data: dict = None) -> Dict:
        """Faz requisição à API ProtonMail"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
            elif method == "PUT":
                response = requests.put(url, headers=self.headers, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=self.headers, timeout=10)
            else:
                return {"erro": "Método não suportado"}

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"erro": str(e), "sucesso": False}

    def listar_emails(self, label: str = "0", max_results: int = 10) -> str:
        """Lista emails do ProtonMail"""
        if not self.autenticado:
            return "❌ ProtonMail não autenticado. Configure PROTONMAIL_API_TOKEN no .env"

        resultado = self._request("GET", f"/messages?label={label}&Limit={max_results}")

        if "erro" in resultado:
            return f"Erro: {resultado['erro']}"

        mensagens = resultado.get("Messages", [])
        if not mensagens:
            return "📧 Nenhum email encontrado."

        output = "📧 Emails ProtonMail:\n\n"
        for msg in mensagens:
            assunto = msg.get("Subject", "Sem assunto")
            remetente = msg.get("Sender", {}).get("Address", "Desconhecido")
            data = msg.get("Time", 0)
            tamanho = msg.get("Size", 0)

            # Converte timestamp
            try:
                data_fmt = datetime.fromtimestamp(data).strftime("%d/%m/%Y %H:%M")
            except:
                data_fmt = str(data)

            status = "🔴" if msg.get("Unread", 0) else "✉️"

            output += f"{status} **{assunto}**\n"
            output += f"   De: {remetente} | {data_fmt}\n"
            output += f"   Tamanho: {tamanho} bytes\n\n"

        return output

    def ler_email(self, msg_id: str) -> str:
        """Lê conteúdo de um email"""
        if not self.autenticado:
            return "❌ Não autenticado."

        resultado = self._request("GET", f"/messages/{msg_id}")

        if "erro" in resultado:
            return f"Erro: {resultado['erro']}"

        msg = resultado.get("Message", {})
        assunto = msg.get("Subject", "Sem assunto")
        remetente = msg.get("Sender", {}).get("Address", "Desconhecido")
        corpo = msg.get("Body", "Sem conteúdo")

        return f"📧 **{assunto}**\nDe: {remetente}\n\n{corpo[:2000]}"

    def enviar_email(self, para: str, assunto: str, corpo: str) -> str:
        """Envia email via ProtonMail"""
        if not self.autenticado:
            return "❌ Não autenticado."

        payload = {
            "Message": {
                "ToList": [{"Address": para}],
                "Subject": assunto,
                "Body": corpo,
                "MIMEType": "text/plain"
            }
        }

        resultado = self._request("POST", "/messages", payload)

        if resultado.get("Code") == 1001:
            return f"✅ Email enviado para {para} via ProtonMail"
        else:
            return f"❌ Erro: {resultado.get('Error', 'Desconhecido')}"

    def deletar_email(self, msg_id: str) -> str:
        """Move email para lixeira"""
        if not self.autenticado:
            return "❌ Não autenticado."

        resultado = self._request("PUT", f"/messages/{msg_id}", {"LabelIDs": ["3"]})

        if "erro" not in resultado:
            return "🗑️ Email movido para lixeira."
        else:
            return f"❌ Erro: {resultado['erro']}"

    def info(self) -> str:
        """Retorna informações da conta"""
        if not self.autenticado:
            return "❌ ProtonMail não configurado."

        resultado = self._request("GET", "/users")

        if "erro" in resultado:
            return f"Erro: {resultado['erro']}"

        usuario = resultado.get("User", {})
        nome = usuario.get("DisplayName", "Desconhecido")
        email = usuario.get("Email", "Não disponível")

        return f"🔒 ProtonMail: {nome} ({email})"


# ── Funções de módulo ─────────────────────────────────────────────────────────
def listar_emails_proton(max_results: int = 10, apenas_nao_lidos: bool = False) -> str:
    try:
        return ProtonMailTool().listar_emails(max_results=max_results)
    except Exception as e:
        return f"Erro ProtonMail: {e}"

def enviar_email_proton(destinatario: str, assunto: str, corpo: str) -> str:
    try:
        return ProtonMailTool().enviar_email(destinatario, assunto, corpo)
    except Exception as e:
        return f"Erro ao enviar ProtonMail: {e}"
