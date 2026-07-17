from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from tools.google_calendar_tool import criar_evento_calendar
from tools.notion_tool import criar_tarefa_notion

router = APIRouter(tags=["Agendamento"])

API_TOKEN_HEADER = APIKeyHeader(name="X-Agente-API-Token", auto_error=True)

def verificar_token(token: str = Security(API_TOKEN_HEADER)):
    token_esperado = os.getenv("AGENDAR_API_TOKEN")
    if not token_esperado or token != token_esperado:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de integração inválido ou não configurado."
        )
    return token

class EventoSchema(BaseModel):
    titulo: str = Field(..., example="Reunião com Cláudio")
    data_hora: str = Field(..., example="14/07/2026 15:30", description="Formato: DD/MM/AAAA HH:MM")
    duracao_horas: Optional[int] = Field(1, example=1)
    descricao: Optional[str] = Field("", example="Alinhamento estratégico de IA")
    local: Optional[str] = Field("", example="Google Meet")

class LoteEventosSchema(BaseModel):
    eventos: List[EventoSchema]

@router.post("/agendar", dependencies=[Depends(verificar_token)])
async def agendar_eventos_em_lote(lote: LoteEventosSchema):
    resultados = []
    
    for idx, evento in enumerate(lote.eventos):
        detalhes_finais = []
        try:
            # 1. Cria no Google Calendar
            res_calendar = criar_evento_calendar(
                titulo=evento.titulo,
                data_hora=evento.data_hora,
                duracao_horas=evento.duracao_horas,
                descricao=evento.descricao,
                local=evento.local
            )
            detalhes_finais.append(f"Calendar: {res_calendar}")
            sucesso_calendar = "✅" in res_calendar or "Evento criado" in res_calendar
            
            # 2. Cria no Notion em paralelo
            res_notion = criar_tarefa_notion(
                titulo=evento.titulo,
                descricao=evento.descricao if evento.descricao else "Criado via OpenClaw",
                prioridade="Média"
            )
            detalhes_finais.append(f"Notion: {res_notion}")
            
            resultados.append({
                "index": idx,
                "titulo": evento.titulo,
                "status": "sucesso" if sucesso_calendar else "erro",
                "detalhe": " | ".join(detalhes_finais)
            })
        except Exception as e:
            resultados.append({
                "index": idx,
                "titulo": evento.titulo,
                "status": "erro",
                "detalhe": f"Falha no lote: {str(e)}"
            })
            
    return {"status": "processado", "resultados": resultados}
