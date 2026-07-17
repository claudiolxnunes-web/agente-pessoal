import requests
import logging

logger = logging.getLogger(__name__)


def _notion_habilitado() -> bool:
    import os
    return os.getenv("NOTION_ENABLED", "false").strip().lower() == "true"


def _norm_prioridade(p):
    if not p:
        return "Média"
    m = {"alta": "Alta", "média": "Média", "media": "Média",
         "média": "Média", "baixa": "Baixa"}
    return m.get(str(p).strip().lower(), "Média")


class NotionTool:
    def __init__(self, token: str, database_id: str):
        self.token = token
        self.database_id = database_id
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    def _request(self, method, endpoint, data=None):
        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.request(method, url, headers=self.headers, json=data)

            if response.status_code >= 400:
                return {"error": response.text}

            return response.json()

        except Exception as e:
            return {"error": str(e)}

    # ─────────────────────────────────────────────
    # CRIAR TAREFA
    # ─────────────────────────────────────────────
    def criar_tarefa(self, titulo, status="A fazer", prioridade="Média",
                     contexto=None, cliente=None, origem="OpenClaw",
                     data_vencimento=None):
        props = {
            "Tarefa": {"title": [{"text": {"content": titulo}}]},
            "Status": {"status": {"name": status or "A fazer"}},
            "Prioridade": {"select": {"name": _norm_prioridade(prioridade)}},
        }
        if contexto:
            props["Contexto"] = {"select": {"name": contexto}}
        if cliente:
            props["Cliente/Conta"] = {"rich_text": [{"text": {"content": cliente}}]}
        if origem:
            props["Origem"] = {"select": {"name": origem}}
        if data_vencimento:
            props["Prazo"] = {"date": {"start": data_vencimento}}

        data = {"parent": {"database_id": self.database_id}, "properties": props}
        resultado = self._request("POST", "pages", data)

        if "error" in resultado:
            logger.warning("Erro ao criar tarefa no Notion: %s", resultado["error"])
            return None

        return resultado.get("id")

    # ─────────────────────────────────────────────
    # LISTAR TAREFAS
    # ─────────────────────────────────────────────
    def listar_tarefas(self):
        data = {"filter": {"property": "Status", "status": {"does_not_equal": "Concluída"}}}

        resultado = self._request("POST", f"databases/{self.database_id}/query", data)

        if "error" in resultado:
            return f"Erro ao listar tarefas: {resultado['error']}"

        tarefas = resultado.get("results", [])

        if not tarefas:
            return "Nenhuma tarefa encontrada."

        texto = "📋 Tarefas no Notion:\n\n"

        for tarefa in tarefas:
            try:
                titulo = tarefa["properties"]["Tarefa"]["title"][0]["text"]["content"]
            except Exception:
                titulo = "Sem título"

            texto += f"• {titulo}\n"

        return texto

    # ─────────────────────────────────────────────
    # ATUALIZAR TAREFA
    # ─────────────────────────────────────────────
    def atualizar_tarefa(self, page_id, novo_titulo=None, novo_status=None):
        data = {"properties": {}}

        if novo_titulo:
            data["properties"]["Tarefa"] = {
                "title": [{"text": {"content": novo_titulo}}]
            }

        if novo_status:
            data["properties"]["Status"] = {
                "status": {"name": novo_status}
            }

        resultado = self._request("PATCH", f"pages/{page_id}", data)

        if "error" in resultado:
            return f"Erro ao atualizar: {resultado['error']}"

        return "✅ Tarefa atualizada com sucesso!"


# ─────────────────────────────────────────────
# FUNÇÕES DE MÓDULO (usadas no agente)
# ─────────────────────────────────────────────

def criar_tarefa_notion(titulo: str, descricao: str = "", prioridade: str = "Média",
                        contexto: str = None, cliente: str = None,
                        origem: str = "OpenClaw") -> str:
    if not _notion_habilitado():
        return "Notion desabilitado (NOTION_ENABLED=false)"
    import os
    try:
        tool = NotionTool(
            token=os.getenv("NOTION_TOKEN", ""),
            database_id=os.getenv("NOTION_DATABASE_ID", "")
        )
        page_id = tool.criar_tarefa(titulo, prioridade=prioridade, contexto=contexto,
                                    cliente=cliente, origem=origem)
        return "✅ Tarefa criada com sucesso!" if page_id else "Erro ao criar tarefa no Notion"
    except Exception as e:
        return f"Erro Notion: {e}"


def criar_tarefa_notion_id(titulo: str, prioridade: str = "Média",
                           contexto: str = None, cliente: str = None,
                           origem: str = "OpenClaw"):
    """Cria a tarefa no Notion e retorna o page_id (ou None em falha)."""
    if not _notion_habilitado():
        return None
    import os
    try:
        tool = NotionTool(
            token=os.getenv("NOTION_TOKEN", ""),
            database_id=os.getenv("NOTION_DATABASE_ID", "")
        )
        return tool.criar_tarefa(titulo, prioridade=prioridade, contexto=contexto,
                                 cliente=cliente, origem=origem)
    except Exception as e:
        logger.warning("criar_tarefa_notion_id falhou: %s", e)
        return None


def listar_tarefas_notion() -> str:
    if not _notion_habilitado():
        return "Notion desabilitado (NOTION_ENABLED=false)"
    import os
    try:
        tool = NotionTool(
            token=os.getenv("NOTION_TOKEN", ""),
            database_id=os.getenv("NOTION_DATABASE_ID", "")
        )
        return tool.listar_tarefas()
    except Exception as e:
        return f"Erro Notion: {e}"


def concluir_tarefa_notion_por_id(page_id: str, status_concluido: str = "Concluída") -> str:
    """Marca a página do Notion (por id) como concluída."""
    if not _notion_habilitado():
        return "Notion desabilitado (NOTION_ENABLED=false)"
    import os
    try:
        tool = NotionTool(
            token=os.getenv("NOTION_TOKEN", ""),
            database_id=os.getenv("NOTION_DATABASE_ID", "")
        )
        return tool.atualizar_tarefa(page_id, novo_status=status_concluido)
    except Exception as e:
        return f"Erro Notion: {e}"


def concluir_tarefa_notion(titulo: str, status_concluido: str = "Concluída") -> str:
    """Busca tarefa pelo titulo (parcial, sem diferenciar maiusculas) e marca como concluida."""
    if not _notion_habilitado():
        return "Notion desabilitado (NOTION_ENABLED=false)"
    import os
    try:
        tool = NotionTool(
            token=os.getenv("NOTION_TOKEN", ""),
            database_id=os.getenv("NOTION_DATABASE_ID", "")
        )
        resultado = tool._request("POST", f"databases/{tool.database_id}/query", {})
        if "error" in resultado:
            return f"Erro ao buscar tarefas: {resultado['error']}"
        candidatas = []
        for tarefa in resultado.get("results", []):
            try:
                t = tarefa["properties"]["Tarefa"]["title"][0]["text"]["content"]
            except Exception:
                continue
            if titulo.lower() in t.lower():
                candidatas.append((tarefa["id"], t))
        if not candidatas:
            return f"Nenhuma tarefa encontrada com '{titulo}'."
        if len(candidatas) > 1:
            nomes = "; ".join(c[1] for c in candidatas[:5])
            return f"Encontrei mais de uma: {nomes}. Seja mais especifico."
        page_id, nome = candidatas[0]
        r = tool.atualizar_tarefa(page_id, novo_status=status_concluido)
        return f"{r} ({nome})"
    except Exception as e:
        return f"Erro Notion: {e}"
