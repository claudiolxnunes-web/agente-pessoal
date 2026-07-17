# 📋 Cheat Sheet - Agente Pessoal v3.0

## 🚀 Início Rápido (30 segundos)

```bash
# 1. Configure
cp .env.example .env  # edite com sua OPENAI_API_KEY

# 2. Inicialize
python -c "from database.models import init_db; init_db()"

# 3. Execute
python agents/coordenador.py
```

## 🎯 Comandos Essenciais

### Dia a Dia
```
"Bom dia!"                    → Resumo completo do dia
"O que tenho hoje?"           → Calendário + tarefas
"Checkpoint"                  → Status rápido
"Foco"                        → Agenda bloco de deep work
"Fechamento"                  → Resumo do dia + amanhã
```

### Tarefas
```
"Adicione tarefa: [X]"        → Cria tarefa
"Liste tarefas"               → Mostra pendentes
"Complete tarefa [X]"         → Marca como feita
"Tarefas urgentes"            → Filtra por prioridade
```

### Calendário
```
"Agenda [evento] [data] [hora]" → Cria evento
"O que tenho [dia]?"            → Lista eventos
"Deleta evento [X]"             → Remove (pede confirmação)
```

### Email (Gmail)
```
"Emails não lidos"            → Lista
"Resuma emails"               → Resumo inteligente
"Envie email para [X]: [assunto], [corpo]"
"Emails de [pessoa]"          → Filtra
```

### Busca
```
"Busca [termo]"               → Pesquisa web
"Novidades sobre [X]"         → Últimas notícias
"Compare [A] vs [B]"          → Análise comparativa
```

### Documentos
```
"Analise [arquivo.pdf]"       → Extrai e resume
"Pergunte ao documento [X]: [pergunta]"
"Compare [arq1] com [arq2]"   → Análise comparativa
```

### Agendamento
```
"Agende [tarefa] todo dia [hora]"
"Agende [tarefa] toda [dia] às [hora]"
"Agende [tarefa] a cada [N] minutos"
"Liste agendamentos"          → Mostra tarefas automáticas
"Desative [id]"               → Pausa agendamento
```

### Comunicação
```
"Envie WhatsApp para [número]: [mensagem]"
"Envie Telegram para [chat_id]: [mensagem]"
"Me notifique quando for [hora]"
```

### Voz
```bash
# API REST
curl -X POST -F "file=@audio.mp3" http://localhost:8000/voz/transcrever

# Resposta: {"texto": "...", "idioma": "pt", "duracao": 3.5}
```

### Preferências
```
"Meu nome é [X]"              → Salva identidade
"Eu sou [profissão]"          → Salva contexto
"Eu prefiro [X]"              → Salva preferência
"O que você sabe sobre mim?"  → Lista preferências
```

## 🐳 Docker (Produção)

```bash
# Tudo
docker-compose -f docker/docker-compose.yml up -d

# Serviços individuais
docker-compose up -d api          # API :8000
docker-compose up -d web          # Web :8501
docker-compose up -d dashboard    # Analytics :8502
docker-compose up -d telegram     # Bot Telegram
docker-compose up -d postgres     # Banco

# Logs
docker-compose logs -f [servico]

# Parar
docker-compose down
```

## 🌐 API REST

```bash
# Conversar
curl -X POST http://localhost:8000/conversar   -H "Content-Type: application/json"   -d '{"mensagem": "Bom dia!", "thread_id": "work"}'

# Upload documento
curl -X POST http://localhost:8000/documentos/analisar   -F "file=@relatorio.pdf"

# Transcrever áudio
curl -X POST http://localhost:8000/voz/transcrever   -F "file=@audio.mp3"

# Estatísticas
curl http://localhost:8000/analytics/estatisticas
```

## ⚙️ .env Otimizado

```env
# Essencial
OPENAI_API_KEY=sk-xxx
MODEL_NAME=gpt-4o-mini
TEMPERATURE=0.1
AGENT_NAME=Jarvis
USER_NAME=SeuNome

# Tudo ativo
GOOGLE_CALENDAR_ENABLED=true
GMAIL_ENABLED=true
NOTION_ENABLED=true
WHATSAPP_ENABLED=true
TELEGRAM_ENABLED=true
AUTO_SCHEDULE_ENABLED=true
VOICE_ENABLED=true

# Performance
DATABASE_URL=sqlite:///memory/agente.db
WHISPER_MODEL=base
```

## 🛠️ Troubleshooting (10s)

| Erro | Solução |
|------|---------|
| `OPENAI_API_KEY` | `echo "OPENAI_API_KEY=sk-xxx" > .env` |
| Google falha | Delete `config/token.json` |
| Notion falha | Verifique compartilhamento do database |
| Telegram | Verifique token no @BotFather |
| WhatsApp | Verifique DDI (55 para BR) |
| Whisper | `apt-get install ffmpeg` |
| Docker | `docker-compose down` → troque porta |
| Memória | Botão "Limpar Memória" no sidebar |
| Lento | Use `gpt-4o-mini` |
| Banco | `rm memory/agente.db` → reinicie |

## 📈 Fluxo de Eficiência

```
Manhã (5min):    "Bom dia" → 📅 + 📝 + 📧
Tarde (3min):    "Checkpoint" → status
Noite (5min):    "Fechamento" → resumo + amanhã
Total: 13 min/dia (vs 50 min manual)
```

---

**Guarde este arquivo!** Imprima ou deixe aberto nos primeiros dias.
