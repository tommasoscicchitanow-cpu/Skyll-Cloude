#!/usr/bin/env python3
"""
Analyze calendar events to detect scheduling conflicts and issues.
Checks for overlaps, insufficient travel time, overbooked days, and more.
"""

import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any


def parse_event(event: Dict) -> Dict:
    """Parse and standardize event data."""
    start = event.get('start', {})
    end = event.get('end', {})
    
    # Handle both dateTime and date formats
    start_time = start.get('dateTime') or start.get('date')
    end_time = end.get('dateTime') or end.get('date')
    
    if start_time:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    else:
        start_dt = None
    
    if end_time:
        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
    else:
        end_dt = None
    
    return {
        'id': event.get('id', 'unknown'),
        'summary': event.get('summary', 'Senza titolo'),
        'location': event.get('location', ''),
        'start': start_dt,
        'end': end_dt,
        'description': event.get('description', ''),
        'all_day': 'date' in start
    }


def check_time_overlap(event1: Dict, event2: Dict) -> bool:
    """Check if two events overlap in time."""
    if event1['all_day'] or event2['all_day']:
        return False
    
    if not (event1['start'] and event1['end'] and event2['start'] and event2['end']):
        return False
    
    return (event1['start'] < event2['end'] and event2['start'] < event1['end'])


def check_insufficient_travel_time(event1: Dict, event2: Dict, travel_minutes: int) -> bool:
    """
    Check if there's insufficient time between events for travel.
    
    Args:
        event1: First event (should end before event2)
        event2: Second event
        travel_minutes: Required travel time in minutes
    """
    if event1['all_day'] or event2['all_day']:
        return False
    
    if not (event1['end'] and event2['start']):
        return False
    
    gap = (event2['start'] - event1['end']).total_seconds() / 60
    return gap < travel_minutes


def analyze_schedule(events: List[Dict], travel_times: Dict[str, int] = None, 
                     max_daily_hours: int = 10) -> Dict[str, Any]:
    """
    Analyze calendar events for various issues.
    
    Args:
        events: List of calendar events
        travel_times: Dict mapping (location1, location2) tuples to travel minutes
        max_daily_hours: Maximum recommended working hours per day
    
    Returns:
        Dict containing lists of different issue types
    """
    parsed_events = [parse_event(e) for e in events]
    parsed_events.sort(key=lambda e: e['start'] if e['start'] else datetime.max)
    
    issues = {
        'overlaps': [],
        'insufficient_travel': [],
        'overbooked_days': [],
        'back_to_back': [],
        'long_days': []
    }
    
    # Check for overlaps and travel time issues
    for i, event1 in enumerate(parsed_events):
        if event1['all_day'] or not event1['start']:
            continue
            
        for event2 in parsed_events[i+1:]:
            if event2['all_day'] or not event2['start']:
                continue
            
            # Same day check
            if event1['start'].date() != event2['start'].date():
                break
            
            # Time overlap
            if check_time_overlap(event1, event2):
                issues['overlaps'].append({
                    'event1': event1['summary'],
                    'event2': event2['summary'],
                    'time1': f"{event1['start'].strftime('%H:%M')} - {event1['end'].strftime('%H:%M')}",
                    'time2': f"{event2['start'].strftime('%H:%M')} - {event2['end'].strftime('%H:%M')}",
                    'date': event1['start'].strftime('%Y-%m-%d')
                })
            
            # Check if event2 comes right after event1
            if event1['end'] and event2['start'] and event1['end'] <= event2['start']:
                # Calculate required travel time
                if travel_times and event1['location'] and event2['location']:
                    key = (event1['location'], event2['location'])
                    required_travel = travel_times.get(key, 0)
                    
                    if check_insufficient_travel_time(event1, event2, required_travel):
                        gap_minutes = int((event2['start'] - event1['end']).total_seconds() / 60)
                        issues['insufficient_travel'].append({
                            'event1': event1['summary'],
                            'event2': event2['summary'],
                            'location1': event1['location'],
                            'location2': event2['location'],
                            'gap_minutes': gap_minutes,
                            'required_minutes': required_travel,
                            'shortage_minutes': required_travel - gap_minutes,
                            'date': event1['start'].strftime('%Y-%m-%d'),
                            'time': f"{event1['end'].strftime('%H:%M')} → {event2['start'].strftime('%H:%M')}"
                        })
                
                # Back to back events (less than 15 minutes gap)
                gap = (event2['start'] - event1['end']).total_seconds() / 60
                if gap < 15:
                    issues['back_to_back'].append({
                        'event1': event1['summary'],
                        'event2': event2['summary'],
                        'gap_minutes': int(gap),
                        'date': event1['start'].strftime('%Y-%m-%d'),
                        'time': f"{event1['end'].strftime('%H:%M')} → {event2['start'].strftime('%H:%M')}"
                    })
    
    # Check for overbooked days
    daily_hours = {}
    for event in parsed_events:
        if event['all_day'] or not (event['start'] and event['end']):
            continue
        
        date = event['start'].date()
        duration = (event['end'] - event['start']).total_seconds() / 3600
        
        if date not in daily_hours:
            daily_hours[date] = {'total': 0, 'events': [], 'start': event['start'], 'end': event['end']}
        
        daily_hours[date]['total'] += duration
        daily_hours[date]['events'].append(event['summary'])
        
        # Update day span
        if event['start'] < daily_hours[date]['start']:
            daily_hours[date]['start'] = event['start']
        if event['end'] > daily_hours[date]['end']:
            daily_hours[date]['end'] = event['end']
    
    for date, data in daily_hours.items():
        if data['total'] > max_daily_hours:
            issues['overbooked_days'].append({
                'date': date.strftime('%Y-%m-%d'),
                'total_hours': round(data['total'], 1),
                'max_hours': max_daily_hours,
                'excess_hours': round(data['total'] - max_daily_hours, 1),
                'event_count': len(data['events']),
                'events': data['events']
            })
        
        # Check for very long days (first to last event > 12 hours)
        day_span = (data['end'] - data['start']).total_seconds() / 3600
        if day_span > 12:
            issues['long_days'].append({
                'date': date.strftime('%Y-%m-%d'),
                'span_hours': round(day_span, 1),
                'start_time': data['start'].strftime('%H:%M'),
                'end_time': data['end'].strftime('%H:%M'),
                'event_count': len(data['events'])
            })
    
    # Add summary
    total_issues = sum(len(v) for v in issues.values())
    
    return {
        'issues': issues,
        'summary': {
            'total_issues': total_issues,
            'has_conflicts': total_issues > 0,
            'events_analyzed': len(parsed_events),
            'issue_breakdown': {k: len(v) for k, v in issues.items()}
        }
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: analyze_schedule.py <events_json_file> [travel_times_json_file]")
        print("Example: analyze_schedule.py events.json travel_times.json")
        sys.exit(1)
    
    # Load events
    with open(sys.argv[1], 'r') as f:
        events = json.load(f)
    
    # Load travel times if provided
    travel_times = None
    if len(sys.argv) > 2:
        with open(sys.argv[2], 'r') as f:
            travel_times_data = json.load(f)
            # Convert keys from strings back to tuples
            travel_times = {tuple(k.split(' -> ')): v for k, v in travel_times_data.items()}
    
    result = analyze_schedule(events, travel_times)
    print(json.dumps(result, indent=2, ensure_ascii=False))
