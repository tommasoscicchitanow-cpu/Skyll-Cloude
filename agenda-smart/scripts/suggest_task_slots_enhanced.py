#!/usr/bin/env python3
"""
Script migliorato per suggerire slot task
Integra: Pomodoro 25 min, categorie, difficoltà, energia
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from typing import List, Dict, Tuple

# Rendi importabili i moduli affiancati indipendentemente dalla cartella di
# installazione dello skill (non piu' vincolato a /home/claude).
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
for _candidate_path in (_SCRIPT_DIR, "/home/claude"):
    if _candidate_path and _candidate_path not in sys.path:
        sys.path.insert(0, _candidate_path)

from task_analyzer import TaskAnalyzer, TaskCategory


def resolve_output_dir() -> str:
    """Restituisce una cartella di output scrivibile, con fallback robusti.

    Ordine di preferenza:
      1. Variabile d'ambiente AGENDA_SMART_OUTPUT_DIR (se impostata)
      2. /mnt/user-data/outputs  (cartella download standard di Claude)
      3. Cartella di lavoro corrente
      4. Cartella temporanea di sistema (ultima spiaggia)

    La cartella scelta viene creata se non esiste. Evita gli errori di accesso
    quando le cartelle interne di Claude non sono disponibili o scrivibili.
    """
    candidates = []
    env_dir = os.environ.get("AGENDA_SMART_OUTPUT_DIR")
    if env_dir:
        candidates.append(env_dir)
    candidates.append("/mnt/user-data/outputs")
    candidates.append(os.getcwd())
    candidates.append(tempfile.gettempdir())

    for directory in candidates:
        try:
            os.makedirs(directory, exist_ok=True)
            if os.access(directory, os.W_OK):
                return directory
        except OSError:
            continue

    return tempfile.gettempdir()

class SmartTaskScheduler:
    """Scheduler intelligente per task con ottimizzazione Pomodoro"""
    
    def __init__(self):
        self.task_analyzer = TaskAnalyzer()
        
        # Fasce orarie ottimali per tipo di lavoro
        self.optimal_hours = {
            "intellettuale_alta": [(9, 12)],  # Mattino
            "creativo": [(9, 12), (16, 18)],  # Mattino e tardo pomeriggio
            "amministrativo": [(14, 16)],  # Primo pomeriggio
            "energia_alta": [(9, 11)],  # Prima mattina
            "routine": [(14, 18)],  # Pomeriggio
        }
    
    def suggest_slots(self, 
                     calendar_events: List[Dict],
                     tasks: List[Dict],
                     strategy: str = "deadline_priority") -> Dict:
        """
        Suggerisce slot ottimali per task considerando Pomodoro e difficoltà
        
        Args:
            calendar_events: Eventi già in calendario
            tasks: Task da schedulare
            strategy: Strategia prioritizzazione
            
        Returns:
            Dict con suggestions, unscheduled, summary
        """
        # Analizza task
        enriched_tasks = []
        for task in tasks:
            enriched = self._enrich_task(task)
            enriched_tasks.append(enriched)
        
        # Prioritizza task secondo strategia
        prioritized_tasks = self._prioritize_tasks(enriched_tasks, strategy)
        
        # Trova slot liberi nel calendario
        free_slots = self._find_free_slots(calendar_events)
        
        # Schedula task negli slot ottimali
        suggestions = []
        unscheduled = []
        
        for task in prioritized_tasks:
            slot = self._find_best_slot_for_task(task, free_slots, calendar_events)
            
            if slot:
                suggestion = self._create_suggestion(task, slot)
                suggestions.append(suggestion)
                
                # Rimuovi slot utilizzato
                free_slots = self._remove_used_slot(free_slots, slot, task)
            else:
                unscheduled.append({
                    "task": task,
                    "reason": self._determine_unscheduled_reason(task, free_slots)
                })
        
        # Genera summary
        summary = self._generate_summary(suggestions, unscheduled, enriched_tasks)
        
        return {
            "suggestions": suggestions,
            "unscheduled": unscheduled,
            "summary": summary
        }
    
    def _enrich_task(self, task: Dict) -> Dict:
        """Arricchisce task con analisi difficoltà e Pomodoro"""
        task_name = task.get("name", "Task")
        task_description = task.get("description", "")
        duration_minutes = task.get("duration_minutes", 30)
        
        # Analizza difficoltà
        difficulty = self.task_analyzer.analyze_difficulty(task_name, task_description)
        
        # Calcola Pomodoro
        pomodoro = self.task_analyzer.calculate_pomodoro_blocks(duration_minutes)
        
        # Determina categoria se non presente
        if "category" not in task:
            category = self.task_analyzer.categorize_task(task_name, task_description)
            task["category"] = category.name.lower()
        
        # Calcola durata effettiva con buffer e pause Pomodoro
        effective_duration = pomodoro["total_time_with_breaks"] + difficulty["buffer_minutes"]
        
        # Arricchisci task
        task["difficulty_analysis"] = difficulty
        task["pomodoro_info"] = pomodoro
        task["effective_duration_minutes"] = effective_duration
        
        return task
    
    def _prioritize_tasks(self, tasks: List[Dict], strategy: str) -> List[Dict]:
        """Prioritizza task secondo strategia"""
        from datetime import timezone
        
        # datetime.max con timezone
        max_datetime = datetime.max.replace(tzinfo=timezone.utc)
        
        if strategy == "deadline_priority":
            # Ordina per deadline (imminente prima)
            return sorted(tasks, key=lambda t: (
                datetime.fromisoformat(t["deadline"].replace("Z", "+00:00")) if "deadline" in t else max_datetime,
                -t.get("priority", 0)
            ))
        
        elif strategy == "priority_first":
            # Ordina per priorità
            return sorted(tasks, key=lambda t: (
                -t.get("priority", 0),
                datetime.fromisoformat(t["deadline"].replace("Z", "+00:00")) if "deadline" in t else max_datetime
            ))
        
        elif strategy == "longest_first":
            # Ordina per durata (più lungo prima)
            return sorted(tasks, key=lambda t: -t["effective_duration_minutes"])
        
        else:  # balanced
            # Mix: considera deadline, priorità e durata
            return sorted(tasks, key=lambda t: (
                datetime.fromisoformat(t["deadline"].replace("Z", "+00:00")) if "deadline" in t else max_datetime,
                -t.get("priority", 0),
                -t["effective_duration_minutes"]
            ))
    
    def _find_free_slots(self, calendar_events: List[Dict]) -> List[Dict]:
        """Trova slot liberi nel calendario"""
        # Definisci orari lavorativi (9-18 di default)
        work_start = 9
        work_end = 18
        
        # Raggruppa eventi per giorno
        events_by_day = {}
        for event in calendar_events:
            if "start" not in event:
                continue
            
            start_dt = datetime.fromisoformat(event["start"].replace("Z", "+00:00"))
            date_key = start_dt.date()
            
            if date_key not in events_by_day:
                events_by_day[date_key] = []
            
            events_by_day[date_key].append(event)
        
        # Trova slot liberi
        free_slots = []
        
        # Considera oggi + prossimi 14 giorni
        today = datetime.now()
        for day_offset in range(15):
            current_day = (today + timedelta(days=day_offset)).date()
            
            # Skip weekend (opzionale - può essere configurato)
            if current_day.weekday() >= 5:  # Sabato/Domenica
                continue
            
            day_events = events_by_day.get(current_day, [])
            
            # Trova gaps tra eventi
            day_start = datetime.combine(current_day, datetime.min.time().replace(hour=work_start))
            day_end = datetime.combine(current_day, datetime.min.time().replace(hour=work_end))
            
            if not day_events:
                # Giorno completamente libero
                free_slots.append({
                    "start": day_start,
                    "end": day_end,
                    "duration_minutes": (day_end - day_start).total_seconds() / 60
                })
            else:
                # Trova gaps tra eventi
                sorted_events = sorted(day_events, key=lambda e: e.get("start", ""))
                
                # Gap prima del primo evento
                first_event_start = datetime.fromisoformat(sorted_events[0]["start"].replace("Z", "+00:00"))
                if day_start < first_event_start:
                    gap_duration = (first_event_start - day_start).total_seconds() / 60
                    if gap_duration >= 25:  # Almeno un Pomodoro
                        free_slots.append({
                            "start": day_start,
                            "end": first_event_start,
                            "duration_minutes": gap_duration
                        })
                
                # Gaps tra eventi
                for i in range(len(sorted_events) - 1):
                    current_end = datetime.fromisoformat(sorted_events[i]["end"].replace("Z", "+00:00"))
                    next_start = datetime.fromisoformat(sorted_events[i + 1]["start"].replace("Z", "+00:00"))
                    
                    gap_duration = (next_start - current_end).total_seconds() / 60
                    if gap_duration >= 25:  # Almeno un Pomodoro
                        free_slots.append({
                            "start": current_end,
                            "end": next_start,
                            "duration_minutes": gap_duration
                        })
                
                # Gap dopo ultimo evento
                last_event_end = datetime.fromisoformat(sorted_events[-1]["end"].replace("Z", "+00:00"))
                if last_event_end < day_end:
                    gap_duration = (day_end - last_event_end).total_seconds() / 60
                    if gap_duration >= 25:
                        free_slots.append({
                            "start": last_event_end,
                            "end": day_end,
                            "duration_minutes": gap_duration
                        })
        
        return free_slots
    
    def _find_best_slot_for_task(self, task: Dict, free_slots: List[Dict], calendar_events: List[Dict]) -> Dict:
        """Trova slot ottimale per task considerando difficoltà e orari"""
        difficulty = task["difficulty_analysis"]
        duration_needed = task["effective_duration_minutes"]
        
        # Filtra slot abbastanza lunghi
        suitable_slots = [s for s in free_slots if s["duration_minutes"] >= duration_needed]
        
        if not suitable_slots:
            return None
        
        # Determina tipo di lavoro per orari ottimali
        work_type = None
        if difficulty["difficulty_intellectual"] == "alta":
            work_type = "intellettuale_alta"
        elif task.get("category") == "benessere":
            work_type = "energia_alta"
        elif task.get("category") in ["lavoro", "progetti"]:
            work_type = "creativo"
        else:
            work_type = "routine"
        
        # Trova slot in orari ottimali
        optimal_slots = []
        for slot in suitable_slots:
            slot_hour = slot["start"].hour
            
            # Verifica se slot è in fascia ottimale
            is_optimal = False
            if work_type in self.optimal_hours:
                for start_hour, end_hour in self.optimal_hours[work_type]:
                    if start_hour <= slot_hour < end_hour:
                        is_optimal = True
                        break
            
            if is_optimal:
                optimal_slots.append(slot)
        
        # Se ci sono slot ottimali, usa quelli; altrimenti usa qualsiasi slot adatto
        candidate_slots = optimal_slots if optimal_slots else suitable_slots
        
        # Preferisci slot mattutini per task intellettuali alti
        if difficulty["difficulty_intellectual"] == "alta":
            candidate_slots = sorted(candidate_slots, key=lambda s: s["start"].hour)
        
        # Preferisci slot pomeridiani per task amministrativi
        elif work_type == "routine":
            candidate_slots = sorted(candidate_slots, key=lambda s: -s["start"].hour)
        
        # Prendi il primo slot ottimale
        return candidate_slots[0] if candidate_slots else None
    
    def _create_suggestion(self, task: Dict, slot: Dict) -> Dict:
        """Crea suggerimento dettagliato"""
        start_time = slot["start"]
        duration = task["effective_duration_minutes"]
        end_time = start_time + timedelta(minutes=duration)
        
        # Genera reasoning
        reasoning_parts = []
        
        # Deadline reasoning
        if "deadline" in task:
            deadline_dt = datetime.fromisoformat(task["deadline"].replace("Z", "+00:00"))
            days_to_deadline = (deadline_dt - start_time).days
            reasoning_parts.append(f"Deadline tra {days_to_deadline} giorni")
        
        # Difficoltà reasoning
        difficulty = task["difficulty_analysis"]
        if difficulty["difficulty_intellectual"] == "alta":
            reasoning_parts.append("Richiede alta concentrazione → schedulato in orario ottimale")
        if difficulty["difficulty_physical"] == "alta":
            reasoning_parts.append("Attività fisica intensa → buffer aggiuntivo incluso")
        
        # Energia reasoning
        if difficulty["energy_impact"] == "draining":
            reasoning_parts.append("Attività drenante → evitato accumulo con altre simili")
        elif difficulty["energy_impact"] == "energizing":
            reasoning_parts.append("Attività energizzante → ottima per momentum")
        
        # Pomodoro reasoning
        pomodoro = task["pomodoro_info"]
        reasoning_parts.append(f"Strutturato in {pomodoro['pomodoros']} Pomodori da 25 min con pause strategiche")
        
        reasoning = " | ".join(reasoning_parts)
        
        return {
            "name": task.get("name"),
            "description": task.get("description", ""),
            "category": task.get("category"),
            "suggested_start": start_time.isoformat(),
            "suggested_end": end_time.isoformat(),
            "duration_minutes": task.get("duration_minutes"),
            "effective_duration_minutes": duration,
            "reasoning": reasoning,
            "difficulty_physical": difficulty["difficulty_physical"],
            "difficulty_intellectual": difficulty["difficulty_intellectual"],
            "energy_impact": difficulty["energy_impact"],
            "pomodoro_blocks": pomodoro["pomodoros"],
            "buffer_minutes": difficulty["buffer_minutes"],
            "priority": task.get("priority", 0),
            "deadline": task.get("deadline") if "deadline" in task else None,
        }
    
    def _remove_used_slot(self, free_slots: List[Dict], used_slot: Dict, task: Dict) -> List[Dict]:
        """Rimuove slot utilizzato dalla lista"""
        new_slots = []
        
        for slot in free_slots:
            if slot == used_slot:
                # Slot utilizzato: calcola eventuali frammenti rimasti
                task_end = used_slot["start"] + timedelta(minutes=task["effective_duration_minutes"])
                
                if task_end < slot["end"]:
                    # C'è spazio dopo il task
                    remaining_duration = (slot["end"] - task_end).total_seconds() / 60
                    if remaining_duration >= 25:  # Almeno un Pomodoro
                        new_slots.append({
                            "start": task_end,
                            "end": slot["end"],
                            "duration_minutes": remaining_duration
                        })
            else:
                new_slots.append(slot)
        
        return new_slots
    
    def _determine_unscheduled_reason(self, task: Dict, free_slots: List[Dict]) -> str:
        """Determina perché un task non è stato schedulato"""
        duration_needed = task["effective_duration_minutes"]
        
        if not free_slots:
            return "Nessuno slot libero disponibile nel periodo considerato"
        
        max_slot_duration = max([s["duration_minutes"] for s in free_slots])
        
        if max_slot_duration < duration_needed:
            return f"Task richiede {duration_needed} min ma lo slot più lungo disponibile è {int(max_slot_duration)} min"
        
        return "Nessuno slot ottimale trovato per tipo e difficoltà task"
    
    def _generate_summary(self, suggestions: List[Dict], unscheduled: List[Dict], all_tasks: List[Dict]) -> Dict:
        """Genera summary dei risultati"""
        total_scheduled_minutes = sum([s["effective_duration_minutes"] for s in suggestions])
        
        # Conta per categoria
        category_breakdown = {}
        for s in suggestions:
            cat = s["category"]
            if cat not in category_breakdown:
                category_breakdown[cat] = 0
            category_breakdown[cat] += 1
        
        # Conta per difficoltà intellettuale
        difficulty_breakdown = {
            "alta": len([s for s in suggestions if s["difficulty_intellectual"] == "alta"]),
            "media": len([s for s in suggestions if s["difficulty_intellectual"] == "media"]),
            "bassa": len([s for s in suggestions if s["difficulty_intellectual"] == "bassa"]),
        }
        
        # Conta Pomodori totali
        total_pomodoros = sum([s["pomodoro_blocks"] for s in suggestions])
        
        return {
            "total_tasks": len(all_tasks),
            "scheduled": len(suggestions),
            "unscheduled": len(unscheduled),
            "total_scheduled_minutes": total_scheduled_minutes,
            "total_pomodoros": total_pomodoros,
            "category_breakdown": category_breakdown,
            "difficulty_breakdown": difficulty_breakdown,
            "average_buffer_minutes": sum([s["buffer_minutes"] for s in suggestions]) / len(suggestions) if suggestions else 0
        }


def main():
    """Funzione principale"""
    if len(sys.argv) < 3:
        print("Uso: python suggest_task_slots_enhanced.py <calendar_events.json> <tasks.json> [strategy]")
        print("Strategie: deadline_priority, priority_first, longest_first, balanced")
        sys.exit(1)
    
    events_file = sys.argv[1]
    tasks_file = sys.argv[2]
    strategy = sys.argv[3] if len(sys.argv) > 3 else "deadline_priority"
    
    # Carica dati
    with open(events_file, 'r', encoding='utf-8') as f:
        events = json.load(f)
    
    with open(tasks_file, 'r', encoding='utf-8') as f:
        tasks = json.load(f)
    
    # Schedula
    scheduler = SmartTaskScheduler()
    result = scheduler.suggest_slots(events, tasks, strategy)
    
    # Salva risultato in una cartella scrivibile (con creazione e fallback)
    output_path = os.path.join(resolve_output_dir(), "task_suggestions_enhanced.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"✅ Suggerimenti generati: {output_path}")
    print(f"\n📊 **SUMMARY**")
    print(f"   Task totali: {result['summary']['total_tasks']}")
    print(f"   Schedulati: {result['summary']['scheduled']}")
    print(f"   Non schedulati: {result['summary']['unscheduled']}")
    print(f"   Tempo totale: {result['summary']['total_scheduled_minutes']} min")
    print(f"   🍅 Pomodori totali: {result['summary']['total_pomodoros']}")
    print(f"   Buffer medio: {result['summary']['average_buffer_minutes']:.0f} min")
    
    print(f"\n📂 **Per Categoria:**")
    for cat, count in result['summary']['category_breakdown'].items():
        print(f"   {cat}: {count}")
    
    print(f"\n🎓 **Per Difficoltà Intellettuale:**")
    for diff, count in result['summary']['difficulty_breakdown'].items():
        print(f"   {diff}: {count}")
    
    if result['unscheduled']:
        print(f"\n⚠️ **Task Non Schedulati:**")
        for item in result['unscheduled']:
            print(f"   • {item['task']['name']}: {item['reason']}")


if __name__ == "__main__":
    main()
