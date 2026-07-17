"""Bot Telegram standalone para o Agente Pessoal"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from config.settings import Config
from agents.coordenador import conversar
from tools.tts_tool import texto_para_audio
import os
from tools.agenda_draft_store import salvar_rascunho, obter_rascunho, limpar_rascunho
from tools.agenda_extracao_tool import extrair_eventos_da_semana
from tools.google_calendar_tool import criar_evento_calendar
import re
from tools.voice_tool import transcrever_audio
import tempfile, os

# Inicializa bot
bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"🤖 Olá! Sou *{Config.AGENT_NAME}*, seu assistente pessoal.\n\n"
        "Posso ajudar com:\n"
        "📅 Calendário | 📝 Tarefas | 📧 Emails\n"
        "🔍 Busca | 📄 Documentos | ⏰ Agendamentos\n\n"
        "Envie qualquer mensagem ou use /ajuda",
        parse_mode="Markdown"
    )

@dp.message(Command("ajuda"))
async def cmd_help(message: Message):
    ajuda = """🤖 *Comandos disponíveis:*

/start - Iniciar conversa
/ajuda - Mostrar esta ajuda
/status - Ver integrações ativas

*Exemplos de comandos:*
📅 "Agenda reunião amanhã às 14h"
📝 "Adiciona tarefa: comprar leite"
📧 "Liste meus emails não lidos"
🔍 "Busca previsão do tempo SP"
📄 "Analise o arquivo relatorio.pdf"
⏰ "Agende backup diário às 23h"

Ou simplesmente converse comigo!"""
    await message.answer(ajuda, parse_mode="Markdown")

@dp.message(Command("status"))
async def cmd_status(message: Message):
    status = f"""🔌 *Status das Integrações:*

📅 Google Calendar: {'🟢' if Config.GOOGLE_CALENDAR_ENABLED else '🔴'}
📧 Gmail: {'🟢' if Config.GMAIL_ENABLED else '🔴'}
📝 Notion: {'🟢' if Config.NOTION_ENABLED else '🔴'}
📱 WhatsApp: {'🟢' if Config.WHATSAPP_ENABLED else '🔴'}
✈️ Telegram: 🟢
⏰ Agendamento: {'🟢' if Config.AUTO_SCHEDULE_ENABLED else '🔴'}

🤖 *Modelo:* {Config.MODEL_NAME}
👤 *Usuário:* {Config.USER_NAME}"""
    await message.answer(status, parse_mode="Markdown")

@dp.message()
async def handle_message(message: Message):
    """Processa todas as mensagens via agente"""

    # indica que está digitando
    await bot.send_chat_action(message.chat.id, "typing")

    # captura texto corretamente (texto, legenda, ou transcrição de áudio)
    texto = message.text or message.caption or ""

    if not texto.strip() and (message.voice or message.audio):
        file_id = message.voice.file_id if message.voice else message.audio.file_id
        file = await bot.get_file(file_id)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            await bot.download_file(file.file_path, destination=tmp.name)
            tmp_path = tmp.name
        try:
            texto = transcrever_audio(tmp_path)
            await message.answer(f"🎤 Transcrito: {texto}")
        finally:
            os.remove(tmp_path)

    # valida se veio vazio
    if not texto.strip():
        await message.answer("⚠️ Envie uma mensagem de texto.")
        return

    # Detecta pedido de resposta em voz
    frases_voz = ["responde por voz", "fala isso", "responda por voz",
                  "me responde em audio", "resposta em audio", "fala para mim"]
    pedir_voz = any(f in texto.lower() for f in frases_voz)
    texto_limpo = texto.lower()
    for f in frases_voz:
        texto_limpo = texto_limpo.replace(f, "").strip()
    if not texto_limpo:
        texto_limpo = texto

    chat_id = str(message.chat.id)

    rascunho = obter_rascunho(chat_id)
    if rascunho:
        resposta_lower = texto.strip().lower()
        if resposta_lower in ("sim", "confirma", "confirmo", "ok", "pode criar"):
            criados, erros = 0, 0
            falhas = []
            for ev in rascunho:
                try:
                    resultado_evento = criar_evento_calendar(
                        titulo=ev.get("titulo", "Evento"),
                        data_hora=ev.get("data_hora", ""),
                        duracao_horas=ev.get("duracao_horas", 1),
                        descricao=ev.get("descricao", ""),
                        local=ev.get("local", ""),
                    )
                    if resultado_evento and ("erro" in resultado_evento.lower() or resultado_evento.startswith("\u274c")):
                        erros += 1
                        falhas.append(f"{ev.get('titulo','?')}: {resultado_evento}")
                    else:
                        criados += 1
                except Exception as e:
                    erros += 1
                    falhas.append(f"{ev.get('titulo','?')}: {e}")
            limpar_rascunho(chat_id)
            extra = ""
            if erros:
                extra = " (" + str(erros) + " com erro: " + "; ".join(falhas[:3]) + ")"
            await message.answer("Eventos criados: " + str(criados) + "." + extra)
            return
        elif resposta_lower in ("nao", "não", "cancela", "cancelar"):
            limpar_rascunho(chat_id)
            await message.answer("Rascunho cancelado, nada foi criado.")
            return
        else:
            await message.answer("Você tem uma agenda pendente de confirmacao. Responda sim para criar ou nao para cancelar.")
            return

    marcas_horario = re.findall(r"\d{1,2}\s*h(?:oras|s)?\s*\d{0,2}\b|\d{1,2}:\d{2}", texto.lower())
    if len(marcas_horario) >= 3:
        eventos = extrair_eventos_da_semana(texto)
        if len(eventos) >= 2:
            salvar_rascunho(chat_id, eventos)
            linhas = ["Entendi os seguintes compromissos:", ""]
            for ev in eventos:
                local_str = " - " + ev["local"] if ev.get("local") else ""
                linhas.append("- " + ev["data_hora"] + " - " + ev["titulo"] + local_str)
            linhas.append("")
            linhas.append("Confirma a criacao desses eventos? Responda sim ou nao.")
            await message.answer("\n".join(linhas))
            return

    # processa via agente
    resposta = conversar(
        texto_limpo if pedir_voz else texto,
        thread_id=f"telegram_{message.chat.id}"
    )

    # envia resposta
    if pedir_voz:
        try:
            audio_path = texto_para_audio(resposta)
            from aiogram.types import FSInputFile
            await bot.send_voice(message.chat.id, FSInputFile(audio_path))
            os.remove(audio_path)
        except Exception as e:
            await message.answer(resposta)
            await message.answer(f"(Nao consegui gerar audio: {e})")
    else:
        await message.answer(resposta)


async def main():
    print("🚀 Bot Telegram iniciado!")
    print(f"🤖 Nome: {Config.AGENT_NAME}")
    print("Pressione Ctrl+C para parar.\n")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if not Config.TELEGRAM_ENABLED:
        print("❌ Telegram não configurado. Verifique .env")
        print("TELEGRAM_ENABLED=true")
        print("TELEGRAM_BOT_TOKEN=seu_token")
        sys.exit(1)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot parado.")
