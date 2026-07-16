#!/usr/bin/env python3
"""
Script per gestione categorie task e analisi difficoltà
"""

import json
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from enum import Enum

class TaskCategory(Enum):
    """Categorie task disponibili"""
    LAVORO = "💼 Lavoro"
    PERSONALE = "🏠 Personale"
    PROGETTI = "🎯 Progetti"
    URGENTE = "🚨 Urgente"
    FORMAZIONE = "🎓 Formazione"
    BENESSERE = "💪 Benessere"

class DifficultyLevel(Enum):
    """Livelli di difficoltà"""
    BASSA = "bassa"
    MEDIA = "media"
    ALTA = "alta"

class TaskAnalyzer:
    """Analizza task per difficoltà e raccomandazioni"""
    
    # Mapping keywords → difficoltà fisica
    PHYSICAL_KEYWORDS = {
        "alta": ["spostare", "sistemare", "pulire", "organizzare fisicamente", 
                "archivio", "trasloco", "montare", "installare", "riparare"],
        "media": ["incontrare", "visita", "consegna", "ritiro", "spesa"],
        "bassa": ["email", "chiamata", "videocall", "scrivere", "leggere", 
                 "analizzare", "pianificare", "report"]
    }
    
    # Mapping keywords → difficoltà intellettuale
    INTELLECTUAL_KEYWORDS = {
        "alta": ["strategia", "analisi complessa", "report", "presentazione", 
                "pianificazione", "budget", "forecast", "progettare", "problem solving",
                "coding", "programmazione", "studio", "ricerca"],
        "media": ["riunione", "meeting", "coordinamento", "revisione", "feedback",
                 "brainstorming", "discussione"],
        "bassa": ["email routine", "archiviazione", "data entry", "upload",
                 "organizzazione semplice", "checklist"]
    }
    
    # Attività che danno energia vs drenano
    ENERGY_MAPPING = {
        "energizing": ["brainstorming", "creativo", "sport", "hobby", "networking",
                      "mentoring", "insegnare", "presentare"],
        "draining": ["email", "burocrazia", "amministrativo", "chiamate difficili",
                    "conflitti", "multitasking", "interruzioni continue"]
    }
    
    def __init__(self):
        self.home_address = "Via Alessandro Manzoni 60, Taverna di Montalto Uffugo (CS)"
    
    def analyze_difficulty(self, task_name: str, task_description: str = "") -> Dict:
        """
        Analizza la difficoltà fisica e intellettuale di un task
        
        Args:
            task_name: Nome del task
            task_description: Descrizione dettagliata (opzionale)
            
        Returns:
            Dict con analisi difficoltà e raccomandazioni
        """
        text = f"{task_name} {task_description}".lower()
        
        # Analizza difficoltà fisica
        physical_score = 0
        for keyword in self.PHYSICAL_KEYWORDS["alta"]:
            if keyword in text:
                physical_score += 3
        for keyword in self.PHYSICAL_KEYWORDS["media"]:
            if keyword in text:
                physical_score += 2
        for keyword in self.PHYSICAL_KEYWORDS["bassa"]:
            if keyword in text:
                physical_score += 1
        
        if physical_score >= 3:
            difficulty_physical = DifficultyLevel.ALTA.value
        elif physical_score >= 1:
            difficulty_physical = DifficultyLevel.MEDIA.value
        else:
            difficulty_physical = DifficultyLevel.BASSA.value
        
        # Analizza difficoltà intellettuale
        intellectual_score = 0
        for keyword in self.INTELLECTUAL_KEYWORDS["alta"]:
            if keyword in text:
                intellectual_score += 3
        for keyword in self.INTELLECTUAL_KEYWORDS["media"]:
            if keyword in text:
                intellectual_score += 2
        for keyword in self.INTELLECTUAL_KEYWORDS["bassa"]:
            if keyword in text:
                intellectual_score += 1
        
        if intellectual_score >= 3:
            difficulty_intellectual = DifficultyLevel.ALTA.value
        elif intellectual_score >= 1:
            difficulty_intellectual = DifficultyLevel.MEDIA.value
        else:
            difficulty_intellectual = DifficultyLevel.BASSA.value
        
        # Analizza impatto energia
        energy_impact = "neutral"
        for keyword in self.ENERGY_MAPPING["energizing"]:
            if keyword in text:
                energy_impact = "energizing"
                break
        for keyword in self.ENERGY_MAPPING["draining"]:
            if keyword in text:
                energy_impact = "draining"
                break
        
        # Calcola buffer raccomandato (minuti)
        buffer_minutes = 10  # base
        if difficulty_physical == "alta":
            buffer_minutes += 10
        if difficulty_intellectual == "alta":
            buffer_minutes += 10
        if energy_impact == "draining":
            buffer_minutes += 5
        
        # Raccomandazioni orarie
        time_recommendations = []
        if difficulty_intellectual == "alta":
            time_recommendations.append("Mattino (9-12): massima concentrazione")
        if difficulty_physical == "alta":
            time_recommendations.append("Quando hai maggiore energia fisica")
        if energy_impact == "draining":
            time_recommendations.append("Evita di accumulare troppe attività drenanti consecutive")
        
        return {
            "difficulty_physical": difficulty_physical,
            "difficulty_intellectual": difficulty_intellectual,
            "energy_impact": energy_impact,
            "buffer_minutes": buffer_minutes,
            "time_recommendations": time_recommendations,
            "analysis": {
                "physical_score": physical_score,
                "intellectual_score": intellectual_score
            }
        }
    
    def categorize_task(self, task_name: str, task_description: str = "") -> TaskCategory:
        """
        Suggerisce una categoria per il task basandosi sul contenuto
        
        Args:
            task_name: Nome del task
            task_description: Descrizione (opzionale)
            
        Returns:
            TaskCategory suggerita
        """
        text = f"{task_name} {task_description}".lower()
        
        # Keywords per categoria
        if any(kw in text for kw in ["urgente", "asap", "immediato", "critico", "emergenza"]):
            return TaskCategory.URGENTE
        
        if any(kw in text for kw in ["corso", "studio", "imparare", "formazione", "training"]):
            return TaskCategory.FORMAZIONE
        
        if any(kw in text for kw in ["sport", "palestra", "yoga", "salute", "medico", "benessere"]):
            return TaskCategory.BENESSERE
        
        if any(kw in text for kw in ["progetto", "sviluppo", "implementare", "strategia", "piano"]):
            return TaskCategory.PROGETTI
        
        if any(kw in text for kw in ["famiglia", "casa", "personale", "privato", "hobby"]):
            return TaskCategory.PERSONALE
        
        # Default: lavoro
        return TaskCategory.LAVORO
    
    def calculate_pomodoro_blocks(self, duration_minutes: int) -> Dict:
        """
        Calcola numero di blocchi Pomodoro (25 min) necessari
        
        Args:
            duration_minutes: Durata totale stimata
            
        Returns:
            Dict con breakdown Pomodoro
        """
        # Un blocco Pomodoro completo = 25 min lavoro + 5 min pausa
        full_pomodoro = 30
        
        # Calcola blocchi necessari
        num_pomodoros = duration_minutes // 25
        remainder = duration_minutes % 25
        
        # Aggiungi un blocco se c'è resto > 10 minuti
        if remainder >= 10:
            num_pomodoros += 1
        
        # Calcola pause
        short_breaks = num_pomodoros - 1 if num_pomodoros > 1 else 0
        long_breaks = (num_pomodoros - 1) // 4  # Ogni 4 pomodori, pausa lunga
        
        total_time_with_breaks = (num_pomodoros * 25) + (short_breaks * 5) + (long_breaks * 15)
        
        return {
            "pomodoros": num_pomodoros,
            "work_time": num_pomodoros * 25,
            "short_breaks": short_breaks,
            "long_breaks": long_breaks,
            "total_time_with_breaks": total_time_with_breaks,
            "schedule": self._generate_pomodoro_schedule(num_pomodoros)
        }
    
    def _generate_pomodoro_schedule(self, num_pomodoros: int) -> List[str]:
        """Genera schedule dettagliato dei Pomodoro"""
        schedule = []
        for i in range(1, num_pomodoros + 1):
            schedule.append(f"🍅 Pomodoro {i}: 25 min focus")
            if i < num_pomodoros:
                if i % 4 == 0:
                    schedule.append(f"☕ Pausa lunga: 15-20 min")
                else:
                    schedule.append(f"⏸️ Pausa breve: 5 min")
        return schedule
    
    def analyze_weekly_patterns(self, events: List[Dict]) -> Dict:
        """
        Identifica pattern negativi ricorrenti nella settimana
        
        Args:
            events: Lista eventi calendario
            
        Returns:
            Dict con pattern identificati
        """
        patterns = {
            "overloaded_days": [],
            "energy_draining_sequence": False,
            "no_breaks_pattern": False,
            "good_balance": False
        }
        
        # Raggruppa eventi per giorno della settimana
        days_load = {}
        for event in events:
            if "start" not in event:
                continue
            
            start_dt = datetime.fromisoformat(event["start"].replace("Z", "+00:00"))
            day_name = start_dt.strftime("%A")  # Nome giorno
            
            if day_name not in days_load:
                days_load[day_name] = {"events": 0, "hours": 0}
            
            days_load[day_name]["events"] += 1
            
            # Calcola durata
            if "end" in event:
                end_dt = datetime.fromisoformat(event["end"].replace("Z", "+00:00"))
                duration_hours = (end_dt - start_dt).total_seconds() / 3600
                days_load[day_name]["hours"] += duration_hours
        
        # Identifica giorni sovraccarichi (>8 ore o >6 eventi)
        for day, load in days_load.items():
            if load["hours"] > 8 or load["events"] > 6:
                patterns["overloaded_days"].append(day)
        
        # Verifica sequenze drenanti
        draining_count = 0
        for event in sorted(events, key=lambda e: e.get("start", "")):
            if "draining" in event.get("summary", "").lower():
                draining_count += 1
                if draining_count >= 3:
                    patterns["energy_draining_sequence"] = True
                    break
            else:
                draining_count = 0
        
        # Verifica pause insufficienti
        sorted_events = sorted(events, key=lambda e: e.get("start", ""))
        for i in range(len(sorted_events) - 1):
            current_end = sorted_events[i].get("end")
            next_start = sorted_events[i + 1].get("start")
            
            if current_end and next_start:
                end_dt = datetime.fromisoformat(current_end.replace("Z", "+00:00"))
                start_dt = datetime.fromisoformat(next_start.replace("Z", "+00:00"))
                gap_minutes = (start_dt - end_dt).total_seconds() / 60
                
                if gap_minutes < 10:  # Meno di 10 minuti di pausa
                    patterns["no_breaks_pattern"] = True
                    break
        
        # Valuta se bilanciamento è buono
        if not patterns["overloaded_days"] and not patterns["energy_draining_sequence"] and not patterns["no_breaks_pattern"]:
            patterns["good_balance"] = True
        
        return patterns


def main():
    """Test del task analyzer"""
    analyzer = TaskAnalyzer()
    
    # Test 1: Analisi difficoltà
    print("=" * 60)
    print("TEST 1: Analisi difficoltà task")
    print("=" * 60)
    
    tasks = [
        ("Scrivere report Q4", "Analisi finanziaria completa con forecast"),
        ("Sistemare archivio ufficio", "Riorganizzazione fisica documenti"),
        ("Rispondere a email", "Email routine giornaliere"),
        ("Presentazione strategia 2025", "Preparare slides e speech per board"),
    ]
    
    for task_name, task_desc in tasks:
        result = analyzer.analyze_difficulty(task_name, task_desc)
        print(f"\n📋 {task_name}")
        print(f"   Difficoltà Fisica: {result['difficulty_physical']}")
        print(f"   Difficoltà Intellettuale: {result['difficulty_intellectual']}")
        print(f"   Impatto Energia: {result['energy_impact']}")
        print(f"   Buffer raccomandato: {result['buffer_minutes']} minuti")
        if result['time_recommendations']:
            print(f"   Raccomandazioni orarie:")
            for rec in result['time_recommendations']:
                print(f"      - {rec}")
    
    # Test 2: Categorizzazione
    print("\n" + "=" * 60)
    print("TEST 2: Categorizzazione task")
    print("=" * 60)
    
    for task_name, task_desc in tasks:
        category = analyzer.categorize_task(task_name, task_desc)
        print(f"\n{task_name} → {category.value}")
    
    # Test 3: Calcolo Pomodoro
    print("\n" + "=" * 60)
    print("TEST 3: Breakdown Pomodoro")
    print("=" * 60)
    
    durations = [30, 60, 90, 120]
    for duration in durations:
        result = analyzer.calculate_pomodoro_blocks(duration)
        print(f"\n⏱️ Task da {duration} minuti:")
        print(f"   Pomodori necessari: {result['pomodoros']} 🍅")
        print(f"   Tempo totale con pause: {result['total_time_with_breaks']} min")
        print(f"   Schedule:")
        for item in result['schedule']:
            print(f"      {item}")


if __name__ == "__main__":
    main()
