#!/usr/bin/env python3
"""
agro_rc_crm.py
==============
Ferramenta de integracao com o Agro RC CRM via API REST.
"""
import os
import requests

CRM_BASE_URL = "https://ngrepqqlvglzqnoswfug.supabase.co/functions/v1/crm-external-api"
CRM_API_KEY  = os.getenv("AGRO_RC_CRM_KEY", "")

HEADERS = {
    "Authorization": f"Bearer {CRM_API_KEY}",
    "Content-Type": "application/json"
}


def crm_get(endpoint: str, params: dict = None) -> dict:
    try:
        r = requests.get(f"{CRM_BASE_URL}{endpoint}", headers=HEADERS, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"erro": str(e)}


def crm_post(endpoint: str, payload: dict) -> dict:
    try:
        r = requests.post(f"{CRM_BASE_URL}{endpoint}", headers=HEADERS, json=payload, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"erro": str(e)}


# ── CLIENTES ──────────────────────────────────────────────────────────────────

def listar_clientes(search: str = "", limit: int = 10) -> str:
    params = {"limit": limit}
    if search:
        params["search"] = search
    result = crm_get("/clients", params)
    if "erro" in result:
        return f"Erro ao listar clientes: {result['erro']}"
    clientes = result if isinstance(result, list) else result.get("data", [])
    if not clientes:
        return "Nenhum cliente encontrado."
    linhas = [f"Clientes ({len(clientes)}):"]
    for c in clientes[:20]:
        linhas.append(f"- {c.get('razao_social','?')} | {c.get('cidade','?')}/{c.get('estado','?')}")
    return "\n".join(linhas)


def detalhar_cliente(client_id: str) -> str:
    result = crm_get(f"/clients/{client_id}")
    if "erro" in result:
        return f"Erro ao buscar cliente: {result['erro']}"
    c = result
    linhas = [
        f"Cliente: {c.get('razao_social','?')}",
        f"CNPJ: {c.get('cnpj','?')}",
        f"Email: {c.get('email','?')}",
        f"Cidade: {c.get('cidade','?')}/{c.get('estado','?')}",
    ]
    interacoes = c.get("interactions", [])
    if interacoes:
        linhas.append(f"\nUltimas interacoes ({len(interacoes)}):")
        for i in interacoes[:5]:
            linhas.append(f"- {i.get('created_at','?')[:10]}: {i.get('summary','?')[:80]}")
    return "\n".join(linhas)


def criar_cliente(razao_social: str, cnpj: str = "", email: str = "",
                  cidade: str = "", estado: str = "") -> str:
    result = crm_post("/clients", {
        "razao_social": razao_social, "cnpj": cnpj,
        "email": email, "cidade": cidade, "estado": estado
    })
    if "erro" in result:
        return f"Erro ao criar cliente: {result['erro']}"
    return f"Cliente '{razao_social}' criado no CRM."


# ── INTERACOES ────────────────────────────────────────────────────────────────

def listar_interacoes(client_id: str = "", limit: int = 10) -> str:
    params = {"limit": limit}
    if client_id:
        params["client_id"] = client_id
    result = crm_get("/interactions", params)
    if "erro" in result:
        return f"Erro ao listar interacoes: {result['erro']}"
    items = result if isinstance(result, list) else result.get("data", [])
    if not items:
        return "Nenhuma interacao encontrada."
    linhas = [f"Interacoes ({len(items)}):"]
    for i in items[:10]:
        linhas.append(f"- {i.get('created_at','?')[:10]}: {i.get('summary','?')[:100]}")
    return "\n".join(linhas)

def registrar_interacao(notes: str, client_name: str = "", type: str = "visita") -> str:
    """Busca client_id pelo nome e registra interacao em /interactions."""
    client_id = ""
    if client_name:
        # Tenta busca exata
        r = crm_get("/clients", {"search": client_name, "limit": 3})
        clientes = r.get("data", [])
        if not clientes:
            # Tenta busca parcial com primeira palavra
            primeira = client_name.split()[0]
            r2 = crm_get("/clients", {"search": primeira, "limit": 5})
            clientes = r2.get("data", [])
        if clientes:
            client_id = clientes[0].get("id", "")
    if not client_id:
        return f"Cliente '{client_name}' nao encontrado no CRM. Verifique o nome e tente novamente."
    result = crm_post("/interactions", {
        "client_id": client_id,
        "type": type,
        "notes": notes
    })
    if "erro" in result:
        return f"Erro ao registrar interacao: {result['erro']}"
    nome = result.get("data", {}).get("cliente_nome", client_name)
    return f"Interacao registrada no CRM para {nome}: {notes[:80]}"


# ── PIPELINE ──────────────────────────────────────────────────────────────────

def ver_pipeline() -> str:
    result = crm_get("/pipeline")
    if "erro" in result:
        return f"Erro ao buscar pipeline: {result['erro']}"
    etapas = result if isinstance(result, list) else result.get("data", [])
    if not etapas:
        return "Pipeline vazio."
    linhas = ["Pipeline de oportunidades:"]
    for e in etapas:
        nome  = e.get("etapa") or e.get("stage") or e.get("name","?")
        count = e.get("count", 0)
        valor = e.get("total_value") or e.get("value", 0)
        linhas.append(f"- {nome}: {count} oportunidade(s) | R$ {valor:,.2f}" if isinstance(valor, (int,float)) else f"- {nome}: {count} oportunidade(s)")
    return "\n".join(linhas)


# ── OPORTUNIDADES ─────────────────────────────────────────────────────────────

def criar_oportunidade(titulo: str, client_id: str = "", valor: float = 0,
                       etapa: str = "prospeccao") -> str:
    result = crm_post("/opportunities", {
        "titulo": titulo, "client_id": client_id,
        "valor": valor, "etapa": etapa
    })
    if "erro" in result:
        return f"Erro ao criar oportunidade: {result['erro']}"
    return f"Oportunidade '{titulo}' criada no CRM."


# ── TAREFAS ───────────────────────────────────────────────────────────────────

def listar_tarefas_crm(status: str = "", limit: int = 10) -> str:
    params = {"limit": limit}
    if status:
        params["status"] = status
    result = crm_get("/tasks", params)
    if "erro" in result:
        return f"Erro ao listar tarefas: {result['erro']}"
    items = result if isinstance(result, list) else result.get("data", [])
    if not items:
        return "Nenhuma tarefa encontrada."
    linhas = [f"Tarefas CRM ({len(items)}):"]
    for t in items[:10]:
        linhas.append(f"- [{t.get('status','?')}] {t.get('titulo','?')[:80]}")
    return "\n".join(linhas)


def criar_tarefa(titulo: str, client_id: str = "", prazo: str = "",
                 priority: str = "media") -> str:
    result = crm_post("/tasks", {
        "titulo": titulo, "client_id": client_id,
        "prazo": prazo, "priority": priority
    })
    if "erro" in result:
        return f"Erro ao criar tarefa: {result['erro']}"
    return f"Tarefa '{titulo}' criada no CRM."


# ── EMAIL ANALYSIS ────────────────────────────────────────────────────────────

def analisar_email_crm(email_summary: str, category: str = "venda",
                       priority: str = "media", urgency_score: int = 50,
                       suggested_action: str = "") -> str:
    result = crm_post("/email-analysis", {
        "email_summary": email_summary, "category": category,
        "priority": priority, "urgency_score": urgency_score,
        "suggested_action": suggested_action
    })
    if "erro" in result:
        return f"Erro na analise: {result['erro']}"
    return f"Analise registrada no CRM: {email_summary[:80]}"
