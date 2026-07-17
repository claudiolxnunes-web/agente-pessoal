"""Transcrição de áudio via OpenAI Whisper API"""
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcrever_audio(audio_path: str) -> dict:
    """Transcreve áudio usando OpenAI Whisper API."""
    try:
        with open(audio_path, "rb") as f:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="pt"
            )
        return {
            "sucesso": True,
            "texto": transcription.text,
            "idioma": "pt",
            "duracao": 0.0
        }
    except Exception as e:
        return {
            "sucesso": False,
            "erro": f"Erro ao transcrever: {e}"
        }

class VoiceTool:
    """Adaptador de classe para a API — embrulha a funcao transcrever_audio."""
    def __init__(self, model: str = "whisper-1"):
        self.model = model

    def transcrever_audio(self, audio_path: str) -> dict:
        return transcrever_audio(audio_path)
