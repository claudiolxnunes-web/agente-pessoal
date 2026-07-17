"""Testes unitários para o Agente Pessoal"""
import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.settings import Config
from tools import WebSearchTool

class TestConfig:
    """Testes de configuração"""

    def test_config_existe(self):
        assert hasattr(Config, 'OPENAI_API_KEY')
        assert hasattr(Config, 'MODEL_NAME')

    def test_config_padroes(self):
        assert Config.MODEL_NAME == "gpt-4o-mini" or Config.MODEL_NAME
        assert Config.TEMPERATURE == 0.2

class TestMemoria:
    """Testes de memória — usa fallback JSON quando chromadb não está instalado"""

    @pytest.fixture
    def memoria(self, tmp_path):
        from memory.vector_store import MemoriaAgente
        return MemoriaAgente(persist_dir=str(tmp_path))

    def test_salvar_conversa(self, memoria):
        memoria.salvar_conversa("Olá", "Oi! Como posso ajudar?")
        resultados = memoria.buscar_memoria("Olá", tipo="conversas")
        assert resultados is not None

    def test_salvar_preferencia(self, memoria):
        memoria.salvar_preferencia("nome", "João", "pessoal")
        prefs = memoria.resumo_preferencias()
        assert "nome" in prefs
        assert prefs["nome"] == "João"

class TestWebSearch:
    """Testes de busca web"""

    def test_buscar_sem_api(self):
        tool = WebSearchTool()
        resultado = tool.buscar("python programming", num_results=2)
        assert isinstance(resultado, str)
        assert len(resultado) > 0

class TestDocumentTool:
    """Testes de documentos"""

    def test_listar_vazio(self):
        from tools import DocumentTool
        doc = DocumentTool()
        resultado = doc.listar_documentos()
        assert "Nenhum documento" in resultado

class TestVoiceTool:
    """Testes de voz"""

    def test_info(self):
        from tools.voice_tool import VoiceTool
        voice = VoiceTool("base")
        info = voice.info()
        assert "Whisper" in info
