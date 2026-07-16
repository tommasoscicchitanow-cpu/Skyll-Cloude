#!/usr/bin/env python3
"""
Calculate travel time and distance between two locations by car.
Uses Google Maps Distance Matrix API for accurate, real-time routing.
"""

import sys
import json
import requests
from datetime import datetime

def calculate_travel(origin, destination, departure_time=None, api_key=None):
    """
    Calculate travel time and distance between two locations.
    
    Args:
        origin: Starting location (address or place name)
        destination: Destination location (address or place name)
        departure_time: Optional datetime for departure (for traffic estimates)
        api_key: Google Maps API key (can also be set via GOOGLE_MAPS_API_KEY env var)
    
    Returns:
        dict with 'duration_minutes', 'distance_km', 'duration_in_traffic_minutes'
    """
    
    if not api_key:
        import os
        api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    
    if not api_key:
        return {
            'error': 'API key required. Set GOOGLE_MAPS_API_KEY environment variable or pass as argument',
            'manual_estimate': True
        }
    
    # Build API request
    url = 'https://maps.googleapis.com/maps/api/distancematrix/json'
    params = {
        'origins': origin,
        'destinations': destination,
        'mode': 'driving',
        'key': api_key,
        'language': 'it'
    }
    
    # Add departure time for traffic estimates if provided
    if departure_time:
        if isinstance(departure_time, str):
            departure_time = datetime.fromisoformat(departure_time)
        timestamp = int(departure_time.timestamp())
        params['departure_time'] = timestamp
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] != 'OK':
            return {'error': f"API error: {data['status']}", 'manual_estimate': True}
        
        element = data['rows'][0]['elements'][0]
        
        if element['status'] != 'OK':
            return {'error': f"Route error: {element['status']}", 'manual_estimate': True}
        
        result = {
            'duration_minutes': element['duration']['value'] // 60,
            'duration_text': element['duration']['text'],
            'distance_km': element['distance']['value'] / 1000,
            'distance_text': element['distance']['text'],
            'origin': origin,
            'destination': destination
        }
        
        # Add traffic info if available
        if 'duration_in_traffic' in element:
            result['duration_in_traffic_minutes'] = element['duration_in_traffic']['value'] // 60
            result['duration_in_traffic_text'] = element['duration_in_traffic']['text']
        
        return result
        
    except requests.RequestException as e:
        return {'error': f"Request failed: {str(e)}", 'manual_estimate': True}


def estimate_travel_manual(distance_km=None, city_type='urban'):
    """
    Provide manual estimates when API is not available.
    
    Args:
        distance_km: Distance in kilometers
        city_type: 'urban' (40 km/h avg), 'suburban' (60 km/h avg), 'highway' (90 km/h avg)
    
    Returns:
        dict with estimated duration_minutes
    """
    avg_speeds = {
        'urban': 40,      # City center
        'suburban': 60,   # Periferia/cittadina
        'highway': 90     # Autostrada
    }
    
    avg_speed = avg_speeds.get(city_type, 50)
    
    if distance_km:
        duration_minutes = int((distance_km / avg_speed) * 60)
        return {
            'duration_minutes': duration_minutes,
            'distance_km': distance_km,
            'estimate_type': 'manual',
            'note': f'Stima basata su velocità media {avg_speed} km/h per {city_type}'
        }
    
    return {
        'error': 'Distance required for manual estimate',
        'manual_estimate': True
    }


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: calculate_travel.py <origin> <destination> [departure_time] [api_key]")
        print("Example: calculate_travel.py 'Roma, Italia' 'Milano, Italia'")
        print("Example: calculate_travel.py 'Via Roma 1, Pescara' 'Piazza Salotto, Pescara' '2025-10-27T09:00:00'")
        sys.exit(1)
    
    origin = sys.argv[1]
    destination = sys.argv[2]
    departure_time = sys.argv[3] if len(sys.argv) > 3 else None
    api_key = sys.argv[4] if len(sys.argv) > 4 else None
    
    result = calculate_travel(origin, destination, departure_time, api_key)
    print(json.dumps(result, indent=2, ensure_ascii=False))
