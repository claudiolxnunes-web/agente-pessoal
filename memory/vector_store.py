"""Sistema de memória persistente — ChromaDB opcional, fallback em memória simples"""
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logger.warning("chromadb/sentence-transformers não instalados — usando memória simples em JSON.")


class MemoriaAgente:
    """Memória de longo prazo do agente. Usa ChromaDB se disponível, senão JSON simples."""

    def __init__(self, persist_dir="./memory/chroma_db"):
        self.persist_dir = persist_dir
        os.makedirs(persist_dir, exist_ok=True)
        self._fallback_path = os.path.join(persist_dir, "memoria_fallback.json")

        if CHROMADB_AVAILABLE:
            self.client = chromadb.Client(Settings(
                persist_directory=persist_dir,
                is_persistent=True
            ))
            self.conversas = self.client.get_or_create_collection("conversas")
            self.preferencias = self.client.get_or_create_collection("preferencias")
            self.conhecimento = self.client.get_or_create_collection("conhecimento")
            self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            self.client = None
            self._dados = self._carregar_fallback()

    # ── Fallback JSON ─────────────────────────────────────────────────────────

    def _carregar_fallback(self):
        if os.path.exists(self._fallback_path):
            try:
                with open(self._fallback_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"conversas": [], "preferencias": {}, "conhecimento": []}

    def _salvar_fallback(self):
        with open(self._fallback_path, "w", encoding="utf-8") as f:
            json.dump(self._dados, f, ensure_ascii=False, indent=2)

    # ── API pública ───────────────────────────────────────────────────────────

    def salvar_conversa(self, mensagem_usuario, resposta_agente, metadata=None):
        timestamp = datetime.now().isoformat()
        texto = f"Usuário: {mensagem_usuario}\nAgente: {resposta_agente}"

        if CHROMADB_AVAILABLE:
            embedding = self.embedder.encode(texto).tolist()
            self.conversas.add(
                ids=[f"conv_{timestamp}"],
                embeddings=[embedding],
                documents=[texto],
                metadatas=[{"timestamp": timestamp, "tipo": "conversa", **(metadata or {})}]
            )
        else:
            self._dados["conversas"].append({"texto": texto, "timestamp": timestamp})
            self._salvar_fallback()

        return f"conv_{timestamp}"

    def salvar_preferencia(self, chave, valor, categoria="geral"):
        if CHROMADB_AVAILABLE:
            texto = f"{chave}: {valor}"
            embedding = self.embedder.encode(texto).tolist()
            self.preferencias.add(
                ids=[f"pref_{chave}_{datetime.now().isoformat()}"],
                embeddings=[embedding],
                documents=[texto],
                metadatas=[{"chave": chave, "valor": str(valor), "categoria": categoria,
                             "timestamp": datetime.now().isoformat()}]
            )
        else:
            self._dados["preferencias"][chave] = valor
            self._salvar_fallback()

    def buscar_memoria(self, query, tipo="conversas", n_resultados=5):
        if not CHROMADB_AVAILABLE:
            entradas = self._dados.get(tipo if tipo != "conversas" else "conversas", [])
            return {"documents": [[e.get("texto", "") for e in entradas[-n_resultados:]]]}

        embedding = self.embedder.encode(query).tolist()
        colecao = {"conversas": self.conversas, "preferencias": self.preferencias,
                   "conhecimento": self.conhecimento}.get(tipo, self.conversas)
        return colecao.query(query_embeddings=[embedding], n_results=n_resultados,
                             include=["documents", "metadatas", "distances"])

    def resumo_preferencias(self):
        if not CHROMADB_AVAILABLE:
            return dict(self._dados.get("preferencias", {}))
        try:
            todos = self.preferencias.get()
            return {m["chave"]: m["valor"] for m in todos["metadatas"]}
        except Exception:
            return {}

    def limpar_memoria(self, tipo=None):
        if not CHROMADB_AVAILABLE:
            if tipo:
                self._dados[tipo] = [] if tipo != "preferencias" else {}
            else:
                self._dados = {"conversas": [], "preferencias": {}, "conhecimento": []}
            self._salvar_fallback()
            return
        colecoes = [self.conversas, self.preferencias, self.conhecimento] if not tipo else [
            {"conversas": self.conversas, "preferencias": self.preferencias}.get(tipo)
        ]
        for col in colecoes:
            if col:
                try:
                    todos = col.get()
                    if todos["ids"]:
                        col.delete(ids=todos["ids"])
                except Exception:
                    pass


# ── Singleton e funções de módulo (usadas em coordenador.py) ─────────────────

_memoria: MemoriaAgente | None = None


def _get_memoria() -> MemoriaAgente:
    global _memoria
    if _memoria is None:
        _memoria = MemoriaAgente()
    return _memoria


def salvar_memoria(texto: str, metadata: dict = None) -> str:
    partes = texto.split("\nAgente: ", 1)
    usuario = partes[0].replace("Usuário: ", "").strip() if len(partes) > 1 else texto
    agente = partes[1].strip() if len(partes) > 1 else ""
    _get_memoria().salvar_conversa(usuario, agente, metadata)
    return "Memória salva."


def buscar_memorias(query: str, n: int = 3) -> str:
    try:
        resultado = _get_memoria().buscar_memoria(query, n_resultados=n)
        docs = resultado.get("documents", [[]])[0]
        if not docs:
            return "Nenhuma memória relevante encontrada."
        return "\n---\n".join(docs[:n])
    except Exception:
        return ""
