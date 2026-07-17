#!/usr/bin/env python3
import os
import json
import logging
import requests
import feedparser
import imaplib
import email as email_lib
import urllib.request
from datetime import datetime
from dotenv import load_dotenv
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.conab_tool import buscar_cotacoes_conab
from tools.precos_manuais_store import formatar_para_resumo as precos_manuais_resumo

load_dotenv()

logging.basicConfig(level=logging.WARNING, format="%(asctime)s [resumo_agro] %(levelname)s: %(message)s")
logger = logging.getLogger("resumo_agro")
logger.setLevel(logging.INFO)

OPENWEATHER_KEY    = os.getenv("OPENWEATHER_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")
SERPAPI_KEY        = os.getenv("SERPAPI_KEY")

CIDADES_CLIMA = [
    {"nome": "Goiania (GO)",                     "query": "Goiania,BR"},
    {"nome": "Paracatu (MG - Noroeste de Minas)", "query": "Paracatu,BR"},
    {"nome": "Patrocinio (MG - Alto Paranai ba)", "query": "Patrocinio,BR"},
]

RSS_FEEDS = [
    {"nome": "Canal Rural",  "url": "https://www.canalrural.com.br/feed/"},
    {"nome": "Globo Rural",  "url": "https://g1.globo.com/dynamo/economia/agronegocios/rss2.xml"},
    {"nome": "CompreRural",  "url": "https://www.comprerural.com/feed/"},
    {"nome": "Agrolink",     "url": "https://news.google.com/rss/search?q=site:agrolink.com.br&hl=pt-BR&gl=BR&ceid=BR:pt-419"},
    {"nome": "Google Agro",  "url": "https://news.google.com/rss/search?q=agronegocio+pecuaria+GO+MG&hl=pt-BR&gl=BR&ceid=BR:pt-419"},
]

CEPEA_PRODUTOS = [
    {"id": "soja",             "nome": "Soja CEPEA/ESALQ",  "unidade": "sc 60kg"},
    {"id": "milho",            "nome": "Milho CEPEA/ESALQ", "unidade": "sc 60kg"},
    {"id": "boi_gordo",        "nome": "Boi Gordo CEPEA",   "unidade": "@"},
    {"id": "trigo",            "nome": "Trigo CEPEA",       "unidade": "ton"},
    {"id": "algodao",          "nome": "Algodao CEPEA",     "unidade": "@"},
    {"id": "frango_congelado", "nome": "Frango CEPEA",      "unidade": "kg"},
    {"id": "suino",            "nome": "Suino CEPEA",       "unidade": "kg"},
    {"id": "arroz",            "nome": "Arroz CEPEA",       "unidade": "sc 50kg"},
]

NOTICIAS_QUERY = "agronegocio pecuaria nutricao animal boi gordo leite soja milho insumos Goias Minas Gerais hoje Brasil"


def buscar_clima():
    if not OPENWEATHER_KEY:
        return []
    resultados = []
    for cidade in CIDADES_CLIMA:
        try:
            r = requests.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={"q": cidade["query"], "appid": OPENWEATHER_KEY, "units": "metric", "lang": "pt_br"},
                timeout=15
            )
            r.raise_for_status()
            d = r.json()
            resultados.append({
                "cidade": cidade["nome"],
                "temp": round(d["main"]["temp"]),
                "min": round(d["main"]["temp_min"]),
                "max": round(d["main"]["temp_max"]),
                "descricao": d["weather"][0]["description"].capitalize(),
            })
        except Exception as e:
            logger.warning("Clima %s: %s", cidade["nome"], e)
    return resultados


def buscar_cotacoes_cepea():
    resultados = []
    try:
        from agrobr.sync import cepea
        for p in CEPEA_PRODUTOS:
            try:
                u = cepea.ultimo(p["id"])
                resultados.append({
                    "nome": p["nome"],
                    "info": "R$ {:.2f}/{} ({})".format(u.valor, p["unidade"], u.data.strftime("%d/%m"))
                })
            except Exception as e:
                logger.warning("CEPEA %s: %s", p["id"], e)
    except ImportError:
        logger.error("agrobr nao instalado no venv")
    return resultados


def buscar_dolar():
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados/ultimos/1?formato=json"
        with urllib.request.urlopen(url, timeout=10) as r:
            d = json.loads(r.read())[0]
            return "R$ {} (PTAX {})".format(d["valor"], d["data"])
    except Exception as e:
        logger.warning("Dolar BCB: %s", e)
        return "indisponivel"


def buscar_noticias_rss():
    resultados = []
    for feed in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed["url"])
            for entry in parsed.entries[:2]:
                titulo = entry.get("title")
                link = entry.get("link")
                if titulo and link:
                    resultados.append({"titulo": "[{}] {}".format(feed["nome"], titulo), "link": link})
        except Exception as e:
            logger.warning("RSS %s: %s", feed["nome"], e)
    return resultados


def buscar_noticias_serpapi():
    if not SERPAPI_KEY:
        return []
    try:
        r = requests.get(
            "https://serpapi.com/search",
            params={"engine": "google", "q": NOTICIAS_QUERY, "hl": "pt-br", "gl": "br", "num": 5, "api_key": SERPAPI_KEY},
            timeout=15
        )
        r.raise_for_status()
        data = r.json()
        return [
            {"titulo": i.get("title"), "link": i.get("link")}
            for i in data.get("organic_results", [])[:4]
            if i.get("title") and i.get("link")
        ]
    except Exception as e:
        logger.warning("Noticias SerpAPI: %s", e)
        return []


def buscar_email_agrifatto():
    try:
        yahoo_email = os.getenv("YAHOO_EMAIL")
        yahoo_senha = os.getenv("YAHOO_APP_PASSWORD")
        if not yahoo_email or not yahoo_senha:
            return ""
        mail = imaplib.IMAP4_SSL("imap.mail.yahoo.com", 993)
        mail.login(yahoo_email, yahoo_senha)
        mail.select("inbox")
        status, messages = mail.search(None, 'FROM "agrifatto@agrifatto.com.br"')
        if status != "OK" or not messages[0]:
            status, messages = mail.search(None, 'FROM "agrifatto"')
        if status != "OK" or not messages[0]:
            mail.close(); mail.logout()
            return ""
        msg_id = messages[0].split()[-1]
        status, msg_data = mail.fetch(msg_id, "(RFC822)")
        mail.close(); mail.logout()
        if status != "OK":
            return ""
        msg = email_lib.message_from_bytes(msg_data[0][1])
        texto = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        texto = payload.decode("utf-8", errors="replace")
                        break
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                texto = payload.decode("utf-8", errors="replace")
        linhas = [l.strip() for l in texto.splitlines() if l.strip()]
        return "\n".join(linhas[:30])
    except Exception as e:
        logger.warning("Agrifatto email: %s", e)
        return ""


def montar_mensagem(clima, cotacoes_conab, cotacoes_cepea, dolar, precos_manuais, noticias, agrifatto=""):
    hoje = datetime.now().strftime("%d/%m/%Y")
    L = ["<b>Resumo Agro - {}</b>".format(hoje), ""]

    L.append("<b>Clima</b>")
    if clima:
        for c in clima:
            L.append("- {}: {}C ({}-{}C), {}".format(c["cidade"], c["temp"], c["min"], c["max"], c["descricao"]))
    else:
        L.append("- Indisponivel")
    L.append("")

    L.append("<b>Dolar:</b> {}".format(dolar))
    L.append("")

    L.append("<b>Cotacoes CONAB (oficiais)</b>")
    if cotacoes_conab:
        for c in cotacoes_conab:
            L.append("- {}: {}".format(c["nome"], c["info"]))
    else:
        L.append("- Indisponivel")
    L.append("")

    L.append("<b>Indicadores CEPEA/ESALQ</b>")
    if cotacoes_cepea:
        for c in cotacoes_cepea:
            L.append("- {}: {}".format(c["nome"], c["info"]))
    else:
        L.append("- Indisponivel")
    L.append("")

    if precos_manuais and precos_manuais.strip():
        L.append("<b>Precos Manuais (referencia)</b>")
        L.append(precos_manuais)
        L.append("")

    if agrifatto:
        L.append("<b>Agrifatto - Bom Dia Commodities</b>")
        L.append(agrifatto[:800])
        L.append("")

    L.append("<b>Noticias</b>")
    if noticias:
        for n in noticias[:8]:
            L.append("- <a href=\"{}\">{}</a>".format(n["link"], n["titulo"]))
    else:
        L.append("- Nenhuma noticia encontrada")

    return "\n".join(L)


def enviar_telegram(mensagem):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Token ou chat_id nao configurados.")
        return False
    try:
        import time
        url = "https://api.telegram.org/bot{}/sendMessage".format(TELEGRAM_BOT_TOKEN)
        limite = 4000
        partes = []
        while len(mensagem) > limite:
            corte = mensagem.rfind("\n", 0, limite)
            if corte == -1:
                corte = limite
            partes.append(mensagem[:corte])
            mensagem = mensagem[corte:].lstrip("\n")
        partes.append(mensagem)
        for parte in partes:
            r = requests.post(url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": parte,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }, timeout=15)
            r.raise_for_status()
            if len(partes) > 1:
                time.sleep(1)
        logger.info("Resumo enviado (%d parte(s)).", len(partes))
        return True
    except Exception as e:
        logger.error("Falha ao enviar Telegram: %s", e)
        return False


def main():
    logger.info("Iniciando resumo agro diario...")
    clima          = buscar_clima()
    dolar          = buscar_dolar()
    cotacoes_conab = buscar_cotacoes_conab()
    cotacoes_cepea = buscar_cotacoes_cepea()
    precos_manuais = precos_manuais_resumo()
    agrifatto      = buscar_email_agrifatto()
    noticias       = buscar_noticias_serpapi() + buscar_noticias_rss()
    mensagem = montar_mensagem(clima, cotacoes_conab, cotacoes_cepea, dolar, precos_manuais, noticias, agrifatto)
    enviar_telegram(mensagem)
    logger.info("Concluido.")


if __name__ == "__main__":
    main()
