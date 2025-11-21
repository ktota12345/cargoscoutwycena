"""
Skrypt do masowego sprawdzania stawek historycznych dla tras.
Używa mapowania regionów i pobiera dane z bazy PostgreSQL.
"""

import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
import time
import glob
import requests

# Załaduj zmienne środowiskowe
load_dotenv()

# Konfiguracja bazy danych
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_USER = os.getenv("POSTGRES_USER")
DB_NAME = os.getenv("POSTGRES_DB")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

# Konfiguracja AWS Location Service
AWS_LOCATION_API_KEY = os.getenv("AWS_LOCATION_API_KEY")
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")

# Minimum dystans w km - trasy poniżej tej wartości nie są w bazie
MIN_DISTANCE_KM = 150

# Interwał zapisu w sekundach (5 minut)
AUTOSAVE_INTERVAL_SECONDS = 300


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Oblicza dystans między dwoma punktami na Ziemi używając wzoru Haversine.
    Zwraca dystans w kilometrach.
    """
    # Konwersja ze stopni na radiany
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Wzór Haversine
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Promień Ziemi w km
    r = 6371
    
    return c * r


def get_aws_route_distance(start_lat: float, start_lng: float, end_lat: float, end_lng: float) -> Optional[float]:
    """
    Wywołuje AWS Location Service Routes API aby obliczyć rzeczywisty dystans drogowy.
    Zwraca dystans w kilometrach lub None w przypadku błędu.
    
    Args:
        start_lat: Szerokość geograficzna punktu startowego
        start_lng: Długość geograficzna punktu startowego
        end_lat: Szerokość geograficzna punktu docelowego
        end_lng: Długość geograficzna punktu docelowego
    
    Returns:
        float: Dystans w kilometrach lub None
    """
    if not AWS_LOCATION_API_KEY:
        return None
    
    try:
        # AWS Location Service Routes API v2 endpoint
        # API key jest przekazywany jako parametr URL
        url = f"https://routes.geo.{AWS_REGION}.amazonaws.com/v2/routes?key={AWS_LOCATION_API_KEY}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "Origin": [start_lng, start_lat],
            "Destination": [end_lng, end_lat],
            "TravelMode": "Truck",
            "OptimizeRoutingFor": "FastestRoute"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Pobierz dystans z pierwszej trasy (Routes[0].Summary.Distance)
            # AWS zwraca dystans w metrach
            if 'Routes' in data and len(data['Routes']) > 0:
                # Suma dystansów ze wszystkich legs
                total_distance = 0
                for leg in data['Routes'][0].get('Legs', []):
                    vehicle_details = leg.get('VehicleLegDetails', {})
                    travel_steps = vehicle_details.get('TravelSteps', [])
                    for step in travel_steps:
                        total_distance += step.get('Distance', 0)
                
                distance_km = total_distance / 1000.0
                return round(distance_km, 2)
            return None
        else:
            return None
            
    except requests.exceptions.Timeout:
        return None
    except Exception:
        return None


def load_region_coordinates() -> Dict[int, Tuple[float, float]]:
    """Ładuje współrzędne regionów TimoCom z pliku GeoJSON"""
    with open('static/data/timocom_regions.geojson', 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    coordinates = {}
    for feature in geojson_data['features']:
        region_id = feature['properties']['id']
        # GeoJSON używa [longitude, latitude]
        coords = feature['geometry']['coordinates']
        # Zamieniamy na [latitude, longitude]
        coordinates[region_id] = (coords[1], coords[0])
    
    return coordinates


def load_postal_coordinates() -> Dict[str, Tuple[float, float]]:
    """
    Ładuje współrzędne kodów pocztowych z filtered_postal_codes.geojson.
    Zwraca dict: {'PL50': (lat, lng), 'DE10': (lat, lng), ...}
    """
    with open('package/filtered_postal_codes.geojson', 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    coordinates = {}
    for feature in geojson_data['features']:
        country_code = feature['properties']['country_code']
        postal_code = feature['properties']['postal_code']
        latitude = feature['properties']['latitude']
        longitude = feature['properties']['longitude']
        
        # Klucz: country_code + postal_code (np. "PL50", "DE10")
        key = f"{country_code}{postal_code}"
        coordinates[key] = (latitude, longitude)
    
    return coordinates


def load_mappings() -> Tuple[Dict, Dict]:
    """Ładuje mapowania regionów z plików JSON"""
    
    # Mapowanie Trans.eu -> TimoCom
    with open('static/data/transeu_to_timocom_mapping.json', 'r', encoding='utf-8') as f:
        transeu_to_timocom = json.load(f)
    
    # Mapowanie kod pocztowy -> region Trans.eu
    with open('static/data/postal_code_to_region_transeu.json', 'r', encoding='utf-8') as f:
        postal_to_transeu = json.load(f)
    
    # Mapowanie kod pocztowy -> region TimoCom
    with open('static/data/postal_code_to_region_timocom.json', 'r', encoding='utf-8') as f:
        postal_to_timocom = json.load(f)
    
    return {
        'transeu_to_timocom': transeu_to_timocom,
        'postal_to_transeu': postal_to_transeu,
        'postal_to_timocom': postal_to_timocom
    }, postal_to_transeu


def parse_route_code(route_code: str) -> Tuple[str, str, str, str]:
    """
    Parsuje kod trasy np. 'NL89-CZ50' na komponenty.
    Zwraca: (start_country, start_postal, end_country, end_postal)
    """
    parts = route_code.split('-')
    if len(parts) != 2:
        raise ValueError(f"Nieprawidłowy format trasy: {route_code}")
    
    start = parts[0]
    end = parts[1]
    
    # Wyciągnij kraj (2 pierwsze znaki) i kod pocztowy (reszta)
    start_country = start[:2]
    start_postal = start[2:]
    
    end_country = end[:2]
    end_postal = end[2:]
    
    return start_country, start_postal, end_country, end_postal


def map_route_to_regions(route_code: str, mappings: Dict) -> Dict[str, Any]:
    """
    Mapuje trasę na regiony TimoCom i Trans.eu.
    Zwraca słownik z informacjami o mapowaniu.
    """
    start_country, start_postal, end_country, end_postal = parse_route_code(route_code)
    
    # Stwórz klucze dla mapowania
    start_key = f"{start_country}{start_postal}"
    end_key = f"{end_country}{end_postal}"
    
    result = {
        'original_route': route_code,
        'start_country': start_country,
        'start_postal': start_postal,
        'end_country': end_country,
        'end_postal': end_postal,
        'transeu_start': None,
        'transeu_end': None,
        'timocom_start': None,
        'timocom_end': None,
        'mapping_success': False
    }
    
    # Mapowanie Trans.eu (wyciągnij region_id z obiektu)
    if start_key in mappings['postal_to_transeu']:
        transeu_start_obj = mappings['postal_to_transeu'][start_key]
        if isinstance(transeu_start_obj, dict):
            result['transeu_start'] = transeu_start_obj.get('region_id')
        else:
            result['transeu_start'] = transeu_start_obj
    
    if end_key in mappings['postal_to_transeu']:
        transeu_end_obj = mappings['postal_to_transeu'][end_key]
        if isinstance(transeu_end_obj, dict):
            result['transeu_end'] = transeu_end_obj.get('region_id')
        else:
            result['transeu_end'] = transeu_end_obj
    
    # Mapowanie TimoCom (przez Trans.eu jeśli bezpośrednie mapowanie nie istnieje)
    if start_key in mappings['postal_to_timocom']:
        timocom_start_obj = mappings['postal_to_timocom'][start_key]
        if isinstance(timocom_start_obj, dict):
            result['timocom_start'] = timocom_start_obj.get('timocom_id') or timocom_start_obj.get('region_id')
        else:
            result['timocom_start'] = timocom_start_obj
    elif result['transeu_start'] and str(result['transeu_start']) in mappings['transeu_to_timocom']:
        timocom_mapped = mappings['transeu_to_timocom'][str(result['transeu_start'])]
        if isinstance(timocom_mapped, dict):
            result['timocom_start'] = timocom_mapped.get('timocom_id') or timocom_mapped.get('region_id')
        else:
            result['timocom_start'] = timocom_mapped
    
    if end_key in mappings['postal_to_timocom']:
        timocom_end_obj = mappings['postal_to_timocom'][end_key]
        if isinstance(timocom_end_obj, dict):
            result['timocom_end'] = timocom_end_obj.get('timocom_id') or timocom_end_obj.get('region_id')
        else:
            result['timocom_end'] = timocom_end_obj
    elif result['transeu_end'] and str(result['transeu_end']) in mappings['transeu_to_timocom']:
        timocom_mapped = mappings['transeu_to_timocom'][str(result['transeu_end'])]
        if isinstance(timocom_mapped, dict):
            result['timocom_end'] = timocom_mapped.get('timocom_id') or timocom_mapped.get('region_id')
        else:
            result['timocom_end'] = timocom_mapped
    
    # Sprawdź czy mapowanie się powiodło
    if result['timocom_start'] and result['timocom_end']:
        result['mapping_success'] = True
    
    return result


def get_all_historical_data_timocom_batch(route_pairs: List[Tuple[int, int]]) -> Dict:
    """
    Pobiera dane historyczne z TimoCom dla wszystkich par regionów naraz.
    Pobiera dane dla wszystkich typów pojazdów: naczepa, do 3.5t, do 12t.
    Zwraca dict: {(start, end, days): {vehicle_type: {avg, median, offers}}}
    """
    if not route_pairs:
        return {}
    
    results = {}
    
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Dla każdego okresu (7, 30, 90) zrób jedno zapytanie dla wszystkich par
        for days in [7, 30, 90]:
            # Buduj listę warunków OR dla wszystkich par
            conditions = []
            for start, end in route_pairs:
                conditions.append(f"(o.starting_id = {start} AND o.destination_id = {end})")
            
            where_clause = " OR ".join(conditions)
            
            query = f"""
                SELECT
                    o.starting_id,
                    o.destination_id,
                    COUNT(DISTINCT o.enlistment_date) AS num_days,
                    
                    -- Naczepa (Trailer)
                    ROUND(AVG(o.trailer_avg_price_per_km), 4) AS trailer_avg,
                    ROUND(AVG(o.trailer_median_price_per_km), 4) AS trailer_median,
                    SUM(o.number_of_offers_total) AS trailer_offers,
                    
                    -- Do 3.5t
                    ROUND(AVG(o.vehicle_up_to_3_5_t_avg_price_per_km), 4) AS v3_5t_avg,
                    SUM(o.number_of_offers_total) AS v3_5t_offers,
                    
                    -- Do 12t
                    ROUND(AVG(o.vehicle_up_to_12_t_avg_price_per_km), 4) AS v12t_avg,
                    SUM(o.number_of_offers_total) AS v12t_offers
                    
                FROM public.offers AS o
                WHERE ({where_clause})
                  AND o.enlistment_date >= CURRENT_DATE - {days}
                GROUP BY o.starting_id, o.destination_id
                HAVING 
                    AVG(o.trailer_avg_price_per_km) IS NOT NULL
                    OR AVG(o.vehicle_up_to_3_5_t_avg_price_per_km) IS NOT NULL
                    OR AVG(o.vehicle_up_to_12_t_avg_price_per_km) IS NOT NULL
            """
            
            cur.execute(query)
            rows = cur.fetchall()
            
            for row in rows:
                key = (row['starting_id'], row['destination_id'], days)
                
                result_data = {
                    'days': row['num_days'] or 0,
                    'trailer': {},
                    'vehicle_3_5t': {},
                    'vehicle_12t': {}
                }
                
                # Naczepa
                if row['trailer_avg']:
                    result_data['trailer'] = {
                        'avg': float(row['trailer_avg']),
                        'median': float(row['trailer_median']) if row['trailer_median'] else None,
                        'offers': int(row['trailer_offers']) if row['trailer_offers'] else 0
                    }
                
                # Do 3.5t
                if row['v3_5t_avg']:
                    result_data['vehicle_3_5t'] = {
                        'avg': float(row['v3_5t_avg']),
                        'offers': int(row['v3_5t_offers']) if row['v3_5t_offers'] else 0
                    }
                
                # Do 12t
                if row['v12t_avg']:
                    result_data['vehicle_12t'] = {
                        'avg': float(row['v12t_avg']),
                        'offers': int(row['v12t_offers']) if row['v12t_offers'] else 0
                    }
                
                results[key] = result_data
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n[ERROR] Batch TimoCom query failed: {e}")
    
    return results


def get_all_historical_data_transeu_batch(route_pairs: List[Tuple[int, int]]) -> Dict:
    """
    Pobiera dane historyczne z Trans.eu dla wszystkich par regionów naraz.
    Pobiera dane dla wszystkich typów pojazdów: lorry, solo, bus, double_trailer.
    Zwraca dict: {(start, end, days): {vehicle_type: {avg, median, records}}}
    """
    if not route_pairs:
        return {}
    
    results = {}
    
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            dbname=DB_NAME
        )
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Dla każdego okresu (7, 30, 90) zrób jedno zapytanie dla wszystkich par
        for days in [7, 30, 90]:
            # Buduj listę warunków OR dla wszystkich par
            conditions = []
            for start, end in route_pairs:
                conditions.append(f"(o.starting_id = {start} AND o.destination_id = {end})")
            
            where_clause = " OR ".join(conditions)
            
            query = f"""
                SELECT
                    o.starting_id,
                    o.destination_id,
                    COUNT(DISTINCT o.enlistment_date) AS num_days,
                    
                    -- Lorry (ciężarówka z naczepą)
                    ROUND(AVG(o.lorry_avg_price_per_km), 4) AS lorry_avg,
                    ROUND(AVG(o.lorry_median_price_per_km), 4) AS lorry_median,
                    COUNT(CASE WHEN o.lorry_avg_price_per_km IS NOT NULL THEN 1 END) AS lorry_records,
                    
                    -- Solo (samochód bez naczepy)
                    ROUND(AVG(o.solo_avg_price_per_km), 4) AS solo_avg,
                    ROUND(AVG(o.solo_median_price_per_km), 4) AS solo_median,
                    COUNT(CASE WHEN o.solo_avg_price_per_km IS NOT NULL THEN 1 END) AS solo_records,
                    
                    -- Bus (autobusy)
                    ROUND(AVG(o.bus_avg_price_per_km), 4) AS bus_avg,
                    ROUND(AVG(o.bus_median_price_per_km), 4) AS bus_median,
                    COUNT(CASE WHEN o.bus_avg_price_per_km IS NOT NULL THEN 1 END) AS bus_records,
                    
                    -- Double Trailer (podwójna naczepa)
                    ROUND(AVG(o.double_trailer_avg_price_per_km), 4) AS double_avg,
                    ROUND(AVG(o.double_trailer_median_price_per_km), 4) AS double_median,
                    COUNT(CASE WHEN o.double_trailer_avg_price_per_km IS NOT NULL THEN 1 END) AS double_records
                    
                FROM public."OffersTransEU" AS o
                WHERE ({where_clause})
                  AND o.enlistment_date >= CURRENT_DATE - {days}
                GROUP BY o.starting_id, o.destination_id
                HAVING 
                    AVG(o.lorry_avg_price_per_km) IS NOT NULL
                    OR AVG(o.solo_avg_price_per_km) IS NOT NULL
                    OR AVG(o.bus_avg_price_per_km) IS NOT NULL
                    OR AVG(o.double_trailer_avg_price_per_km) IS NOT NULL
            """
            
            cur.execute(query)
            rows = cur.fetchall()
            
            for row in rows:
                key = (row['starting_id'], row['destination_id'], days)
                
                result_data = {
                    'days': row['num_days'] or 0,
                    'lorry': {},
                    'solo': {},
                    'bus': {},
                    'double_trailer': {}
                }
                
                # Lorry
                if row['lorry_avg']:
                    result_data['lorry'] = {
                        'avg': float(row['lorry_avg']),
                        'median': float(row['lorry_median']) if row['lorry_median'] else None,
                        'records': int(row['lorry_records']) if row['lorry_records'] else 0
                    }
                
                # Solo
                if row['solo_avg']:
                    result_data['solo'] = {
                        'avg': float(row['solo_avg']),
                        'median': float(row['solo_median']) if row['solo_median'] else None,
                        'records': int(row['solo_records']) if row['solo_records'] else 0
                    }
                
                # Bus
                if row['bus_avg']:
                    result_data['bus'] = {
                        'avg': float(row['bus_avg']),
                        'median': float(row['bus_median']) if row['bus_median'] else None,
                        'records': int(row['bus_records']) if row['bus_records'] else 0
                    }
                
                # Double Trailer
                if row['double_avg']:
                    result_data['double_trailer'] = {
                        'avg': float(row['double_avg']),
                        'median': float(row['double_median']) if row['double_median'] else None,
                        'records': int(row['double_records']) if row['double_records'] else 0
                    }
                
                results[key] = result_data
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n[ERROR] Batch Trans.eu query failed: {e}")
    
    return results


def save_progress(results: List[Dict], filename: str):
    """Zapisuje wyniki do pliku (checkpoint)"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        # \n na początku żeby nie nadpisać progress bara
        print(f"\n[AUTOSAVE] Zapisano postęp ({len(results)} tras) do {filename}")
    except Exception as e:
        print(f"\n[AUTOSAVE ERROR] Nie udało się zapisać: {e}")


def process_single_route(route_code: str, mappings: Dict, postal_coords: Dict[str, Tuple[float, float]], 
                         timocom_data_cache: Dict, transeu_data_cache: Dict) -> Dict:
    """
    Przetwarza pojedynczą trasę i zwraca wynik.
    Używa cache z batch queries - bardzo szybkie!
    Oblicza dystans używając AWS Location Service API Routes.
    """
    try:
        # Mapowanie
        mapping = map_route_to_regions(route_code, mappings)
        
        if not mapping['mapping_success']:
            return {
                **mapping,
                'status': 'mapping_failed',
                'data': None
            }
        
        # Oblicz dystans używając AWS Location Service API
        # Pobierz współrzędne z postal_coords używając country_code + postal_code
        start_key = f"{mapping['start_country']}{mapping['start_postal']}"
        end_key = f"{mapping['end_country']}{mapping['end_postal']}"
        
        if start_key in postal_coords and end_key in postal_coords:
            start_lat, start_lng = postal_coords[start_key]
            end_lat, end_lng = postal_coords[end_key]
            
            # Wywołaj AWS API aby obliczyć rzeczywisty dystans drogowy
            distance_km = get_aws_route_distance(start_lat, start_lng, end_lat, end_lng)
            
            if distance_km is not None:
                mapping['distance_km'] = distance_km
                
                if distance_km < MIN_DISTANCE_KM:
                    return {
                        **mapping,
                        'status': 'too_short',
                        'data': None,
                        'reason': f'Dystans {distance_km:.0f} km jest poniżej minimum {MIN_DISTANCE_KM} km'
                    }
            else:
                # Jeśli AWS API nie zadziałało, użyj fallback (haversine)
                distance_km = haversine_distance(start_lat, start_lng, end_lat, end_lng)
                mapping['distance_km'] = round(distance_km, 2)
                mapping['distance_method'] = 'haversine_fallback'
                print(f"[WARNING] AWS API failed for {route_code}, using Haversine fallback")
                
                if distance_km < MIN_DISTANCE_KM:
                    return {
                        **mapping,
                        'status': 'too_short',
                        'data': None,
                        'reason': f'Dystans {distance_km:.0f} km jest poniżej minimum {MIN_DISTANCE_KM} km'
                    }
        else:
            mapping['distance_km'] = None
            print(f"[WARNING] Missing postal coordinates for {route_code}: {start_key} or {end_key}")
        
        # Pobierz dane dla różnych okresów z cache
        route_data = {
            'timocom': {},
            'transeu': {}
        }
        
        for period in [7, 30, 90]:
            # TimoCom - pobierz z cache
            timocom_key = (mapping['timocom_start'], mapping['timocom_end'], period)
            route_data['timocom'][f'{period}d'] = timocom_data_cache.get(timocom_key, {})
            
            # Trans.eu - pobierz z cache
            transeu_key = (mapping['transeu_start'], mapping['transeu_end'], period)
            route_data['transeu'][f'{period}d'] = transeu_data_cache.get(transeu_key, {})
        
        return {
            **mapping,
            'status': 'success',
            'data': route_data
        }
        
    except Exception as e:
        return {
            'original_route': route_code,
            'status': 'error',
            'error': str(e),
            'data': None
        }


def process_routes(routes: List[str], mappings: Dict, postal_coords: Dict[str, Tuple[float, float]], output_filename: str, resume_from: int = 0) -> List[Dict]:
    """
    Przetwarza listę tras i pobiera dla nich dane historyczne.
    OPTYMALIZACJA: Używa batch queries - 6 zapytań SQL zamiast ~7600!
    1. Zbiera wszystkie unikalne pary regionów
    2. Wykonuje batch queries dla wszystkich par naraz
    3. Przetwarza trasy używając cache (szybko!)
    
    Filtruje trasy < 150 km (nie ma ich w bazie).
    Zapisuje postęp co 5 minut.
    Może wznawiać od checkpointu.
    Używa AWS Location Service API Routes do obliczania dystansów.
    """
    checkpoint_file = output_filename.replace('.json', '_checkpoint.json')
    
    # Wczytaj istniejące dane z checkpointu jeśli wznawiamy
    if resume_from > 0 and os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        print(f"[RESUME] Wczytano {len(results)} już przetworzonych tras z checkpointu")
    else:
        results = []
    
    total = len(routes)
    last_save_time = time.time()
    start_time = time.time()
    
    # Liczniki dla postępu - zlicz już przetworzone
    processed = resume_from
    success_count = sum(1 for r in results if r.get('status') in ['success', 'cached'])
    skipped_count = sum(1 for r in results if r.get('status') not in ['success', 'cached'])
    
    print(f"\n[BATCH] Przygotowuję batch queries...")
    
    # Krok 1: Zbierz wszystkie unikalne pary regionów które trzeba sprawdzić
    timocom_pairs = set()
    transeu_pairs = set()
    
    print(f"[BATCH] Filtrowanie tras i obliczanie dystansów...")
    for idx, route_code in enumerate(routes, 1):
        if idx <= resume_from:
            continue
        
        # Progress dla filtrowania
        if idx % 100 == 0:
            print(f"\r  Sprawdzono {idx}/{len(routes)} tras...", end='', flush=True)
        
        try:
            mapping = map_route_to_regions(route_code, mappings)
            if mapping['mapping_success']:
                # Sprawdź dystans używając postal coordinates
                start_key = f"{mapping['start_country']}{mapping['start_postal']}"
                end_key = f"{mapping['end_country']}{mapping['end_postal']}"
                
                if start_key in postal_coords and end_key in postal_coords:
                    start_lat, start_lng = postal_coords[start_key]
                    end_lat, end_lng = postal_coords[end_key]
                    
                    # Użyj AWS API lub haversine jako fallback do szybkiego filtrowania
                    # Dla batch queries używamy haversine jako szybkiej metody filtrowania
                    # Dokładny dystans AWS będzie obliczony później dla każdej trasy
                    distance_km = haversine_distance(start_lat, start_lng, end_lat, end_lng)
                    
                    if distance_km >= MIN_DISTANCE_KM:
                        timocom_pairs.add((mapping['timocom_start'], mapping['timocom_end']))
                        transeu_pairs.add((mapping['transeu_start'], mapping['transeu_end']))
        except:
            pass
    
    print(f"\r  Sprawdzono {len(routes)} tras. Gotowe!       ")
    
    print(f"[BATCH] Znaleziono {len(timocom_pairs)} unikalnych par TimoCom")
    print(f"[BATCH] Znaleziono {len(transeu_pairs)} unikalnych par Trans.eu")
    
    # Krok 2: Pobierz wszystkie dane batch queries (6 zapytań zamiast ~7600!)
    print(f"[BATCH] Wykonuję batch queries...")
    timocom_data_cache = get_all_historical_data_timocom_batch(list(timocom_pairs))
    transeu_data_cache = get_all_historical_data_transeu_batch(list(transeu_pairs))
    print(f"[BATCH] Wczytano {len(timocom_data_cache)} wyników TimoCom")
    print(f"[BATCH] Wczytano {len(transeu_data_cache)} wyników Trans.eu")
    
    # Krok 3: Przetwarzaj trasy używając cache (szybko, bez zapytań SQL!)
    print(f"\n[PROCESS] Przetwarzam trasy...")
    
    for idx, route_code in enumerate(routes, 1):
        if idx <= resume_from:
            continue
        
        # Progress bar
        percent = (idx - 1) / total * 100
        elapsed = time.time() - start_time
        if idx > resume_from + 1:
            eta_seconds = elapsed / (idx - resume_from - 1) * (total - idx + 1)
            eta_minutes = int(eta_seconds / 60)
            print(f"\r[{idx}/{total}] {percent:.1f}% | Sukces: {success_count} | Pominięto: {skipped_count} | ETA: {eta_minutes}m", end='', flush=True)
        
        try:
            result = process_single_route(route_code, mappings, postal_coords, timocom_data_cache, transeu_data_cache)
            results.append(result)
            
            # Aktualizuj liczniki
            if result.get('status') in ['success', 'cached']:
                success_count += 1
            else:
                skipped_count += 1
            
            # Autosave co 5 minut
            current_time = time.time()
            if current_time - last_save_time >= AUTOSAVE_INTERVAL_SECONDS:
                save_progress(results, checkpoint_file)
                last_save_time = current_time
                
        except Exception as e:
            skipped_count += 1
            results.append({
                'original_route': route_code,
                'status': 'error',
                'error': str(e),
                'data': None
            })
    
    # Wyczyść linię progress bara i pokaż finalny status
    print(f"\r[{total}/{total}] 100.0% | Sukces: {success_count} | Pominięto: {skipped_count} | ZAKOŃCZONO   ")
    
    # Ostateczny zapis na końcu
    save_progress(results, checkpoint_file)
    print(f"\n[INFO] Przetwarzanie zakończone. Finalny checkpoint: {checkpoint_file}")
    
    return results


def main():
    """Główna funkcja skryptu"""
    # Windows console fix
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 80)
    print("BATCH ROUTE CHECKER - Sprawdzanie stawek historycznych")
    print("=" * 80)
    
    # Wczytaj trasy
    print("\n[LOAD] Wczytuję trasy z pliku unikalne_trasy.json...")
    with open('unikalne_trasy.json', 'r', encoding='utf-8') as f:
        routes = json.load(f)
    
    # TEST MODE - tylko pierwsze 10 tras (zmień na False aby przetworzyć wszystkie)
    TEST_MODE = False
    if TEST_MODE:
        routes = routes[:10]
        print(f"[TEST] TRYB TESTOWY - przetwarzam tylko pierwsze 10 tras")
    else:
        print(f"[PROD] TRYB PRODUKCYJNY - przetwarzam wszystkie trasy")
    
    # Sprawdź czy istnieje checkpoint do wznowienia
    checkpoint_pattern = 'route_analysis_*_checkpoint.json'
    checkpoints = sorted(glob.glob(checkpoint_pattern), key=os.path.getmtime, reverse=True)
    
    resume_from = 0
    if checkpoints:
        latest_checkpoint = checkpoints[0]
        print(f"\n[RESUME?] Znaleziono checkpoint: {latest_checkpoint}")
        
        try:
            with open(latest_checkpoint, 'r', encoding='utf-8') as f:
                checkpoint_data = json.load(f)
            
            if checkpoint_data:
                resume_from = len(checkpoint_data)
                print(f"[RESUME] Wznawiam od trasy #{resume_from + 1}/{len(routes)}")
                print(f"[INFO] Pomiń {resume_from} już przetworzonych tras")
        except:
            print(f"[WARN] Nie udało się odczytać checkpointu, zaczynam od początku")
    
    print(f"[OK] Wczytano {len(routes)} tras (do przetworzenia: {len(routes) - resume_from})")
    
    # Wczytaj mapowania
    print("\n[LOAD] Wczytuję mapowania regionów...")
    mappings, _ = load_mappings()
    print("[OK] Mapowania załadowane")
    
    # Wczytaj współrzędne kodów pocztowych (używane do obliczania dystansów)
    print("\n[LOAD] Wczytuję współrzędne kodów pocztowych z filtered_postal_codes.geojson...")
    postal_coords = load_postal_coordinates()
    print(f"[OK] Załadowano współrzędne dla {len(postal_coords)} kodów pocztowych")
    print("[INFO] Będą pobierane dane z OBU giełd: TimoCom + Trans.eu")
    print("[INFO] Dystanse będą obliczane za pomocą AWS Location Service API Routes")
    
    # Przygotuj nazwę pliku wyjściowego
    if resume_from > 0 and checkpoints:
        # Użyj istniejącego checkpointu
        output_file = checkpoints[0].replace('_checkpoint.json', '.json')
        print(f"[RESUME] Kontynuuję zapis do: {output_file}")
    else:
        # Nowy plik
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'route_analysis_{timestamp}.json'
    
    # Przetwórz trasy (z automatycznym zapisem co 5 minut)
    print("\n[START] Rozpoczynam przetwarzanie tras...")
    print(f"[INFO] OPTYMALIZACJA: Batch queries - 6 zapytań SQL zamiast ~7600!")
    print(f"[INFO] Automatyczny zapis co {AUTOSAVE_INTERVAL_SECONDS // 60} minut")
    print(f"[INFO] Plik checkpoint: {output_file.replace('.json', '_checkpoint.json')}")
    
    results = process_routes(routes, mappings, postal_coords, output_file, resume_from)
    
    # Zapisz finalny wynik
    print(f"\n[SAVE] Zapisuję finalne wyniki do pliku {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Statystyki
    print("\n" + "=" * 80)
    print("STATYSTYKI")
    print("=" * 80)
    
    success = sum(1 for r in results if r.get('status') == 'success')
    cached = sum(1 for r in results if r.get('status') == 'cached')
    too_short = sum(1 for r in results if r.get('status') == 'too_short')
    mapping_failed = sum(1 for r in results if r.get('status') == 'mapping_failed')
    errors = sum(1 for r in results if r.get('status') == 'error')
    
    print(f"Łącznie tras:               {len(results)}")
    print(f"[OK] Sukces (nowe):         {success}")
    print(f"[CACHE] Sukces (cache):     {cached}")
    print(f"[SKIP] Za krótkie (<150km): {too_short}")
    print(f"[WARN] Błąd mapowania:      {mapping_failed}")
    print(f"[ERROR] Błędy:              {errors}")
    print(f"\nWyniki zapisano do: {output_file}")
    print("=" * 80)


if __name__ == '__main__':
    main()
