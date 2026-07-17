#!/usr/bin/env python3
"""Cria em lote a agenda da semana de 22 a 26/06, confirmada por áudio."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from tools.google_calendar_tool import criar_evento_calendar

EVENTOS = [
    # Segunda-feira, 22/06
    {"titulo": "Verificar faturamento dos representantes e meta da regional", "data_hora": "22/06/2026 09:00", "duracao_horas": 1, "local": ""},
    {"titulo": "Listagem de clientes inativos", "data_hora": "22/06/2026 10:00", "duracao_horas": 1, "local": ""},
    {"titulo": "Revisão de cotações em aberto e cadastro de produtos", "data_hora": "22/06/2026 11:00", "duracao_horas": 1, "local": ""},
    {"titulo": "Verificar números da regional", "data_hora": "22/06/2026 14:00", "duracao_horas": 1, "local": ""},
    {"titulo": "Reunião com a equipe", "data_hora": "22/06/2026 16:00", "duracao_horas": 1, "local": ""},

    # Terça-feira, 23/06
    {"titulo": "Cartório - documentos para Álvaro Alberto assinar", "data_hora": "23/06/2026 08:00", "duracao_horas": 1, "local": "Nerópolis"},
    {"titulo": "Fábrica - reunião com Ademar", "data_hora": "23/06/2026 09:00", "duracao_horas": 1, "local": "Goianira"},
    {"titulo": "Reunião com Alexandre, candidato a ARC", "data_hora": "23/06/2026 10:00", "duracao_horas": 1, "local": ""},
    {"titulo": "Reunião com Fernando Coelho (Rações Coelho)", "data_hora": "23/06/2026 16:00", "duracao_horas": 1, "local": "Nerópolis"},

    # Quarta-feira, 24/06
    {"titulo": "Agrocampo", "data_hora": "24/06/2026 09:00", "duracao_horas": 1, "local": "Abadiânia"},
    {"titulo": "Reunião com Ivonaldo", "data_hora": "24/06/2026 11:00", "duracao_horas": 1, "local": "Alexânia"},
    {"titulo": "Reunião com Ivonildo", "data_hora": "24/06/2026 12:00", "duracao_horas": 1, "local": "Alexânia"},
    {"titulo": "Rações Criador", "data_hora": "24/06/2026 13:00", "duracao_horas": 1, "local": "Luziânia"},
    {"titulo": "Confinamento Realeza - com Carlos Henrique", "data_hora": "24/06/2026 15:00", "duracao_horas": 1, "local": ""},

    # Quinta-feira, 25/06
    {"titulo": "Alipã", "data_hora": "25/06/2026 09:00", "duracao_horas": 1, "local": "Brasília"},
    {"titulo": "Bov", "data_hora": "25/06/2026 14:00", "duracao_horas": 1, "local": "Padre Bernardo"},

    # Sexta-feira, 26/06
    {"titulo": "Norte e Sul", "data_hora": "26/06/2026 09:00", "duracao_horas": 1, "local": "Anápolis"},
    {"titulo": "Loja do Bruno", "data_hora": "26/06/2026 10:00", "duracao_horas": 1, "local": ""},
    {"titulo": "Zoocampo", "data_hora": "26/06/2026 14:00", "duracao_horas": 1, "local": ""},
    {"titulo": "Casa Fernandes", "data_hora": "26/06/2026 16:00", "duracao_horas": 1, "local": ""},
]

def main():
    print(f"Criando {len(EVENTOS)} eventos...\n")
    sucesso, falha = 0, 0
    for ev in EVENTOS:
        try:
            resultado = criar_evento_calendar(
                titulo=ev["titulo"],
                data_hora=ev["data_hora"],
                duracao_horas=ev["duracao_horas"],
                descricao="",
                local=ev["local"],
            )
            print(f"✅ {ev['data_hora']} - {ev['titulo']}")
            sucesso += 1
        except Exception as e:
            print(f"❌ {ev['data_hora']} - {ev['titulo']} | erro: {e}")
            falha += 1

    print(f"\nConcluído: {sucesso} criados, {falha} com erro.")

if __name__ == "__main__":
    main()
