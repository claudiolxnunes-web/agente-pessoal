"""Interface Web principal do Agente Pessoal usando Streamlit"""
import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agents.coordenador import conversar
from memory.vector_store import MemoriaAgente
from config.settings import Config

st.set_page_config(
    page_title=f"{Config.AGENT_NAME} - Agente Pessoal",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1f77b4; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.1rem; color: #666; margin-bottom: 2rem; }
    .chat-message-user { background-color: #e3f2fd; border-radius: 15px; padding: 12px 16px; margin: 8px 0; border-left: 4px solid #2196f3; }
    .chat-message-agent { background-color: #f3e5f5; border-radius: 15px; padding: 12px 16px; margin: 8px 0; border-left: 4px solid #9c27b0; }
    .status-badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 0.85rem; font-weight: 500; }
    .status-active { background-color: #e8f5e9; color: #2e7d32; }
    .status-inactive { background-color: #ffebee; color: #c62828; }
    .memory-card { background-color: #fff8e1; border-radius: 10px; padding: 10px; margin: 5px 0; border: 1px solid #ffe082; }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    import uuid
    st.session_state.thread_id = str(uuid.uuid4())
if "memoria" not in st.session_state:
    st.session_state.memoria = MemoriaAgente()

with st.sidebar:
    st.markdown(f"<h2 style='text-align: center;'>⚙️ Configurações</h2>", unsafe_allow_html=True)

    st.markdown("### 🔌 Integrações")

    integracoes = [
        ("Google Calendar", Config.GOOGLE_CALENDAR_ENABLED),
        ("Gmail", Config.GMAIL_ENABLED),
        ("Notion", Config.NOTION_ENABLED),
        ("WhatsApp", Config.WHATSAPP_ENABLED),
        ("Telegram", Config.TELEGRAM_ENABLED),
        ("Agendamento", Config.AUTO_SCHEDULE_ENABLED),
    ]

    for nome, ativo in integracoes:
        status = "Ativo" if ativo else "Inativo"
        classe = "status-active" if ativo else "status-inactive"
        st.markdown(f"<span class='status-badge {classe}'>{nome}: {status}</span>", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### 🧠 Memória")
    prefs = st.session_state.memoria.resumo_preferencias()
    if prefs:
        for k, v in prefs.items():
            st.markdown(f"<div class='memory-card'><b>{k}:</b> {v}</div>", unsafe_allow_html=True)
    else:
        st.info("Nenhuma preferência salva.")

    st.markdown("---")

    st.markdown("### 🛠️ Ações")

    if st.button("🗑️ Limpar Conversa", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.button("🧹 Limpar Memória", use_container_width=True):
        st.session_state.memoria.limpar_memoria()
        st.success("Memória limpa!")
        st.rerun()

    if st.button("🆕 Nova Sessão", use_container_width=True):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 Links")
    st.markdown("[📈 Dashboard](dashboard)")
    st.markdown("[📱 Bot Telegram](bot_telegram)")
    st.caption(f"Thread ID: {st.session_state.thread_id[:8]}...")

col1, col2 = st.columns([1, 4])
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=100)
with col2:
    st.markdown(f"<div class='main-header'>🤖 {Config.AGENT_NAME}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-header'>Seu assistente pessoal inteligente | Olá, {Config.USER_NAME}!</div>", unsafe_allow_html=True)

st.markdown("---")

chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-message-user'><b>👤 {Config.USER_NAME}</b><br>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-message-agent'><b>🤖 {Config.AGENT_NAME}</b><br>{msg['content']}</div>", unsafe_allow_html=True)

st.markdown("---")

with st.container():
    col1, col2 = st.columns([6, 1])

    with col1:
        user_input = st.text_input(
            "",
            placeholder="Digite sua mensagem...",
            key="user_input",
            label_visibility="collapsed"
        )

    with col2:
        send_button = st.button("📤 Enviar", use_container_width=True)

if send_button and user_input.strip():
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("🤖 Pensando..."):
        try:
            resposta = conversar(user_input, thread_id=st.session_state.thread_id)
        except Exception as e:
            resposta = f"❌ Erro: {str(e)}"

    st.session_state.messages.append({"role": "agent", "content": resposta})
    st.rerun()

if not st.session_state.messages:
    st.markdown("---")
    st.markdown("### 💡 Exemplos de comandos:")

    exemplos = [
        ("📅", "Agenda uma reunião com a equipe sexta às 15h"),
        ("📝", "Adicione tarefa: comprar presente de aniversário"),
        ("📧", "Liste meus emails não lidos"),
        ("🔍", "Quais as novidades sobre inteligência artificial?"),
        ("🧠", "Meu nome é João e eu trabalho com design"),
        ("📄", "Analise o arquivo relatorio.pdf"),
        ("📱", "Envie mensagem no WhatsApp para 11999999999: Olá!"),
        ("⏰", "Agende lembrete diário às 8h para beber água"),
    ]

    cols = st.columns(4)
    for i, (emoji, texto) in enumerate(exemplos):
        with cols[i % 4]:
            if st.button(f"{emoji} {texto}", use_container_width=True, key=f"exemplo_{i}"):
                st.session_state.messages.append({"role": "user", "content": texto})
                with st.spinner("🤖 Pensando..."):
                    try:
                        resposta = conversar(texto, thread_id=st.session_state.thread_id)
                    except Exception as e:
                        resposta = f"❌ Erro: {str(e)}"
                st.session_state.messages.append({"role": "agent", "content": resposta})
                st.rerun()

st.markdown("---")
st.caption("🤖 Agente Pessoal v2.0 | Multi-Agent com LangGraph | 2026")
