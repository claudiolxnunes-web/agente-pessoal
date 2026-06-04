"""Processamento de voz e áudio com Whisper"""
import os
import tempfile
from typing import Optional, Dict, Any

class VoiceTool:
    """Ferramenta para transcrição e síntese de voz"""

    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self.model = None
        self._loaded = False

    def _load_model(self):
        """Carrega modelo Whisper (lazy loading)"""
        if not self._loaded:
            try:
                import whisper
            except ImportError:
                raise ImportError("openai-whisper não instalado. Execute: pip install openai-whisper")
            print(f"Carregando modelo Whisper: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            self._loaded = True

    def transcrever_audio(self, caminho_audio: str, idioma: str = "pt") -> Dict[str, Any]:
        """Transcreve arquivo de áudio para texto"""
        try:
            self._load_model()

            resultado = self.model.transcribe(
                caminho_audio,
                language=idioma,
                fp16=False
            )

            return {
                "sucesso": True,
                "texto": resultado["text"],
                "idioma": resultado.get("language", idioma),
                "duracao": resultado.get("duration", 0),
                "segmentos": len(resultado.get("segments", []))
            }

        except Exception as e:
            return {
                "sucesso": False,
                "erro": str(e),
                "texto": ""
            }

    def transcrever_bytes(self, audio_bytes: bytes, idioma: str = "pt") -> Dict[str, Any]:
        """Transcreve áudio de bytes (para webhooks)"""
        try:
            # Salva em arquivo temporário
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            resultado = self.transcrever_audio(tmp_path, idioma)

            # Limpa arquivo temporário
            os.unlink(tmp_path)

            return resultado

        except Exception as e:
            return {
                "sucesso": False,
                "erro": str(e),
                "texto": ""
            }

    def transcrever_ogg(self, caminho_ogg: str, idioma: str = "pt") -> Dict[str, Any]:
        """Transcreve áudio OGG (formato WhatsApp/Telegram)"""
        try:
            from pydub import AudioSegment

            # Converte OGG para WAV
            audio = AudioSegment.from_ogg(caminho_ogg)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                audio.export(tmp.name, format="wav")
                tmp_path = tmp.name

            resultado = self.transcrever_audio(tmp_path, idioma)
            os.unlink(tmp_path)

            return resultado

        except ImportError:
            return {
                "sucesso": False,
                "erro": "Instale pydub: pip install pydub",
                "texto": ""
            }
        except Exception as e:
            return {
                "sucesso": False,
                "erro": str(e),
                "texto": ""
            }

    def resumo_transcricao(self, texto: str, llm) -> str:
        """Gera resumo inteligente da transcrição"""
        prompt = f"""Resuma a transcrição abaixo de forma concisa:

TRANSCRIÇÃO:
{texto}

Resumo (3-5 pontos principais):"""

        try:
            resposta = llm.invoke(prompt)
            return resposta.content
        except:
            return texto[:500] + "..."

    def info(self) -> str:
        """Retorna informações sobre a ferramenta"""
        return f"""🎙️ Voice Tool
Modelo: Whisper {self.model_name}
Status: {'Carregado' if self._loaded else 'Não carregado'}

Suporta: MP3, WAV, OGG, M4A
Idiomas: pt (português), en (inglês), es (espanhol), etc.
"""
