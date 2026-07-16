---
name: agenda-smart
description: Gestione intelligente dell'agenda personale con analisi delle distanze, rilevamento incongruenze, e suggerimenti automatici per schedulare task rispettando le deadline. Usa questa skill quando l'utente chiede di organizzare il calendario, trovare slot per task, verificare conflitti, calcolare tempi di spostamento, o ottimizzare la pianificazione settimanale.
---

# Agenda Smart - Gestione Intelligente Calendario 🧠⚡

Questa skill aiuta a gestire l'agenda personale in modo intelligente, considerando tempi di spostamento, deadline dei task, ottimizzazione del carico di lavoro, **e programmazione mentale positiva anti-sabotaggio**.

## 🆕 Funzionalità Avanzate (v2.0)

### Programmazione Mentale Anti-Sabotaggio
Ogni evento/task include **frasi personalizzate** che:
- Prevengono procrastinazione
- Contrastano sottovalutazione dei tempi
- Programmano il cervello al successo
- Eliminano autosabotaggio

### Indirizzo Base dell'Utente
**📍 Via Alessandro Manzoni 60, Taverna di Montalto Uffugo (CS)**
- Usato come origine per calcoli spostamenti
- Aggiornato automaticamente quando l'utente specifica location eventi

### Categorie Task
- 💼 Lavoro
- 🏠 Personale  
- 🎯 Progetti
- 🚨 Urgente
- 🎓 Formazione
- 💪 Benessere

### Analisi Difficoltà Attività
- **Fisica**: bassa/media/alta
- **Intellettuale**: bassa/media/alta
- **Buffer intelligenti** basati su difficoltà

### Deep Work Ottimizzato
- Blocchi da **25 minuti** (tecnica Pomodoro)
- Pause strategiche tra sessioni
- Massima produttività

### Pattern Recognition
- Identifica **ricorrenze negative** settimanali
- Suggerisce riorganizzazioni proattive

### Prioritizzazione Emotiva
- Valuta attività che **danno energia** vs **drenanti**
- Bilancia carico emotivo giornaliero

### Celebrazioni Micro
- **Rinforzo positivo** automatico per completamenti
- Messaggi motivazionali personalizzati

## Quando Usare Questa Skill

- Analizzare il calendario per rilevare incongruenze (sovrapposizioni, tempi di viaggio insufficienti, giorni sovraccarichi, pause insufficienti)
- Calcolare distanze e tempi di spostamento tra appuntamenti (da Via Alessandro Manzoni 60 come base)
- Suggerire quando lavorare su task specifici rispettando le deadline **in blocchi da 25 minuti**
- Trovare slot liberi ottimali per nuovi appuntamenti o task considerando **difficoltà fisica/intellettuale**
- Ottimizzare la pianificazione settimanale bilanciando impegni, lavoro e **energia emotiva**
- Generare **frasi anti-sabotaggio** personalizzate per ogni attività
- Identificare **pattern negativi ricorrenti** (es. "ogni martedì sei sovraccarico")
- Categorizzare e prioritizzare task per massima efficacia
- Programmare il cervello al successo con **celebrazioni micro**

## 🎯 Funzionalità Principali v2.0

### 1. Programmazione Mentale Anti-Sabotaggio

**NOVITÀ**: Ogni evento e task include frasi personalizzate che programmano il cervello al successo.

**Trigger**: Ogni volta che si creano eventi o si schedulano task.

**Script**: `scripts/anti_sabotage_phrases.py`

**Cosa Fa**:
- Genera frasi contro procrastinazione
- Contrasta sottovalutazione dei tempi
- Fornisce motivazione specifica per difficoltà task
- Include celebrazioni micro post-completamento

**Pattern Contrastati**:
- 🚫 Procrastinazione: "Il momento perfetto è adesso"
- 🚫 Sottovalutazione tempo: "Questo blocco è calibrato sulla realtà"
- 🚫 Perfezionismo: "Fatto è meglio che perfetto"
- 🚫 Overwhelm: "Un passo alla volta"
- 🚫 Distrazioni: "Ogni interruzione costa 23 minuti"

**Frasi Incluse in Ogni Evento**:
1. Frase anti-procrastinazione principale
2. Avviso gestione tempo realistica
3. Adattamento per difficoltà specifica
4. Reminder energia/focus
5. Celebrazione post-completamento

### 2. Analisi Difficoltà e Categorie Task

**Script**: `scripts/task_analyzer.py`

**Analisi Automatica**:

**Difficoltà Fisica**: bassa/media/alta
- Keywords rilevate: "spostare", "sistemare", "organizzare fisicamente"
- Buffer automatico: +10 min se alta

**Difficoltà Intellettuale**: bassa/media/alta  
- Keywords rilevate: "strategia", "analisi", "report", "presentazione"
- Orario ottimale: mattino (9-12) se alta
- Buffer automatico: +10 min se alta

**Impatto Energia**: energizing/neutral/draining
- Energizing: "creativo", "brainstorming", "networking"
- Draining: "email", "burocrazia", "amministrativo"
- Sistema bilancia carico emotivo giornaliero

**Categorie Automatiche**:
- 💼 Lavoro: task professionali standard
- 🏠 Personale: famiglia, casa, privato
- 🎯 Progetti: sviluppo, implementazione, strategia
- 🚨 Urgente: deadline immediata, critico
- 🎓 Formazione: studio, corsi, apprendimento
- 💪 Benessere: sport, salute, mindfulness

**Buffer Intelligenti**:
- Base: 10 minuti
- +10 min se fisica alta
- +10 min se intellettuale alta
- +5 min se drenante

### 3. Ottimizzazione Pomodoro (25 Minuti)

**NOVITÀ**: Ogni task viene strutturato in blocchi Pomodoro da 25 minuti.

**Calcolo Automatico**:
- Task 30 min → 1 Pomodoro (25 min lavoro)
- Task 60 min → 3 Pomodori (75 min con 2 pause da 5 min)
- Task 90 min → 4 Pomodori (100 min con 3 pause da 5 min)
- Task 120 min → 5 Pomodori (145 min con pause + 1 pausa lunga)

**Pause Automatiche**:
- Ogni Pomodoro: pausa 5 minuti
- Ogni 4 Pomodori: pausa lunga 15-20 minuti

**Schedule Dettagliato**:
Ogni evento ICS include breakdown completo:
```
🍅 Pomodoro 1: 25 min focus
⏸️ Pausa breve: 5 min
🍅 Pomodoro 2: 25 min focus
⏸️ Pausa breve: 5 min
🍅 Pomodoro 3: 25 min focus
```

**Vantaggi**:
- ✅ Massima produttività in sessioni brevi
- ✅ Previene burnout con pause strategiche
- ✅ Facilita deep work con timeboxing
- ✅ Compatibile con energie variabili

### 4. Pattern Recognition Settimanale

**NOVITÀ**: Identifica automaticamente ricorrenze negative.

**Pattern Rilevati**:

**Giorni Sovraccarichi**:
- Rileva giorni > 8 ore o > 6 eventi
- Identifica giorni ricorrenti (es. "ogni martedì")
- Suggerisce redistribuzione

**Sequenze Drenanti**:
- Rileva 3+ attività drenanti consecutive
- Avvisa rischio burnout
- Suggerisce inserimento attività energizzanti

**Pause Insufficienti**:
- Rileva eventi < 10 min di gap
- Avvisa back-to-back pericolosi
- Raccomanda buffer strategici

**Esempio Output**:
```
⚠️ Pattern rilevato: Martedì, Giovedì tendono ad essere sovraccarichi
🔋 Attenzione energia: Troppi task drenanti consecutivi
🧘 Pause insufficienti: Cervello necessita micro-pause
```

### 5. Analisi Incongruenze Calendario

**Trigger**: L'utente chiede di verificare il calendario, controllare conflitti, o rilevare problemi.

**Processo**:
1. Recuperare eventi calendario con `list_gcal_events` per il periodo richiesto
2. Se gli eventi includono location diverse, calcolare tempi di viaggio con `calculate_travel.py`
3. Eseguire `analyze_schedule.py` passando eventi e tempi di viaggio
4. Presentare risultati all'utente con priorità alle issue critiche

**Script**: `scripts/analyze_schedule.py`

**Input**: 
- File JSON con eventi calendario
- (Opzionale) File JSON con tempi di viaggio calcolati

**Output**: Report con:
- `overlaps`: sovrapposizioni temporali tra eventi
- `insufficient_travel`: tempo insufficiente per spostarsi tra location
- `back_to_back`: eventi consecutivi senza buffer
- `overbooked_days`: giorni con > 10 ore di impegni
- `long_days`: giorni con span > 12 ore (primo-ultimo evento)

**Comunicare all'utente**:
- Numero totale di problemi e breakdown per tipo
- Dettagli delle issue più critiche (overlaps, insufficient_travel)
- Suggerimenti pratici per risolvere

### 6. Calcolo Tempi di Spostamento (con Indirizzo Base)

**NOVITÀ**: Indirizzo base predefinito per calcoli automatici.

**Indirizzo Base Utente**: 📍 **Via Alessandro Manzoni 60, Taverna di Montalto Uffugo (CS)**

**Trigger**: Quando eventi hanno location diverse o utente chiede tempi spostamento.

**Processo**:
1. Usa indirizzo base come origine (se non specificato diversamente)
2. Calcola tempo per ogni destinazione
3. Include buffer traffico e parcheggio
4. Aggiorna automaticamente se utente specifica nuova location

**Script**: `scripts/calculate_travel.py`

**Parametri**:
- `origin`: indirizzo/luogo di partenza
- `destination`: indirizzo/luogo di arrivo  
- `departure_time`: (opzionale) orario partenza per stime traffico
- `api_key`: (opzionale) Google Maps API key

**Modalità**:
- **Con API key**: calcoli precisi tramite Google Maps Distance Matrix API
- **Senza API key**: stime manuali basate su distanza e tipo di percorso
  - Urbano: 40 km/h → 1 km = 1.5 min
  - Suburbano: 60 km/h → 1 km = 1 min
  - Autostrada: 90 km/h → 1 km = 0.7 min

**Best practice**:
- Aggiungere sempre 10-15 minuti buffer per parcheggio/imprevisti
- Considerare traffico in orari di punta (8-9, 13-14, 17-19)
- Per distanze > 30 km, preferire stime con traffic incluso

### 7. Suggerimenti Task Scheduling Intelligenti

**NOVITÀ**: Scheduler potenziato con Pomodoro, difficoltà e prioritizzazione emotiva.

**Trigger**: Utente chiede quando lavorare su task o come organizzare lavoro.

**Processo**:
1. Recuperare eventi calendario per periodo rilevante
2. Raccogliere info task (nome, durata, deadline, categoria)
3. **Analizzare automaticamente difficoltà fisica/intellettuale**
4. **Calcolare breakdown Pomodoro (25 min)**
5. **Valutare impatto energia (energizing vs draining)**
6. Eseguire `suggest_task_slots_enhanced.py` con strategia
7. Presentare suggerimenti con reasoning dettagliato

**Script**: `scripts/suggest_task_slots_enhanced.py`

**Input**:
- File JSON con eventi calendario
- File JSON con task da schedulare:
  ```json
  {
    "name": "Scrivere report Q4",
    "description": "Analisi completa con forecast",
    "duration_minutes": 90,
    "deadline": "2025-11-01T17:00:00Z",
    "priority": 8,
    "category": "lavoro"
  }
  ```

**Strategie Disponibili**:
- `deadline_priority` (default): urgenza prima
- `priority_first`: importanza prima
- `longest_first`: task lunghi prima
- `balanced`: mix equilibrato

**Output Arricchito**:
```json
{
  "name": "Scrivere report Q4",
  "suggested_start": "2025-10-29T09:00:00",
  "suggested_end": "2025-10-29T11:35:00",
  "duration_minutes": 90,
  "effective_duration_minutes": 115,
  "reasoning": "Deadline tra 3 giorni | Alta concentrazione → orario ottimale | 4 Pomodori con pause",
  "difficulty_physical": "bassa",
  "difficulty_intellectual": "alta",
  "energy_impact": "neutral",
  "pomodoro_blocks": 4,
  "buffer_minutes": 20
}
```

**Ottimizzazioni Automatiche**:
- ✅ Task intellettuali → mattino (9-12)
- ✅ Task fisici → quando hai energia
- ✅ Task drenanti → distribuiti, non consecutivi
- ✅ Deadline vicine → priorità massima
- ✅ Blocchi Pomodoro → 25 min con pause
- ✅ Buffer intelligenti → basati su difficoltà

**Fasce Orarie Ottimali**:
- **9-12**: Concentrazione massima (task intellettuali alti)
- **14-16**: Collaborazione, meeting (energia media)
- **16-18**: Amministrativo, routine (energia calante)

### 8. Creazione File ICS con Programmazione Mentale

**NOVITÀ**: File ICS potenziati con frasi anti-sabotaggio e analisi completa.

**Trigger**: Utente vuole aggiungere eventi/task al calendario.

**Processo**:
1. Dopo aver generato suggerimenti task
2. **Genera automaticamente frasi anti-sabotaggio personalizzate**
3. **Analizza difficoltà e calcola Pomodoro**
4. Eseguire `create_ics_enhanced.py` con i dati
5. Fornire file .ics per importazione in Google Calendar

**Script**: `scripts/create_ics_enhanced.py`

**Input**:
- File JSON con task suggestions (output di `suggest_task_slots_enhanced.py`)
- Nome file output (opzionale)

**Output**: File `.ics` avanzato con:

**📝 Descrizione Evento Include**:
```
🎯 **Nome Task**

💪 Frase anti-procrastinazione
⏱️ Gestione tempo realistica
🎓 Avviso difficoltà specifica
⚡ Reminder energia/focus
🔔 Anti-distrazione

─────────────────
📊 ANALISI TASK
Categoria: 💼 Lavoro
Difficoltà Fisica: media
Difficoltà Intellettuale: alta
Impatto Energia: neutral

🍅 BREAKDOWN POMODORO
Pomodori necessari: 4
Tempo lavoro effettivo: 100 min
Pause brevi: 3
Pause lunghe: 0
Tempo totale con pause: 115 min

📅 SCHEDULE POMODORO
🍅 Pomodoro 1: 25 min focus
⏸️ Pausa breve: 5 min
🍅 Pomodoro 2: 25 min focus
...

💡 RACCOMANDAZIONI
• Mattino (9-12): massima concentrazione
• Spegni notifiche 15 min prima

🎯 PERCHÉ QUESTO SLOT
Deadline tra 3 giorni | Orario ottimale per task complessi

─────────────────
✨ Dopo completamento: 
🎉 Task completato! Il tuo io futuro sta sorridendo
```

**🔔 Reminder Motivazionale**:
- 15 minuti prima dell'inizio
- Include frase anti-procrastinazione
- Prepara mentalmente al task

**Categorie ICS**:
- LAVORO, PERSONALE, PROGETTI, URGENTE, FORMAZIONE, BENESSERE

**Vantaggi vs Versione Base**:
- ✅ Programmazione mentale in ogni evento
- ✅ Analisi difficoltà visibile
- ✅ Breakdown Pomodoro esplicito
- ✅ Raccomandazioni contestuali
- ✅ Celebrazioni post-completamento
- ✅ Reminder motivazionali intelligenti

### 5. Integrazione Google Tasks

**Trigger**: L'utente vuole gestire task come checklist, non solo come blocchi temporali.

**Processo**:
1. Dopo aver generato suggerimenti task
2. Eseguire `create_google_tasks.py` con i task suggestions
3. Fornire 3 file all'utente:
   - JSON con dati task
   - Markdown con istruzioni passo-passo
   - Script Python per import automatico (opzionale)

**Script**: `scripts/create_google_tasks.py`

**Input**:
- File JSON con task suggestions (stesso output di `suggest_task_slots.py`)
- Nome base per file output (opzionale)

**Output**: 
- **JSON file**: Task in formato Google Tasks-compatible
- **Markdown file**: Istruzioni dettagliate per import manuale
- **Python script**: Script opzionale per import automatico via API

**Approccio Ibrido - Due Sistemi Complementari**:

**Google Calendar (file .ics)**:
- 📅 **QUANDO** fare le cose
- Blocchi temporali dedicati
- Visione timeline giornaliera/settimanale
- Notifiche prima dell'ora di inizio

**Google Tasks (JSON + istruzioni)**:
- ✅ **COSA** fare  
- Checklist con spunta completamento
- Note dettagliate per ogni task
- Visualizzazione per deadline
- Subtasks per scomporre attività complesse

**Workflow completo**:
1. Skill genera suggerimenti → `suggest_task_slots.py`
2. Crea file calendario → `create_ics.py` → utente importa in Calendar
3. Crea lista task → `create_google_tasks.py` → utente aggiunge in Tasks
4. Risultato: Calendar mostra QUANDO, Tasks mostra COSA con checklist

**Metodi di Import Google Tasks**:

**Metodo 1: Manuale (Consigliato per semplicità)**
- Seguire istruzioni nel file markdown generato
- Aprire Google Tasks (in Gmail, Calendar, o app mobile)
- Creare lista e aggiungere task seguendo la guida
- Tempo: ~2-3 minuti per 5 task

**Metodo 2: API Automatico (Per utenti avanzati)**
- Usare script Python fornito
- Richiede setup iniziale OAuth (5 minuti una tantum)
- Import completamente automatico
- Documentazione: https://developers.google.com/tasks/quickstart/python

**Caratteristiche Task Generati**:
- Titolo numerato per ordine di priorità
- Note complete con:
  - 💡 Reasoning del suggerimento
  - ⭐ Priorità
  - ⏱️ Durata stimata
  - 📅 Link concettuale al blocco calendario
- Due date (quando applicabile)
- Status: needsAction (pronto da completare)

**Best practice**:
- Usare ENTRAMBI i sistemi per massima efficacia
- Calendario per organizzare il tempo
- Tasks per tracciare completamento e dettagli
- Spuntare task in Google Tasks man mano che si completano
- Aggiungere subtask se necessario per task complessi

## 🔄 Workflow v2.0 (con Programmazione Mentale)

### Scenario 1: Revisione Settimanale Completa
```
1. list_gcal_events (prossimi 7 giorni)
2. calculate_travel.py per location diverse (da Via Manzoni 60)
3. analyze_schedule.py
4. NUOVO: Identifica pattern settimanali negativi
5. Presentare overview + incongruenze + pattern + suggerimenti
6. (Se ci sono task) suggest_task_slots_enhanced.py
   → Analisi automatica difficoltà
   → Calcolo Pomodoro 25 min
   → Ottimizzazione energia
7. (Se utente conferma)
   → create_ics_enhanced.py → file con frasi anti-sabotaggio
   → create_google_tasks.py → lista task + istruzioni
8. NUOVO: Messaggio pattern settimanale personalizzato
```

### Scenario 2: Schedulare Task con Programmazione Mentale
```
User: "Ho un report da scrivere (90 min) con deadline venerdì"

1. list_gcal_events (oggi → venerdì)

2. Crea task JSON:
{
  "name": "Scrivere report Q4",
  "description": "Analisi finanziaria completa",
  "duration_minutes": 90,
  "deadline": "2025-11-01T17:00:00Z",
  "priority": 8,
  "category": "lavoro"
}

3. suggest_task_slots_enhanced.py
   → Analizza automaticamente:
     - Difficoltà intellettuale: ALTA
     - Difficoltà fisica: BASSA
     - Energia: NEUTRAL
     - Pomodori: 4 (115 min con pause)
     - Buffer: 20 min
     - Slot ottimale: Martedì 9-11:35
   
   → Reasoning: "Deadline tra 3 giorni | Alta concentrazione 
                 → mattino ottimale | 4 Pomodori strutturati"

4. Presentare suggerimento:
   "Ti suggerisco **Martedì 9:00-11:35** perché:
    • Hai 4 ore libere continue
    • Mattino = massima concentrazione (task complesso)
    • Deadline tra 3 giorni (priorità alta)
    • Strutturato in 4 Pomodori da 25 min con pause strategiche"

5. User: "Perfetto!"

6. create_ics_enhanced.py
   → Genera evento con:
     - 💪 "L'azione imperfetta batte la perfezione immaginata"
     - ⏱️ "Ogni task ha imprevisti: la stima include anche quelli"
     - 🎓 "Task complesso: respira profondo, focus totale"
     - ⚡ "Energia spesa ora = risultati dopo"
     - 🔔 "Le distrazioni rubano i sogni: difendili"
     - 🎯 Breakdown Pomodoro completo
     - 💡 Raccomandazioni specifiche
     - ✨ Celebrazione post-completamento

7. Fornire file:
   "📥 **report_q4_smart.ics**
    
    Importa in Google Calendar per attivare:
    ✅ Programmazione mentale anti-sabotaggio
    ✅ Breakdown Pomodoro automatico
    ✅ Reminder motivazionali
    ✅ Celebrazione dopo completamento
    
    Il tuo cervello è ora programmato per il successo!"
```

### Scenario 3: Analisi Pattern + Riorganizzazione Proattiva
```
User: "Come va la mia settimana?"

1. list_gcal_events (7 giorni)

2. analyze_schedule.py + pattern recognition
   → Rileva:
     - Martedì: 9 ore, 7 eventi (SOVRACCARICO)
     - Giovedì: 8.5 ore, 6 eventi (SOVRACCARICO)
     - Venerdì: 4 task drenanti consecutivi (BURNOUT RISK)
     - 12 coppie back-to-back < 10 min pause

3. Genera messaggio pattern:
   "⚠️ **Pattern Critico Rilevato**
    
    **Giorni Sovraccarichi**: Martedì, Giovedì
    → Considera spostare meeting non urgenti
    
    **Rischio Burnout**: Venerdì hai 4 attività drenanti consecutive
    → Inserisci attività energizzante (es. brainstorming, sport)
    
    **Pause Insufficienti**: 12 eventi back-to-back
    → Il tuo cervello ha bisogno di buffer per performance ottimali"

4. User: "Cosa posso fare?"

5. Suggerimenti proattivi:
   "💡 **Riorganizzazione Proposta**
    
    **Martedì**:
    • Sposta meeting X a Mercoledì (giorno più leggero)
    • Aggiungi 15 min buffer dopo pranzo
    
    **Giovedì**:
    • Converti meeting Y in email update
    • Proteggi 1 ora pomeriggio per deep work
    
    **Venerdì**:
    • Inserisci "Coffee break brainstorming" dopo 2° task
    • Chiudi giornata con attività energizzante
    
    Vuoi che generi nuovi ICS con questi aggiustamenti?"

6. (Se sì) Crea eventi buffer e celebrazioni
```

### Scenario 4: Task Urgente con Difficoltà Alta
```
User: "Devo preparare presentazione cliente per domani! 2 ore"

1. Analisi situazione:
   - Deadline: < 24 ore (CRITICO)
   - Durata: 120 min
   - Tipo: Presentazione (intellettuale ALTA)

2. suggest_task_slots_enhanced.py
   → Analisi:
     - Difficoltà intellettuale: ALTA
     - Pomodori: 5 (160 min con pause)
     - Slot: OGGI 14:00-16:40 (unico disponibile)
     - Energia: ALTA richiesta

3. Genera frasi anti-sabotaggio potenziate:
   "💪 Il primo passo è sempre il più potente
    ⏱️ Rispettare i tempi significa rispettare te stesso
    🎓 Sfida intellettuale: elimina OGNI distrazione
    ⚡ Questa attività richiede la tua energia migliore: sei pronto
    🔔 Le distrazioni rubano i sogni: difendili
    ⏰ DEADLINE VICINA: questo è il momento di agire, NON di rimandare
    🧭 La montagna si scala un metro alla volta"

4. Preparazione pre-task:
   "🎯 **Setup per Successo**
    
    ADESSO (5 min prima):
    ✅ Silenzia telefono + notifiche
    ✅ Chiudi tutte le tab browser non necessarie
    ✅ Prepara acqua + snack
    ✅ Avvisa colleghi: "Deep work 3 ore"
    ✅ Respira 3 volte profondamente
    
    DURANTE (5 Pomodori):
    🍅 25 min → Focus totale su slides
    ⏸️ 5 min → Stretch, acqua
    🍅 25 min → Focus contenuto
    ⏸️ 5 min → Walk, respira
    🍅 25 min → Focus design
    ⏸️ 5 min → Snack leggero
    🍅 25 min → Revisione
    ☕ 15 min → Pausa lunga
    🍅 25 min → Practice speech
    
    DOPO:
    ✨ Celebra! Hai battuto la procrastinazione in situazione critica!"

5. create_ics_enhanced.py + reminder 10 min prima
```

### Scenario 5: Settimana Bilanciata (Proattivo)
```
User: "Organizza la mia settimana"

1. list_gcal_events (7 giorni)
2. Raccolta task pendenti (da Google Tasks o input)
3. analyze_schedule.py → tutto OK, nessuna incongruenza
4. NUOVO: Analisi energia settimanale:
   - Lunedì: 2 task energizzanti, 1 drenante → BILANCIATO
   - Martedì: 3 drenanti, 0 energizzanti → SBILANCIATO
   - ...

5. suggest_task_slots_enhanced.py con strategia "balanced"
   → Distribuisce task bilanciando energia
   → Alterna energizzanti e drenanti
   → Rispetta picchi energia giornalieri

6. create_ics_enhanced.py per tutti i task

7. Messaggio finale:
   "✅ **Settimana Ottimizzata**
    
    📊 Summary:
    • 15 task schedulati in 5 giorni
    • 47 Pomodori totali (20 ore effettive)
    • Buffer medio: 18 min/task
    • Energia ben bilanciata ogni giorno
    • 0 pattern critici rilevati
    
    🧠 Programmazione Mentale Attiva:
    • Ogni task ha frasi anti-sabotaggio personalizzate
    • Celebrazioni micro dopo ogni completamento
    • Reminder motivazionali pre-task
    
    🍅 Deep Work Ottimizzato:
    • 47 blocchi Pomodoro da 25 min
    • 32 pause brevi (5 min)
    • 8 pause lunghe (15 min)
    
    💪 Sei pronto per una settimana produttiva e soddisfacente!"
```

## Linee Guida Avanzate

Per principi dettagliati su gestione agenda, buffer temporali, prioritizzazione, e best practices, consultare: `references/linee_guida.md`

**Quando leggere le linee guida**:
- Per definire buffer appropriate tra eventi
- Per calcolare stime manuali di viaggio
- Per comprendere carico giornaliero ottimale
- Per strategie di pianificazione avanzate
- Per interpretare e comunicare problemi di calendario

## Preferenze Utente da Memorizzare

Durante l'uso, apprendere e applicare:
- **Orari di lavoro preferiti**: (default 9-18)
- **Location ricorrenti**: (ufficio, casa, clienti frequenti)
- **Buffer preferito**: tra appuntamenti e dopo spostamenti
- **Strategia scheduling**: quale funziona meglio per l'utente
- **Carico massimo**: ore/giorno che l'utente gestisce bene

## Best Practices Comunicazione

### Tono
- Proattivo ma non autoritario
- Usare "ti suggerisco" non "devi"
- Spiegare sempre il reasoning

### Presentazione Risultati
- Iniziare con summary/overview
- Poi dettagli problemi critici
- Infine suggerimenti pratici e azionabili

### Gestione Problemi
- **Issue critiche** (overlaps, travel): presentare subito con urgenza
- **Issue moderate** (back-to-back, long days): menzionare con contesto
- **Suggerimenti ottimizzazione**: dopo aver gestito problemi

### Flessibilità
- Task senza deadline: offrire più opzioni
- Se utente rifiuta suggerimento: chiedere preferenze e ricalcolare
- Adattare strategia in base a feedback

## Limitazioni

- **API Google Maps**: richiede API key per calcoli precisi. Senza key, usa stime manuali meno accurate.
- **Modifiche calendario**: questa skill crea file .ics per l'importazione. L'utente deve importare manualmente il file in Google Calendar (processo di 1 click).
- **Preferenze personali**: la skill impara preferenze nel tempo, inizialmente usa defaults conservativi.
- **Task management**: non gestisce progetti complessi con dipendenze; ottimale per task individuali.
- **Importazione batch**: file .ics permette di aggiungere eventi in blocco, ma Google Calendar potrebbe richiedere conferma per importazioni multiple.

## 📚 Esempi d'Uso v2.0

**Esempio 1 - Verifica incongruenze + Pattern**:
```
User: "Controlla il mio calendario questa settimana"

→ list_gcal_events (7 giorni)
→ calculate_travel.py per location (da Via Manzoni 60)
→ analyze_schedule.py + pattern recognition

→ Response:
"📊 **Analisi Settimana**

**Incongruenze Rilevate**: 3
• 1 sovrapposizione: Martedì 14:00 (Meeting A vs Meeting B)
• 1 tempo viaggio insufficiente: Mercoledì 11:00→12:00
  (Da Cosenza a Rende: serve 35 min, hai 30 min)
• 1 giornata sovraccarica: Giovedì 9 ore di impegni

⚠️ **Pattern Settimanale Negativo**
• Martedì e Giovedì sono ricorrentemente sovraccarichi
• Venerdì: 3 task drenanti consecutivi (rischio burnout)
• 8 eventi back-to-back senza pause sufficienti

💡 **Raccomandazioni**:
1. Sposta Meeting B a Mercoledì pomeriggio
2. Parti 15 min prima per viaggio Cosenza-Rende
3. Redistribuisci carico: sposta 2 meeting da Giovedì
4. Inserisci buffer 10 min dopo ogni meeting
5. Venerdì: aggiungi pausa energizzante dopo 2° task"
```

**Esempio 2 - Task con Programmazione Mentale Completa**:
```
User: "Ho da scrivere una proposta progetto (3 ore), deadline giovedì"

→ list_gcal_events (oggi → giovedì)
→ Create task JSON:
{
  "name": "Proposta Progetto Cliente X",
  "description": "Documento strategico completo",
  "duration_minutes": 180,
  "deadline": "2025-10-31T17:00:00Z",
  "category": "progetti",
  "priority": 9
}

→ suggest_task_slots_enhanced.py
  Analisi automatica:
  • Difficoltà Intellettuale: ALTA
  • Difficoltà Fisica: BASSA
  • Energia: NEUTRAL
  • Pomodori: 8 (240 min con pause)
  • Buffer: 20 min

→ Response:
"🎯 **Slot Ottimale Trovato**

**Quando**: Mercoledì 9:00-13:00

**Perché questo slot**:
• Deadline tra 2 giorni → priorità alta
• Mattino = massima concentrazione (task complesso)
• 4 ore libere continue disponibili
• Post-pranzo hai meeting (non puoi sforare)

🍅 **Struttura Pomodoro** (8 blocchi):
1. 🍅 25 min: Ricerca e outline
2. ⏸️ 5 min: Pausa
3. 🍅 25 min: Sezione intro
4. ⏸️ 5 min: Pausa
5. 🍅 25 min: Analisi situazione
6. ⏸️ 5 min: Pausa
7. 🍅 25 min: Proposta soluzione
8. ☕ 15 min: Pausa lunga + snack
9. 🍅 25 min: Timeline e budget
10. ⏸️ 5 min: Pausa
11. 🍅 25 min: Risk analysis
12. ⏸️ 5 min: Pausa
13. 🍅 25 min: Conclusioni
14. ⏸️ 5 min: Pausa
15. 🍅 25 min: Revisione finale

🧠 **Programmazione Mentale Attiva**:
Quando importi l'ICS, vedrai:
• 💪 "L'azione imperfetta batte la perfezione immaginata"
• ⏱️ "Questo blocco è calibrato sulla realtà, non sull'ottimismo"
• 🎓 "Task complesso: respira profondo, focus totale"
• ⏰ "Deadline tra 2 giorni: momento di agire"
• 🔔 "Ogni interruzione costa 23 minuti: elimina fonti"

✨ Post-Completamento:
"🎉 Proposta completata! Il tuo io futuro sta sorridendo"

Vuoi che generi il file ICS?"

User: "Sì!"

→ create_ics_enhanced.py
→ Output: proposta_progetto_smart.ics

"📥 **File Pronto**: proposta_progetto_smart.ics

Importa in Google Calendar per:
✅ Programmazione mentale anti-sabotaggio
✅ Breakdown Pomodoro visibile
✅ Reminder motivazionale 15 min prima
✅ Celebrazione automatica dopo

Il tuo cervello è programmato per creare una proposta vincente! 💪"
```

**Esempio 3 - Calcolo spostamento da indirizzo base**:
```
User: "Quanto ci metto ad arrivare a Cosenza centro?"

→ calculate_travel.py
  Origin: Via Alessandro Manzoni 60, Taverna di Montalto Uffugo
  Destination: Cosenza centro
  
→ "🚗 **Tempo Spostamento**

Da casa tua (Via Manzoni 60, Taverna di Montalto Uffugo)
A: Cosenza centro

Distanza: ~12 km
Tempo stimato: 22 minuti (traffico normale)
Tipo percorso: Suburbano (SP)

💡 **Raccomandazioni**:
• Prevedi 35 minuti totali (incluso parcheggio)
• Orari critici traffico: 8:00-9:00, 13:00-14:00, 17:00-19:00
• Se devi arrivare per meeting, parti con 10 min buffer extra

Buffer consigliato da aggiungere: +13 minuti"
```

**Esempio 4 - Settimana Completa con Bilanciamento Energia**:
```
User: "Ho 8 task da fare questa settimana, organizzali"

→ Raccolta task:
1. Report mensile (90 min) - drenante
2. Brainstorming nuovo progetto (60 min) - energizzante
3. Email clienti (45 min) - drenante
4. Call team (30 min) - energizzante
5. Analisi budget (120 min) - drenante
6. Presentazione risultati (90 min) - neutral
7. Formazione online (60 min) - energizzante
8. Sistemazione archivio (90 min) - drenante

→ list_gcal_events (7 giorni)

→ suggest_task_slots_enhanced.py con strategia "balanced"
  Ottimizzazione automatica:
  • Bilancia energia ogni giorno
  • Alterna drenanti e energizzanti
  • Rispetta orari ottimali per difficoltà
  • Inserisce buffer adeguati

→ Response:
"✅ **Pianificazione Ottimale Generata**

**Lunedì**: Energia bilanciata ⚖️
• 9:00-10:30: Brainstorming progetto (energizzante) 🔋
• 11:00-12:00: Email clienti (drenante) 💧
• 14:00-15:00: Call team (energizzante) 🔋

**Martedì**: Focus intellettuale 🧠
• 9:00-11:35: Report mensile (drenante - ma mattino) 💧
• 14:00-16:35: Analisi budget (drenante - ma necessario) 💧
→ ⚠️ Giornata intellettualmente intensa, meritati pausa serale

**Mercoledì**: Recupero attivo 🌟
• 14:00-15:30: Formazione online (energizzante) 🔋
→ Giorno più leggero, 5 ore libere per imprevisti

**Giovedì**: Presentazione 🎯
• 9:00-11:00: Preparazione presentazione (neutral)
• 14:30-16:00: Sistemazione archivio (drenante) 💧

**Venerdì**: Light day 🎈
• Nessun nuovo task
→ Buffer per completamenti o urgenze settimana

📊 **Summary**:
• Task schedulati: 8/8 ✅
• Pomodori totali: 23 🍅
• Ore effettive: 9.5 ore (ben distribuite)
• Energia: BILANCIATA ogni giorno
• Pattern critici: 0 ⚠️

🧠 **Programmazione Mentale**:
Ogni task ha frasi personalizzate:
• Task drenanti → "Dopo questo, pausa meritata"
• Task energizzanti → "Questa attività ti ricarica"
• Task complessi → "Un passo alla volta"

Genero file ICS?"

User: "Perfetto, procedi"

→ create_ics_enhanced.py (8 eventi con programmazione completa)

"📥 **settimana_ottimizzata.ics**

8 task schedulati con:
✅ 23 blocchi Pomodoro strutturati
✅ Frasi anti-sabotaggio per ogni task
✅ Bilanciamento energia giornaliero
✅ Buffer intelligenti (media 17 min)
✅ Celebrazioni micro post-completamento

Importa e conquista la settimana! 🚀"
```

**Esempio 5 - Solo Analisi Pattern (Nessun Task da Aggiungere)**:
```
User: "Dimmi se c'è qualche problema nel mio calendario"

→ list_gcal_events (14 giorni)
→ analyze_schedule.py + pattern recognition

→ "🔍 **Analisi Approfondita Calendario**

**Incongruenze Immediate**: 2
• Sovrapposizione: Domani 15:00
• Viaggio impossibile: Mercoledì 11:00→12:30

⚠️ **Pattern Negativi Rilevati**:

1. **Giorni Ricorrentemente Sovraccarichi**
   • Martedì: 4 settimane consecutive > 8 ore
   • Giovedì: 3 settimane consecutive > 8 ore
   
   💡 Soluzione: Sposta 1-2 meeting fissi a Mercoledì

2. **Sequenza Drenante Pericolosa**
   • Venerdì pomeriggio: 4 task amministrativi consecutivi
   • Rischio: Burnout fine settimana
   
   💡 Soluzione: Inserisci 15 min "coffee break creativo" a metà

3. **Back-to-Back Eccessivi**
   • 18 coppie eventi < 10 min pausa
   • Il tuo cervello ha bisogno di buffer
   
   💡 Soluzione: Accorcia meeting di 5 min (55 min invece 60)

✅ **Pattern Positivi**:
• Lunedì e Mercoledì ben bilanciati
• Weekend protetti (ottimo!)
• Pause pranzo rispettate

🎯 **Azione Raccomandata**:
Vuoi che riorganizzo i meeting problematici con frasi 
anti-sabotaggio per gestire meglio lo stress?"
```
