"""Armazena rascunhos de agenda pendentes de confirmação, por chat_id."""
import json
import os

DRAFTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "agenda_drafts")
os.makedirs(DRAFTS_DIR, exist_ok=True)


def _path(chat_id):
    return os.path.join(DRAFTS_DIR, f"{chat_id}.json")


def salvar_rascunho(chat_id, eventos):
    with open(_path(chat_id), "w", encoding="utf-8") as f:
        json.dump(eventos, f, ensure_ascii=False, indent=2)


def obter_rascunho(chat_id):
    path = _path(chat_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def limpar_rascunho(chat_id):
    path = _path(chat_id)
    if os.path.exists(path):
        os.remove(path)
