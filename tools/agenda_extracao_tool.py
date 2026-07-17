"""Extrai uma lista estruturada de compromissos a partir de texto livre."""
import os
import json
from datetime import datetime
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extrair_eventos_da_semana(texto: str) -> list:
    prompt = f"""Extraia TODOS os compromissos mencionados no texto abaixo e retorne uma lista JSON pura (sem markdown, sem explicação), no formato:
[{{"titulo": "...", "data_hora": "DD/MM/AAAA HH:MM", "duracao_horas": 1, "local": "...", "descricao": ""}}]

Regras:
- Use a data atual ({datetime.now().strftime('%d/%m/%Y')}) como referência para calcular datas relativas (ex: "segunda-feira" = próxima segunda-feira a partir de hoje).
- duracao_horas padrão é 1 se não especificado.
- Se não houver local mencionado, deixe "local": "".
- Não invente compromissos que não foram mencionados no texto.

Texto:
\"\"\"{texto}\"\"\"

JSON:"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    content = resp.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        if content.startswith("json"):
            content = content[4:].strip()
    try:
        return json.loads(content)
    except Exception:
        return []
