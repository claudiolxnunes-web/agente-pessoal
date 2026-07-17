#!/usr/bin/env python3
"""Síntese de voz via OpenAI TTS — converte texto em áudio MP3."""
import os
import tempfile
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def texto_para_audio(texto: str) -> str:
    """Converte texto em áudio e salva em arquivo temporário. Retorna o caminho do arquivo."""
    response = client.audio.speech.create(
        model="tts-1",
        voice="nova",
        input=texto,
    )
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.write(response.content)
    tmp.close()
    return tmp.name
