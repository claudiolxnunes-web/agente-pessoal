#!/usr/bin/env python3
"""Integração com dados de preços da CONAB (dados abertos, sem API key)."""
import requests
import io
import csv
from datetime import datetime

CONAB_URL = "https://portaldeinformacoes.conab.gov.br/downloads/arquivos/PrecosSemanalUF.txt"

PRODUTOS_MAPA = {
    "BOI":               "Boi Gordo",
    "SOJA":              "Soja",
    "MILHO":             "Milho",
    "SORGO GRANIFERO":   "Sorgo em Grão",
    "TRIGO":             "Trigo",
    "FARELO DE SOJA":    "Farelo de Soja",
    "LEITE DE VACA":     "Leite de Vaca",
    "CAROCO DE ALGODAO": "Caroço de Algodão",
    "SUPERFOSFATO SIMPLES": "Superfosfato Simples",
    "SUPERFOSFATO TRIPLO":  "Superfosfato Triplo",
}

UFS_INTERESSE = {"GO", "MG", "MT", "MS"}


def buscar_cotacoes_conab() -> list:
    """Baixa e filtra preços semanais da CONAB por produto e UF."""
    try:
        r = requests.get(CONAB_URL, timeout=30)
        r.raise_for_status()

        reader = csv.DictReader(
            io.StringIO(r.text),
            delimiter=";",
            fieldnames=["produto", "classificacao", "id_produto", "uf",
                        "regiao", "ano", "mes", "semana_periodo",
                        "semana_num", "nivel", "valor_kg"]
        )
        next(reader)  # pula cabecalho

        # Agrupa: produto -> uf -> linha mais recente
        melhores = {}
        for row in reader:
            prod_raw = row["produto"].strip().upper()
            uf = row["uf"].strip().upper()

            if uf not in UFS_INTERESSE:
                continue

            # Verifica se é produto de interesse
            nome_amigavel = None
            for chave, nome in PRODUTOS_MAPA.items():
                if chave == prod_raw:
                    nome_amigavel = nome
                    break
            if not nome_amigavel:
                continue

            try:
                valor = float(row["valor_kg"].strip().replace(",", "."))
                ano = int(row["ano"].strip())
                mes = int(row["mes"].strip())
                semana = int(row["semana_num"].strip())
            except (ValueError, KeyError):
                continue

            chave_prod = f"{nome_amigavel}_{uf}"
            existente = melhores.get(chave_prod)
            if not existente or (ano, mes, semana) > (existente["ano"], existente["mes"], existente["semana"]):
                melhores[chave_prod] = {
                    "nome": nome_amigavel,
                    "uf": uf,
                    "valor_kg": valor,
                    "ano": ano,
                    "mes": mes,
                    "semana": semana,
                    "periodo": row["semana_periodo"].strip(),
                    "nivel": row["nivel"].strip(),
                }

        # Formata resultado agrupado por produto
        por_produto = {}
        for item in melhores.values():
            nome = item["nome"]
            if nome not in por_produto:
                por_produto[nome] = []
            por_produto[nome].append(item)

        resultado = []
        for nome, itens in sorted(por_produto.items()):
            partes = []
            for it in sorted(itens, key=lambda x: x["uf"]):
                # Converte R$/kg para unidade mais comum
                val_kg = it["valor_kg"]
                if nome in ("Boi Gordo",):
                    # R$/kg -> R$/@ (arroba = 15kg)
                    val_arr = val_kg * 15
                    partes.append(f"{it['uf']}: R${val_arr:.2f}/@")
                elif nome in ("Leite de Vaca",):
                    partes.append(f"{it['uf']}: R${val_kg:.4f}/L")
                else:
                    # R$/kg -> R$/ton
                    val_ton = val_kg * 1000
                    partes.append(f"{it['uf']}: R${val_ton:.0f}/ton")
            resultado.append({
                "nome": f"{nome} (CONAB)",
                "info": " | ".join(partes)
            })

        return resultado

    except Exception as e:
        return [{"nome": "CONAB", "info": f"Erro ao buscar dados: {e}"}]
