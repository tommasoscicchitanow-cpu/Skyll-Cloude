#!/usr/bin/env python3
"""
Generate .ics (iCalendar) files for importing events into Google Calendar or other calendar applications.
Creates properly formatted calendar files that can be directly imported.
"""

import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid


def format_datetime_ics(dt: datetime) -> str:
    """
    Format datetime for iCalendar format.
    
    Args:
        dt: datetime object
    
    Returns:
        String in format YYYYMMDDTHHMMSS or YYYYMMDDTHHMMSSZ for UTC
    """
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
    
    if dt.tzinfo:
        # Convert to UTC for universal compatibility
        dt_utc = dt.astimezone(datetime.now().astimezone().tzinfo)
        return dt_utc.strftime('%Y%m%dT%H%M%SZ')
    else:
        return dt.strftime('%Y%m%dT%H%M%S')


def escape_ics_text(text: str) -> str:
    """
    Escape special characters for iCalendar format.
    
    Args:
        text: Text to escape
    
    Returns:
        Escaped text safe for .ics files
    """
    if not text:
        return ""
    
    # Replace special characters
    text = text.replace('\\', '\\\\')
    text = text.replace(',', '\\,')
    text = text.replace(';', '\\;')
    text = text.replace('\n', '\\n')
    
    return text


def create_ics_event(summary: str, start: datetime, end: datetime,
                     description: str = "", location: str = "",
                     uid: str = None) -> str:
    """
    Create a single VEVENT component for iCalendar.
    
    Args:
        summary: Event title
        start: Start datetime
        end: End datetime
        description: Event description (optional)
        location: Event location (optional)
        uid: Unique identifier (generated if not provided)
    
    Returns:
        String containing VEVENT component
    """
    if not uid:
        uid = str(uuid.uuid4())
    
    now = datetime.now().strftime('%Y%m%dT%H%M%SZ')
    
    event = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{now}",
        f"DTSTART:{format_datetime_ics(start)}",
        f"DTEND:{format_datetime_ics(end)}",
        f"SUMMARY:{escape_ics_text(summary)}"
    ]
    
    if description:
        event.append(f"DESCRIPTION:{escape_ics_text(description)}")
    
    if location:
        event.append(f"LOCATION:{escape_ics_text(location)}")
    
    # Add alarm reminder 15 minutes before
    event.extend([
        "BEGIN:VALARM",
        "TRIGGER:-PT15M",
        "ACTION:DISPLAY",
        f"DESCRIPTION:Promemoria: {escape_ics_text(summary)}",
        "END:VALARM"
    ])
    
    event.append("END:VEVENT")
    
    return "\n".join(event)


def create_ics_file(events: List[Dict[str, Any]], filename: str = None,
                   calendar_name: str = "Agenda Smart") -> str:
    """
    Create a complete .ics file with multiple events.
    
    Args:
        events: List of event dictionaries with 'summary', 'start', 'end', 'description', 'location'
        filename: Output filename (optional, generated if not provided)
        calendar_name: Name of the calendar
    
    Returns:
        Filename of created .ics file
    """
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"agenda_smart_{timestamp}.ics"
    
    # Ensure .ics extension
    if not filename.endswith('.ics'):
        filename += '.ics'
    
    # Build iCalendar file
    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Agenda Smart//Calendar Export//IT",
        f"X-WR-CALNAME:{escape_ics_text(calendar_name)}",
        "X-WR-TIMEZONE:Europe/Rome",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]
    
    # Add each event
    for event in events:
        start = event.get('start') or event.get('suggested_start')
        end = event.get('end') or event.get('suggested_end')
        summary = event.get('summary') or event.get('task', 'Evento')
        description = event.get('description', '')
        location = event.get('location', '')
        
        # Add reasoning to description if available (for task suggestions)
        if event.get('reasoning'):
            if description:
                description += f"\\n\\nSuggerimento: {event['reasoning']}"
            else:
                description = f"Suggerimento: {event['reasoning']}"
        
        # Add priority info if available
        if event.get('priority'):
            description += f"\\nPriorità: {event['priority']}"
        
        # Add duration info if available
        if event.get('duration_minutes'):
            description += f"\\nDurata: {event['duration_minutes']} minuti"
        
        vevent = create_ics_event(
            summary=summary,
            start=start,
            end=end,
            description=description,
            location=location
        )
        
        ics_content.append(vevent)
    
    ics_content.append("END:VCALENDAR")
    
    # Write to file
    full_content = "\n".join(ics_content)
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    return filename


def create_task_block_events(task_suggestions: List[Dict], output_file: str = None) -> str:
    """
    Create .ics file from task scheduling suggestions.
    
    Args:
        task_suggestions: List of task suggestions from suggest_task_slots.py
        output_file: Output filename (optional)
    
    Returns:
        Filename of created .ics file
    """
    events = []
    
    for suggestion in task_suggestions:
        events.append({
            'task': f"⏰ {suggestion['task']}",  # Add emoji for task blocks
            'suggested_start': suggestion['suggested_start'],
            'suggested_end': suggestion['suggested_end'],
            'description': suggestion.get('reasoning', ''),
            'priority': suggestion.get('priority'),
            'duration_minutes': suggestion.get('duration_minutes'),
            'location': ''
        })
    
    if not output_file:
        output_file = "task_blocks.ics"
    
    return create_ics_file(events, output_file, "Task da Completare")


def create_event_from_dict(event_dict: Dict, output_file: str = None) -> str:
    """
    Create .ics file from a single event dictionary.
    
    Args:
        event_dict: Event dictionary with required fields
        output_file: Output filename (optional)
    
    Returns:
        Filename of created .ics file
    """
    if not output_file:
        event_name = event_dict.get('summary', 'evento').replace(' ', '_').lower()
        output_file = f"{event_name}.ics"
    
    return create_ics_file([event_dict], output_file)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  1. From task suggestions JSON:")
        print("     create_ics.py <suggestions_json> [output_file.ics]")
        print("  2. From events JSON:")
        print("     create_ics.py <events_json> [output_file.ics]")
        print()
        print("Examples:")
        print("  create_ics.py task_suggestions.json my_tasks.ics")
        print("  create_ics.py events.json calendar_events.ics")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Load JSON data
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Determine if it's task suggestions or events
    if isinstance(data, dict) and 'suggestions' in data:
        # Task suggestions format
        suggestions = data['suggestions']
        if suggestions:
            filename = create_task_block_events(suggestions, output_file)
            print(f"✅ Created {filename} with {len(suggestions)} task blocks")
            print(f"   Import this file into Google Calendar to add the suggested time blocks")
        else:
            print("❌ No task suggestions found in JSON")
            sys.exit(1)
    
    elif isinstance(data, list):
        # Events list format
        if data:
            if not output_file:
                output_file = "calendar_events.ics"
            filename = create_ics_file(data, output_file)
            print(f"✅ Created {filename} with {len(data)} events")
            print(f"   Import this file into Google Calendar to add the events")
        else:
            print("❌ No events found in JSON")
            sys.exit(1)
    
    else:
        print("❌ Unrecognized JSON format")
        print("   Expected: task suggestions dict with 'suggestions' key, or list of events")
        sys.exit(1)
