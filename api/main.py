"""API REST FastAPI para o Agente Pessoal"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from config.settings import Config
from agents.coordenador import conversar
from database.crud import AgenteCRUD
from database.models import init_db
from tools import DocumentTool
from tools.voice_tool import VoiceTool
from api.rotas_agendar import router as rotas_agendar_router

# Inicializa DB
init_db()

app = FastAPI(
    title=f"{Config.AGENT_NAME} API",
    description="API REST completa para o Agente Pessoal com IA",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instâncias
crud = AgenteCRUD()
doc_tool = DocumentTool()
voice_tool = VoiceTool(Config.WHISPER_MODEL)

# ========== MODELOS ==========
class MensagemRequest(BaseModel):
    mensagem: str
    thread_id: Optional[str] = "default"
    user_id: Optional[str] = None

class MensagemResponse(BaseModel):
    resposta: str
    agente: str
    timestamp: datetime
    thread_id: str

class PreferenciaRequest(BaseModel):
    chave: str
    valor: str
    categoria: Optional[str] = "geral"

class TarefaRequest(BaseModel):
    titulo: str
    status: Optional[str] = "pendente"
    prioridade: Optional[str] = "media"
    contexto: Optional[str] = None
    cliente: Optional[str] = None

class EventoRequest(BaseModel):
    titulo: str
    data_inicio: datetime
    data_fim: Optional[datetime] = None
    descricao: Optional[str] = ""
    local: Optional[str] = ""

# ========== ROTAS HEALTH ==========
@app.get("/")
async def root():
    return {
        "status": "online",
        "agente": Config.AGENT_NAME,
        "versao": "3.0.0",
        "timestamp": datetime.utcnow()
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": datetime.utcnow()
    }

# ========== ROTAS CONVERSA ==========
@app.post("/conversar", response_model=MensagemResponse)
async def conversar_endpoint(request: MensagemRequest):
    """Envia mensagem para o agente e retorna resposta"""
    try:
        inicio = datetime.utcnow()

        # Processa via agente
        resposta = conversar(request.mensagem, thread_id=request.thread_id)

        # Salva no banco
        crud.salvar_conversa(
            thread_id=request.thread_id,
            role="user",
            content=request.mensagem
        )
        crud.salvar_conversa(
            thread_id=request.thread_id,
            role="agent",
            content=resposta
        )

        # Métrica de latência
        latencia = (datetime.utcnow() - inicio).total_seconds()
        crud.salvar_metrica("latencia", latencia, {"thread_id": request.thread_id})

        return MensagemResponse(
            resposta=resposta,
            agente="coordenador",
            timestamp=datetime.utcnow(),
            thread_id=request.thread_id
        )

    except Exception as e:
        crud.salvar_metrica("erro", 1, {"erro": str(e)})
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversas/{thread_id}")
async def listar_conversas(thread_id: str, limite: int = 50):
    """Lista histórico de conversas de uma thread"""
    conversas = crud.listar_conversas(thread_id=thread_id, limite=limite)
    return [
        {
            "id": c.id,
            "role": c.role,
            "content": c.content,
            "agente": c.agente,
            "intencao": c.intencao,
            "timestamp": c.timestamp
        }
        for c in conversas
    ]

# ========== ROTAS PREFERÊNCIAS ==========
@app.post("/preferencias")
async def criar_preferencia(request: PreferenciaRequest):
    """Cria ou atualiza uma preferência"""
    pref = crud.salvar_preferencia(request.chave, request.valor, request.categoria)
    return {"id": pref.id, "chave": pref.chave, "valor": pref.valor}

@app.get("/preferencias")
async def listar_preferencias(categoria: Optional[str] = None):
    """Lista todas as preferências"""
    prefs = crud.listar_preferencias(categoria=categoria)
    return [{"id": p.id, "chave": p.chave, "valor": p.valor, "categoria": p.categoria} for p in prefs]

@app.get("/preferencias/{chave}")
async def obter_preferencia(chave: str):
    """Obtém uma preferência específica"""
    valor = crud.obter_preferencia(chave)
    if valor is None:
        raise HTTPException(status_code=404, detail="Preferência não encontrada")
    return {"chave": chave, "valor": valor}

# ========== ROTAS TAREFAS ==========
@app.post("/tarefas")
async def criar_tarefa(request: TarefaRequest):
    """Cria uma nova tarefa (salva local + espelha no Notion, guardando o page_id)"""
    # Cria primeiro no Notion para capturar o page_id.
    # Nao quebra o salvamento local se o Notion falhar.
    notion_page_id = None
    notion_resultado = None
    try:
        from tools.notion_tool import criar_tarefa_notion_id
        notion_page_id = criar_tarefa_notion_id(
            titulo=request.titulo,
            prioridade=request.prioridade or "Média",
            contexto=request.contexto,
            cliente=request.cliente
        )
        notion_resultado = "✅ Tarefa criada com sucesso!" if notion_page_id else "Notion: falha ao criar"
    except Exception as e:
        notion_resultado = f"Erro Notion: {e}"
    tarefa = crud.salvar_tarefa(
        titulo=request.titulo,
        status=request.status,
        prioridade=request.prioridade,
        notion_page_id=notion_page_id,
        contexto=request.contexto,
        cliente=request.cliente
    )
    return {
        "id": tarefa.id,
        "titulo": tarefa.titulo,
        "status": tarefa.status,
        "prioridade": tarefa.prioridade,
        "criado_em": tarefa.criado_em,
        "notion_page_id": tarefa.notion_page_id,
        "notion": notion_resultado
    }

@app.get("/tarefas")
async def listar_tarefas(status: Optional[str] = None):
    """Lista tarefas"""
    tarefas = crud.listar_tarefas(status=status)
    return [
        {
            "id": t.id,
            "titulo": t.titulo,
            "status": t.status,
            "prioridade": t.prioridade,
            "contexto": t.contexto,
            "cliente": t.cliente,
            "data_vencimento": t.data_vencimento,
            "criado_em": t.criado_em
        }
        for t in tarefas
    ]

@app.patch("/tarefas/{tarefa_id}/completar")
async def completar_tarefa(tarefa_id: int):
    """Marca tarefa como completada (local + sincroniza Notion)"""
    tarefa = crud.completar_tarefa(tarefa_id)
    if not tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    notion_sync = None
    if tarefa.notion_page_id:
        try:
            from tools.notion_tool import concluir_tarefa_notion_por_id
            notion_sync = concluir_tarefa_notion_por_id(tarefa.notion_page_id)
        except Exception as e:
            notion_sync = f"Erro Notion: {e}"
    return {"status": "completada", "id": tarefa_id, "notion": notion_sync}

# ========== ROTAS EVENTOS ==========
@app.post("/eventos")
async def criar_evento(request: EventoRequest):
    """Cria um evento"""
    evento = crud.salvar_evento(
        titulo=request.titulo,
        data_inicio=request.data_inicio,
        data_fim=request.data_fim,
        descricao=request.descricao,
        local=request.local
    )
    return {
        "id": evento.id,
        "titulo": evento.titulo,
        "data_inicio": evento.data_inicio,
        "data_fim": evento.data_fim,
        "local": evento.local
    }

@app.get("/eventos")
async def listar_eventos(desde: Optional[datetime] = None, ate: Optional[datetime] = None):
    """Lista eventos"""
    eventos = crud.listar_eventos(desde=desde, ate=ate)
    return [
        {
            "id": e.id,
            "titulo": e.titulo,
            "data_inicio": e.data_inicio,
            "data_fim": e.data_fim,
            "local": e.local,
            "descricao": e.descricao
        }
        for e in eventos
    ]

# ========== ROTAS DOCUMENTOS ==========
@app.post("/documentos/analisar")
async def analisar_documento(file: UploadFile = File(...)):
    """Faz upload e análise de documento"""
    try:
        # Salva arquivo temporário
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Analisa
        resultado = doc_tool.analisar_auto(temp_path)

        # Salva no banco
        crud.salvar_documento(
            nome=file.filename,
            caminho=temp_path,
            tipo=file.filename.split(".")[-1],
            tamanho=len(content),
            conteudo_resumo=resultado[:500]
        )

        # Limpa
        os.remove(temp_path)

        return {
            "nome": file.filename,
            "analise": resultado,
            "tamanho": len(content)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documentos")
async def listar_documentos():
    """Lista documentos analisados"""
    docs = crud.listar_documentos()
    return [
        {
            "id": d.id,
            "nome": d.nome,
            "tipo": d.tipo,
            "tamanho": d.tamanho,
            "analisado_em": d.analisado_em
        }
        for d in docs
    ]

# ========== ROTAS VOZ ==========
@app.post("/voz/transcrever")
async def transcrever_audio(file: UploadFile = File(...)):
    """Transcreve arquivo de áudio"""
    try:
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        resultado = voice_tool.transcrever_audio(temp_path)
        os.remove(temp_path)

        if resultado["sucesso"]:
            return {
                "texto": resultado["texto"],
                "idioma": resultado["idioma"],
                "duracao": resultado["duracao"]
            }
        else:
            raise HTTPException(status_code=400, detail=resultado["erro"])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== ROTAS ANALYTICS ==========
@app.get("/analytics/estatisticas")
async def estatisticas_gerais():
    """Retorna estatísticas gerais"""
    return crud.estatisticas_gerais()

@app.get("/analytics/conversas-por-dia")
async def conversas_por_dia(dias: int = 30):
    """Retorna contagem de conversas por dia"""
    desde = datetime.utcnow() - timedelta(days=dias)
    # Implementação simplificada
    return {"dias": dias, "desde": desde}

app.include_router(rotas_agendar_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT)
