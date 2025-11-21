"""
Skrypt tworzący mapowanie Trans.eu ID -> TimoCom ID
Na podstawie najbliższych punktów geograficznych
"""

import csv
import json
from pathlib import Path
from math import radians, cos, sin, asin, sqrt

def haversine(lon1, lat1, lon2, lat2):
    """
    Oblicza odległość między dwoma punktami na kuli ziemskiej (w km)
    """
    # Konwersja na radiany
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Wzór haversine
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Promień Ziemi w km
    return c * r

def load_timocom_centers():
    """Wczytuje punkty TimoCom z CSV"""
    csv_path = Path(__file__).parent / 'timo_centers.csv'
    centers = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            centers.append({
                'id': int(row['id']),
                'lat': float(row['latitude']),
                'lon': float(row['longitude']),
                'country': row['country'],
                'city': row['city_name']
            })
    
    return centers

def load_transeu_regions():
    """Wczytuje regiony Trans.eu z GeoJSON"""
    geojson_path = Path(__file__).parent / 'static' / 'data' / 'voronoi_regions.geojson'
    
    with open(geojson_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    regions = []
    for feature in data['features']:
        props = feature['properties']
        
        # Oblicz centroid z geometrii (uproszczone - użyj lat/lon z properties)
        regions.append({
            'id': props['id'],
            'lat': props['latitude'],
            'lon': props['longitude'],
            'country': props.get('country_code', props.get('country', '')),
            'city': props.get('city_name', '')
        })
    
    return regions

def generate_mapping():
    """Generuje mapowanie Trans.eu -> TimoCom"""
    
    timocom_centers = load_timocom_centers()
    transeu_regions = load_transeu_regions()
    
    print(f"Wczytano {len(timocom_centers)} punktów TimoCom")
    print(f"Wczytano {len(transeu_regions)} regionów Trans.eu")
    
    # Dla każdego regionu Trans.eu znajdź najbliższy punkt TimoCom
    mapping = {}
    
    for trans_region in transeu_regions:
        trans_id = trans_region['id']
        trans_lat = trans_region['lat']
        trans_lon = trans_region['lon']
        trans_country = trans_region['country']
        
        # Znajdź najbliższy punkt TimoCom
        min_distance = float('inf')
        closest_timocom_id = None
        
        for timo_center in timocom_centers:
            # Oblicz odległość
            distance = haversine(trans_lon, trans_lat, timo_center['lon'], timo_center['lat'])
            
            # Premiuj punkty z tego samego kraju
            if timo_center['country'] == trans_country:
                distance *= 0.5  # Zmniejsz odległość o połowę dla tego samego kraju
            
            if distance < min_distance:
                min_distance = distance
                closest_timocom_id = timo_center['id']
        
        mapping[trans_id] = {
            'timocom_id': closest_timocom_id,
            'distance_km': round(min_distance, 2),
            'trans_country': trans_country,
            'trans_city': trans_region['city']
        }
    
    print(f"\nWygenerowano mapowanie dla {len(mapping)} regionów")
    
    # Zapisz mapowanie do pliku JSON
    output_path = Path(__file__).parent / 'static' / 'data' / 'transeu_to_timocom_mapping.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)
    
    print(f"Zapisano mapowanie do: {output_path}")
    
    # Wyświetl przykłady
    print("\nPrzykładowe mapowania:")
    for trans_id in sorted(mapping.keys())[:10]:
        data = mapping[trans_id]
        print(f"  Trans.eu ID {trans_id} -> TimoCom ID {data['timocom_id']} (dystans: {data['distance_km']} km)")
    
    # Statystyki
    distances = [data['distance_km'] for data in mapping.values()]
    avg_distance = sum(distances) / len(distances)
    max_distance = max(distances)
    
    print(f"\nStatystyki:")
    print(f"  Średnia odległość: {avg_distance:.2f} km")
    print(f"  Maksymalna odległość: {max_distance:.2f} km")

if __name__ == '__main__':
    generate_mapping()
