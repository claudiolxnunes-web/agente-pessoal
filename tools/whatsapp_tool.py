"""Integração WhatsApp via Meta Cloud API"""
import requests
import json
from typing import Optional, Dict, Any

class WhatsAppTool:
    """Ferramenta para enviar e receber mensagens WhatsApp"""

    def __init__(self, phone_number_id: str, access_token: str, verify_token: str = ""):
        self.phone_number_id = phone_number_id
        self.access_token = access_token
        self.verify_token = verify_token
        self.base_url = "https://graph.facebook.com/v18.0"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def enviar_mensagem(self, numero_destino: str, mensagem: str) -> Dict[str, Any]:
        """Envia mensagem de texto via WhatsApp"""
        # Remove caracteres não numéricos e adiciona prefixo se necessário
        numero = "".join(filter(str.isdigit, numero_destino))
        if not numero.startswith("55"):  # Assume Brasil se não tiver DDI
            numero = "55" + numero

        url = f"{self.base_url}/{self.phone_number_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {"body": mensagem}
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return {"sucesso": True, "resposta": response.json()}
        except requests.exceptions.RequestException as e:
            return {"sucesso": False, "erro": str(e)}

    def enviar_template(self, numero_destino: str, template_name: str, idioma: str = "pt_BR") -> Dict[str, Any]:
        """Envia mensagem usando template aprovado"""
        numero = "".join(filter(str.isdigit, numero_destino))
        if not numero.startswith("55"):
            numero = "55" + numero

        url = f"{self.base_url}/{self.phone_number_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": idioma}
            }
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            response.raise_for_status()
            return {"sucesso": True, "resposta": response.json()}
        except requests.exceptions.RequestException as e:
            return {"sucesso": False, "erro": str(e)}

    def verificar_webhook(self, mode: str, token: str, challenge: str) -> bool:
        """Verifica requisição de webhook do Meta"""
        if mode == "subscribe" and token == self.verify_token:
            return True
        return False

    def processar_webhook(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Processa mensagem recebida via webhook"""
        try:
            entry = data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})

            if "messages" not in value:
                return None

            mensagem = value["messages"][0]

            return {
                "id": mensagem.get("id"),
                "de": mensagem.get("from"),
                "tipo": mensagem.get("type"),
                "texto": mensagem.get("text", {}).get("body", ""),
                "timestamp": mensagem.get("timestamp")
            }

        except (KeyError, IndexError):
            return None

    def marcar_lida(self, mensagem_id: str) -> bool:
        """Marca mensagem como lida"""
        url = f"{self.base_url}/{self.phone_number_id}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": mensagem_id
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            return response.status_code == 200
        except:
            return False

    def obter_info_contato(self, numero: str) -> Dict[str, Any]:
        """Obtém informações do perfil do contato"""
        url = f"{self.base_url}/{self.phone_number_id}/contacts"

        payload = {
            "blocking": "wait",
            "contacts": [numero]
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            return response.json()
        except:
            return {}
