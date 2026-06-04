"""Sistema de memória persistente usando ChromaDB + embeddings"""
import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from datetime import datetime
import json

class MemoriaAgente:
    """Memória de longo prazo do agente usando vector database"""

    def __init__(self, persist_dir="./memory/chroma_db"):
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)

        # Inicializa ChromaDB
        self.client = chromadb.Client(Settings(
            persist_directory=persist_dir,
            is_persistent=True
        ))

        # Cria coleções separadas para diferentes tipos de memória
        self.conversas = self.client.get_or_create_collection("conversas")
        self.preferencias = self.client.get_or_create_collection("preferencias")
        self.conhecimento = self.client.get_or_create_collection("conhecimento")

        # Modelo de embeddings local (não precisa de API)
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')

    def salvar_conversa(self, mensagem_usuario, resposta_agente, metadata=None):
        """Salva uma interação na memória de conversas"""
        timestamp = datetime.now().isoformat()
        doc_id = f"conv_{timestamp}"

        texto = f"Usuário: {mensagem_usuario}\nAgente: {resposta_agente}"
        embedding = self.embedder.encode(texto).tolist()

        self.conversas.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[texto],
            metadatas=[{
                "timestamp": timestamp,
                "tipo": "conversa",
                **(metadata or {})
            }]
        )
        return doc_id

    def salvar_preferencia(self, chave, valor, categoria="geral"):
        """Salva uma preferência do usuário"""
        doc_id = f"pref_{chave}_{datetime.now().isoformat()}"
        texto = f"{chave}: {valor}"
        embedding = self.embedder.encode(texto).tolist()

        self.preferencias.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[texto],
            metadatas=[{
                "chave": chave,
                "valor": str(valor),
                "categoria": categoria,
                "timestamp": datetime.now().isoformat()
            }]
        )
        return doc_id

    def buscar_memoria(self, query, tipo="conversas", n_resultados=5):
        """Busca memórias relevantes por similaridade semântica"""
        embedding = self.embedder.encode(query).tolist()

        colecao = {
            "conversas": self.conversas,
            "preferencias": self.preferencias,
            "conhecimento": self.conhecimento
        }.get(tipo, self.conversas)

        resultados = colecao.query(
            query_embeddings=[embedding],
            n_results=n_resultados,
            include=["documents", "metadatas", "distances"]
        )

        return resultados

    def buscar_todas_memorias(self, query, n_por_tipo=3):
        """Busca em todas as coleções de memória"""
        embedding = self.embedder.encode(query).tolist()
        memorias = []

        for nome, colecao in [("conversas", self.conversas), 
                              ("preferencias", self.preferencias),
                              ("conhecimento", self.conhecimento)]:
            try:
                resultados = colecao.query(
                    query_embeddings=[embedding],
                    n_results=n_por_tipo,
                    include=["documents", "metadatas"]
                )
                if resultados["documents"][0]:
                    for doc, meta in zip(resultados["documents"][0], resultados["metadatas"][0]):
                        memorias.append({
                            "tipo": nome,
                            "conteudo": doc,
                            "metadata": meta
                        })
            except Exception:
                pass

        # Ordena por relevância (simplificado)
        return memorias

    def resumo_preferencias(self):
        """Retorna todas as preferências salvas como dicionário"""
        try:
            todos = self.preferencias.get()
            prefs = {}
            for meta in todos["metadatas"]:
                prefs[meta["chave"]] = meta["valor"]
            return prefs
        except Exception:
            return {}

    def limpar_memoria(self, tipo=None):
        """Limpa memórias (útil para testes ou reset)"""
        if tipo is None:
            for colecao in [self.conversas, self.preferencias, self.conhecimento]:
                try:
                    todos = colecao.get()
                    if todos["ids"]:
                        colecao.delete(ids=todos["ids"])
                except Exception:
                    pass
        else:
            colecao = {"conversas": self.conversas, "preferencias": self.preferencias}.get(tipo)
            if colecao:
                todos = colecao.get()
                if todos["ids"]:
                    colecao.delete(ids=todos["ids"])
