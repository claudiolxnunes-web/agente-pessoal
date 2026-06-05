"""Integração com Notion"""
import requests
from datetime import datetime

class NotionTool:
    """Ferramenta para gerenciar tarefas e notas no Notion"""

    def __init__(self, token, database_id):
        self.token = token
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.base_url = "https://api.notion.com/v1"

    def _request(self, method, endpoint, data=None):
        """Faz requisição à API do Notion"""
        url = f"{self.base_url}/{endpoint}"
        try:
            if method == "GET":
                response = requests.get(url, headers=self.headers)
            elif method == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method == "PATCH":
                response = requests.patch(url, headers=self.headers, json=data)
            else:
                return None

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def listar_tarefas(self, status=None, limite=10):
        """Lista tarefas do database"""
        data = {
            "page_size": limite,
            "filter": {"property": "object", "value": "page"}
        }

        if status:
            data["filter"] = {
                "property": "Status",
                "select": {"equals": status}
            }

        resultado = self._request("POST", f"databases/{self.database_id}/query", data)

        if "error" in resultado:
            return f"Erro ao buscar tarefas: {resultado['error']}"

        tarefas = resultado.get("results", [])
        if not tarefas:
            return "Nenhuma tarefa encontrada."

        output = "📋 Tarefas no Notion:\n\n"
        for tarefa in tarefas:
            props = tarefa.get("properties", {})
            titulo = "Sem título"

            # Extrai título
            if "Name" in props and props["Name"]["title"]:
                titulo = props["Name"]["title"][0]["text"]["content"]

            status_tarefa = ""
            if "Status" in props and props["Status"]["select"]:
                status_tarefa = props["Status"]["select"]["name"]

            output += f"• {titulo}"
            if status_tarefa:
                output += f" [{status_tarefa}]"
            output += "\n"

        return output

    def criar_tarefa(self, titulo, status="A fazer", prioridade="Média", data_vencimento=None):
        """Cria uma nova tarefa no Notion"""
        data = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": titulo}}]
                },
                "Status": {
                    "select": {"name": status}
                }
            }
        }

        # Adiciona prioridade se o campo existir
        if prioridade:
            data["properties"]["Prioridade"] = {
                "select": {"name": prioridade}
            }

        # Adiciona data de vencimento
        if data_vencimento:
            data["properties"]["Data de Vencimento"] = {
                "date": {"start": data_vencimento}
            }

        resultado = self._request("POST", "pages", data)

        if "error" in resultado:
            return f"Erro ao criar tarefa: {resultado['error']}"

        return f"✅ Tarefa criada no Notion: {titulo}"

    def criar_nota(self, titulo, conteudo, parent_page_id=None):
        """Cria uma página/nota no Notion"""
        if parent_page_id is None:
            parent_page_id = self.database_id

        data = {
            "parent": {"page_id": parent_page_id},
            "properties": {
                "title": [{"text": {"content": titulo}}]
            },
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": conteudo}}]
                    }
                }
            ]
        }

        resultado = self._request("POST", "pages", data)

        if "error" in resultado:
            return f"Erro ao criar nota: {resultado['error']}"

        return f"📝 Nota criada: {titulo}"

    def atualizar_tarefa(self, page_id, novo_status=None, novo_titulo=None):
        """Atualiza uma tarefa existente"""
        data = {"properties": {}}

        if novo_status:
            data["properties"]["Status"] = {"select": {"name": novo_status}}

        if novo_titulo:
            data["properties"]["Name"] = {
                "title": [{"text": {"content": novo_titulo}}]
            }

        resultado = self._request("PATCH", f"pages/{page_id}", data)

        if "error" in resultado:
            return f"Erro ao atualizar: {resultado['error']}"

        return "✅ Tarefa atualizada com sucesso."


# ── Funções de módulo ─────────────────────────────────────────────────────────
def criar_tarefa_notion(titulo: str, descricao: str = "", prioridade: str = "Média") -> str:
    import os
    try:
        tool = NotionTool(
            token=os.getenv("NOTION_TOKEN", ""),
            database_id=os.getenv("NOTION_DATABASE_ID", "")
        )
        return tool.criar_tarefa(titulo, prioridade=prioridade)
    except Exception as e:
        return f"Erro Notion: {e}"

def listar_tarefas_notion() -> str:
    import os
    try:
        tool = NotionTool(
            token=os.getenv("NOTION_TOKEN", ""),
            database_id=os.getenv("NOTION_DATABASE_ID", "")
        )
        return tool.listar_tarefas()
    except Exception as e:
        return f"Erro Notion: {e}"
