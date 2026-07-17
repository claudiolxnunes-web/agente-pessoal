"""
Coordenador principal — 16 agentes orquestrados com LangGraph
Agente Pessoal v3.2 — Refatorado e sem duplicidades
"""
import os, sys, uuid, json, re, logging
from datetime import datetime
from typing import TypedDict, Annotated, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── LangChain / LangGraph ────────────────────────────────────────────────────
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# ── Ferramentas ───────────────────────────────────────────────────────────────
from tools.google_calendar_tool import criar_evento_calendar, listar_eventos_calendar
from tools.gmail_tool import listar_emails_gmail, enviar_email_gmail, enviar_analise_para_crm
from tools.outlook_tool import listar_emails_outlook, enviar_email_outlook, listar_eventos_outlook
from tools.yahoo_mail_tool import listar_emails_yahoo, enviar_email_yahoo
from tools.titan_tool import list_emails as listar_emails_titan, send_email as enviar_email_titan, TITAN_ENABLED
from tools.protonmail_tool import listar_emails_proton, enviar_email_proton
from tools.email_config import verificar_gmail, verificar_yahoo, verificar_outlook, verificar_proton
from tools.notion_tool import criar_tarefa_notion, listar_tarefas_notion
from tools.web_search_tool import buscar_web
from tools.document_tool import analisar_documento
from tools.whatsapp_tool import enviar_mensagem_whatsapp
from tools.telegram_tool import enviar_mensagem_telegram
from tools.voice_tool import transcrever_audio
from tools.scheduler_tool import agendar_diario, listar_tarefas_agendadas
from memory.vector_store import salvar_memoria, buscar_memorias
from config.settings import OPENAI_API_KEY, MODEL_NAME, TEMPERATURE, AGENT_NAME, USER_NAME
from config.settings import GMAIL_ENABLED, OUTLOOK_ENABLED, YAHOO_MAIL_ENABLED, PROTONMAIL_ENABLED

# ── Estado do grafo ───────────────────────────────────────────────────────────
class EstadoAgente(TypedDict):
    messages: Annotated[List, add_messages]
    entrada_usuario: str
    agente_selecionado: str
    resultado: str
    aguardando_confirmacao: bool
    acao_pendente: dict
    sessao_id: str
    historico_contexto: str


# ── LLM ───────────────────────────────────────────────────────────────────────
llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model=MODEL_NAME,
    temperature=TEMPERATURE,
)


# ══════════════════════════════════════════════════════════════════════════════
# UTILITÁRIO — Parser JSON seguro
# ══════════════════════════════════════════════════════════════════════════════
def _parse_json_llm(texto: str) -> dict:
    """Limpa e parseia JSON retornado pelo LLM."""
    limpo = texto.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(limpo)


# ══════════════════════════════════════════════════════════════════════════════
# AGENTE 1 — Roteador
# ══════════════════════════════════════════════════════════════════════════════
def agente_roteador(estado: EstadoAgente) -> EstadoAgente:
    """Decide qual agente especialista deve tratar a mensagem."""
    entrada = estado["entrada_usuario"]

    prompt = f"""Você é um roteador inteligente. Analise a mensagem abaixo e retorne SOMENTE o nome do agente
responsável, sem explicações.

Agentes disponíveis:
- memoria: guardar preferências, nome, profissão, dados do usuário
- calendario: criar/listar/deletar eventos no Google Calendar
- gmail: ler, enviar ou deletar e-mails do Gmail
- outlook: ler, enviar e-mails e eventos do Outlook/Microsoft 365
- yahoo: ler, enviar e-mails do Yahoo Mail
- proton: ler, enviar e-mails do ProtonMail
- titan: ler, enviar e-mails do contato@bpfconsult.com.br (Titan/GoDaddy)
- precos_manuais: salvar ou listar precos manuais de insumos (fosfato, ureia, enxofre, minerais etc). Use quando o usuario disser "atualiza preco", "salva preco", "listar precos manuais"
- resumo_agro: gerar e enviar resumo diário do agronegócio (cotações, clima, notícias). Use quando o usuario disser: "resumo agro", "cotações de hoje", "me manda o resumo", "resumo do dia", "como estao as cotacoes", "gera o resumo agro"
- todos_emails: listar emails NAO LIDOS de TODAS as caixas ao mesmo tempo (Gmail + Outlook + Yahoo + Titan juntos)
- planejar_dia: planejar o dia com base na agenda do Google Calendar e tarefas do Notion. Use quando o usuario disser "planejar meu dia", "planejamento do dia", "como esta minha agenda hoje", "o que tenho hoje"
- crm: consultar ou registrar clientes, interacoes, oportunidades, tarefas e pipeline no Agro RC CRM. Use quando o usuario disser "clientes", "pipeline", "oportunidade", "interacao", "tarefa crm", "ver clientes", "registra no crm", "cria cliente"
- email_generico: detectar provedor e enviar e-mail automaticamente
- notion: criar tarefas, notas ou listar itens no Notion
- busca: buscar informações na web, notícias, previsão do tempo
- documento: analisar PDF, DOCX, CSV, XLSX, TXT
- whatsapp: enviar mensagem pelo WhatsApp
- telegram: enviar mensagem pelo Telegram
- agendamento: agendar tarefas automáticas, backups, lembretes
- voz: transcrever arquivo de áudio
- confirmacao: ação sensível que precisa de aprovação (deletar, cancelar)
- workdev: backlog, tasks, subtasks, projetos e conhecimento da plataforma WorkDev (criar task, marcar done, listar backlog, decompor)
- conversa: conversa geral, perguntas, ajuda, cumprimentos

Mensagem do usuário: "{entrada}"
Agente:"""

    resposta = llm.invoke([HumanMessage(content=prompt)])
    agente = resposta.content.strip().lower().split()[0]

    agentes_validos = {
        "memoria", "calendario", "gmail", "outlook", "yahoo", "proton", "titan", "todos_emails", "planejar_dia", "crm",
        "email_generico", "notion", "busca", "documento", "whatsapp",
        "telegram", "agendamento", "voz", "confirmacao", "conversa",
        "workdev"
    }
    if agente not in agentes_validos:
        agente = "conversa"

    logger.info(f"🔀 Agente selecionado: {agente} | Entrada: {entrada[:50]}")
    return {**estado, "agente_selecionado": agente}


# ══════════════════════════════════════════════════════════════════════════════
# AGENTE 2 — Memória
# ══════════════════════════════════════════════════════════════════════════════
def agente_memoria(estado: EstadoAgente) -> EstadoAgente:
    """Extrai e salva informações pessoais do usuário."""
    entrada = estado["entrada_usuario"]
    memoria_relevante = buscar_memorias(entrada, n=3)

    resultado = salvar_memoria(
        texto=f"[{datetime.now().strftime('%d/%m/%Y')}] {USER_NAME}: {entrada}",
        metadata={"tipo": "preferencia", "usuario": USER_NAME}
    )
    return {**estado, "resultado": f"🧠 {resultado}\n\n{memoria_relevante}"}


# ══════════════════════════════════════════════════════════════════════════════
# AGENTE 3 — Calendário
# ══════════════════════════════════════════════════════════════════════════════
def agente_calendario(estado: EstadoAgente) -> EstadoAgente:
    """Gerencia eventos no Google Calendar."""
    entrada = estado["entrada_usuario"].lower()

    if any(p in entrada for p in ["listar", "lista", "mostrar", "ver", "próximos"]):
        dias = 7
        for palavra in entrada.split():
            if palavra.isdigit():
                dias = int(palavra)
                break
        resultado = listar_eventos_calendar(dias=dias)
    else:
        prompt = f"""Extraia TODOS os eventos da mensagem abaixo e retorne JSON puro: uma LISTA de eventos.
A mensagem pode conter UM ou VARIOS eventos (ex.: "dia 13 com Tiago e dia 14 com Clovis" = 2 eventos separados).
Formato (sempre lista, mesmo com 1 evento):
[{{"titulo": "...", "data_hora": "DD/MM/AAAA HH:MM", "duracao_horas": N, "descricao": "...", "local": "..."}}]
Regras:
- Sem horario explicito: manha=08:00, tarde=14:00, noite=19:00; sem indicacao, 09:00.
- Eventos de mais de um dia (ex.: "dia 16 e 17") viram um evento por dia.
- Use o MES ATUAL como padrao. Exemplo: se hoje e 06/07 e a mensagem diz "dia 13", o evento e 13/07 (o dia 13 ainda vai chegar neste mes).
- So use o mes seguinte se o dia mencionado JA PASSOU (ex.: hoje 06/07 e mensagem diz "dia 2" -> 02/08).
Mensagem: "{estado['entrada_usuario']}"
Data atual: {datetime.now().strftime('%d/%m/%Y')}
JSON:"""
        resp = llm.invoke([HumanMessage(content=prompt)])
        try:
            dados = _parse_json_llm(resp.content)
            if isinstance(dados, dict):
                dados = [dados]
            criados = []
            from datetime import datetime as _dt
            _hoje = _dt.now()
            for ev in dados:
                # Corrige mes: se o modelo jogou pro mes seguinte mas o dia ainda nao passou, volta pro mes atual
                try:
                    _d = _dt.strptime(ev.get("data_hora", ""), "%d/%m/%Y %H:%M")
                    if _d.day >= _hoje.day and (_d.month - _hoje.month == 1 or (_d.month == 1 and _hoje.month == 12)) and _d.year >= _hoje.year:
                        _d = _d.replace(month=_hoje.month, year=_hoje.year)
                        ev["data_hora"] = _d.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    pass
                r = criar_evento_calendar(
                    titulo=ev.get("titulo", "Evento"),
                    data_hora=ev.get("data_hora", ""),
                    duracao_horas=ev.get("duracao_horas", 1),
                    descricao=ev.get("descricao", ""),
                    local=ev.get("local", ""),
                )
                criados.append(f"- {ev.get('titulo','Evento')} ({ev.get('data_hora','')}): {r}")
            resultado = "\n".join(criados) if criados else "Nenhum evento identificado."
        except Exception:
            resultado = "Nao entendi os dados do evento. Tente: 'Agenda reuniao amanha as 14h'"

    return {**estado, "resultado": resultado}


# ══════════════════════════════════════════════════════════════════════════════
# UTILITÁRIO — Processador genérico de e-mail
# ══════════════════════════════════════════════════════════════════════════════
def _processar_email(entrada: str, listar_fn, enviar_fn, provedor: str) -> str:
    """Lógica genérica para agentes de e-mail."""
    entrada_lower = entrada.lower()

    if any(p in entrada_lower for p in ["listar", "lista", "ver", "ler", "mostrar", "não lidos", "inbox"]):
        nao_lidos = "não lido" in entrada_lower or "unread" in entrada_lower
        return listar_fn(max_results=10, apenas_nao_lidos=nao_lidos)

    if any(p in entrada_lower for p in ["enviar", "envie", "manda", "mandar", "send"]):
        prompt = f"""Extraia os dados do e-mail e retorne JSON puro:
{{"destinatario": "email@exemplo.com", "assunto": "...", "corpo": "..."}}

Mensagem: "{entrada}"
JSON:"""
        resp = llm.invoke([HumanMessage(content=prompt)])
        try:
            dados = _parse_json_llm(resp.content)
            return enviar_fn(
                destinatario=dados.get("destinatario", ""),
                assunto=dados.get("assunto", "Sem assunto"),
                corpo=dados.get("corpo", ""),
            )
        except Exception:
            return f"❌ Não entendi os dados do e-mail. Tente: 'Envie e-mail para x@y.com: assunto Z, corpo W'"

    return listar_fn(max_results=5)


def _formatar_emails_titan(r) -> str:
    """Formata lista de e-mails do Titan para exibição."""
    if isinstance(r, list):
        if not r:
            return "📭 Nenhum e-mail encontrado."
        linhas = ["📧 E-mails do Titan/BPF:"]
        for m in r:
            linhas.append(f"✉️ {m.get('de','?')} | {m.get('assunto','?')} | {m.get('data','?')}")
        return "\n".join(linhas)
    return str(r)


# ══════════════════════════════════════════════════════════════════════════════
# AGENTES 4-9 — E-mails
# ══════════════════════════════════════════════════════════════════════════════
def agente_gmail(estado: EstadoAgente) -> EstadoAgente:
    """Gerencia e-mails do Gmail com filtro de resumo agro e envio ao CRM."""
    aviso = verificar_gmail()
    if aviso:
        return {**estado, "resultado": aviso}

    entrada = estado["entrada_usuario"]
    entrada_lower = entrada.lower()
    r = _processar_email(entrada, listar_emails_gmail, enviar_email_gmail, "Gmail")

    # Filtro especial: resumo agro
    if "resumo agro" in entrada_lower:
        palavras_agro = [
            "soja", "milho", "boi", "boi gordo", "arroba", "pecuária", "agro",
            "safra", "clima", "mapa", "nutrição animal", "confinamento", "pastagem",
            "leite", "produção de leite", "gado leiteiro", "vaca leiteira",
            "bovinocultura de leite", "preço do leite", "captação de leite",
            "qualidade do leite", "mastite", "silagem", "dieta de vacas",
            "nutrição de vacas leiteiras"
        ]
        linhas_agro = [
            linha for linha in str(r).splitlines()
            if any(p in linha.lower() for p in palavras_agro)
        ]
        if linhas_agro:
            return {**estado, "resultado": "📊 Resumo Agro IA\n\n" + "\n".join(linhas_agro[:10])}
        return {**estado, "resultado": "📭 Nenhum alerta agro encontrado."}

    # Envio de análise ao CRM (silencioso, não bloqueia resposta)
    try:
        enviar_analise_para_crm(
            subject="Email processado pelo agente",
            sender="gmail-agent@local",
            email_summary=str(r)[:1000],
            category="geral",
            priority="normal",
            suggested_action="revisar"
        )
    except Exception as e:
        logger.warning(f"Erro ao enviar análise ao CRM: {e}")

    return {**estado, "resultado": r}


def agente_outlook(estado: EstadoAgente) -> EstadoAgente:
    """Gerencia e-mails e eventos do Outlook/Microsoft 365."""
    aviso = verificar_outlook()
    if aviso:
        return {**estado, "resultado": aviso}

    entrada_lower = estado["entrada_usuario"].lower()

    if any(p in entrada_lower for p in ["evento", "reunião", "calendário"]):
        r = listar_eventos_outlook()
    else:
        r = _processar_email(
            estado["entrada_usuario"],
            listar_emails_outlook,
            enviar_email_outlook,
            "Outlook"
        )
    return {**estado, "resultado": r}


def agente_yahoo(estado: EstadoAgente) -> EstadoAgente:
    """Gerencia e-mails do Yahoo Mail."""
    aviso = verificar_yahoo()
    if aviso:
        return {**estado, "resultado": aviso}

    r = _processar_email(
        estado["entrada_usuario"],
        listar_emails_yahoo,
        enviar_email_yahoo,
        "Yahoo"
    )
    return {**estado, "resultado": r}


def agente_proton(estado: EstadoAgente) -> EstadoAgente:
    """Gerencia e-mails do ProtonMail."""
    aviso = verificar_proton()
    if aviso:
        return {**estado, "resultado": aviso}

    r = _processar_email(
        estado["entrada_usuario"],
        listar_emails_proton,
        enviar_email_proton,
        "ProtonMail"
    )
    return {**estado, "resultado": r}


def agente_titan(estado: EstadoAgente) -> EstadoAgente:
    """Gerencia e-mails do Titan/GoDaddy (contato@bpfconsult.com.br)."""
    r = _processar_email(
        estado["entrada_usuario"],
        listar_emails_titan,
        enviar_email_titan,
        "Titan/BPF"
    )
    return {**estado, "resultado": _formatar_emails_titan(r)}


def agente_email_generico(estado: EstadoAgente) -> EstadoAgente:
    """Detecta o provedor de e-mail ativo e encaminha automaticamente."""
    if GMAIL_ENABLED:
        return agente_gmail(estado)
    elif OUTLOOK_ENABLED:
        return agente_outlook(estado)
    elif YAHOO_MAIL_ENABLED:
        return agente_yahoo(estado)
    elif PROTONMAIL_ENABLED:
        return agente_proton(estado)
    elif TITAN_ENABLED:
        return agente_titan(estado)
    else:
        return {**estado, "resultado": "⚠️ Nenhum provedor de e-mail habilitado. Configure no .env"}


# ══════════════════════════════════════════════════════════════════════════════
# AGENTE 10 — Notion
# ══════════════════════════════════════════════════════════════════════════════
def agente_notion(estado: EstadoAgente) -> EstadoAgente:
    """Cria e lista tarefas no Notion."""
    entrada = estado["entrada_usuario"]
    entrada_lower = entrada.lower()

    if any(p in entrada_lower for p in ["listar", "lista", "mostrar", "ver tarefas"]):
        resultado = listar_tarefas_notion()
    else:
        prompt = f"""Extraia dados da tarefa e retorne JSON puro:
{{"titulo": "...", "descricao": "...", "prioridade": "Alta|Média|Baixa"}}

Mensagem: "{entrada}"
JSON:"""
        resp = llm.invoke([HumanMessage(content=prompt)])
        try:
            dados = _parse_json_llm(resp.content)
            resultado = criar_tarefa_notion(
                titulo=dados.get("titulo", entrada[:50]),
                descricao=dados.get("descricao", ""),
                prioridade=dados.get("prioridade", "Média"),
            )
        except Exception:
            resultado = criar_tarefa_notion(titulo=entrada[:100])

    return {**estado, "resultado": resultado}


# ══════════════════════════════════════════════════════════════════════════════
# AGENTE 11 — Busca Web
# ══════════════════════════════════════════════════════════════════════════════
def agente_busca(estado: EstadoAgente) -> EstadoAgente:
    """Busca informações na web."""
    entrada = estado["entrada_usuario"]
    for prefixo in ["busca ", "pesquisa ", "procura ", "search ", "buscar "]:
        if entrada.lower().startswith(prefixo):
            entrada = entrada[len(prefixo):]
            break
    resultado = buscar_web(entrada.strip(), max_results=5)
    return {**estado, "resultado": resultado}


# ══════════════════════════════════════════════════════════════════════════════
# AGENTE 12 — Documento
# ══════════════════════════════════════════════════════════════════════════════
def agente_documento(estado: EstadoAgente) -> EstadoAgente:
    """Analisa documentos PDF, DOCX, CSV, XLSX, TXT."""
    entrada = estado["entrada_usuario"]
    match = re.search(r'[\w/\\.]+\.(pdf|docx|csv|xlsx|txt)', entrada, re.IGNORECASE)
    if match:
        caminho = match.group(0)
        pergunta = entrada.replace(caminho, "").strip()
        resultado = analisar_documento(caminho, pergunta)
    else:
        resultado = "❌ Não encontrei um arquivo na sua mensagem. Exemplo: 'Analise relatorio.pdf'"
    return {**estado, "resultado": resultado}


# ══════════════════════════════════════════════════════════════════════════════
# AGENTE 13 — WhatsApp
# ══════════════════════════════════════════════════════════════════════════════
def agente_whatsapp(estado: EstadoAgente) -> EstadoAgente:
    """Envia mensagens pelo WhatsApp Cloud API."""
    entrada = estado["entrada_usuario"]
    match_num = re.search(r'(\+?[\d\s\(\)\-]{10,})', entrada)
    numero_regex = re.sub(r'\D', '', match_num.group(1)) if match_num else ""

    prompt = f"""Extraia número e mensagem do WhatsApp. Retorne JSON:
{{"numero": "5511999999999", "mensagem": "..."}}

Entrada: "{entrada}"
JSON:"""
    resp = llm.invoke([HumanMessage(content=prompt)])
    try:
        dados = _parse_json_llm(resp.content)
        resultado = enviar_mensagem_whatsapp(
            numero=dados.get("numero", numero_regex),
            mensagem=dados.get("mensagem", "Olá!"),
        )
    except Exception:
        resultado = "❌ Não entendi. Tente: 'Envie WhatsApp para 11999999999: Olá'"
    return {**estado, "resultado": resultado}


# ══════════════════════════════════════════════════════════════════════════════
# AGENTE 14 — Telegram
# ══════════════════════════════════════════════════════════════════════════════
def agente_telegram(estado: EstadoAgente) -> EstadoAgente:
    """Envia mensagens pelo Telegram."""
    entrada = estado["entrada_usuario"]
    prompt = f"""Extraia chat_id e mensagem do Telegram. Retorne JSON:
{{"chat_id": "123456789", "mensagem": "..."}}

Entrada: "{entrada}"
JSON:"""
    resp = llm.invoke([HumanMessage(content=prompt)])
    try:
        dados = _parse_json_llm(resp.content)
        resultado = enviar_mensagem_telegram(
            chat_id=dados.get("chat_id", ""),
            mensagem=dados.get("mensagem", "Olá!"),
        )
    except Exception:
        resultado = "❌ Não entendi. Tente: 'Envie Telegram para chat 123456: Olá'"
    return {**estado, "resultado": resultado}


# ══════════════════════════════════════════════════════════════════════════════
# AGENTE 15 — Agendamento
# ══════════════════════════════════════════════════════════════════════════════
def agente_agendamento(estado: EstadoAgente) -> EstadoAgente:
    """Agenda tarefas automáticas e recorrentes."""
    entrada = estado["entrada_usuario"].lower()

    if any(p in entrada for p in ["listar", "lista", "ver agendadas", "quais"]):
        resultado = listar_tarefas_agendadas()
    else:
        hora_match = re.search(r'(\d{1,2})h(?:(\d{2}))?', entrada)
        hora = int(hora_match.group(1)) if hora_match else 9
        minuto = int(hora_match.group(2)) if hora_match and hora_match.group(2) else 0
        nome = "tarefa_agendada"
        for palavra in ["backup", "relatório", "lembrete", "resumo"]:
            if palavra in entrada:
                nome = palavra
                break
        resultado = agendar_diario(lambda: logger.info(f"⏰ Executando {nome}"), hora, minuto, nome)

    return {**estado, "resultado": resultado}


# ══════════════════════════════════════════════════════════════════════════════
# AGENTE 16 — Voz
# ══════════════════════════════════════════════════════════════════════════════
def agente_voz(estado: EstadoAgente) -> EstadoAgente:
    """Transcreve arquivos de áudio."""
    match = re.search(r'[\w/\\.]+\.(mp3|mp4|wav|m4a|ogg|webm)', estado["entrada_usuario"], re.IGNORECASE)
    if match:
        resultado = transcrever_audio(match.group(0))
    else:
        resultado = "❌ Não encontrei arquivo de áudio. Exemplo: 'Transcreva audio.mp3'"
    return {**estado, "resultado": resultado}


# ══════════════════════════════════════════════════════════════════════════════
# AGENTE 17 — Confirmação (Human-in-the-Loop)
# ══════════════════════════════════════════════════════════════════════════════
def agente_confirmacao(estado: EstadoAgente) -> EstadoAgente:
    """Solicita confirmação antes de ações destrutivas."""
    entrada = estado["entrada_usuario"]
    resultado = (
        f"⚠️ **Ação que requer confirmação:**\n"
        f"→ {entrada}\n\n"
        f"❓ Confirma esta ação? Responda **SIM** para prosseguir ou **NÃO** para cancelar."
    )
    return {**estado, "resultado": resultado, "aguardando_confirmacao": True,
            "acao_pendente": {"acao": entrada}}


# ══════════════════════════════════════════════════════════════════════════════
# AGENTE CONVERSA — Fallback geral
# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# AGENTE CONSOLIDADO — Todos os emails
# ══════════════════════════════════════════════════════════════════════════════
def agente_todos_emails(estado: EstadoAgente) -> EstadoAgente:
    """Lista emails nao lidos de todos os provedores de uma vez."""
    entrada = estado["entrada_usuario"]
    secoes = []

    provedores = [
        ("Gmail",   verificar_gmail,   listar_emails_gmail),
        ("Outlook", verificar_outlook, listar_emails_outlook),
        ("Yahoo",   verificar_yahoo,   listar_emails_yahoo),
    ]

    if TITAN_ENABLED:
        provedores.append(("Titan/BPF", None, listar_emails_titan))

    for nome, verificar_fn, listar_fn in provedores:
        try:
            if verificar_fn:
                aviso = verificar_fn()
                if aviso:
                    secoes.append("Indisponivel: " + nome)
                    continue
            resultado = _processar_email(entrada, listar_fn, None, nome)
            secoes.append("--- " + nome + " ---\n" + str(resultado))
        except Exception as e:
            secoes.append("Erro " + nome + ": " + str(e))

    consolidado = "\n\n".join(secoes) if secoes else "Nenhum email encontrado."
    return {**estado, "resultado": consolidado}


# ══════════════════════════════════════════════════════════════════════════════
# AGENTE RESUMO AGRO — Dispara resumo diário manualmente
# ══════════════════════════════════════════════════════════════════════════════
def agente_resumo_agro(estado: EstadoAgente) -> EstadoAgente:
    """Gera e envia o resumo agro diário sob demanda."""
    try:
        import subprocess
        import sys
        resultado = subprocess.run(
            [sys.executable, "/home/workdev/agente_pessoal/scripts/resumo_agro.py"],
            capture_output=True, text=True, timeout=120
        )
        if resultado.returncode == 0:
            return {**estado, "resultado": "✅ Resumo agro gerado e enviado para o Telegram!"}
        else:
            return {**estado, "resultado": f"❌ Erro ao gerar resumo: {resultado.stderr[-300:]}"}
    except Exception as e:
        return {**estado, "resultado": f"❌ Erro: {e}"}


# ══════════════════════════════════════════════════════════════════════════════
# AGENTE PREÇOS MANUAIS — Atualiza preços de insumos via Telegram
# ══════════════════════════════════════════════════════════════════════════════
def agente_precos_manuais(estado: EstadoAgente) -> EstadoAgente:
    """Salva ou lista precos manuais de insumos."""
    from tools.precos_manuais_store import salvar_preco, listar_precos
    entrada = estado["entrada_usuario"]
    entrada_lower = entrada.lower()

    if any(p in entrada_lower for p in ["listar", "lista", "ver", "mostrar", "quais precos"]):
        resultado = listar_precos()
    else:
        prompt = f"""Extraia o ingrediente e o valor de preco da mensagem abaixo.
Retorne JSON puro sem markdown: {{"ingrediente": "nome do produto", "valor": "R$X.XXX/unidade"}}
Se nao conseguir extrair, retorne: {{"erro": "nao entendi"}}
Mensagem: "{entrada}"
JSON:"""
        resp = llm.invoke([HumanMessage(content=prompt)])
        try:
            dados = _parse_json_llm(resp.content)
            if "erro" in dados:
                resultado = "Nao entendi. Tente: atualiza preco fosfato bicalcico R$9.000/ton"
            else:
                resultado = salvar_preco(dados["ingrediente"], dados["valor"])
        except Exception:
            resultado = "Nao entendi. Tente: atualiza preco fosfato bicalcico R$9.000/ton"

    return {**estado, "resultado": resultado}


def agente_crm(estado: EstadoAgente) -> EstadoAgente:
    """Agente do Agro RC CRM — consultas e registros."""
    import json, re as _re
    from tools.agro_rc_crm import (
        listar_clientes, criar_cliente,
        listar_interacoes, registrar_interacao,
        ver_pipeline, criar_oportunidade,
        listar_tarefas_crm, criar_tarefa
    )
    entrada = estado["entrada_usuario"]
    prompt = f"""Voce e um assistente do CRM Agro RC. Analise a mensagem e retorne JSON puro.
Acoes disponiveis e seus parametros EXATOS (nao invente outros):
- listar_clientes: params aceitos: search (str, opcional), limit (int, max 20)
- ver_pipeline: sem params
- listar_interacoes: params aceitos: limit (int, max 20)
- listar_tarefas: params aceitos: status (str, opcional), limit (int, max 20)
- criar_cliente: params aceitos: razao_social (str), cnpj (str), email (str), cidade (str), estado (str)
- registrar_interacao: params aceitos: notes (str), client_name (str), type (str: cotacao|visita|ligacao|email)
- criar_oportunidade: params aceitos: titulo (str), valor (float), etapa (str)
- criar_tarefa: params aceitos: titulo (str), prazo (str), priority (str)
Retorne APENAS JSON: {{"acao": "nome_da_acao", "params": {{}}}}
Mensagem: "{entrada}"
JSON:"""
    resp = llm.invoke([HumanMessage(content=prompt)])
    try:
        texto = _re.sub(r"```json|```", "", resp.content).strip()
        dados = json.loads(texto)
        acao = dados.get("acao", "")
        params = dados.get("params", {})
        if acao == "listar_clientes":
            params.setdefault("limit", 10)
            resultado = listar_clientes(**params)
        elif acao == "ver_pipeline":
            resultado = ver_pipeline()
        elif acao == "listar_interacoes":
            resultado = listar_interacoes(**params)
        elif acao == "listar_tarefas":
            resultado = listar_tarefas_crm(**params)
        elif acao == "criar_cliente":
            resultado = criar_cliente(**params)
        elif acao == "registrar_interacao":
            resultado = registrar_interacao(**params)
        elif acao == "criar_oportunidade":
            resultado = criar_oportunidade(**params)
        elif acao == "criar_tarefa":
            resultado = criar_tarefa(**params)
        else:
            resultado = listar_clientes()
    except Exception as ex:
        resultado = f"Erro no CRM: {ex}"
    return {**estado, "resultado": resultado}

def agente_workdev(estado: EstadoAgente) -> EstadoAgente:
    """Agente WorkDev — repassa comando ao Fable via /api/ai/voz."""
    from tools.workdev_tool import executar_comando_workdev
    resultado = executar_comando_workdev(estado["entrada_usuario"])
    return {**estado, "resultado": f"🛠️ WorkDev: {resultado}"}


def agente_conversa(estado: EstadoAgente) -> EstadoAgente:
    """Agente de conversa geral com contexto de memória."""
    memorias = buscar_memorias(estado["entrada_usuario"], n=3)
    system = f"""Você é {AGENT_NAME}, assistente pessoal inteligente de {USER_NAME}.
Seja prestativo, conciso e amigável. Responda em português.

Contexto de memórias relevantes:
{memorias}

Capacidades: Google Calendar, Gmail, Outlook, Yahoo Mail, ProtonMail, Titan/BPF,
Notion, WhatsApp, Telegram, busca web, análise de documentos, agendamento e transcrição de áudio."""

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=estado["entrada_usuario"]),
    ]
    resposta = llm.invoke(messages)
    return {**estado, "resultado": resposta.content}


# ══════════════════════════════════════════════════════════════════════════════
# CONSTRUÇÃO DO GRAFO
# ══════════════════════════════════════════════════════════════════════════════
def construir_grafo():
    grafo = StateGraph(EstadoAgente)

    nos = [
        "roteador", "memoria", "calendario", "gmail", "outlook", "yahoo", "proton", "titan", "todos_emails", "planejar_dia", "crm",
        "email_generico", "notion", "busca", "documento",
        "whatsapp", "telegram", "agendamento", "voz", "confirmacao", "conversa",
        "workdev"
    ]

    funcoes = {
        "roteador":      agente_roteador,
        "memoria":       agente_memoria,
        "calendario":    agente_calendario,
        "gmail":         agente_gmail,
        "outlook":       agente_outlook,
        "yahoo":         agente_yahoo,
        "proton":        agente_proton,
        "titan":         agente_titan,
        "todos_emails":  agente_todos_emails,
        "resumo_agro":   agente_resumo_agro,
        "planejar_dia":  lambda estado: _planejar_com_memoria(estado),
        "crm":           agente_crm,
        "precos_manuais": agente_precos_manuais,
        "email_generico":agente_email_generico,
        "notion":        agente_notion,
        "busca":         agente_busca,
        "documento":     agente_documento,
        "whatsapp":      agente_whatsapp,
        "telegram":      agente_telegram,
        "agendamento":   agente_agendamento,
        "voz":           agente_voz,
        "confirmacao":   agente_confirmacao,
        "conversa":      agente_conversa,
        "workdev":       agente_workdev,
    }

    for nome in nos:
        grafo.add_node(nome, funcoes[nome])

    grafo.set_entry_point("roteador")

    grafo.add_conditional_edges(
        "roteador",
        lambda estado: estado["agente_selecionado"],
        {nome: nome for nome in nos if nome != "roteador"}
    )

    for nome in nos:
        if nome != "roteador":
            grafo.add_edge(nome, END)

    return grafo.compile()


# ── Instância global ──────────────────────────────────────────────────────────
_app = None

def get_app():
    global _app
    if _app is None:
        _app = construir_grafo()
    return _app


def processar_mensagem(mensagem: str, sessao_id: str = "") -> str:

    msg_lower = mensagem.lower()
    if any(p in msg_lower for p in ["atualiza preco", "atualiza preço", "salva preco",
                                     "salva preço", "listar precos manuais",
                                     "listar preços manuais", "ver precos manuais",
                                     "quais precos manuais"]):
        return agente_precos_manuais(EstadoAgente(
            messages=[], entrada_usuario=mensagem, agente_selecionado="precos_manuais",
            resultado="", aguardando_confirmacao=False, acao_pendente={},
            sessao_id=sessao_id, historico_contexto=""
        ))["resultado"]
    if any(p in msg_lower for p in ["resumo agro", "cotações de hoje", "cotacoes de hoje",
                                     "me manda o resumo", "resumo do dia agro",
                                     "gera o resumo agro", "resumo agropecuario"]):
        return agente_resumo_agro(EstadoAgente(
            messages=[], entrada_usuario=mensagem, agente_selecionado="resumo_agro",
            resultado="", aguardando_confirmacao=False, acao_pendente={},
            sessao_id=sessao_id, historico_contexto=""
        ))["resultado"]

    """Processa uma mensagem e retorna a resposta do agente."""
    if not sessao_id:
        sessao_id = str(uuid.uuid4())[:8]

    estado_inicial = EstadoAgente(
        messages=[HumanMessage(content=mensagem)],
        entrada_usuario=mensagem,
        agente_selecionado="",
        resultado="",
        aguardando_confirmacao=False,
        acao_pendente={},
        sessao_id=sessao_id,
        historico_contexto="",
    )

    app = get_app()
    estado_final = app.invoke(estado_inicial)
    return estado_final.get("resultado", "❌ Não foi possível processar sua mensagem.")


def conversar(mensagem: str, thread_id: str = "") -> str:
    return processar_mensagem(mensagem, sessao_id=thread_id)


# ── Interface de Terminal ──────────────────────────────────────────────────────
if __name__ == "__main__":
    from database.models import init_db
    init_db()

    print(f"\n{'='*55}")
    print(f"  🤖 {AGENT_NAME} — Agente Pessoal v3.2")
    print(f"  Olá, {USER_NAME}! Como posso ajudar?")
    print(f"  Digite 'sair' para encerrar.")
    print(f"{'='*55}\n")

    sessao = str(uuid.uuid4())[:8]
    while True:
        try:
            entrada = input(f"[{USER_NAME}]: ").strip()
            if not entrada:
                continue
            if entrada.lower() in ("sair", "exit", "quit"):
                print(f"\n👋 Até logo, {USER_NAME}!")
                break

            print(f"\n[{AGENT_NAME}]: ", end="", flush=True)
            resposta = processar_mensagem(entrada, sessao)
            print(resposta)
            print()

        except KeyboardInterrupt:
            print(f"\n\n👋 Até logo, {USER_NAME}!")
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}\n")
def _planejar_com_memoria(estado: EstadoAgente) -> EstadoAgente:
    """Se a mensagem do usuario contiver um planejamento ditado (texto substancial), salva na memoria antes de planejar."""
    entrada = estado.get("entrada_usuario", "")
    # Mensagem substancial = mais de 80 caracteres (nao e so "planeja meu dia")
    if len(entrada.strip()) > 80:
        try:
            salvar_memoria(
                texto=f"[{datetime.now().strftime('%d/%m/%Y')}] {USER_NAME} (planejamento ditado): {entrada}",
                metadata={"tipo": "planejamento", "usuario": USER_NAME}
            )
        except Exception:
            pass
    return {**estado, "resultado": planejar_dia()}

def planejar_dia():
    try:
        tarefas = listar_tarefas_notion()
    except Exception as e:
        tarefas = f"Erro ao buscar tarefas: {e}"

    try:
        eventos = listar_eventos_calendar()
    except Exception as e:
        eventos = f"Erro ao buscar agenda: {e}"

    from datetime import datetime
    dias_semana = ["segunda-feira", "terca-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sabado", "domingo"]
    agora = datetime.now()
    hoje_str = f"{dias_semana[agora.weekday()]}, {agora.strftime('%d/%m/%Y')}"
    # Anotacoes recentes (planejamento semanal ditado, etc.)
    anotacoes = ""
    try:
        import json as _json
        from datetime import datetime as _dt, timedelta as _td
        _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _fb = _json.load(open(os.path.join(_base, "memory/chroma_db/memoria_fallback.json")))
        _mem = _fb.get("conversas", [])
        _corte = _dt.now() - _td(days=14)
        _recentes = [m["texto"].split("\nAgente:")[0].replace("Usuário: ", "") for m in _mem if _dt.fromisoformat(m.get("timestamp", "2000-01-01T00:00:00")) >= _corte]
        anotacoes = "\n".join(_recentes[-10:]) if _recentes else "Nenhuma."
    except Exception:
        anotacoes = "Nenhuma."
    prompt = f"""
Voce e o assistente executivo de um consultor de nutricao animal que trabalha em campo (visitas a clientes, viagens entre cidades de GO e MG) e em home office.
HOJE E {hoje_str}. Planeje APENAS o dia de hoje ({agora.strftime('%d/%m/%Y')}).

DADOS REAIS (unica fonte permitida):
AGENDA DO CALENDAR:
{eventos}
TAREFAS DO NOTION:
{tarefas}
ANOTACOES RECENTES DO USUARIO (podem conter o planejamento semanal ditado por ele):
{anotacoes}

REGRAS OBRIGATORIAS:
1. NUNCA invente atividades que nao estejam nos dados acima (proibido: "pausa para cafe", "revisao de e-mails", "tempo livre", "follow-ups" genericos).
2. NUNCA invente horarios: so use horario se o evento da agenda tiver horario real. Tarefas sem horario vao para uma lista "Prioridades de hoje" sem hora marcada.
3. Se as anotacoes recentes mencionarem compromissos para HOJE, inclua-os (indicando que vieram do planejamento ditado).
4. Se houver evento em outra cidade, lembre do tempo de deslocamento antes e depois.
5. Tarefas/compromissos com datas que JA PASSARAM viram secao "Pendencias atrasadas" no final.
6. Dia sem eventos na agenda = NAO monte grade horaria; entregue apenas: Prioridades de hoje (max 5, em ordem de importancia) + Pendencias.
7. Titulo sempre com a data de hoje ({agora.strftime('%d/%m/%Y')}) e o dia da semana.
8. Seja enxuto: sem observacoes genericas, sem dicas obvias, sem frases de encerramento.
"""

    resposta = llm.invoke([HumanMessage(content=prompt)])
    return resposta.content
