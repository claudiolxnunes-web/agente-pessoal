"""Operações CRUD para o banco de dados"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from database.models import (
    get_session, ConversaDB, PreferenciaDB, EventoDB,
    TarefaDB, MetricaDB, DocumentoDB
)

class AgenteCRUD:
    """CRUD completo para o agente pessoal"""

    def __init__(self):
        self.session = get_session()

    # ========== CONVERSAS ==========
    def salvar_conversa(self, thread_id: str, role: str, content: str, 
                        agente: str = "", intencao: str = "") -> ConversaDB:
        """Salva uma mensagem da conversa"""
        conv = ConversaDB(
            thread_id=thread_id,
            role=role,
            content=content,
            agente=agente,
            intencao=intencao
        )
        self.session.add(conv)
        self.session.commit()
        return conv

    def listar_conversas(self, thread_id: str = None, limite: int = 50) -> List[ConversaDB]:
        """Lista conversas, opcionalmente filtradas por thread"""
        query = self.session.query(ConversaDB)
        if thread_id:
            query = query.filter(ConversaDB.thread_id == thread_id)
        return query.order_by(desc(ConversaDB.timestamp)).limit(limite).all()

    def contar_conversas(self, dias: int = 30) -> int:
        """Conta conversas dos últimos N dias"""
        desde = datetime.utcnow() - timedelta(days=dias)
        return self.session.query(ConversaDB).filter(
            ConversaDB.timestamp >= desde
        ).count()

    def estatisticas_agentes(self) -> Dict[str, int]:
        """Retorna estatísticas de uso por agente"""
        resultados = self.session.query(
            ConversaDB.agente,
            func.count(ConversaDB.id)
        ).group_by(ConversaDB.agente).all()

        return {r[0] or "desconhecido": r[1] for r in resultados}

    def estatisticas_intencoes(self) -> Dict[str, int]:
        """Retorna estatísticas de intenções"""
        resultados = self.session.query(
            ConversaDB.intencao,
            func.count(ConversaDB.id)
        ).group_by(ConversaDB.intencao).all()

        return {r[0] or "conversa": r[1] for r in resultados}

    # ========== PREFERÊNCIAS ==========
    def salvar_preferencia(self, chave: str, valor: str, categoria: str = "geral") -> PreferenciaDB:
        """Salva ou atualiza uma preferência"""
        pref = self.session.query(PreferenciaDB).filter(
            PreferenciaDB.chave == chave
        ).first()

        if pref:
            pref.valor = valor
            pref.categoria = categoria
            pref.timestamp = datetime.utcnow()
        else:
            pref = PreferenciaDB(chave=chave, valor=valor, categoria=categoria)
            self.session.add(pref)

        self.session.commit()
        return pref

    def listar_preferencias(self, categoria: str = None) -> List[PreferenciaDB]:
        """Lista preferências"""
        query = self.session.query(PreferenciaDB)
        if categoria:
            query = query.filter(PreferenciaDB.categoria == categoria)
        return query.all()

    def obter_preferencia(self, chave: str) -> Optional[str]:
        """Obtém valor de uma preferência"""
        pref = self.session.query(PreferenciaDB).filter(
            PreferenciaDB.chave == chave
        ).first()
        return pref.valor if pref else None

    # ========== EVENTOS ==========
    def salvar_evento(self, titulo: str, data_inicio: datetime, 
                      data_fim: datetime = None, descricao: str = "",
                      local: str = "", google_event_id: str = "") -> EventoDB:
        """Salva um evento"""
        evento = EventoDB(
            titulo=titulo,
            data_inicio=data_inicio,
            data_fim=data_fim,
            descricao=descricao,
            local=local,
            google_event_id=google_event_id
        )
        self.session.add(evento)
        self.session.commit()
        return evento

    def listar_eventos(self, desde: datetime = None, ate: datetime = None) -> List[EventoDB]:
        """Lista eventos em um período"""
        query = self.session.query(EventoDB)
        if desde:
            query = query.filter(EventoDB.data_inicio >= desde)
        if ate:
            query = query.filter(EventoDB.data_inicio <= ate)
        return query.order_by(EventoDB.data_inicio).all()

    # ========== TAREFAS ==========
    def salvar_tarefa(self, titulo: str, status: str = "pendente",
                      prioridade: str = "media", data_vencimento: datetime = None,
                      notion_page_id: str = None) -> TarefaDB:
        """Salva uma tarefa"""
        tarefa = TarefaDB(
            titulo=titulo,
            status=status,
            prioridade=prioridade,
            data_vencimento=data_vencimento,
            notion_page_id=notion_page_id
        )
        self.session.add(tarefa)
        self.session.commit()
        return tarefa

    def listar_tarefas(self, status: str = None) -> List[TarefaDB]:
        """Lista tarefas"""
        query = self.session.query(TarefaDB)
        if status:
            query = query.filter(TarefaDB.status == status)
        return query.order_by(TarefaDB.criado_em).all()

    def completar_tarefa(self, tarefa_id: int) -> bool:
        """Marca tarefa como completada"""
        tarefa = self.session.query(TarefaDB).filter(TarefaDB.id == tarefa_id).first()
        if tarefa:
            tarefa.status = "completada"
            tarefa.completado_em = datetime.utcnow()
            self.session.commit()
            return True
        return False

    # ========== MÉTRICAS ==========
    def salvar_metrica(self, tipo: str, valor: float, metadata: Dict = None) -> MetricaDB:  # noqa: A002
        """Salva uma métrica"""
        metrica = MetricaDB(
            tipo=tipo,
            valor=valor,
            extra_data=metadata or {}
        )
        self.session.add(metrica)
        self.session.commit()
        return metrica

    def estatisticas_gerais(self) -> Dict[str, Any]:
        """Retorna estatísticas gerais do sistema"""
        total_conversas = self.session.query(ConversaDB).count()
        total_prefs = self.session.query(PreferenciaDB).count()
        total_tarefas = self.session.query(TarefaDB).count()
        total_eventos = self.session.query(EventoDB).count()

        hoje = datetime.utcnow().date()
        conv_hoje = self.session.query(ConversaDB).filter(
            func.date(ConversaDB.timestamp) == hoje
        ).count()

        return {
            "total_conversas": total_conversas,
            "total_preferencias": total_prefs,
            "total_tarefas": total_tarefas,
            "total_eventos": total_eventos,
            "conversas_hoje": conv_hoje,
            "agentes_usados": self.estatisticas_agentes(),
            "intencoes": self.estatisticas_intencoes()
        }

    # ========== DOCUMENTOS ==========
    def salvar_documento(self, nome: str, caminho: str, tipo: str,
                         tamanho: int, conteudo_resumo: str = "") -> DocumentoDB:
        """Salva registro de documento analisado"""
        doc = DocumentoDB(
            nome=nome,
            caminho=caminho,
            tipo=tipo,
            tamanho=tamanho,
            conteudo_resumo=conteudo_resumo
        )
        self.session.add(doc)
        self.session.commit()
        return doc

    def listar_documentos(self) -> List[DocumentoDB]:
        """Lista documentos analisados"""
        return self.session.query(DocumentoDB).order_by(
            desc(DocumentoDB.analisado_em)
        ).all()
