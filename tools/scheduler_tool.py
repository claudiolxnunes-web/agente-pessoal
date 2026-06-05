"""Agendamento automático de tarefas"""
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional
import json
import os

class SchedulerTool:
    """Ferramenta para agendar tarefas automáticas do agente"""

    def __init__(self, tarefas_path="memory/tarefas_agendadas.json"):
        self.tarefas_path = tarefas_path
        self.tarefas: Dict[str, Dict] = {}
        self.funcoes: Dict[str, Callable] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._carregar_tarefas()

    def _carregar_tarefas(self):
        """Carrega tarefas salvas"""
        if os.path.exists(self.tarefas_path):
            try:
                with open(self.tarefas_path, 'r') as f:
                    self.tarefas = json.load(f)
            except:
                self.tarefas = {}

    def _salvar_tarefas(self):
        """Persiste tarefas em disco"""
        os.makedirs(os.path.dirname(self.tarefas_path), exist_ok=True)
        with open(self.tarefas_path, 'w') as f:
            json.dump(self.tarefas, f, ensure_ascii=False, indent=2)

    def registrar_funcao(self, nome: str, funcao: Callable):
        """Registra uma função que pode ser chamada pelo scheduler"""
        self.funcoes[nome] = funcao

    def agendar_diario(self, id_tarefa: str, hora: str, funcao_nome: str, args=None, descricao=""):
        """Agenda tarefa diária (formato hora: HH:MM)"""
        self.tarefas[id_tarefa] = {
            "tipo": "diario",
            "hora": hora,
            "funcao": funcao_nome,
            "args": args or [],
            "descricao": descricao,
            "ativo": True,
            "ultima_execucao": None,
            "proxima_execucao": None,
            "criado_em": datetime.now().isoformat()
        }
        self._salvar_tarefas()

        # Registra no schedule
        if funcao_nome in self.funcoes:
            schedule.every().day.at(hora).do(self._executar_tarefa, id_tarefa)

        return f"✅ Tarefa '{id_tarefa}' agendada diariamente às {hora}"

    def agendar_semanal(self, id_tarefa: str, dia_semana: str, hora: str, funcao_nome: str, args=None, descricao=""):
        """Agenda tarefa semanal (dia: monday-sunday)"""
        dias = {
            "segunda": "monday", "terca": "tuesday", "quarta": "wednesday",
            "quinta": "thursday", "sexta": "friday", "sabado": "saturday", "domingo": "sunday"
        }
        dia_en = dias.get(dia_semana.lower(), dia_semana.lower())

        self.tarefas[id_tarefa] = {
            "tipo": "semanal",
            "dia": dia_en,
            "hora": hora,
            "funcao": funcao_nome,
            "args": args or [],
            "descricao": descricao,
            "ativo": True,
            "ultima_execucao": None,
            "criado_em": datetime.now().isoformat()
        }
        self._salvar_tarefas()

        if funcao_nome in self.funcoes:
            job = getattr(schedule.every(), dia_en)
            job.at(hora).do(self._executar_tarefa, id_tarefa)

        return f"✅ Tarefa '{id_tarefa}' agendada toda {dia_semana} às {hora}"

    def agendar_unico(self, id_tarefa: str, data_hora: str, funcao_nome: str, args=None, descricao=""):
        """Agenda tarefa única (formato: YYYY-MM-DD HH:MM)"""
        self.tarefas[id_tarefa] = {
            "tipo": "unico",
            "data_hora": data_hora,
            "funcao": funcao_nome,
            "args": args or [],
            "descricao": descricao,
            "ativo": True,
            "executado": False,
            "criado_em": datetime.now().isoformat()
        }
        self._salvar_tarefas()

        return f"✅ Tarefa '{id_tarefa}' agendada para {data_hora}"

    def agendar_intervalo(self, id_tarefa: str, minutos: int, funcao_nome: str, args=None, descricao=""):
        """Agenda tarefa a cada N minutos"""
        self.tarefas[id_tarefa] = {
            "tipo": "intervalo",
            "minutos": minutos,
            "funcao": funcao_nome,
            "args": args or [],
            "descricao": descricao,
            "ativo": True,
            "ultima_execucao": None,
            "criado_em": datetime.now().isoformat()
        }
        self._salvar_tarefas()

        if funcao_nome in self.funcoes:
            schedule.every(minutos).minutes.do(self._executar_tarefa, id_tarefa)

        return f"✅ Tarefa '{id_tarefa}' a cada {minutos} minutos"

    def _executar_tarefa(self, id_tarefa: str):
        """Executa uma tarefa agendada"""
        if id_tarefa not in self.tarefas:
            return

        tarefa = self.tarefas[id_tarefa]
        if not tarefa["ativo"]:
            return

        funcao_nome = tarefa["funcao"]
        if funcao_nome not in self.funcoes:
            print(f"❌ Função '{funcao_nome}' não registrada")
            return

        try:
            print(f"🔄 Executando tarefa: {id_tarefa}")
            args = tarefa.get("args", [])
            resultado = self.funcoes[funcao_nome](*args)

            tarefa["ultima_execucao"] = datetime.now().isoformat()
            tarefa["ultimo_resultado"] = str(resultado)

            # Se for tarefa única, desativa
            if tarefa["tipo"] == "unico":
                tarefa["ativo"] = False
                tarefa["executado"] = True

            self._salvar_tarefas()

        except Exception as e:
            print(f"❌ Erro na tarefa {id_tarefa}: {e}")
            tarefa["ultimo_erro"] = str(e)
            self._salvar_tarefas()

    def listar_tarefas(self) -> str:
        """Lista todas as tarefas agendadas"""
        if not self.tarefas:
            return "Nenhuma tarefa agendada."

        output = "⏰ Tarefas agendadas:\n\n"

        for id_tarefa, tarefa in self.tarefas.items():
            status = "🟢" if tarefa["ativo"] else "🔴"
            tipo = tarefa["tipo"]
            desc = tarefa.get("descricao", "Sem descrição")

            if tipo == "diario":
                info = f"Todo dia às {tarefa['hora']}"
            elif tipo == "semanal":
                info = f"Toda {tarefa['dia']} às {tarefa['hora']}"
            elif tipo == "unico":
                info = f"Único: {tarefa['data_hora']}"
            elif tipo == "intervalo":
                info = f"A cada {tarefa['minutos']} min"
            else:
                info = tipo

            ultima = tarefa.get("ultima_execucao", "Nunca")
            if ultima != "Nunca":
                ultima = ultima[:16]

            output += f"{status} **{id_tarefa}**\n"
            output += f"   {desc}\n"
            output += f"   📅 {info} | 🕐 Última: {ultima}\n\n"

        return output

    def desativar_tarefa(self, id_tarefa: str) -> str:
        """Desativa uma tarefa"""
        if id_tarefa in self.tarefas:
            self.tarefas[id_tarefa]["ativo"] = False
            self._salvar_tarefas()
            return f"🛑 Tarefa '{id_tarefa}' desativada."
        return f"Tarefa '{id_tarefa}' não encontrada."

    def ativar_tarefa(self, id_tarefa: str) -> str:
        """Reativa uma tarefa"""
        if id_tarefa in self.tarefas:
            self.tarefas[id_tarefa]["ativo"] = True
            self._salvar_tarefas()
            return f"▶️ Tarefa '{id_tarefa}' ativada."
        return f"Tarefa '{id_tarefa}' não encontrada."

    def deletar_tarefa(self, id_tarefa: str) -> str:
        """Remove uma tarefa"""
        if id_tarefa in self.tarefas:
            del self.tarefas[id_tarefa]
            self._salvar_tarefas()
            # Note: não remove do schedule (schedule não suporta remoção fácil)
            return f"🗑️ Tarefa '{id_tarefa}' removida."
        return f"Tarefa '{id_tarefa}' não encontrada."

    def iniciar_scheduler(self):
        """Inicia o loop do scheduler em thread separada"""
        if self._running:
            return "Scheduler já está rodando."

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

        return "⏰ Scheduler iniciado em background."

    def _loop(self):
        """Loop principal do scheduler"""
        while self._running:
            schedule.run_pending()
            time.sleep(60)  # Verifica a cada minuto

    def parar_scheduler(self):
        """Para o scheduler"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        return "🛑 Scheduler parado."


# ── Funções de módulo ─────────────────────────────────────────────────────────
_scheduler = None

def _get_scheduler():
    global _scheduler
    if _scheduler is None:
        from tools.scheduler_tool import SchedulerTool
        _scheduler = SchedulerTool()
    return _scheduler

def agendar_diario(funcao, hora: int, minuto: int = 0, nome: str = "tarefa") -> str:
    try:
        hora_str = f"{hora:02d}:{minuto:02d}"
        return _get_scheduler().agendar_diario(nome, hora_str, nome)
    except Exception as e:
        return f"Erro ao agendar: {e}"

def listar_tarefas_agendadas() -> str:
    try:
        return _get_scheduler().listar_tarefas()
    except Exception as e:
        return f"Erro ao listar agendamentos: {e}"
