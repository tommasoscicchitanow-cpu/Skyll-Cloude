#!/usr/bin/env python3
"""
Script per generare frasi anti-sabotaggio personalizzate
Focus: procrastinazione e sottovalutazione del tempo
"""

import random
import json
from typing import Dict, List
from datetime import datetime, timedelta

class AntiSabotageGenerator:
    """Generatore di frasi motivazionali anti-sabotaggio"""
    
    # Pattern di sabotaggio da contrastare
    SABOTAGE_PATTERNS = {
        "procrastination": [
            "Il momento perfetto è adesso, non domani",
            "Ogni minuto speso a rimandare è un minuto perso per sempre",
            "Il primo passo è sempre il più potente",
            "L'azione imperfetta batte la perfezione immaginata",
            "Iniziare è vincere metà della battaglia",
            "Il tuo io futuro ti ringrazierà per aver iniziato ora",
            "Non aspettare l'ispirazione: l'ispirazione arriva facendo",
            "Cinque minuti di azione valgono più di ore di pianificazione",
        ],
        "time_underestimation": [
            "Questa attività richiede più tempo di quanto pensi: rispetta la stima",
            "Aggiungere buffer non è pessimismo, è realismo",
            "Il tempo corre più veloce quando sei concentrato: proteggilo",
            "Ogni task ha imprevisti: la stima include anche quelli",
            "Sottovalutare i tempi è il sabotaggio più comune: non caderci",
            "Questo blocco temporale è calibrato sulla realtà, non sull'ottimismo",
            "Il tempo è come lo spazio: si riempie sempre più del previsto",
            "Rispettare i tempi significa rispettare te stesso",
        ],
        "energy_management": [
            "Questa attività richiede la tua energia migliore: sei pronto",
            "Il tuo corpo e mente sono risorse: usale strategicamente",
            "Dopo questo task, prenditi una vera pausa: la meriti",
            "L'energia spesa ora verrà restituita con i risultati",
            "Non sei pigro, sei strategico: questa è la priorità ora",
            "La fatica è temporanea, i risultati permanenti",
            "Il tuo focus è il tuo superpotere: usalo adesso",
            "Sei nella fascia oraria ottimale: sfruttala al massimo",
        ],
        "perfectionism": [
            "Fatto è meglio che perfetto",
            "La perfezione è nemica del progresso",
            "Inizia con una versione 0.1, migliorai dopo",
            "Nessuno giudica la tua prima bozza: inizia",
            "Il perfezionismo è procrastinazione sotto mentite spoglie",
            "Obiettivo: completamento, non perfezione",
            "Puoi sempre migliorare dopo: prima completa",
            "Il tuo 80% è il 100% di molti altri",
        ],
        "overwhelm": [
            "Un passo alla volta: il resto non esiste ancora",
            "Spezza il gigante in piccoli bocconi masticabili",
            "Non devi fare tutto ora, solo questo pezzo",
            "La montagna si scala un metro alla volta",
            "Concentrati solo sul prossimo 25 minuti",
            "L'unica cosa che conta ora è iniziare",
            "Grande o piccolo, ogni progresso è progresso",
            "Hai già fatto cose più difficili: ce la farai",
        ],
        "distraction": [
            "Le notifiche possono aspettare: tu no",
            "Questo momento è tuo: proteggilo dalle distrazioni",
            "Ogni interruzione costa 23 minuti di recupero: elimina le fonti",
            "Il multitasking è un mito: focus su uno",
            "Il tuo telefono non ha urgenze vere: tu hai obiettivi veri",
            "25 minuti di focus totale = 2 ore di lavoro distratto",
            "Silenzioso il mondo, massimizza il risultato",
            "Le distrazioni rubano i sogni: difendili",
        ]
    }
    
    # Frasi per celebrazioni (da usare dopo completamento)
    CELEBRATION_PHRASES = [
        "🎉 Task completato! Il tuo io futuro sta sorridendo",
        "✅ Grande lavoro! Hai battuto la procrastinazione",
        "🏆 Fatto! Ogni completamento è una vittoria",
        "⭐ Eccellente! Hai rispettato i tempi previsti",
        "🚀 Missione compiuta! Il momentum è dalla tua parte",
        "💪 Fantastico! Hai dimostrato disciplina",
        "🎯 Obiettivo centrato! Stai costruendo risultati",
        "🌟 Perfetto! Continua così e raggiungerai ogni traguardo",
        "👏 Bravo! Hai trasformato l'intenzione in azione",
        "🔥 Straordinario! La produttività è diventata un'abitudine",
    ]
    
    # Frasi pre-task per difficoltà specifiche
    DIFFICULTY_PHRASES = {
        "fisica_alta": [
            "Questa attività è fisicamente impegnativa: idratati e fai stretching prima",
            "Energia fisica richiesta: prepara il corpo prima di iniziare",
            "Task fisico intenso: riscaldamento + idratazione = successo",
        ],
        "intellettuale_alta": [
            "Sfida intellettuale: elimina ogni distrazione, serve massima concentrazione",
            "Questo richiede il tuo cervello al 100%: spegni notifiche e inizia",
            "Task complesso: respira profondo, focus totale, un passo alla volta",
        ],
        "fisica_media_intellettuale_alta": [
            "Impegno misto: mente lucida e corpo pronto, ce la farai",
            "Questa richiede equilibrio: concentrazione mentale + resistenza fisica",
        ],
        "back_to_back": [
            "⚠️ Task consecutivi: prevedi pause micro tra uno e l'altro",
            "Sessione intensa: ogni 50 minuti fermati 10 minuti per recuperare",
            "Marathon mode: idratazione frequente + pause strategiche",
        ]
    }
    
    def generate_phrase(self, 
                       task_name: str,
                       category: str = "general",
                       difficulty_physical: str = "media",
                       difficulty_intellectual: str = "media",
                       is_deadline_close: bool = False,
                       is_back_to_back: bool = False,
                       time_estimate_minutes: int = 30) -> Dict:
        """
        Genera una frase anti-sabotaggio personalizzata
        
        Args:
            task_name: Nome del task
            category: Categoria task (lavoro, personale, etc.)
            difficulty_physical: bassa/media/alta
            difficulty_intellectual: bassa/media/alta  
            is_deadline_close: Se la deadline è vicina (< 2 giorni)
            is_back_to_back: Se il task è seguito da altro senza pause
            time_estimate_minutes: Durata stimata in minuti
            
        Returns:
            Dict con frasi per diverse situazioni
        """
        
        phrases = {}
        
        # Frase principale anti-procrastinazione
        phrases["main"] = random.choice(self.SABOTAGE_PATTERNS["procrastination"])
        
        # Frase gestione tempo (sempre presente per contrastare sottovalutazione)
        phrases["time_management"] = random.choice(self.SABOTAGE_PATTERNS["time_underestimation"])
        
        # Frase basata su difficoltà
        if difficulty_physical == "alta" and difficulty_intellectual == "alta":
            difficulty_key = "fisica_media_intellettuale_alta"
        elif difficulty_physical == "alta":
            difficulty_key = "fisica_alta"
        elif difficulty_intellectual == "alta":
            difficulty_key = "intellettuale_alta"
        else:
            difficulty_key = None
            
        if difficulty_key and difficulty_key in self.DIFFICULTY_PHRASES:
            phrases["difficulty"] = random.choice(self.DIFFICULTY_PHRASES[difficulty_key])
        
        # Frase energia
        phrases["energy"] = random.choice(self.SABOTAGE_PATTERNS["energy_management"])
        
        # Se deadline vicina, aggiungi urgenza controllata
        if is_deadline_close:
            phrases["urgency"] = "⏰ Deadline vicina: questo è il momento di agire, non di rimandare"
        
        # Se back-to-back, avvisa
        if is_back_to_back:
            phrases["back_to_back"] = random.choice(self.DIFFICULTY_PHRASES["back_to_back"])
        
        # Se task lungo (>45 min), aggiungi gestione overwhelm
        if time_estimate_minutes > 45:
            phrases["overwhelm"] = random.choice(self.SABOTAGE_PATTERNS["overwhelm"])
        
        # Frase anti-distrazione (sempre utile)
        phrases["focus"] = random.choice(self.SABOTAGE_PATTERNS["distraction"])
        
        # Celebrazione da usare dopo
        phrases["celebration"] = random.choice(self.CELEBRATION_PHRASES)
        
        # Componi messaggio finale per descrizione evento
        description_parts = [
            f"🎯 **{task_name}**",
            "",
            f"💪 {phrases['main']}",
            f"⏱️ {phrases['time_management']}",
        ]
        
        if "difficulty" in phrases:
            description_parts.append(f"🎓 {phrases['difficulty']}")
            
        description_parts.append(f"⚡ {phrases['energy']}")
        description_parts.append(f"🔔 {phrases['focus']}")
        
        if "urgency" in phrases:
            description_parts.append(f"{phrases['urgency']}")
            
        if "overwhelm" in phrases:
            description_parts.append(f"🧭 {phrases['overwhelm']}")
            
        if "back_to_back" in phrases:
            description_parts.append(f"{phrases['back_to_back']}")
        
        description_parts.extend([
            "",
            "---",
            f"✨ Dopo il completamento: {phrases['celebration']}",
        ])
        
        phrases["full_description"] = "\n".join(description_parts)
        
        return phrases
    
    def generate_weekly_pattern_message(self, pattern_analysis: Dict) -> str:
        """
        Genera messaggio basato su pattern settimanali identificati
        
        Args:
            pattern_analysis: Dict con pattern identificati
            
        Returns:
            Messaggio motivazionale personalizzato
        """
        messages = []
        
        if pattern_analysis.get("overloaded_days"):
            days_str = ", ".join(pattern_analysis["overloaded_days"])
            messages.append(
                f"⚠️ **Pattern rilevato**: {days_str} tendono ad essere sovraccarichi. "
                f"Considera di spostare attività non urgenti in altri giorni."
            )
        
        if pattern_analysis.get("energy_draining_sequence"):
            messages.append(
                "🔋 **Attenzione energia**: Hai troppi task drenanti consecutivi. "
                "Alterna con attività che ti ricaricano per mantenere il momentum."
            )
        
        if pattern_analysis.get("no_breaks_pattern"):
            messages.append(
                "🧘 **Pause insufficienti**: Stai schedulando troppe attività back-to-back. "
                "Il tuo cervello ha bisogno di micro-pause per mantenere performance ottimali."
            )
        
        if pattern_analysis.get("good_balance"):
            messages.append(
                "✅ **Ottimo bilanciamento**: La tua settimana è ben strutturata. "
                "Continua così e raggiungerai i tuoi obiettivi con energia da vendere!"
            )
        
        return "\n\n".join(messages) if messages else "Settimana analizzata: nessun pattern critico rilevato."


def main():
    """Test del generatore"""
    generator = AntiSabotageGenerator()
    
    # Test 1: Task normale
    print("=" * 60)
    print("TEST 1: Task normale")
    print("=" * 60)
    result = generator.generate_phrase(
        task_name="Scrivere report Q4",
        category="lavoro",
        difficulty_intellectual="alta",
        time_estimate_minutes=90
    )
    print(result["full_description"])
    print()
    
    # Test 2: Task con deadline vicina
    print("=" * 60)
    print("TEST 2: Task con deadline imminente")
    print("=" * 60)
    result = generator.generate_phrase(
        task_name="Preparare presentazione cliente",
        category="lavoro",
        difficulty_intellectual="alta",
        is_deadline_close=True,
        time_estimate_minutes=60
    )
    print(result["full_description"])
    print()
    
    # Test 3: Task fisico
    print("=" * 60)
    print("TEST 3: Task fisico impegnativo")
    print("=" * 60)
    result = generator.generate_phrase(
        task_name="Sistemare archivio ufficio",
        category="personale",
        difficulty_physical="alta",
        time_estimate_minutes=120
    )
    print(result["full_description"])
    print()
    
    # Test 4: Pattern settimanale
    print("=" * 60)
    print("TEST 4: Analisi pattern settimanale")
    print("=" * 60)
    pattern_analysis = {
        "overloaded_days": ["Martedì", "Giovedì"],
        "energy_draining_sequence": True,
        "no_breaks_pattern": True
    }
    message = generator.generate_weekly_pattern_message(pattern_analysis)
    print(message)


if __name__ == "__main__":
    main()
