#!/usr/bin/env python3
"""Armazena preços manuais de insumos atualizados pelo usuario via Telegram."""
import json
import os
from datetime import datetime

PRECOS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "precos_manuais.json")

def carregar_precos() -> dict:
    if not os.path.exists(PRECOS_FILE):
        return {}
    with open(PRECOS_FILE, encoding="utf-8") as f:
        return json.load(f)

def salvar_preco(ingrediente: str, valor: str) -> str:
    precos = carregar_precos()
    chave = ingrediente.lower().strip()
    precos[chave] = {
        "ingrediente": ingrediente,
        "valor": valor,
        "atualizado_em": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    with open(PRECOS_FILE, "w", encoding="utf-8") as f:
        json.dump(precos, f, ensure_ascii=False, indent=2)
    return f"Preco de {ingrediente} atualizado para {valor}."

def listar_precos() -> str:
    precos = carregar_precos()
    if not precos:
        return "Nenhum preco manual cadastrado ainda."
    linhas = ["Precos manuais cadastrados:"]
    for item in precos.values():
        linhas.append(f"- {item['ingrediente']}: {item['valor']} (atualizado em {item['atualizado_em']})")
    return "\n".join(linhas)

def formatar_para_resumo() -> str:
    precos = carregar_precos()
    if not precos:
        return ""
    linhas = []
    for item in precos.values():
        linhas.append(f"• {item['ingrediente']}: {item['valor']} (ref. {item['atualizado_em']})")
    return "\n".join(linhas)
