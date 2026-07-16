#!/usr/bin/env python3
"""
Script migliorato per creare file ICS con frasi anti-sabotaggio
Integra: categorie, difficoltà, Pomodoro, programmazione mentale
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from typing import List, Dict
import uuid

# Rendi importabili i moduli affiancati indipendentemente dalla cartella di
# installazione dello skill (non piu' vincolato a /home/claude).
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
for _candidate_path in (_SCRIPT_DIR, "/home/claude"):
    if _candidate_path and _candidate_path not in sys.path:
        sys.path.insert(0, _candidate_path)

from anti_sabotage_phrases import AntiSabotageGenerator
from task_analyzer import TaskAnalyzer, TaskCategory


# Cartella "download" di Claude: e' l'UNICA i cui file vengono resi
# scaricabili dall'utente. Va quindi creata e usata come destinazione primaria.
DOWNLOAD_DIR = "/mnt/user-data/outputs"


def resolve_output_dir() -> str:
    """Restituisce una cartella di output scrivibile, con fallback robusti.

    Ordine di preferenza:
      1. Variabile d'ambiente AGENDA_SMART_OUTPUT_DIR (se impostata)
      2. /mnt/user-data/outputs  (cartella download di Claude)
      3. Cartella di lavoro corrente
      4. Cartella temporanea di sistema (ultima spiaggia)

    La cartella scelta viene creata se non esiste. Se non e' possibile usare la
    cartella download, viene stampato un avviso esplicito su stderr: cosi'
    l'utente sa sempre dove trovare il file (evita i file "spariti" e i
    "non riesco ad accedere alla cartella download").
    """
    candidates = []
    env_dir = os.environ.get("AGENDA_SMART_OUTPUT_DIR")
    if env_dir:
        candidates.append(env_dir)
    candidates.append(DOWNLOAD_DIR)
    candidates.append(os.getcwd())
    candidates.append(tempfile.gettempdir())

    for directory in candidates:
        try:
            os.makedirs(directory, exist_ok=True)
            if os.access(directory, os.W_OK):
                if os.path.abspath(directory) != os.path.abspath(DOWNLOAD_DIR):
                    print(
                        "⚠️  Cartella download non disponibile: il file verra' "
                        f"salvato in '{directory}'. Se non lo vedi tra i download, "
                        "cercalo in quel percorso.",
                        file=sys.stderr,
                    )
                return directory
        except OSError:
            continue

    # Se proprio nessuna cartella e' scrivibile, ripiega sul temp di sistema.
    return tempfile.gettempdir()

class EnhancedICSCreator:
    """Crea file ICS avanzati con programmazione mentale"""
    
    def __init__(self):
        self.phrase_generator = AntiSabotageGenerator()
        self.task_analyzer = TaskAnalyzer()
    
    def create_ics_from_tasks(self, 
                              tasks: List[Dict], 
                              output_filename: str = "agenda_smart.ics") -> str:
        """
        Crea file ICS da lista task con tutte le funzionalità avanzate
        
        Args:
            tasks: Lista di dict con task suggestions
            output_filename: Nome file output
            
        Returns:
            Path al file creato
        """
        ics_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Agenda Smart//Anti-Sabotage Calendar//IT",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Agenda Smart - Tasks Ottimizzati",
            "X-WR-TIMEZONE:Europe/Rome",
            "X-WR-CALDESC:Task schedulati con programmazione mentale anti-sabotaggio",
        ]
        
        for task in tasks:
            event_lines = self._create_event_from_task(task)
            ics_lines.extend(event_lines)
        
        ics_lines.append("END:VCALENDAR")
        
        # Scrivi file in una cartella scrivibile (con creazione e fallback)
        output_dir = resolve_output_dir()
        output_path = os.path.join(output_dir, output_filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\r\n'.join(ics_lines))

        return output_path
    
    def _create_event_from_task(self, task: Dict) -> List[str]:
        """
        Crea evento singolo con tutte le feature avanzate
        
        Args:
            task: Dict con info task
            
        Returns:
            Lista righe ICS per l'evento
        """
        # Estrai info base
        task_name = task.get("name", "Task")
        start_time = task.get("suggested_start")
        end_time = task.get("suggested_end")
        duration_minutes = task.get("duration_minutes", 30)
        category = task.get("category", "lavoro")
        description = task.get("description", "")
        
        # Analizza difficoltà
        difficulty_analysis = self.task_analyzer.analyze_difficulty(task_name, description)
        
        # Calcola Pomodoro breakdown
        pomodoro_info = self.task_analyzer.calculate_pomodoro_blocks(duration_minutes)
        
        # Determina se deadline vicina
        is_deadline_close = False
        if "deadline" in task:
            deadline_dt = datetime.fromisoformat(task["deadline"].replace("Z", "+00:00"))
            now = datetime.now(deadline_dt.tzinfo)
            days_to_deadline = (deadline_dt - now).days
            is_deadline_close = days_to_deadline <= 2
        
        # Determina se back-to-back (se presente nel task)
        is_back_to_back = task.get("is_back_to_back", False)
        
        # Genera frasi anti-sabotaggio
        phrases = self.phrase_generator.generate_phrase(
            task_name=task_name,
            category=category,
            difficulty_physical=difficulty_analysis["difficulty_physical"],
            difficulty_intellectual=difficulty_analysis["difficulty_intellectual"],
            is_deadline_close=is_deadline_close,
            is_back_to_back=is_back_to_back,
            time_estimate_minutes=duration_minutes
        )
        
        # Componi descrizione completa
        description_parts = [
            phrases["full_description"],
            "",
            "─" * 40,
            "📊 **ANALISI TASK**",
            f"Categoria: {TaskCategory[category.upper()].value}",
            f"Difficoltà Fisica: {difficulty_analysis['difficulty_physical']}",
            f"Difficoltà Intellettuale: {difficulty_analysis['difficulty_intellectual']}",
            f"Impatto Energia: {difficulty_analysis['energy_impact']}",
            "",
            "🍅 **BREAKDOWN POMODORO**",
            f"Pomodori necessari: {pomodoro_info['pomodoros']}",
            f"Tempo lavoro effettivo: {pomodoro_info['work_time']} min",
            f"Pause brevi: {pomodoro_info['short_breaks']}",
            f"Pause lunghe: {pomodoro_info['long_breaks']}",
            f"Tempo totale con pause: {pomodoro_info['total_time_with_breaks']} min",
            "",
            "📅 **SCHEDULE POMODORO**",
        ]
        
        for schedule_item in pomodoro_info['schedule']:
            description_parts.append(schedule_item)
        
        if difficulty_analysis['time_recommendations']:
            description_parts.extend([
                "",
                "💡 **RACCOMANDAZIONI**",
            ])
            for rec in difficulty_analysis['time_recommendations']:
                description_parts.append(f"• {rec}")
        
        if task.get("reasoning"):
            description_parts.extend([
                "",
                "🎯 **PERCHÉ QUESTO SLOT**",
                task["reasoning"]
            ])
        
        full_description = "\\n".join(description_parts)
        
        # Formatta date/time
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        
        # Emoji basato su categoria
        category_emoji = {
            "lavoro": "💼",
            "personale": "🏠",
            "progetti": "🎯",
            "urgente": "🚨",
            "formazione": "🎓",
            "benessere": "💪"
        }
        emoji = category_emoji.get(category, "⏰")
        
        # Crea evento ICS
        uid = str(uuid.uuid4())
        now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        
        event_lines = [
            "BEGIN:VEVENT",
            f"UID:{uid}@agendasmart",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:{emoji} {task_name}",
            f"DESCRIPTION:{full_description}",
            f"CATEGORIES:{category.upper()}",
            "STATUS:CONFIRMED",
            "TRANSP:OPAQUE",
            "SEQUENCE:0",
            # Reminder: 15 minuti prima (con messaggio motivazionale)
            "BEGIN:VALARM",
            "TRIGGER:-PT15M",
            "ACTION:DISPLAY",
            f"DESCRIPTION:🔔 Tra 15 minuti: {task_name}\\n\\n{phrases['main']}",
            "END:VALARM",
            "END:VEVENT",
        ]
        
        return event_lines
    
    def create_celebration_event(self, 
                                 task_name: str,
                                 completion_time: str,
                                 celebration_message: str = None) -> List[str]:
        """
        Crea evento di celebrazione dopo completamento task
        
        Args:
            task_name: Nome task completato
            completion_time: Timestamp completamento
            celebration_message: Messaggio personalizzato (opzionale)
            
        Returns:
            Righe ICS per evento celebrazione
        """
        if not celebration_message:
            celebration_message = self.phrase_generator.CELEBRATION_PHRASES[0]
        
        completion_dt = datetime.fromisoformat(completion_time.replace("Z", "+00:00"))
        
        uid = str(uuid.uuid4())
        now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        
        description = f"🎉 HAI COMPLETATO: {task_name}\\n\\n{celebration_message}\\n\\nIl tuo impegno sta costruendo risultati concreti. Continua così!"
        
        event_lines = [
            "BEGIN:VEVENT",
            f"UID:{uid}@agendasmart",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART:{completion_dt.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND:{(completion_dt + timedelta(minutes=5)).strftime('%Y%m%dT%H%M%S')}",
            f"SUMMARY:✅ Completato: {task_name}",
            f"DESCRIPTION:{description}",
            "CATEGORIES:CELEBRATION",
            "STATUS:CONFIRMED",
            "TRANSP:TRANSPARENT",
            "SEQUENCE:0",
            "END:VEVENT",
        ]
        
        return event_lines


def main():
    """Funzione principale"""
    if len(sys.argv) < 2:
        print("Uso: python create_ics_enhanced.py <task_suggestions.json> [output.ics]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "agenda_smart_enhanced.ics"
    
    # Carica task suggestions
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tasks = data.get("suggestions", [])
    
    if not tasks:
        print("❌ Nessun task trovato nel file JSON")
        sys.exit(1)
    
    # Crea ICS
    creator = EnhancedICSCreator()
    output_path = creator.create_ics_from_tasks(tasks, output_file)
    
    print(f"✅ File ICS creato: {output_path}")
    print(f"📊 Task schedulati: {len(tasks)}")
    print(f"🧠 Ogni task include:")
    print(f"   • Frasi anti-sabotaggio personalizzate")
    print(f"   • Analisi difficoltà fisica/intellettuale")
    print(f"   • Breakdown Pomodoro (25 min)")
    print(f"   • Raccomandazioni orarie")
    print(f"   • Reminder motivazionali")
    print(f"\n📥 Importa il file in Google Calendar per attivare la programmazione mentale!")


if __name__ == "__main__":
    main()
