#!/usr/bin/env python3
"""
precos_minerais_mensais.py
==========================
Busca referencias internacionais de minerais no IndexMundi,
converte para BRL via BCB e envia no Telegram junto com
os precos manuais regionais cadastrados.
Roda todo dia 1 do mes as 7h UTC.
"""
import os
import sys
import json
import requests
import urllib.request
from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.precos_manuais_store import carregar_precos

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")

HEADERS = {"User-Agent": "Mozilla/5.0"}

# Commodities disponiveis no IndexMundi
INDEXMUNDI = [
    # Minerais e fertilizantes
    {"nome": "Fosfato (TSP ref.)",        "slug": "triple-superphosphate", "unidade": "ton", "proxy": "Fosfato Bicalcico",      "fonte": "World Bank/FMB"},
    {"nome": "Ureia",                     "slug": "urea",                   "unidade": "ton", "proxy": "Ureia Pecuaria",          "fonte": "World Bank/FMB"},
    {"nome": "DAP (fosfato diamonico)",   "slug": "dap-fertilizer",         "unidade": "ton", "proxy": "",                        "fonte": "World Bank/FMB"},
    {"nome": "Cloreto de Potassio (KCl)", "slug": "potassium-chloride",     "unidade": "ton", "proxy": "",                        "fonte": "World Bank/FMB"},
    {"nome": "Cobre (ref. sulfato)",      "slug": "copper-grade-a-cathode",                 "unidade": "ton", "proxy": "Sulfato de Cobre",        "fonte": "LME"},
    {"nome": "Zinco (ref. sulfato/oxido)","slug": "zinc",                   "unidade": "ton", "proxy": "Sulfato/Oxido de Zinco",  "fonte": "LME"},
    # Graos e proteicos
    {"nome": "Soja (grao)",               "slug": "soybeans",               "unidade": "ton", "proxy": "",                        "fonte": "CBOT/CME"},
    {"nome": "Farelo de Soja",            "slug": "soybean-meal",           "unidade": "ton", "proxy": "Farelo de Soja",          "fonte": "CBOT/CME"},
    {"nome": "Oleo de Soja",              "slug": "soybean-oil",            "unidade": "ton", "proxy": "",                        "fonte": "CBOT/CME"},
    {"nome": "Milho",                     "slug": "maize-corn",                  "unidade": "ton", "proxy": "",                        "fonte": "CBOT/CME"},
    {"nome": "Sorgo",                     "slug": "sorghum",                "unidade": "ton", "proxy": "",                        "fonte": "CBOT/CME"},
    {"nome": "Trigo",                     "slug": "wheat",                  "unidade": "ton", "proxy": "",                        "fonte": "CBOT/CME"},
    {"nome": "Farinha de Peixe",          "slug": "fishmeal",               "unidade": "ton", "proxy": "",                        "fonte": "Peru (exportador)"},
    {"nome": "Algodao",                   "slug": "cotton-a-index",                 "unidade": "ton", "proxy": "",                        "fonte": "Cotlook A Index"},
    {"nome": "Oleo de Palma",             "slug": "palm-oil",               "unidade": "ton", "proxy": "",                        "fonte": "Bursa Malaysia"},
    {"nome": "Oleo de Canola",            "slug": "rapeseed-oil",           "unidade": "ton", "proxy": "",                        "fonte": "ICE Futures Canada"},
]

# Insumos sem fonte publica — so preco manual
APENAS_MANUAIS = [
    "enxofre ventilado",
    "enxofre 70% lavado",
    "bicarbonato de sodio",
    "sulfato de manganes",
    "oxido de magnesio",
    "sulfato de cobalto",
    "iodato de calcio",
    "selenito de sodio",
]


def buscar_dolar() -> float:
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados/ultimos/1?formato=json"
        with urllib.request.urlopen(url, timeout=10) as r:
            d = json.loads(r.read())[0]
            return float(d["valor"].replace(",", "."))
    except Exception:
        return 0.0


def buscar_indexmundi(slug: str) -> tuple:
    """Retorna (data, valor_usd) ou (None, None)."""
    try:
        url = f"https://www.indexmundi.com/commodities/?commodity={slug}&months=3"
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        tabelas = soup.find_all("table")
        if len(tabelas) > 1:
            linhas = tabelas[1].find_all("tr")
            for linha in reversed(linhas):
                colunas = linha.find_all("td")
                if len(colunas) >= 2:
                    data = colunas[0].text.strip()
                    valor = colunas[1].text.strip().replace(",", "")
                    return data, float(valor)
        return None, None
    except Exception:
        return None, None


def montar_relatorio(dolar: float) -> str:
    hoje = datetime.now().strftime("%d/%m/%Y")
    precos_manuais = carregar_precos()

    L = [f"<b>Relatorio Mensal de Minerais — {hoje}</b>", ""]
    L.append(f"<b>Dolar BCB:</b> R$ {dolar:.4f}")
    L.append("")

    # Secao IndexMundi
    L.append("<b>Referencias Internacionais (IndexMundi)</b>")
    L.append("<i>Precos internacionais — use como referencia de tendencia</i>")
    L.append("")

    for item in INDEXMUNDI:
        data, usd = buscar_indexmundi(item["slug"])
        if usd and dolar:
            brl = usd * dolar
            L.append(f"<b>{item['nome']}</b>")
            L.append(f"  Internacional: USD {usd:,.2f}/{item['unidade']} ({data}) — {item['fonte']}")
            L.append(f"  Ref. BRL: R$ {brl:,.2f}/{item['unidade']}")
            # Preco manual regional se existir
            chave = item["proxy"].lower().strip()
            if chave in precos_manuais:
                p = precos_manuais[chave]
                L.append(f"  Seu preco regional: {p['valor']} (ref. {p['atualizado_em']})")
            else:
                L.append(f"  Seu preco regional: <i>nao cadastrado</i>")
        else:
            L.append(f"<b>{item['nome']}</b>: indisponivel")
        L.append("")

    # Secao apenas manuais
    L.append("<b>Insumos sem fonte publica — apenas preco manual</b>")
    L.append("")

    for insumo in APENAS_MANUAIS:
        chave = insumo.lower().strip()
        if chave in precos_manuais:
            p = precos_manuais[chave]
            L.append(f"• {p['ingrediente']}: {p['valor']} (ref. {p['atualizado_em']})")
        else:
            L.append(f"• {insumo}: <i>nao cadastrado — envie: atualiza preco {insumo} R$X/ton</i>")

    L.append("")
    L.append("<i>Para atualizar qualquer preco regional: atualiza preco NOME R$X/ton</i>")

    return "\n".join(L)


def enviar_telegram(mensagem: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": mensagem,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=15
        )
        r.raise_for_status()
        print("Relatorio enviado.")
        return True
    except Exception as e:
        print(f"Erro: {e}")
        return False


if __name__ == "__main__":
    dolar = buscar_dolar()
    mensagem = montar_relatorio(dolar)
    enviar_telegram(mensagem)
