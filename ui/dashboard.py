"""Dashboard de Analytics do Agente Pessoal"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os

from config.settings import Config
from memory.vector_store import MemoriaAgente

st.set_page_config(
    page_title=f"📊 Dashboard - {Config.AGENT_NAME}",
    page_icon="📊",
    layout="wide"
)

# CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 20px;
        color: white;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 1rem;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# ========== CARREGAR DADOS ==========
memoria = MemoriaAgente()

# Buscar todas as conversas
try:
    todas_conversas = memoria.conversas.get()
    conversas_data = []
    for doc, meta in zip(todas_conversas["documents"], todas_conversas["metadatas"]):
        conversas_data.append({
            "conteudo": doc,
            "timestamp": meta.get("timestamp", ""),
            "agente": meta.get("agente", "desconhecido"),
            "intencao": meta.get("intencao", "conversa")
        })
    df_conversas = pd.DataFrame(conversas_data)
    if not df_conversas.empty:
        df_conversas["data"] = pd.to_datetime(df_conversas["timestamp"]).dt.date
        df_conversas["hora"] = pd.to_datetime(df_conversas["timestamp"]).dt.hour
except:
    df_conversas = pd.DataFrame()

# Buscar preferências
prefs = memoria.resumo_preferencias()

# ========== HEADER ==========
st.title(f"📊 Dashboard - {Config.AGENT_NAME}")
st.caption(f"Visão geral de uso e analytics | Última atualização: {datetime.now().strftime('%H:%M:%S')}")

# ========== MÉTRICAS PRINCIPAIS ==========
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_conv = len(df_conversas) if not df_conversas.empty else 0
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_conv}</div>
            <div class="metric-label">Conversas Totais</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    total_prefs = len(prefs)
    st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <div class="metric-value">{total_prefs}</div>
            <div class="metric-label">Preferências Salvas</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    agentes_unicos = df_conversas["agente"].nunique() if not df_conversas.empty else 0
    st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <div class="metric-value">{agentes_unicos}</div>
            <div class="metric-label">Agentes Utilizados</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    hoje = datetime.now().date()
    conv_hoje = len(df_conversas[df_conversas["data"] == hoje]) if not df_conversas.empty else 0
    st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
            <div class="metric-value">{conv_hoje}</div>
            <div class="metric-label">Conversas Hoje</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ========== GRÁFICOS ==========
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Conversas por Dia")
    if not df_conversas.empty:
        conv_por_dia = df_conversas.groupby("data").size().reset_index(name="conversas")
        fig = px.line(conv_por_dia, x="data", y="conversas", 
                      markers=True, title="Volume de conversas")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados de conversas ainda.")

with col2:
    st.subheader("🎯 Distribuição por Agente")
    if not df_conversas.empty:
        agente_counts = df_conversas["agente"].value_counts()
        fig = px.pie(values=agente_counts.values, names=agente_counts.index,
                     title="Uso por tipo de agente")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados de agentes ainda.")

# ========== GRÁFICOS 2 ==========
col1, col2 = st.columns(2)

with col1:
    st.subheader("⏰ Horário de Pico")
    if not df_conversas.empty:
        hora_counts = df_conversas["hora"].value_counts().sort_index()
        fig = px.bar(x=hora_counts.index, y=hora_counts.values,
                     labels={"x": "Hora do dia", "y": "Conversas"},
                     title="Atividade por hora")
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados de horários ainda.")

with col2:
    st.subheader("🔥 Intenções Mais Comuns")
    if not df_conversas.empty:
        intencao_counts = df_conversas["intencao"].value_counts().head(10)
        fig = px.bar(x=intencao_counts.index, y=intencao_counts.values,
                     labels={"x": "Intenção", "y": "Frequência"},
                     title="Top intenções do usuário", color=intencao_counts.values)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sem dados de intenções ainda.")

st.markdown("---")

# ========== PREFERÊNCIAS ==========
st.subheader("🧠 Preferências do Usuário")
if prefs:
    df_prefs = pd.DataFrame([{"Chave": k, "Valor": v} for k, v in prefs.items()])
    st.dataframe(df_prefs, use_container_width=True)
else:
    st.info("Nenhuma preferência salva ainda.")

# ========== HISTÓRICO RECENTE ==========
st.subheader("💬 Conversas Recentes")
if not df_conversas.empty:
    recentes = df_conversas.tail(10)[::-1]
    for _, row in recentes.iterrows():
        with st.expander(f"🕐 {row['timestamp'][:16]} | Agente: {row['agente']}"):
            st.write(row["conteudo"][:500])
else:
    st.info("Sem conversas recentes.")

# ========== STATUS DAS INTEGRAÇÕES ==========
st.markdown("---")
st.subheader("🔌 Status das Integrações")

cols = st.columns(4)
integracoes = [
    ("Google Calendar", Config.GOOGLE_CALENDAR_ENABLED, "📅"),
    ("Gmail", Config.GMAIL_ENABLED, "📧"),
    ("Notion", Config.NOTION_ENABLED, "📝"),
    ("WhatsApp", Config.WHATSAPP_ENABLED, "📱"),
    ("Telegram", Config.TELEGRAM_ENABLED, "✈️"),
    ("Agendamento", Config.AUTO_SCHEDULE_ENABLED, "⏰"),
]

for i, (nome, ativo, icone) in enumerate(integracoes):
    with cols[i % 4]:
        status = "🟢 Ativo" if ativo else "🔴 Inativo"
        st.metric(f"{icone} {nome}", status)

st.caption("🤖 Agente Pessoal v2.0 | Dashboard Analytics")
