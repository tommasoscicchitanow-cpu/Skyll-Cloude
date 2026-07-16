#!/usr/bin/env python3
"""
Suggest optimal time slots for working on tasks based on calendar availability,
deadlines, task priorities, and personal preferences.
"""

import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


def parse_datetime(dt_str: str) -> datetime:
    """Parse ISO format datetime string."""
    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))


def find_free_slots(events: List[Dict], start_date: datetime, end_date: datetime,
                   min_slot_minutes: int = 30, work_hours: tuple = (9, 18),
                   exclude_weekends: bool = True) -> List[Dict]:
    """
    Find free time slots in the calendar.
    
    Args:
        events: List of calendar events
        start_date: Start of search period
        end_date: End of search period
        min_slot_minutes: Minimum slot duration in minutes
        work_hours: Tuple of (start_hour, end_hour) for work hours
        exclude_weekends: Whether to exclude weekends
    
    Returns:
        List of free slots with start, end, duration
    """
    # Parse and sort events
    parsed_events = []
    for event in events:
        start = event.get('start', {})
        end = event.get('end', {})
        start_time = start.get('dateTime') or start.get('date')
        end_time = end.get('dateTime') or end.get('date')
        
        if start_time and end_time:
            parsed_events.append({
                'start': parse_datetime(start_time),
                'end': parse_datetime(end_time),
                'summary': event.get('summary', 'Evento'),
                'all_day': 'date' in start
            })
    
    parsed_events.sort(key=lambda e: e['start'])
    
    free_slots = []
    # Ensure timezone awareness
    if start_date.tzinfo is None:
        import pytz
        tz = pytz.timezone('Europe/Rome')
        start_date = tz.localize(start_date)
        end_date = tz.localize(end_date)
    
    current_date = start_date.replace(hour=work_hours[0], minute=0, second=0, microsecond=0)
    
    while current_date < end_date:
        # Skip weekends if requested
        if exclude_weekends and current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            current_date = current_date.replace(hour=work_hours[0], minute=0)
            continue
        
        # Define work day boundaries
        day_start = current_date.replace(hour=work_hours[0], minute=0)
        day_end = current_date.replace(hour=work_hours[1], minute=0)
        
        # Find events on this day
        day_events = [e for e in parsed_events 
                     if e['start'].date() == current_date.date() and not e['all_day']]
        
        if not day_events:
            # Entire work day is free
            duration = int((day_end - day_start).total_seconds() / 60)
            if duration >= min_slot_minutes:
                free_slots.append({
                    'start': day_start.isoformat(),
                    'end': day_end.isoformat(),
                    'duration_minutes': duration,
                    'date': current_date.strftime('%Y-%m-%d'),
                    'day_name': current_date.strftime('%A')
                })
        else:
            # Check slot before first event
            first_event = day_events[0]
            if first_event['start'] > day_start:
                duration = int((first_event['start'] - day_start).total_seconds() / 60)
                if duration >= min_slot_minutes:
                    free_slots.append({
                        'start': day_start.isoformat(),
                        'end': first_event['start'].isoformat(),
                        'duration_minutes': duration,
                        'date': current_date.strftime('%Y-%m-%d'),
                        'day_name': current_date.strftime('%A')
                    })
            
            # Check slots between events
            for i in range(len(day_events) - 1):
                gap_start = day_events[i]['end']
                gap_end = day_events[i + 1]['start']
                duration = int((gap_end - gap_start).total_seconds() / 60)
                
                if duration >= min_slot_minutes:
                    free_slots.append({
                        'start': gap_start.isoformat(),
                        'end': gap_end.isoformat(),
                        'duration_minutes': duration,
                        'date': current_date.strftime('%Y-%m-%d'),
                        'day_name': current_date.strftime('%A')
                    })
            
            # Check slot after last event
            last_event = day_events[-1]
            if last_event['end'] < day_end:
                duration = int((day_end - last_event['end']).total_seconds() / 60)
                if duration >= min_slot_minutes:
                    free_slots.append({
                        'start': last_event['end'].isoformat(),
                        'end': day_end.isoformat(),
                        'duration_minutes': duration,
                        'date': current_date.strftime('%Y-%m-%d'),
                        'day_name': current_date.strftime('%A')
                    })
        
        # Move to next day
        current_date += timedelta(days=1)
        current_date = current_date.replace(hour=work_hours[0], minute=0)
    
    return free_slots


def suggest_task_slots(tasks: List[Dict], free_slots: List[Dict],
                       strategy: str = 'deadline_priority') -> Dict[str, Any]:
    """
    Suggest optimal slots for tasks based on various strategies.
    
    Args:
        tasks: List of tasks with 'name', 'duration_minutes', 'deadline', 'priority' (optional)
        free_slots: List of available time slots
        strategy: 'deadline_priority', 'priority_first', 'longest_first', 'balanced'
    
    Returns:
        Dict with suggested task assignments and unscheduled tasks
    """
    suggestions = []
    unscheduled = []
    remaining_slots = free_slots.copy()
    
    # Helper function to safely parse deadline
    def safe_parse_deadline(t):
        if not t.get('deadline'):
            return datetime.max.replace(tzinfo=None)
        dt = parse_datetime(t['deadline'])
        # Make naive for comparison
        return dt.replace(tzinfo=None) if dt.tzinfo else dt
    
    # Sort tasks based on strategy
    if strategy == 'deadline_priority':
        # Sort by deadline (earliest first), then by priority
        sorted_tasks = sorted(tasks, key=lambda t: (
            safe_parse_deadline(t),
            -t.get('priority', 0)
        ))
    elif strategy == 'priority_first':
        # Sort by priority (highest first), then by deadline
        sorted_tasks = sorted(tasks, key=lambda t: (
            -t.get('priority', 0),
            safe_parse_deadline(t)
        ))
    elif strategy == 'longest_first':
        # Sort by duration (longest first)
        sorted_tasks = sorted(tasks, key=lambda t: -t.get('duration_minutes', 0))
    else:  # balanced
        # Mix of deadline urgency and duration
        sorted_tasks = sorted(tasks, key=lambda t: (
            safe_parse_deadline(t),
            -t.get('duration_minutes', 0)
        ))
    
    # Try to assign each task to a slot
    for task in sorted_tasks:
        task_duration = task.get('duration_minutes', 60)
        task_deadline = None
        if task.get('deadline'):
            dt = parse_datetime(task['deadline'])
            task_deadline = dt.replace(tzinfo=None) if dt.tzinfo else dt
        assigned = False
        
        # Find suitable slot
        for i, slot in enumerate(remaining_slots):
            slot_start = parse_datetime(slot['start'])
            slot_start_naive = slot_start.replace(tzinfo=None) if slot_start.tzinfo else slot_start
            
            # Check if slot is before deadline (if deadline exists)
            if task_deadline and slot_start_naive > task_deadline:
                continue
            
            # Check if slot is long enough
            if slot['duration_minutes'] >= task_duration:
                # Assign task to this slot
                suggestions.append({
                    'task': task['name'],
                    'suggested_start': slot['start'],
                    'suggested_end': (slot_start + timedelta(minutes=task_duration)).isoformat(),
                    'duration_minutes': task_duration,
                    'date': slot['date'],
                    'day_name': slot['day_name'],
                    'slot_duration': slot['duration_minutes'],
                    'time_to_deadline': None if not task_deadline else 
                                       int((task_deadline - slot_start_naive).total_seconds() / 86400),
                    'priority': task.get('priority', 'non specificata'),
                    'reasoning': _explain_assignment(task, slot, task_deadline, slot_start_naive)
                })
                
                # Update or remove slot
                remaining_time = slot['duration_minutes'] - task_duration
                if remaining_time >= 30:  # Keep slot if at least 30 min remain
                    new_start = slot_start + timedelta(minutes=task_duration)
                    remaining_slots[i] = {
                        'start': new_start.isoformat(),
                        'end': slot['end'],
                        'duration_minutes': remaining_time,
                        'date': slot['date'],
                        'day_name': slot['day_name']
                    }
                else:
                    remaining_slots.pop(i)
                
                assigned = True
                break
        
        if not assigned:
            reason = _explain_no_assignment(task, task_deadline, remaining_slots)
            unscheduled.append({
                'task': task['name'],
                'duration_minutes': task_duration,
                'deadline': task.get('deadline'),
                'priority': task.get('priority', 'non specificata'),
                'reason': reason
            })
    
    return {
        'suggestions': suggestions,
        'unscheduled': unscheduled,
        'summary': {
            'tasks_scheduled': len(suggestions),
            'tasks_unscheduled': len(unscheduled),
            'remaining_slots': len(remaining_slots),
            'strategy_used': strategy
        }
    }


def _explain_assignment(task: Dict, slot: Dict, deadline: Optional[datetime], 
                       slot_start: datetime) -> str:
    """Generate explanation for why a task was assigned to a slot."""
    reasons = []
    
    if deadline:
        days_until = int((deadline - slot_start).total_seconds() / 86400)
        if days_until <= 1:
            reasons.append(f"deadline imminente (tra {days_until} giorni)")
        elif days_until <= 3:
            reasons.append(f"deadline vicina (tra {days_until} giorni)")
        else:
            reasons.append(f"deadline tra {days_until} giorni")
    
    if task.get('priority'):
        reasons.append(f"priorità {task['priority']}")
    
    if slot['duration_minutes'] >= task.get('duration_minutes', 60) * 1.5:
        reasons.append("slot ampio disponibile")
    
    return ", ".join(reasons) if reasons else "primo slot disponibile"


def _explain_no_assignment(task: Dict, deadline: Optional[datetime], 
                          remaining_slots: List[Dict]) -> str:
    """Generate explanation for why a task couldn't be scheduled."""
    if not remaining_slots:
        return "nessuno slot libero disponibile"
    
    task_duration = task.get('duration_minutes', 60)
    max_slot = max(remaining_slots, key=lambda s: s['duration_minutes'])
    
    if deadline:
        slots_before_deadline = [s for s in remaining_slots 
                                if parse_datetime(s['start']) < deadline]
        if not slots_before_deadline:
            return "nessuno slot disponibile prima della deadline"
        
        max_before_deadline = max(slots_before_deadline, 
                                 key=lambda s: s['duration_minutes'])
        if max_before_deadline['duration_minutes'] < task_duration:
            return f"slot più lungo prima della deadline: {max_before_deadline['duration_minutes']} min (servono {task_duration} min)"
    
    if max_slot['duration_minutes'] < task_duration:
        return f"slot più lungo disponibile: {max_slot['duration_minutes']} min (servono {task_duration} min)"
    
    return "impossibile trovare slot adatto"


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: suggest_task_slots.py <events_json> <tasks_json> [strategy]")
        print("Strategies: deadline_priority (default), priority_first, longest_first, balanced")
        sys.exit(1)
    
    # Load events
    with open(sys.argv[1], 'r') as f:
        events = json.load(f)
    
    # Load tasks
    with open(sys.argv[2], 'r') as f:
        tasks = json.load(f)
    
    # Get strategy
    strategy = sys.argv[3] if len(sys.argv) > 3 else 'deadline_priority'
    
    # Find free slots (next 14 days)
    start = datetime.now()
    end = start + timedelta(days=14)
    free_slots = find_free_slots(events, start, end)
    
    # Suggest task assignments
    result = suggest_task_slots(tasks, free_slots, strategy)
    print(json.dumps(result, indent=2, ensure_ascii=False))
