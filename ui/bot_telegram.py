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

# Inicializa bot
bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"🤖 Olá! Sou *{Config.AGENT_NAME}*, seu assistente pessoal.

"
        "Posso ajudar com:
"
        "📅 Calendário | 📝 Tarefas | 📧 Emails
"
        "🔍 Busca | 📄 Documentos | ⏰ Agendamentos

"
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
    # Indica que está digitando
    await bot.send_chat_action(message.chat.id, "typing")

    # Processa via agente
    resposta = conversar(message.text, thread_id=f"telegram_{message.chat.id}")

    # Envia resposta
    await message.answer(resposta)

async def main():
    print("🚀 Bot Telegram iniciado!")
    print(f"🤖 Nome: {Config.AGENT_NAME}")
    print("Pressione Ctrl+C para parar.
")
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
        print("
🛑 Bot parado.")
