"""Integração Telegram via aiogram"""
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from typing import Callable, Optional

class TelegramTool:
    """Ferramenta para bot Telegram integrado ao agente"""

    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.bot = Bot(token=bot_token)
        self.dp = Dispatcher()
        self.message_handler: Optional[Callable] = None
        self._running = False

    def set_message_handler(self, handler: Callable[[str, int], str]):
        """Define função que processa mensagens e retorna resposta"""
        self.message_handler = handler

    async def enviar_mensagem(self, chat_id: int, mensagem: str):
        """Envia mensagem para um chat específico"""
        try:
            await self.bot.send_message(chat_id=chat_id, text=mensagem)
            return True
        except Exception as e:
            print(f"Erro ao enviar para Telegram: {e}")
            return False

    async def enviar_notificacao(self, chat_id: int, titulo: str, corpo: str):
        """Envia notificação formatada"""
        mensagem = f"🔔 *{titulo}*\n\n{corpo}"
        try:
            await self.bot.send_message(
                chat_id=chat_id, 
                text=mensagem, 
                parse_mode="Markdown"
            )
            return True
        except Exception as e:
            print(f"Erro na notificação: {e}")
            return False

    def _setup_handlers(self):
        """Configura handlers do bot"""

        @self.dp.message(Command("start"))
        async def cmd_start(message: Message):
            await message.answer(
                f"🤖 Olá! Sou {message.bot._me.first_name}.\n"
                "Envie qualquer mensagem e vou ajudar você!\n"
                "Use /ajuda para ver comandos disponíveis."
            )

        @self.dp.message(Command("ajuda"))
        async def cmd_help(message: Message):
            ajuda = """🤖 *Comandos disponíveis:*

/start - Iniciar conversa
/ajuda - Mostrar esta ajuda
/tarefas - Listar tarefas
/calendario - Ver eventos
/buscar <termo> - Buscar na web

Ou simplesmente converse comigo!"""
            await message.answer(ajuda, parse_mode="Markdown")

        @self.dp.message()
        async def handle_message(message: Message):
            if self.message_handler:
                # Processa via agente
                resposta = self.message_handler(message.text, message.chat.id)
                await message.answer(resposta)
            else:
                await message.answer("🤖 Agente ainda não configurado.")

    async def iniciar(self):
        """Inicia o bot em modo polling"""
        self._setup_handlers()
        self._running = True

        print("🚀 Bot Telegram iniciado!")
        print("Pressione Ctrl+C para parar.")

        try:
            await self.dp.start_polling(self.bot)
        finally:
            await self.bot.session.close()

    def iniciar_sync(self):
        """Inicia de forma síncrona (para threading)"""
        asyncio.run(self.iniciar())

    async def parar(self):
        """Para o bot"""
        self._running = False
        await self.bot.session.close()
        print("🛑 Bot Telegram parado.")


# ── Função de módulo ──────────────────────────────────────────────────────────
def enviar_mensagem_telegram(chat_id: str, mensagem: str) -> str:
    import os, asyncio
    try:
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        tool = TelegramTool(token)
        asyncio.get_event_loop().run_until_complete(
            tool.enviar_mensagem(int(chat_id), mensagem)
        )
        return f"✅ Mensagem Telegram enviada para {chat_id}"
    except Exception as e:
        return f"Erro Telegram: {e}"
