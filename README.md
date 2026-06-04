# 🤖 Agente Pessoal com IA - v3.1 (Completo + 4 E-mails)

Sistema multi-agent completo com **16 agentes**, **12 integrações**, memória persistente, interface web, bots WhatsApp/Telegram, análise de documentos, agendamento automático, dashboard de analytics, voz/áudio, banco de dados SQL, API REST, Docker, CI/CD e **4 integrações de e-mail**.

## 🚀 Funcionalidades (v3.1)

| # | Funcionalidade | Status | Arquivo |
|---|---------------|--------|---------|
| 1 | **Multi-Agent LangGraph** | ✅ 16 agentes | `agents/coordenador.py` |
| 2 | **Memória Vetorial** | ✅ ChromaDB | `memory/vector_store.py` |
| 3 | **Google Calendar** | ✅ CRUD eventos | `tools/google_calendar_tool.py` |
| 4 | **Gmail** | ✅ Ler/enviar | `tools/gmail_tool.py` |
| 5 | **Outlook / Microsoft 365** | ✅ Ler/envir/eventos | `tools/outlook_tool.py` |
| 6 | **Yahoo Mail** | ✅ Ler/enviar IMAP | `tools/yahoo_mail_tool.py` |
| 7 | **ProtonMail** | ✅ Ler/enviar API | `tools/protonmail_tool.py` |
| 8 | **Notion** | ✅ Tarefas/notas | `tools/notion_tool.py` |
| 9 | **Busca Web** | ✅ DuckDuckGo/SerpAPI | `tools/web_search_tool.py` |
| 10 | **WhatsApp Bot** | ✅ Cloud API | `ui/bot_whatsapp.py` |
| 11 | **Telegram Bot** | ✅ aiogram | `ui/bot_telegram.py` |
| 12 | **Análise Documentos** | ✅ PDF/DOCX/CSV/XLSX/TXT | `tools/document_tool.py` |
| 13 | **Agendamento Auto** | ✅ Diário/semanal/intervalo | `tools/scheduler_tool.py` |
| 14 | **Interface Web** | ✅ Streamlit | `ui/streamlit_app.py` |
| 15 | **Dashboard Analytics** | ✅ Plotly/gráficos | `ui/dashboard.py` |
| 16 | **Voz/Áudio** | ✅ Whisper | `tools/voice_tool.py` |
| 17 | **Banco de Dados SQL** | ✅ SQLite/PostgreSQL | `database/` |
| 18 | **API REST** | ✅ FastAPI | `api/main.py` |
| 19 | **Docker** | ✅ Compose | `docker/` |
| 20 | **CI/CD** | ✅ GitHub Actions | `.github/workflows/` |
| 21 | **Testes** | ✅ pytest | `tests/` |
| 22 | **Human-in-the-Loop** | ✅ Aprovação | `agents/coordenador.py` |

## 📧 Integrações de E-mail (4 provedores)

| Provedor | Protocolo | Recursos | Setup |
|----------|-----------|----------|-------|
| **Gmail** | Google API | Ler, enviar, listar, deletar | OAuth2 + credentials.json |
| **Outlook / Microsoft 365** | Microsoft Graph API | Ler, enviar, eventos, calendário | Azure App Registration |
| **Yahoo Mail** | IMAP/SMTP | Ler, enviar, listar, deletar | App Password |
| **ProtonMail** | Proton API REST | Ler, enviar, listar, deletar | API Token |

### Comandos de E-mail

```
"Liste meus emails do Gmail"                    → 📧 Gmail
"Emails não lidos do Outlook"                     → 📧 Outlook
"Resuma emails do Yahoo"                          → 📧 Yahoo
"Envie email pelo ProtonMail"                     → 🔒 ProtonMail
"Envie email para [X]: assunto [Y], corpo [Z]"  → Detecta provedor ativo
"Deletar email [ID] no Gmail"                     → 🗑️ Deleta específico
"Eventos do Outlook essa semana"                  → 📅 Calendário Outlook
```

## 📁 Estrutura Completa

```
agente_pessoal/
├── 🤖 agents/
│   └── coordenador.py          ← 16 agentes orquestrados
├── 🧠 memory/
│   └── vector_store.py         ← Memória semântica ChromaDB
├── 📅 tools/
│   ├── google_calendar_tool.py ← Calendar API
│   ├── gmail_tool.py           ← Gmail API
│   ├── outlook_tool.py         ← Microsoft 365 Graph API ⭐ NOVO
│   ├── yahoo_mail_tool.py      ← IMAP/SMTP ⭐ NOVO
│   ├── protonmail_tool.py      ← Proton API ⭐ NOVO
│   ├── notion_tool.py          ← Notion API
│   ├── web_search_tool.py      ← Busca web
│   ├── whatsapp_tool.py        ← WhatsApp Cloud API
│   ├── telegram_tool.py        ← Telegram Bot API
│   ├── document_tool.py        ← PDF/DOCX/CSV/XLSX/TXT
│   ├── scheduler_tool.py       ← Agendamento automático
│   ├── voice_tool.py           ← Whisper transcrição
│   └── __init__.py
├── 🗄️ database/
│   ├── models.py               ← SQLAlchemy models
│   ├── crud.py                 ← Operações CRUD
│   └── __init__.py
├── 🌐 api/
│   ├── main.py                 ← FastAPI REST
│   └── __init__.py
├── 🖥️ ui/
│   ├── streamlit_app.py        ← Interface web
│   ├── dashboard.py            ← Analytics
│   ├── bot_telegram.py         ← Bot Telegram
│   ├── bot_whatsapp.py         ← Webhook WhatsApp
│   └── __init__.py
├── 🐳 docker/
│   ├── Dockerfile              ← Container
│   └── docker-compose.yml      ← Orquestração
├── 🔄 .github/workflows/
│   └── ci-cd.yml               ← Pipeline CI/CD
├── 🧪 tests/
│   └── test_agente.py          ← Testes unitários
├── 📚 docs/
│   ├── GUIA_ALTA_EFICIENCIA.md ← Tutorial prático
│   └── CHEAT_SHEET.md          ← Referência rápida
├── ⚙️ config/
│   ├── settings.py             ← Configurações
│   └── __init__.py
├── 📋 requirements.txt         ← Dependências
├── 📝 .env.example             ← Variáveis de ambiente
├── 🚀 setup.sh                 ← Script instalação
├── 🐳 .dockerignore            ← Docker ignore
├── 🚫 .gitignore               ← Git ignore
└── 📄 README.md                ← Este arquivo
```

## ⚙️ Configuração de E-mails

### 1. Gmail (Google)
```env
GMAIL_ENABLED=true
# Precisa de: config/credentials.json (OAuth2)
```

### 2. Outlook / Microsoft 365
```env
OUTLOOK_ENABLED=true
OUTLOOK_CLIENT_ID=seu_client_id
OUTLOOK_CLIENT_SECRET=seu_client_secret
OUTLOOK_TENANT_ID=seu_tenant_id
OUTLOOK_ACCESS_TOKEN=seu_access_token
```
**Como obter:**
1. https://portal.azure.com > App registrations > New registration
2. API permissions > Microsoft Graph > Mail.Read, Mail.Send, Calendars.ReadWrite
3. Certificates & secrets > New client secret

### 3. Yahoo Mail
```env
YAHOO_MAIL_ENABLED=true
YAHOO_EMAIL=seu@yahoo.com
YAHOO_APP_PASSWORD=sua_app_password
```
**Como obter:**
1. https://mail.yahoo.com > Account Info > Account Security
2. Gere App Password (se tiver 2FA)

### 4. ProtonMail
```env
PROTONMAIL_ENABLED=true
PROTONMAIL_API_TOKEN=seu_token
PROTONMAIL_USERNAME=seu@proton.me
```
**Como obter:**
1. https://mail.proton.me > Configurações > API > Crie token

## 🚀 Instalação

### Rápida
```bash
cd agente_pessoal
chmod +x setup.sh && ./setup.sh
```

### Docker
```bash
docker-compose -f docker/docker-compose.yml up -d
```

## 🖥️ Como Usar

```bash
# Interface Web
streamlit run ui/streamlit_app.py      # :8501
streamlit run ui/dashboard.py          # :8502

# API REST
python api/main.py                     # :8000

# Bots
python ui/bot_telegram.py
python ui/bot_whatsapp.py

# Terminal
python agents/coordenador.py
```

## 📝 Comandos Suportados

```
"Meu nome é João, sou designer"                    → 🧠 Salva preferências
"Agenda reunião amanhã às 14h"                     → 📅 Cria no Calendar
"Liste meus emails do Gmail"                       → 📧 Gmail
"Emails não lidos do Outlook"                        → 📧 Outlook
"Resuma emails do Yahoo"                             → 📧 Yahoo
"Envie email pelo ProtonMail"                        → 🔒 ProtonMail
"Adiciona tarefa: comprar leite"                     → 📝 Cria no Notion
"Busca previsão do tempo SP"                         → 🔍 Pesquisa web
"Analise relatorio.pdf"                              → 📄 Extrai e analisa
"Envie WhatsApp para 1199999: Olá"                   → 📱 Envia mensagem
"Envie mensagem no Telegram"                         → ✈️ Envia no Telegram
"Agende backup diário às 23h"                        → ⏰ Tarefa automática
"Transcreva audio.mp3"                               → 🎙️ Whisper
"Deleta evento da reunião"                           → 🛡️ Pede confirmação
```

## 💰 Custo Estimado

| Componente | Custo Mensal |
|-----------|-------------|
| OpenAI API | $5-20 |
| Hospedagem (VPS) | $5-10 |
| **Total** | **$10-30** |

## 📄 Licença

MIT License

---

**Desenvolvido com ❤️ usando LangGraph, FastAPI, Streamlit, SQLAlchemy, Docker e Whisper**
