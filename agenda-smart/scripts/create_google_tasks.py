#!/usr/bin/env python3
"""
Generate Google Tasks lists from task suggestions.
Creates structured JSON format and provides instructions for manual import or API-based import.
"""

import sys
import json
from datetime import datetime
from typing import List, Dict, Any


def format_date_for_tasks(dt_str: str) -> str:
    """
    Format datetime for Google Tasks (RFC 3339 format, date only).
    
    Args:
        dt_str: ISO datetime string
    
    Returns:
        Date in format YYYY-MM-DD
    """
    if isinstance(dt_str, str):
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d')
    return dt_str


def create_task_dict(task_name: str, notes: str = "", due_date: str = None,
                     status: str = "needsAction") -> Dict:
    """
    Create a Google Tasks-compatible task dictionary.
    
    Args:
        task_name: Task title
        notes: Task notes/description
        due_date: Due date in YYYY-MM-DD format
        status: Task status (needsAction or completed)
    
    Returns:
        Dictionary with task data
    """
    task = {
        "title": task_name,
        "status": status
    }
    
    if notes:
        task["notes"] = notes
    
    if due_date:
        # Google Tasks expects RFC 3339 format for due date
        task["due"] = f"{due_date}T00:00:00.000Z"
    
    return task


def create_tasks_from_suggestions(suggestions: List[Dict], 
                                  include_calendar_link: bool = True) -> Dict:
    """
    Create Google Tasks list from task scheduling suggestions.
    
    Args:
        suggestions: List of task suggestions from suggest_task_slots.py
        include_calendar_link: Whether to add note about calendar block
    
    Returns:
        Dict with task list and tasks
    """
    task_list = {
        "title": "Agenda Smart - Task Settimana",
        "tasks": []
    }
    
    for i, suggestion in enumerate(suggestions, 1):
        task_name = suggestion['task']
        
        # Build notes with reasoning and calendar info
        notes_parts = []
        
        # Add reasoning
        if suggestion.get('reasoning'):
            notes_parts.append(f"💡 {suggestion['reasoning']}")
        
        # Add priority
        if suggestion.get('priority') and suggestion['priority'] != 'non specificata':
            notes_parts.append(f"⭐ Priorità: {suggestion['priority']}")
        
        # Add duration
        if suggestion.get('duration_minutes'):
            hours = suggestion['duration_minutes'] // 60
            minutes = suggestion['duration_minutes'] % 60
            duration_str = f"{hours}h {minutes}m" if minutes else f"{hours}h"
            notes_parts.append(f"⏱️ Durata stimata: {duration_str}")
        
        # Add calendar block info
        if include_calendar_link and suggestion.get('suggested_start'):
            start_dt = datetime.fromisoformat(suggestion['suggested_start'].replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(suggestion['suggested_end'].replace('Z', '+00:00'))
            
            time_str = f"{start_dt.strftime('%a %d/%m alle %H:%M')}-{end_dt.strftime('%H:%M')}"
            notes_parts.append(f"📅 Blocco calendario: {time_str}")
            notes_parts.append(f"(Importa il file .ics per aggiungere al calendario)")
        
        notes = "\n\n".join(notes_parts)
        
        # Determine due date (use time_to_deadline info if available)
        due_date = None
        if suggestion.get('time_to_deadline') is not None:
            # Calculate due date from suggested start + time_to_deadline
            start_dt = datetime.fromisoformat(suggestion['suggested_start'].replace('Z', '+00:00'))
            # For simplicity, use the suggested date as reference
            due_date = start_dt.strftime('%Y-%m-%d')
        
        task = create_task_dict(
            task_name=f"{i}. {task_name}",
            notes=notes,
            due_date=due_date,
            status="needsAction"
        )
        
        task_list["tasks"].append(task)
    
    return task_list


def create_tasks_list_file(suggestions: List[Dict], output_file: str = None,
                           list_name: str = "Agenda Smart - Task") -> str:
    """
    Create a JSON file with Google Tasks-compatible format.
    
    Args:
        suggestions: List of task suggestions
        output_file: Output filename
        list_name: Name of the task list
    
    Returns:
        Filename of created JSON file
    """
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"google_tasks_{timestamp}.json"
    
    if not output_file.endswith('.json'):
        output_file += '.json'
    
    task_list = create_tasks_from_suggestions(suggestions)
    task_list['title'] = list_name
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(task_list, f, indent=2, ensure_ascii=False)
    
    return output_file


def create_markdown_instructions(task_list: Dict, output_file: str = None) -> str:
    """
    Create markdown file with step-by-step instructions for adding tasks manually.
    
    Args:
        task_list: Task list dictionary
        output_file: Output filename
    
    Returns:
        Filename of created markdown file
    """
    if not output_file:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"tasks_instructions_{timestamp}.md"
    
    if not output_file.endswith('.md'):
        output_file += '.md'
    
    md_content = [
        f"# 📋 {task_list['title']}",
        "",
        "## Come Aggiungere i Task a Google Tasks",
        "",
        "### Metodo Rapido (App Mobile)",
        "1. Apri l'app **Google Tasks** sul telefono",
        "2. Tocca **+** per creare nuova lista (se necessario)",
        "3. Aggiungi i task uno per uno seguendo la lista sotto",
        "",
        "### Metodo Desktop (Gmail/Calendar)",
        "1. Apri **Gmail** o **Google Calendar**",
        "2. Clicca sull'icona **Google Tasks** a destra",
        "3. Crea una nuova lista se necessario",
        "4. Aggiungi i task seguendo la lista sotto",
        "",
        "---",
        "",
        f"## ✅ Task da Aggiungere ({len(task_list['tasks'])} task)",
        ""
    ]
    
    for task in task_list['tasks']:
        md_content.append(f"### {task['title']}")
        md_content.append("")
        
        if task.get('notes'):
            md_content.append("**Note:**")
            md_content.append("```")
            md_content.append(task['notes'])
            md_content.append("```")
            md_content.append("")
        
        if task.get('due'):
            due_date = datetime.fromisoformat(task['due'].replace('Z', '+00:00'))
            md_content.append(f"**Scadenza:** {due_date.strftime('%d/%m/%Y')}")
            md_content.append("")
        
        md_content.append("---")
        md_content.append("")
    
    md_content.extend([
        "## 💡 Suggerimenti",
        "",
        "- ✅ Spunta i task appena li completi per tenere traccia dei progressi",
        "- 📅 I blocchi calendario corrispondenti sono nel file .ics da importare",
        "- 🔄 Puoi riordinare i task in base alle tue preferenze",
        "- 📝 Aggiungi subtask se necessario per scomporre task complessi",
        "",
        "## 🔗 Integrazione con Calendario",
        "",
        "Questi task sono sincronizzati concettualmente con i blocchi temporali nel calendario:",
        "1. **Google Tasks** → COSA fare (checklist, completamento)",
        "2. **Google Calendar** → QUANDO farlo (blocchi di tempo dedicati)",
        "",
        "Importa il file `.ics` per avere anche i blocchi temporali nel calendario!",
    ])
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_content))
    
    return output_file


def create_api_import_script(task_list: Dict, output_file: str = None) -> str:
    """
    Create a Python script for importing tasks via Google Tasks API (optional advanced feature).
    
    Args:
        task_list: Task list dictionary
        output_file: Output filename
    
    Returns:
        Filename of created script
    """
    if not output_file:
        output_file = "import_to_google_tasks.py"
    
    script_content = '''#!/usr/bin/env python3
"""
Import tasks to Google Tasks via API.
Requires: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
Setup: https://developers.google.com/tasks/quickstart/python
"""

import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path

SCOPES = ['https://www.googleapis.com/auth/tasks']

def authenticate():
    """Authenticate with Google Tasks API."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds

def import_tasks(task_list_file):
    """Import tasks from JSON file to Google Tasks."""
    creds = authenticate()
    service = build('tasks', 'v1', credentials=creds)
    
    # Load task list from JSON
    with open(task_list_file, 'r', encoding='utf-8') as f:
        task_list_data = json.load(f)
    
    # Create new task list
    new_list = service.tasklists().insert(
        body={'title': task_list_data['title']}
    ).execute()
    
    list_id = new_list['id']
    print(f"✅ Created task list: {task_list_data['title']}")
    
    # Add tasks
    for task_data in task_list_data['tasks']:
        task = service.tasks().insert(
            tasklist=list_id,
            body=task_data
        ).execute()
        print(f"  ✓ Added: {task_data['title']}")
    
    print(f"\\n🎉 Successfully imported {len(task_list_data['tasks'])} tasks!")
    print(f"   View at: https://tasks.google.com")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python import_to_google_tasks.py <task_list.json>")
        sys.exit(1)
    
    import_tasks(sys.argv[1])
'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    return output_file


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  create_google_tasks.py <suggestions_json> [output_base_name]")
        print()
        print("Example:")
        print("  create_google_tasks.py task_suggestions.json my_tasks")
        print()
        print("This will create:")
        print("  - JSON file with task data")
        print("  - Markdown file with manual instructions")
        print("  - (Optional) Python script for API import")
        sys.exit(1)
    
    input_file = sys.argv[1]
    base_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Load task suggestions
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, dict) or 'suggestions' not in data:
        print("❌ Error: Expected task suggestions JSON with 'suggestions' key")
        sys.exit(1)
    
    suggestions = data['suggestions']
    
    if not suggestions:
        print("❌ No task suggestions found in JSON")
        sys.exit(1)
    
    # Generate output filenames
    if base_name:
        json_file = f"{base_name}.json"
        md_file = f"{base_name}_instructions.md"
        script_file = f"{base_name}_api_import.py"
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = f"google_tasks_{timestamp}.json"
        md_file = f"tasks_instructions_{timestamp}.md"
        script_file = f"import_api_{timestamp}.py"
    
    # Create task list
    task_list = create_tasks_from_suggestions(suggestions)
    
    # Generate JSON file
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(task_list, f, indent=2, ensure_ascii=False)
    
    # Generate markdown instructions
    md_filename = create_markdown_instructions(task_list, md_file)
    
    # Generate API import script (optional)
    script_filename = create_api_import_script(task_list, script_file)
    
    print(f"✅ Created Google Tasks files:")
    print(f"   📄 {json_file} - Task data in JSON format")
    print(f"   📋 {md_filename} - Step-by-step instructions")
    print(f"   🔧 {script_filename} - Optional API import script")
    print()
    print(f"📖 Next steps:")
    print(f"   1. READ: {md_filename} for manual import instructions")
    print(f"   2. OR use the API script for automatic import (requires setup)")
    print(f"   3. Import the .ics file for calendar blocks")
    print()
    print(f"💡 Recommended: Follow the markdown instructions for easiest setup!")
