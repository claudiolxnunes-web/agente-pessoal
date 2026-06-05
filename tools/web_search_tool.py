"""Ferramenta de busca na web (simulada - integrar com SerpAPI ou similar)"""
import requests
import json

class WebSearchTool:
    """Busca informações na web usando SerpAPI ou DuckDuckGo"""

    def __init__(self, serpapi_key=None):
        self.serpapi_key = serpapi_key
        self.use_serpapi = serpapi_key is not None

    def buscar(self, query, num_results=5):
        """Busca informações na web"""
        if self.use_serpapi:
            return self._buscar_serpapi(query, num_results)
        else:
            return self._buscar_duckduckgo(query, num_results)

    def _buscar_serpapi(self, query, num_results):
        """Busca usando SerpAPI (mais preciso)"""
        try:
            url = "https://serpapi.com/search"
            params = {
                "q": query,
                "api_key": self.serpapi_key,
                "engine": "google",
                "num": num_results,
                "hl": "pt",
                "gl": "br"
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            resultados = []
            if "organic_results" in data:
                for r in data["organic_results"][:num_results]:
                    resultados.append({
                        "titulo": r.get("title", ""),
                        "link": r.get("link", ""),
                        "snippet": r.get("snippet", "")
                    })

            return self._formatar_resultados(resultados)

        except Exception as e:
            return f"Erro na busca: {e}"

    def _buscar_duckduckgo(self, query, num_results):
        """Busca usando DuckDuckGo (gratuito, menos preciso)"""
        try:
            # DuckDuckGo Instant Answer API
            url = "https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            resultados = []

            # Abstract (resumo direto)
            if data.get("Abstract"):
                resultados.append({
                    "titulo": data.get("Heading", "Resumo"),
                    "link": data.get("AbstractURL", ""),
                    "snippet": data["Abstract"]
                })

            # Related Topics
            for topic in data.get("RelatedTopics", [])[:num_results-1]:
                if "Text" in topic:
                    resultados.append({
                        "titulo": topic.get("FirstURL", "").split("/")[-1].replace("_", " "),
                        "link": topic.get("FirstURL", ""),
                        "snippet": topic["Text"]
                    })

            return self._formatar_resultados(resultados)

        except Exception as e:
            return f"Erro na busca DuckDuckGo: {e}"

    def _formatar_resultados(self, resultados):
        """Formata resultados para texto legível"""
        if not resultados:
            return "Nenhum resultado encontrado."

        output = "🔍 Resultados da busca:\n\n"
        for i, r in enumerate(resultados, 1):
            output += f"{i}. **{r['titulo']}**\n"
            if r['snippet']:
                output += f"   {r['snippet'][:200]}...\n"
            if r['link']:
                output += f"   🔗 {r['link']}\n"
            output += "\n"

        return output


# ── Função de módulo ──────────────────────────────────────────────────────────
def buscar_web(query: str, max_results: int = 5) -> str:
    import os
    try:
        return WebSearchTool(serpapi_key=os.getenv("SERPAPI_KEY")).buscar(query, num_results=max_results)
    except Exception as e:
        return f"Erro na busca: {e}"
