"""Modelos SQLAlchemy para o Agente Pessoal"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from config.settings import Config

Base = declarative_base()

class ConversaDB(Base):
    """Tabela de conversas"""
    __tablename__ = "conversas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    thread_id = Column(String(100), index=True)
    role = Column(String(20))  # user ou agent
    content = Column(Text)
    agente = Column(String(50))
    intencao = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)

class PreferenciaDB(Base):
    """Tabela de preferências"""
    __tablename__ = "preferencias"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chave = Column(String(100), unique=True, index=True)
    valor = Column(Text)
    categoria = Column(String(50))
    timestamp = Column(DateTime, default=datetime.utcnow)

class EventoDB(Base):
    """Tabela de eventos do calendário"""
    __tablename__ = "eventos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(255))
    data_inicio = Column(DateTime)
    data_fim = Column(DateTime)
    descricao = Column(Text)
    local = Column(String(255))
    google_event_id = Column(String(255))
    criado_em = Column(DateTime, default=datetime.utcnow)

class TarefaDB(Base):
    """Tabela de tarefas"""
    __tablename__ = "tarefas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(255))
    status = Column(String(50), default="pendente")
    prioridade = Column(String(20), default="media")
    data_vencimento = Column(DateTime, nullable=True)
    notion_page_id = Column(String(255), nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    completado_em = Column(DateTime, nullable=True)

class MetricaDB(Base):
    """Tabela de métricas/analytics"""
    __tablename__ = "metricas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tipo = Column(String(50))  # conversa, erro, latencia
    valor = Column(Float)
    extra_data = Column(JSON, default={})
    timestamp = Column(DateTime, default=datetime.utcnow)

class DocumentoDB(Base):
    """Tabela de documentos analisados"""
    __tablename__ = "documentos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(255))
    caminho = Column(String(500))
    tipo = Column(String(20))  # pdf, docx, csv, etc
    tamanho = Column(Integer)
    conteudo_resumo = Column(Text)
    analisado_em = Column(DateTime, default=datetime.utcnow)

# Engine e Session
def get_engine():
    return create_engine(Config.DATABASE_URL)

def init_db():
    """Inicializa todas as tabelas"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine

def get_session():
    """Retorna uma nova sessão"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
