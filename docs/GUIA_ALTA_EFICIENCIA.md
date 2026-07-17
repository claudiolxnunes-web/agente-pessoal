# 🚀 Guia de Alta Eficiência - Agente Pessoal v3.0

> Como extrair 90% do potencial do seu agente em 20% do tempo.

---

## 📋 Índice

1. [Primeiros 5 Minutos](#primeiros-5-minutos)
2. [Fluxos de Trabalho Diários](#fluxos-diarios)
3. [Automações Semanais](#automacoes-semanais)
4. [Integrações Avançadas](#integracoes-avancadas)
5. [Atalhos e Comandos Rápidos](#atalhos-rapidos)
6. [Configuração Profissional](#config-pro)
7. [Troubleshooting Express](#troubleshooting)

---

## 🎯 Primeiros 5 Minutos {#primeiros-5-minutos}

### 1. Configure o básico (2 min)
```bash
cp .env.example .env
```

Edite `.env`:
```env
OPENAI_API_KEY=sk-sua-chave
AGENT_NAME=Jarvis          # Dê um nome memorável
USER_NAME=SeuNome          # Para referências pessoais
MODEL_NAME=gpt-4o-mini     # Rápido e barato
TEMPERATURE=0.2            # Respostas focadas
```

### 2. Inicialize tudo (1 min)
```bash
python -c "from database.models import init_db; init_db()"
```

### 3. Teste rápido (2 min)
```bash
python agents/coordenador.py
# Digite: "Meu nome é [SeuNome], sou [Profissão]"
# Depois: "Quais minhas preferências?"
```

✅ **Pronto!** Agora o agente sabe quem você é.

---

## ⚡ Fluxos de Trabalho Diários {#fluxos-diarios}

### Manhã (5 min) - Ritual de Início
```
"Bom dia! O que tenho hoje?"
→ 📅 Lista eventos + 📝 Tarefas pendentes

"Resuma meus emails não lidos"
→ 📧 Lista + resumo dos 5 mais importantes

"Agende 3 blocos de foco de 90 minutos"
→ 📅 Cria eventos Deep Work
```

### Tarde (3 min) - Checkpoint
```
"Quanto tempo até minha próxima reunião?"
→ 📅 Calcula e sugere o que fazer antes

"Adicione tarefa: [o que surgiu]"
→ 📝 Cria no Notion/local

"Busca novidades sobre [tópico do projeto]"
→ 🔍 Atualiza você em 30 segundos
```

### Noite (5 min) - Fechamento
```
"Resuma meu dia"
→ 📊 Conversas + tarefas feitas + eventos

"O que não consegui fazer hoje?"
→ 📝 Lista tarefas pendentes

"Agende prioridades para amanhã"
→ 📅 Cria eventos manhã seguinte
```

---

## 🔄 Automações Semanais {#automacoes-semanais}

### Domingo - Planejamento (10 min)
```
"Analise minha semana que vem"
→ 📅 Mostra calendar + gaps

"Quais meus 3 objetivos principais?"
→ 💬 Ajuda a definir (salva como preferência)

"Agende:
- Review semanal toda sexta 16h
- Planejamento domingo 19h  
- Backup automático todo sábado 23h"
→ ⏰ Cria 3 tarefas automáticas
```

### Sexta - Review (10 min)
```
"Gere relatório da semana"
→ 📊 Analytics: conversas, tarefas, eventos

"O que aprendi essa semana?"
→ 🧠 Busca nas memórias

"Quais padrões de produtividade?"
→ 📊 Dashboard mostra horários de pico
```

---

## 🔗 Integrações Avançadas {#integracoes-avancadas}

### Google Suite (Calendar + Gmail)

**Setup (único, 5 min):**
1. https://console.cloud.google.com/
2. Novo projeto → APIs & Services → Library
3. Ative: Google Calendar API + Gmail API
4. Credentials → Create → OAuth 2.0 (Desktop)
5. Download JSON → salve como `config/credentials.json`
6. `.env`: `GOOGLE_CALENDAR_ENABLED=true` + `GMAIL_ENABLED=true`

**Uso diário:**
```
"Crie evento 'Reunião X' amanhã 14h-15h"
"Liste emails de [pessoa] essa semana"
"Marque como lido emails com assunto 'Newsletter'"
"Envie email para [email]: assunto [x], corpo [y]"
```

### Notion (Tarefas + Notas)

**Setup (único, 3 min):**
1. https://www.notion.so/my-integrations
2. New integration → Internal → copie token
3. No Notion: crie database com campos: Name, Status, Prioridade
4. Share → Add connection → sua integração
5. Copie database ID da URL
6. `.env`: `NOTION_ENABLED=true` + preencha token e ID

**Uso:**
```
"Adicione tarefa: [título] | prioridade alta | vence sexta"
"Liste tarefas pendentes"
"Mova tarefa [x] para concluída"
```

### WhatsApp (Notificações)

**Setup (único, 10 min):**
1. https://developers.facebook.com/
2. Create App → Business → WhatsApp
3. Get Started → copie Phone Number ID e Access Token
4. `.env`: preencha 3 variáveis WhatsApp
5. Para webhook: deploy `ui/bot_whatsapp.py` em servidor com HTTPS

**Uso:**
```
"Envie WhatsApp para [número]: Reunião confirmada"
"Me notifique quando for 14h"
→ ⏰ Agendamento + WhatsApp
```

### Telegram (Bot Pessoal)

**Setup (único, 2 min):**
1. Telegram → @BotFather
2. /newbot → nome → copie token
3. `.env`: `TELEGRAM_ENABLED=true` + token
4. `python ui/bot_telegram.py`

**Uso:**
```
Fale com seu bot no Telegram!
"O que tenho hoje?"
"Adicione tarefa urgente"
"Busca previsão do tempo"
```

---

## ⌨️ Atalhos e Comandos Rápidos {#atalhos-rapidos}

### Padrões de comando que funcionam sempre

| Você diz... | O que acontece |
|-------------|---------------|
| `"Bom dia"` | 📅 + 📝 + 📧 resumo do dia |
| `"Checkpoint"` | ⏱️ Status rápido |
| `"Foco"` | 📅 Agenda bloco de deep work |
| `"Resuma"` | 🧠 Resumo inteligente do contexto |
| `"Lembre-me de [x]"` | 🧠 + ⏰ Salva + agenda |
| `"Analise [arquivo]"` | 📄 Processa documento |
| `"Transcreva [audio]"` | 🎙️ Whisper + resumo |

### Comandos de uma palavra
```
"Tarefas"     → Lista tarefas
"Calendario"  → Próximos eventos
"Emails"      → Não lidos
"Busca [x]"   → Pesquisa web
"Preferencias"→ O que sei sobre você
"Ajuda"       → Lista comandos
```

---

## ⚙️ Configuração Profissional {#config-pro}

### .env otimizado para produtividade
```env
# Essencial
OPENAI_API_KEY=sk-xxx
MODEL_NAME=gpt-4o-mini
TEMPERATURE=0.1              # Mais focado, menos criativo

# Identidade
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
DATABASE_URL=sqlite:///memory/agente.db  # SQLite é rápido para 1 usuário
WHISPER_MODEL=base                         # tiny=mais rápido, large=mais preciso

# API
API_HOST=0.0.0.0
API_PORT=8000
```

### Docker (produção)
```bash
# Subir tudo
docker-compose -f docker/docker-compose.yml up -d

# Ver logs em tempo real
docker-compose logs -f api
docker-compose logs -f telegram

# Reiniciar serviço
docker-compose restart api
```

### Agendamentos recomendados
```
"Agende:
- 'Review emails' todo dia 8h
- 'Checkpoint tarde' todo dia 15h  
- 'Fechamento dia' todo dia 18h
- 'Backup semanal' todo domingo 20h
- 'Review semanal' toda sexta 16h"
```

---

## 🛠️ Troubleshooting Express {#troubleshooting}

| Problema | Solução em 10 segundos |
|----------|----------------------|
| `OPENAI_API_KEY` não encontrada | `echo "OPENAI_API_KEY=sk-xxx" > .env` |
| Google não autentica | Delete `config/token.json` e tente novamente |
| Notion não lista tarefas | Verifique se database foi compartilhado com integração |
| Telegram bot não responde | Verifique token no @BotFather, reinicie bot |
| WhatsApp não envia | Verifique se número tem DDI (55 para BR) |
| Whisper não carrega | `apt-get install ffmpeg` ou `brew install ffmpeg` |
| Docker porta ocupada | `docker-compose down` → mude porta no `.env` |
| Memória cheia | `Limpar Memória` no sidebar ou `memoria.limpar_memoria()` |
| Agente lento | Use `gpt-4o-mini` ao invés de `gpt-4o` |
| Erro no banco | `rm memory/agente.db` → reinicialize |

---

## 💡 Dicas Pro

### 1. Use thread IDs para contextos separados
```python
# Trabalho
conversar("...", thread_id="work")

# Pessoal
conversar("...", thread_id="pessoal")

# Projeto X
conversar("...", thread_id="projeto_x")
```

### 2. Combine ferramentas em um comando
```
"Busca previsão do tempo SP, agende umbrella se chover, 
 e envie WhatsApp para minha mãe avisando"
→ 🔍 + 📅 + 📱 (3 agentes, 1 comando)
```

### 3. Documentos como memória
```
"Analise meu-cv.pdf"
"Analise contrato.docx"
# Depois pergunte:
"Qual minha experiência em Python?"
"O contrato tem cláusula de confidencialidade?"
```

### 4. Voz para velocidade
```bash
# Grave áudio no celular, envie para API:
curl -X POST -F "file=@audio.ogg" http://seu-servidor:8000/voz/transcrever
# Retorna texto → agente processa
```

### 5. Dashboard para insights
```bash
streamlit run ui/dashboard.py
# Abra toda sexta para ver:
# - Horários de pico de produtividade
# - Agentes mais usados
# - Padrões de conversa
```

---

## 📊 Métricas de Eficiência

| Antes do Agente | Com o Agente | Economia |
|-----------------|--------------|----------|
| 15 min organizando dia | 2 min | **87%** |
| 10 min verificando emails | 1 min | **90%** |
| 20 min criando tarefas | 30 seg | **97%** |
| 5 min buscando info | 20 seg | **93%** |
| **Total: 50 min/dia** | **4 min/dia** | **92%** |

> **Economia mensal:** ~23 horas = quase 3 dias úteis!

---

## 🎓 Roadmap de Maestria

**Semana 1:** Configure básico, use terminal
**Semana 2:** Ative Google Calendar + Gmail
**Semana 3:** Adicione Notion + agendamentos
**Semana 4:** Configure WhatsApp/Telegram bots
**Semana 5:** Use API REST + integrações custom
**Semana 6:** Dashboard + analytics + otimização

**Mês 2+:** Automatize 80% das tarefas repetitivas

---

**Pronto para ser 10x mais produtivo?** 🚀

Comece com: `python agents/coordenador.py` e diga `"Bom dia!"`
