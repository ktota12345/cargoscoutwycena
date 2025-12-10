"""
Cargo Scout Wycena - Simple UI Frontend
Frontend który tylko normalizuje kody pocztowe i wywołuje Backend API
"""
from flask import Flask, render_template, jsonify, request
import os
import re
from dotenv import load_dotenv
import requests

# Załaduj zmienne środowiskowe
load_dotenv()

app = Flask(__name__)

# Konfiguracja Backend API
BACKEND_API_URL = os.getenv("API_URL")
BACKEND_API_KEY = os.getenv("API_KEY")

# Konfiguracja AWS Location Service (tylko dla kalkulacji dystansu)
AWS_LOCATION_API_KEY = os.getenv("AWS_LOCATION_API_KEY")
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")


def normalize_postal_code(postal_code):
    """
    Normalizuje kod pocztowy do formatu: <KOD_KRAJU><PIERWSZE_2_CYFRY>
    
    Przykłady:
    - "PL20" -> "PL20"
    - "PL20-123" -> "PL20"
    - "DE49876" -> "DE49"
    - "FR 75001" -> "FR75"
    
    Args:
        postal_code: Kod pocztowy wpisany przez użytkownika
    
    Returns:
        Znormalizowany kod w formacie <KOD_KRAJU><2_CYFRY>
    """
    if not postal_code:
        return None
    
    # Usuń spacje i myślniki
    cleaned = str(postal_code).upper().replace(' ', '').replace('-', '')
    
    # Wyciągnij 2 litery (kod kraju) + pierwsze 2 cyfry
    match = re.match(r'^([A-Z]{2})(\d{2})', cleaned)
    
    if match:
        country_code = match.group(1)
        first_two_digits = match.group(2)
        return f"{country_code}{first_two_digits}"
    
    # Jeśli nie pasuje do wzorca, zwróć None
    return None


# =======================
# ENDPOINTY
# =======================
def _get_db_connection():
    """Nawiązuje połączenie z bazą danych PostgreSQL"""
    if not all([DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME]):
        print("Ostrzeżenie: Brak pełnej konfiguracji bazy danych. Używam losowych danych.")
        return None
    
    try:
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursor_factory=RealDictCursor,
        )
    except Exception as exc:
        print(f"Błąd połączenia z bazą danych: {exc}")
        return None

# Funkcja do konwersji Decimal na float
def _decimal_to_float(record: Dict[str, Any]) -> Dict[str, Any]:
    """Konwertuje wartości Decimal na float w słowniku"""
    converted = {}
    for key, value in record.items():
        if isinstance(value, Decimal):
            converted[key] = float(value)
        else:
            converted[key] = value
    return converted

# Funkcja do obliczania dystansu przez AWS Location Service API
def get_aws_route_distance(start_lat: float, start_lng: float, end_lat: float, end_lng: float, 
                           return_geometry: bool = False) -> Optional[Dict]:
    """
    Wywołuje AWS Location Service Routes API aby obliczyć rzeczywisty dystans drogowy.
    
    Args:
        start_lat, start_lng: Współrzędne startu
        end_lat, end_lng: Współrzędne końca
        return_geometry: Czy zwrócić również geometrię trasy (dla mapy)
    
    Returns:
        Dict z 'distance' (km) i opcjonalnie 'geometry' (lista punktów [lng, lat])
        lub None w przypadku błędu
    """
    if not AWS_LOCATION_API_KEY:
        print("[AWS] ❌ BŁĄD: Brak API key - używam fallback")
        print(f"[AWS] AWS_LOCATION_API_KEY = {AWS_LOCATION_API_KEY}")
        return None
    
    try:
        # AWS Location Service Routes API v2 endpoint
        url = f"https://routes.geo.{AWS_REGION}.amazonaws.com/v2/routes?key={AWS_LOCATION_API_KEY}"
        
        print(f"[AWS] 🌐 URL: {url[:80]}...")
        print(f"[AWS] 📍 Origin: [{start_lng}, {start_lat}]")
        print(f"[AWS] 📍 Destination: [{end_lng}, {end_lat}]")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "Origin": [start_lng, start_lat],
            "Destination": [end_lng, end_lat],
            "TravelMode": "Truck",
            "OptimizeRoutingFor": "FastestRoute",
            "LegGeometryFormat": "Simple"  # Żądaj geometrii trasy
        }
        
        print(f"[AWS] 📤 Wysyłam request do AWS...")
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        print(f"[AWS] 📥 Otrzymano odpowiedź: status={response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'Routes' in data and len(data['Routes']) > 0:
                route = data['Routes'][0]
                
                # Suma dystansów ze wszystkich legs
                total_distance = 0
                for leg in route.get('Legs', []):
                    vehicle_details = leg.get('VehicleLegDetails', {})
                    travel_steps = vehicle_details.get('TravelSteps', [])
                    for step in travel_steps:
                        total_distance += step.get('Distance', 0)
                
                distance_km = total_distance / 1000.0
                result = {'distance': round(distance_km, 2)}
                
                # Dodaj geometrię jeśli żądana
                if return_geometry:
                    geometry_points = []
                    for leg in route.get('Legs', []):
                        leg_geometry = leg.get('Geometry', {})
                        if 'LineString' in leg_geometry:
                            # LineString to lista punktów [lng, lat]
                            geometry_points.extend(leg_geometry['LineString'])
                    
                    result['geometry'] = geometry_points
                    result['duration'] = route.get('Summary', {}).get('Duration', 0)  # Czas w sekundach
                    print(f"[AWS] ✓ Dystans: {distance_km:.2f} km, Punkty trasy: {len(geometry_points)}")
                else:
                    print(f"[AWS] ✓ Dystans AWS: {distance_km:.2f} km")
                
                return result
        
        print(f"[AWS] ❌ Błąd API: status={response.status_code}")
        print(f"[AWS] Response body: {response.text[:500]}")
        return None
            
    except requests.exceptions.Timeout:
        print("[AWS] ❌ Timeout (15s) - brak odpowiedzi od AWS")
        return None
    except requests.exceptions.ConnectionError as e:
        print(f"[AWS] ❌ ConnectionError: {e}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[AWS] ❌ RequestException: {e}")
        return None
    except Exception as e:
        print(f"[AWS] ❌ Nieoczekiwany błąd: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None

# Załaduj mapowanie Trans.eu -> TimoCom z pliku JSON
_TRANSEU_TO_TIMOCOM_MAPPING = None

def _load_transeu_timocom_mapping():
    """Ładuje mapowanie Trans.eu -> TimoCom z pliku JSON"""
    global _TRANSEU_TO_TIMOCOM_MAPPING
    
    if _TRANSEU_TO_TIMOCOM_MAPPING is not None:
        return _TRANSEU_TO_TIMOCOM_MAPPING
    
    try:
        import json
        mapping_path = os.path.join(os.path.dirname(__file__), 'static', 'data', 'transeu_to_timocom_mapping.json')
        with open(mapping_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Konwertuj klucze ze string na int
            _TRANSEU_TO_TIMOCOM_MAPPING = {int(k): v['timocom_id'] for k, v in data.items()}
        print(f"✓ Załadowano mapowanie Trans.eu -> TimoCom ({len(_TRANSEU_TO_TIMOCOM_MAPPING)} regionów)")
    except Exception as e:
        print(f"⚠ Nie udało się załadować mapowania Trans.eu -> TimoCom: {e}")
        _TRANSEU_TO_TIMOCOM_MAPPING = {}
    
    return _TRANSEU_TO_TIMOCOM_MAPPING

# Funkcja do mapowania Trans.eu ID na TimoCom ID
def map_transeu_to_timocom_id(transeu_id: int):
    """Mapuje Trans.eu region ID na TimoCom region ID
    
    Używa wygenerowanego pliku mapowania opartego na odległościach geograficznych
    """
    mapping = _load_transeu_timocom_mapping()
    
    # Zwróć zmapowane ID lub oryginalne jeśli brak w mapowaniu
    return mapping.get(transeu_id, transeu_id)

# Funkcja do pobierania danych z TimoCom
def get_timocom_data(start_region_id: int, end_region_id: int, distance: float, days: int = 7):
    """Pobiera dane cenowe TimoCom z bazy danych PostgreSQL
    
    UWAGA: start_region_id i end_region_id to Trans.eu ID!
    Funkcja konwertuje je na TimoCom ID przed zapytaniem do bazy.
    """
    # Konwertuj Trans.eu ID na TimoCom ID
    timocom_start_id = map_transeu_to_timocom_id(start_region_id)
    timocom_end_id = map_transeu_to_timocom_id(end_region_id)
    
    print(f"🔄 Mapowanie: Trans.eu [{start_region_id} -> {end_region_id}] → TimoCom [{timocom_start_id} -> {timocom_end_id}]")
    
    conn = _get_db_connection()
    
    # Jeśli brak połączenia, zwróć informację o braku danych
    if not conn:
        return {
            'has_data': False,
            'offers': [],
            'average_rate_per_km': None,
            'average_total_price': None,
            'average_offers_per_day': None,
            'days': days,
            'data_source': 'no_connection',
            'message': 'Brak połączenia z bazą danych'
        }
    
    try:
        with conn.cursor() as cur:
            # Zapytanie do bazy - agregacja średnich cen dla różnych typów pojazdów
            # Używamy enlistment_date (format yyyy-mm-dd) do filtrowania po okresie
            # Zoptymalizowane - agregujemy bezpośrednio bez grupowania po datach
            
            query = """
                SELECT
                    ROUND(AVG(o.trailer_avg_price_per_km), 4) AS avg_trailer_price,
                    ROUND(AVG(o.vehicle_up_to_3_5_t_avg_price_per_km), 4) AS avg_3_5t_price,
                    ROUND(AVG(o.vehicle_up_to_12_t_avg_price_per_km), 4) AS avg_12t_price,
                    SUM(o.number_of_offers_total) AS total_offers,
                    COUNT(DISTINCT o.enlistment_date) AS days_count
                FROM public.offers AS o
                WHERE o.starting_id = %s
                  AND o.destination_id = %s
                  AND o.enlistment_date >= CURRENT_DATE - CAST(%s AS INTEGER);
            """
            
            cur.execute(query, (timocom_start_id, timocom_end_id, days))
            result = cur.fetchone()
            
            if not result or (not result['avg_trailer_price'] and not result['avg_3_5t_price'] and not result['avg_12t_price']):
                print(f"Brak danych w bazie dla trasy TimoCom {timocom_start_id} -> {timocom_end_id} (Trans.eu {start_region_id} -> {end_region_id}).")
                return {
                    'has_data': False,
                    'offers': [],
                    'average_rate_per_km': None,
                    'average_total_price': None,
                    'average_offers_per_day': None,
                    'days': days,
                    'data_source': 'database',
                    'message': 'Brak danych dla tej trasy w wybranym okresie'
                }
            
            # Konwersja wyników z bazy na format aplikacji
            # Symulacja ofert dla różnych giełd na podstawie średnich z bazy
            exchanges = ['Trans.eu', 'TimoCom']  # Tylko TimoCom i Trans.eu
            offers = []
            
            # Pobierz średnie ceny bezpośrednio z wyniku
            avg_trailer = float(result['avg_trailer_price']) if result['avg_trailer_price'] else None
            avg_3_5t = float(result['avg_3_5t_price']) if result['avg_3_5t_price'] else None
            avg_12t = float(result['avg_12t_price']) if result['avg_12t_price'] else None
            
            # Użyj najlepszej dostępnej średniej (priorytet: naczepa > 12t > 3.5t)
            base_rate = avg_trailer or avg_12t or avg_3_5t or 0.50
            
            # Pobierz faktyczną liczbę ofert z bazy
            total_offers_sum = int(result['total_offers']) if result['total_offers'] else 0
            
            # Liczba dni z danymi
            num_days = int(result['days_count']) if result['days_count'] else 0
            offers_per_day_estimate = round(total_offers_sum / num_days, 1) if num_days > 0 else 0
            
            # Generuj oferty dla różnych giełd - BEZ losowania, deterministyczne warianty
            # Każda giełda ma stałą wariancję od base_rate
            exchange_offsets = {
                'Trans.eu': -0.02,     # 2 centy taniej
                'TimoCom': 0.00        # Bazowa cena
            }
            
            for exchange in exchanges:
                offset = exchange_offsets[exchange]
                rate_per_km = base_rate + offset
                total_price = rate_per_km * distance
                
                offers.append({
                    'exchange': exchange,
                    'rate_per_km': round(rate_per_km, 2),
                    'total_price': round(total_price, 2),
                    'currency': 'EUR',
                    'date': datetime.now().strftime('%Y-%m-%d'),  # Dzisiejsza data (bez losowania)
                    'offers_per_day': offers_per_day_estimate
                })
            
            # Średnie są teraz deterministyczne (zawsze takie same)
            avg_rate = sum(o['rate_per_km'] for o in offers) / len(offers)
            avg_total = sum(o['total_price'] for o in offers) / len(offers)
            avg_offers_per_day = offers_per_day_estimate  # Nie uśredniaj - to i tak ta sama wartość
            
            print(f"✓ Pobrano dane TimoCom z bazy ({days} dni): {num_days} dni z danymi, {total_offers_sum} ofert, średnia stawka: {avg_rate:.2f} EUR/km")
            
            return {
                'has_data': True,
                'offers': offers,
                'average_rate_per_km': round(avg_rate, 2),
                'average_total_price': round(avg_total, 2),
                'average_offers_per_day': round(avg_offers_per_day, 1),
                'days': days,
                'data_source': 'database_timocom',
                'records_count': num_days,
                'total_offers_sum': total_offers_sum
            }
            
    except Exception as exc:
        print(f"Błąd podczas pobierania danych TimoCom z bazy: {exc}")
        return {
            'has_data': False,
            'offers': [],
            'average_rate_per_km': None,
            'average_total_price': None,
            'average_offers_per_day': None,
            'days': days,
            'data_source': 'error',
            'message': f'Błąd zapytania do bazy: {str(exc)}'
        }
    finally:
        conn.close()

# Funkcja do pobierania danych z Trans.eu
def get_transeu_data(start_region_id: int, end_region_id: int, distance: float, days: int = 7):
    """Pobiera dane cenowe Trans.eu z bazy danych PostgreSQL
    
    Trans.eu używa własnych ID regionów (bez konwersji)
    """
    print(f"🔄 Trans.eu: Zapytanie dla regionów {start_region_id} -> {end_region_id}")
    
    conn = _get_db_connection()
    
    # Jeśli brak połączenia, zwróć informację o braku danych
    if not conn:
        return {
            'has_data': False,
            'offers': [],
            'average_rate_per_km': None,
            'average_total_price': None,
            'average_offers_per_day': None,
            'days': days,
            'data_source': 'no_connection',
            'message': 'Brak połączenia z bazą danych'
        }
    
    try:
        with conn.cursor() as cur:
            # Zapytanie do bazy Trans.eu - tabela OffersTransEU
            # Trans.eu ma tylko jedną kolumnę cenową: lorry_avg_price_per_km
            # UWAGA: Trans.eu nie ma kolumny number_of_offers_total, więc nie liczymy ofert
            # Używamy enlistment_date (format yyyy-mm-dd) do filtrowania po okresie
            # Zoptymalizowane - agregujemy bezpośrednio bez grupowania po datach
            
            query = """
                SELECT
                    ROUND(AVG(o.lorry_avg_price_per_km), 4) AS avg_lorry_price,
                    COUNT(DISTINCT o.enlistment_date) AS days_count
                FROM public."OffersTransEU" AS o
                WHERE o.starting_id = %s
                  AND o.destination_id = %s
                  AND o.enlistment_date >= CURRENT_DATE - CAST(%s AS INTEGER);
            """
            
            cur.execute(query, (start_region_id, end_region_id, days))
            result = cur.fetchone()
            
            if not result or not result['avg_lorry_price']:
                print(f"Brak danych Trans.eu w bazie dla trasy {start_region_id} -> {end_region_id}.")
                return {
                    'has_data': False,
                    'offers': [],
                    'average_rate_per_km': None,
                    'average_total_price': None,
                    'average_offers_per_day': None,
                    'days': days,
                    'data_source': 'database_transeu',
                    'message': 'Brak danych dla tej trasy w wybranym okresie'
                }
            
            # Konwersja wyników z bazy na format aplikacji
            exchanges = ['Trans.eu', 'TimoCom']  # Tylko TimoCom i Trans.eu
            offers = []
            
            # Pobierz średnią cenę bezpośrednio z wyniku
            avg_lorry = float(result['avg_lorry_price']) if result['avg_lorry_price'] else None
            num_days = int(result['days_count']) if result['days_count'] else 0
            
            # Użyj średniej lorry jako base rate
            base_rate = avg_lorry or 0.50
            
            # Generuj oferty dla różnych giełd - BEZ losowania, deterministyczne warianty
            # Każda giełda ma stałą wariancję od base_rate
            exchange_offsets = {
                'Trans.eu': -0.02,     # 2 centy taniej
                'TimoCom': 0.00        # Bazowa cena
            }
            
            for exchange in exchanges:
                offset = exchange_offsets[exchange]
                rate_per_km = base_rate + offset
                total_price = rate_per_km * distance
                
                offers.append({
                    'exchange': exchange,
                    'rate_per_km': round(rate_per_km, 2),
                    'total_price': round(total_price, 2),
                    'currency': 'EUR',
                    'date': datetime.now().strftime('%Y-%m-%d'),  # Dzisiejsza data (bez losowania)
                    'offers_per_day': None  # Trans.eu nie ma danych o liczbie ofert w bazie
                })
            
            # Średnie są teraz deterministyczne (zawsze takie same)
            avg_rate = sum(o['rate_per_km'] for o in offers) / len(offers)
            avg_total = sum(o['total_price'] for o in offers) / len(offers)
            
            print(f"✓ Pobrano dane Trans.eu z bazy ({days} dni): {num_days} dni z danymi, średnia stawka: {avg_rate:.2f} EUR/km")
            
            return {
                'has_data': True,
                'offers': offers,
                'average_rate_per_km': round(avg_rate, 2),
                'average_total_price': round(avg_total, 2),
                'average_offers_per_day': None,  # Trans.eu nie ma danych o liczbie ofert
                'days': days,
                'data_source': 'database_transeu',
                'records_count': num_days
            }
            
    except Exception as exc:
        print(f"Błąd podczas pobierania danych Trans.eu z bazy: {exc}")
        return {
            'has_data': False,
            'offers': [],
            'average_rate_per_km': None,
            'average_total_price': None,
            'average_offers_per_day': None,
            'days': days,
            'data_source': 'error',
            'message': f'Błąd zapytania do bazy Trans.eu: {str(exc)}'
        }
    finally:
        conn.close()

# Funkcja agregująca dane z różnych giełd
def get_aggregated_exchange_data(start_region_id: int, end_region_id: int, distance: float, days: int = 7):
    """Agreguje dane z różnych giełd (TimoCom, Trans.eu, etc.)"""
    
    # Pobierz dane z TimoCom
    timocom_data = get_timocom_data(start_region_id, end_region_id, distance, days)
    
    # Pobierz dane z Trans.eu
    transeu_data = get_transeu_data(start_region_id, end_region_id, distance, days)
    
    # Agreguj oferty z różnych źródeł
    all_offers = []
    
    # Dodaj oferty TimoCom jeśli są dostępne
    if timocom_data['has_data']:
        # Filtruj tylko TimoCom z ofert i dodaj total_offers_sum
        timocom_offers = [o for o in timocom_data['offers'] if o['exchange'] == 'TimoCom']
        for offer in timocom_offers:
            offer['total_offers_sum'] = timocom_data.get('total_offers_sum', 0)
            offer['records_count'] = timocom_data.get('records_count', 0)
        all_offers.extend(timocom_offers)
    else:
        # Brak danych TimoCom - dodaj placeholder
        all_offers.append({
            'exchange': 'TimoCom',
            'rate_per_km': None,
            'total_price': None,
            'currency': 'EUR',
            'has_data': False,
            'message': timocom_data.get('message', 'Brak danych'),
            'total_offers_sum': 0,
            'records_count': 0
        })
    
    # Dodaj oferty Trans.eu jeśli są dostępne
    if transeu_data['has_data']:
        transeu_offers = [o for o in transeu_data['offers'] if o['exchange'] == 'Trans.eu']
        # Trans.eu nie ma total_offers_sum w bazie
        for offer in transeu_offers:
            offer['total_offers_sum'] = 0
            offer['records_count'] = transeu_data.get('records_count', 0)
        all_offers.extend(transeu_offers)
    else:
        # Brak danych Trans.eu - dodaj placeholder
        all_offers.append({
            'exchange': 'Trans.eu',
            'rate_per_km': None,
            'total_price': None,
            'currency': 'EUR',
            'has_data': False,
            'message': transeu_data.get('message', 'Brak danych'),
            'total_offers_sum': 0,
            'records_count': 0
        })
    
    # Agregacja danych - priorytet dla danych, które faktycznie istnieją
    has_any_data = timocom_data['has_data'] or transeu_data['has_data']
    
    if has_any_data:
        # Oblicz średnie z dostępnych źródeł
        rates = []
        totals = []
        offers_per_day = []
        
        if timocom_data['has_data']:
            rates.append(timocom_data['average_rate_per_km'])
            totals.append(timocom_data['average_total_price'])
            if timocom_data['average_offers_per_day'] is not None:
                offers_per_day.append(timocom_data['average_offers_per_day'])
        
        if transeu_data['has_data']:
            rates.append(transeu_data['average_rate_per_km'])
            totals.append(transeu_data['average_total_price'])
            if transeu_data['average_offers_per_day'] is not None:
                offers_per_day.append(transeu_data['average_offers_per_day'])
        
        avg_rate = sum(rates) / len(rates) if rates else None
        avg_total = sum(totals) / len(totals) if totals else None
        avg_offers = sum(offers_per_day) / len(offers_per_day) if offers_per_day else None
        
        # Określ źródło danych
        if timocom_data['has_data'] and transeu_data['has_data']:
            data_source = 'both'
        elif timocom_data['has_data']:
            data_source = 'timocom_only'
        else:
            data_source = 'transeu_only'
        
        # Pobierz total_offers_sum i records_count z TimoCom (Trans.eu nie ma tych danych)
        total_offers_sum = timocom_data.get('total_offers_sum', 0) if timocom_data['has_data'] else 0
        records_count = timocom_data.get('records_count', 0) if timocom_data['has_data'] else 0
        
        return {
            'has_data': True,
            'offers': all_offers,
            'average_rate_per_km': round(avg_rate, 2) if avg_rate else None,
            'average_total_price': round(avg_total, 2) if avg_total else None,
            'average_offers_per_day': round(avg_offers, 1) if avg_offers else None,
            'days': days,
            'data_source': data_source,
            'timocom_data': timocom_data,
            'transeu_data': transeu_data,
            'total_offers_sum': total_offers_sum,
            'records_count': records_count
        }
    else:
        # Brak danych z żadnego źródła
        return {
            'has_data': False,
            'offers': all_offers,
            'average_rate_per_km': None,
            'average_total_price': None,
            'average_offers_per_day': None,
            'days': days,
            'data_source': 'none',
            'message': 'Brak danych dla tej trasy w wybranym okresie'
        }

# Funkcja do generowania przykładowych współrzędnych trasy
def generate_route_coordinates(start_location, end_location):
    """Generuje przykładowe współrzędne trasy między lokalizacjami"""
    # Przykładowe współrzędne dla polskich miast
    cities = {
        'warszawa': [52.2297, 21.0122],
        'kraków': [50.0647, 19.9450],
        'poznań': [52.4064, 16.9252],
        'wrocław': [51.1079, 17.0385],
        'gdańsk': [54.3520, 18.6466],
        'katowice': [50.2649, 19.0238],
        'łódź': [51.7592, 19.4560],
        'szczecin': [53.4285, 14.5528],
        'berlin': [52.5200, 13.4050],
        'praga': [50.0755, 14.4378],
        'wiedeń': [48.2082, 16.3738],
        'budapeszt': [47.4979, 19.0402]
    }
    
    start_coords = cities.get(start_location.lower(), [52.0, 19.0])
    end_coords = cities.get(end_location.lower(), [50.0, 20.0])
    
    # Generowanie punktów pośrednich dla płynniejszej trasy
    route_points = [start_coords]
    steps = 5
    for i in range(1, steps):
        lat = start_coords[0] + (end_coords[0] - start_coords[0]) * i / steps
        lng = start_coords[1] + (end_coords[1] - start_coords[1]) * i / steps
        # Dodanie małego losowego odchylenia dla bardziej realistycznej trasy
        lat += random.uniform(-0.2, 0.2)
        lng += random.uniform(-0.2, 0.2)
        route_points.append([lat, lng])
    route_points.append(end_coords)
    
    return {
        'start': start_coords,
        'end': end_coords,
        'route': route_points
    }

# Funkcja do generowania przykładowych danych giełdowych
def generate_exchange_data(distance, days=7):
    """Generuje przykładowe dane ze stawkami giełdowymi dla określonej liczby dni"""
    base_rate = random.uniform(0.40, 0.55)  # EUR za km
    
    exchanges = ['Trans.eu', 'TimoCom']  # Tylko TimoCom i Trans.eu
    offers = []
    
    # Generuj po jednej ofercie dla każdej giełdy (bez duplikatów)
    for exchange in exchanges:
        rate_per_km = base_rate + random.uniform(-0.3, 0.3)
        total_price = rate_per_km * distance
        
        offers.append({
            'exchange': exchange,
            'rate_per_km': round(rate_per_km, 2),
            'total_price': round(total_price, 2),
            'currency': 'EUR',
            'date': (datetime.now() - timedelta(days=random.randint(0, days))).strftime('%Y-%m-%d')
        })
    
    avg_rate = sum(o['rate_per_km'] for o in offers) / len(offers)
    avg_total = sum(o['total_price'] for o in offers) / len(offers)
    
    # Oblicz liczbę ofert per dzień dla każdej giełdy
    for offer in offers:
        offer['offers_per_day'] = round(random.uniform(0.5, 3.0), 1)
    
    # Oblicz średnią liczbę ofert per dzień
    avg_offers_per_day = sum(o['offers_per_day'] for o in offers) / len(offers)
    
    return {
        'offers': offers,
        'average_rate_per_km': round(avg_rate, 2),
        'average_total_price': round(avg_total, 2),
        'average_offers_per_day': round(avg_offers_per_day, 1),
        'days': days
    }

# Funkcja do generowania historycznych danych firmowych
def generate_historical_data(distance, start_location, end_location, days=7):
    """Generuje przykładowe dane historyczne firmy dla określonej liczby dni"""
    # Losowa decyzja czy mamy dane historyczne dla tej trasy
    has_history = random.choice([True, True, False])
    
    if not has_history:
        return {
            'has_data': False,
            'orders': [],
            'average_rate_per_km': None,
            'average_total_price': None,
            'orders_per_day': None,
            'days': days
        }
    
    base_rate = random.uniform(0.45, 0.62)  # Stawki firmowe zwykle trochę wyższe (EUR za km)
    orders = []
    
    # Liczba zleceń zależy od okresu
    num_orders = min(random.randint(2, 8), days // 3)
    
    for i in range(max(2, num_orders)):
        rate_per_km = base_rate + random.uniform(-0.4, 0.4)
        total_price = rate_per_km * distance
        
        orders.append({
            'order_id': f'ORD-{random.randint(1000, 9999)}',
            'date': (datetime.now() - timedelta(days=random.randint(0, days))).strftime('%Y-%m-%d'),
            'carrier': f'Przewoźnik {random.choice(["A", "B", "C", "D", "E"])} Sp. z o.o.',
            'rate_per_km': round(rate_per_km, 2),
            'total_price': round(total_price, 2),
            'currency': 'EUR'
        })
    
    avg_rate = sum(o['rate_per_km'] for o in orders) / len(orders)
    avg_total = sum(o['total_price'] for o in orders) / len(orders)
    
    # Oblicz liczbę zleceń per dzień
    orders_per_day = round(len(orders) / days, 1)
    
    return {
        'has_data': True,
        'orders': orders,
        'average_rate_per_km': round(avg_rate, 2),
        'average_total_price': round(avg_total, 2),
        'orders_per_day': orders_per_day,
        'days': days
    }

# Funkcja do generowania danych o opłatach drogowych
def generate_toll_data(start_location, end_location, distance):
    """Generuje przykładowe dane o opłatach drogowych"""
    # Symulacja opłat w zależności od trasy
    tolls = []
    
    # Dodaj opłaty dla tras międzynarodowych
    countries = []
    if any(city in start_location.lower() or city in end_location.lower() 
           for city in ['berlin', 'praga', 'wiedeń', 'budapeszt']):
        countries = ['Polska', 'Niemcy'] if 'berlin' in (start_location + end_location).lower() else ['Polska']
    else:
        countries = ['Polska']
    
    total_toll = 0
    for country in countries:
        if country == 'Polska':
            toll_amount = distance * 0.067  # ~0.067 EUR/km dla pojazdów ciężarowych
            tolls.append({
                'country': country,
                'system': 'e-TOLL',
                'amount': round(toll_amount, 2),
                'currency': 'EUR'
            })
            total_toll += toll_amount
        elif country == 'Niemcy':
            toll_amount = distance * 0.19  # ~0.19 EUR/km
            tolls.append({
                'country': country,
                'system': 'Toll Collect',
                'amount': round(toll_amount, 2),
                'currency': 'EUR'
            })
            total_toll += toll_amount
    
    return {
        'tolls': tolls,
        'total_toll': round(total_toll, 2),
        'currency': 'EUR'
    }

# Funkcja do generowania sugerowanych przewoźników
def generate_carrier_suggestions(start_location, end_location):
    """Generuje listę sugerowanych przewoźników"""
    carrier_names = [
        'Trans-Logistics', 'Euro-Transport', 'Fast Cargo', 'Reliable Freight',
        'Express Delivery', 'Safe Transport', 'Quick Route', 'Prime Logistics',
        'Best Carriers', 'Global Transport'
    ]
    
    # Przewoźnicy historyczni (z którymi firma już współpracowała)
    historical_carriers = []
    num_historical = random.randint(2, 4)
    
    for i in range(num_historical):
        historical_carriers.append({
            'name': f'{random.choice(carrier_names)} Sp. z o.o.',
            'rating': round(random.uniform(4.0, 5.0), 1),
            'completed_orders': random.randint(5, 50),
            'avg_rate_per_km': round(random.uniform(0.49, 0.62), 2),
            'reliability': random.choice(['Wysoka', 'Bardzo wysoka']),
            'contact': f'+48 {random.randint(500, 799)} {random.randint(100, 999)} {random.randint(100, 999)}'
        })
    
    # Przewoźnicy z giełdy
    exchange_carriers = []
    num_exchange = random.randint(3, 6)
    
    for i in range(num_exchange):
        exchange_carriers.append({
            'name': f'{random.choice(carrier_names)} S.A.',
            'rating': round(random.uniform(3.5, 4.8), 1),
            'available_trucks': random.randint(1, 5),
            'avg_rate_per_km': round(random.uniform(0.40, 0.55), 2),
            'exchange': random.choice(['Trans.eu', 'TimoCom']),
            'response_time': f'{random.randint(1, 24)}h'
        })
    
    return {
        'historical': historical_carriers,
        'exchange': exchange_carriers
    }

@app.route('/')
def index():
    """Strona główna aplikacji"""
    return render_template('index.html')

@app.route('/api/calculate', methods=['POST'])
def calculate_route():
    """Endpoint do wyceny trasy"""
    data = request.json
    start_location = data.get('start_location', '')
    end_location = data.get('end_location', '')
    start_location_raw = data.get('start_location_raw', start_location)  # Faktyczny kod wpisany przez użytkownika
    end_location_raw = data.get('end_location_raw', end_location)  # Faktyczny kod wpisany przez użytkownika
    vehicle_type = data.get('vehicle_type', 'naczepa')
    body_type = data.get('body_type', 'standard')
    start_coords = data.get('start_coords')
    end_coords = data.get('end_coords')
    calculated_distance = data.get('calculated_distance')
    
    if not start_location or not end_location:
        return jsonify({'error': 'Brak wymaganych lokalizacji'}), 400
    
    # Użyj obliczonej odległości z frontendu lub wygeneruj dane trasy
    if start_coords and end_coords and calculated_distance:
        # Użyj rzeczywistych współrzędnych
        route_data = {
            'start': start_coords,
            'end': end_coords,
            'route': [start_coords, end_coords]  # Prosta linia między punktami
        }
        distance = calculated_distance
    else:
        # Fallback do starej metody
        route_data = generate_route_coordinates(start_location, end_location)
        distance = random.randint(200, 800)
    
    # Pobierz ID regionów (jeśli dostępne)
    start_region_id = data.get('start_region_id')
    end_region_id = data.get('end_region_id')
    
    # Pobierz liczbę dni z zapytania (domyślnie 7)
    days = data.get('days', 7)
    
    # Generowanie/pobieranie danych dla wybranego okresu
    # Jeśli mamy ID regionów, użyj faktycznych danych z bazy, w przeciwnym razie losowe
    if start_region_id and end_region_id:
        print(f"📊 Pobieranie danych z bazy dla regionów: {start_region_id} -> {end_region_id}")
        exchange_data = get_aggregated_exchange_data(start_region_id, end_region_id, distance, days)
        exchange_data_7 = get_aggregated_exchange_data(start_region_id, end_region_id, distance, 7)
        exchange_data_30 = get_aggregated_exchange_data(start_region_id, end_region_id, distance, 30)
        exchange_data_90 = get_aggregated_exchange_data(start_region_id, end_region_id, distance, 90)
    else:
        print("⚠ Brak ID regionów - używam losowych danych")
        exchange_data = generate_exchange_data(distance, days)
        exchange_data_7 = generate_exchange_data(distance, 7)
        exchange_data_30 = generate_exchange_data(distance, 30)
        exchange_data_90 = generate_exchange_data(distance, 90)
    
    historical_data = generate_historical_data(distance, start_location, end_location, days)
    toll_data = generate_toll_data(start_location, end_location, distance)
    carriers = generate_carrier_suggestions(start_location, end_location)
    
    historical_data_7 = generate_historical_data(distance, start_location, end_location, 7)
    historical_data_30 = generate_historical_data(distance, start_location, end_location, 30)
    historical_data_90 = generate_historical_data(distance, start_location, end_location, 90)
    
    # Pobierz metodę obliczania dystansu z zapytania (jeśli dostępna)
    distance_method = data.get('distance_method', 'unknown')
    haversine_distance = data.get('haversine_distance')
    
    result = {
        'route': route_data,
        'distance': distance,
        'distance_method': distance_method,  # 'aws', 'haversine', 'haversine_fallback'
        'haversine_distance': haversine_distance,  # Oryginalny dystans Haversine dla porównania
        'start_location': start_location,
        'end_location': end_location,
        'start_location_raw': start_location_raw,
        'end_location_raw': end_location_raw,
        'start_coords': start_coords,  # Współrzędne dla API giełd
        'end_coords': end_coords,
        'vehicle_type': vehicle_type,
        'body_type': body_type,
        'exchange_rates': exchange_data,
        'historical_rates': historical_data,
        'tolls': toll_data,
        'suggested_carriers': carriers,
        # Dane dla wszystkich okresów
        'exchange_rates_by_days': {
            '7': exchange_data_7,
            '30': exchange_data_30,
            '90': exchange_data_90
        },
        'historical_rates_by_days': {
            '7': historical_data_7,
            '30': historical_data_30,
            '90': historical_data_90
        }
    }
    
    return jsonify(result)

@app.route('/api/current-offers', methods=['POST'])
def get_current_freight_offers():
    """
    Endpoint do pobierania aktualnych ofert z API giełd (tryb 'teraz')
    Używa realnych adresów zamiast ID regionów
    """
    data = request.json
    
    # Pobierz parametry
    start_location = data.get('start_location')  # Znormalizowany (np. "Wrocław, Poland")
    end_location = data.get('end_location')
    start_location_raw = data.get('start_location_raw')  # Raw input (np. "pl00")
    end_location_raw = data.get('end_location_raw')
    start_coords = data.get('start_coords')  # [lat, lng]
    end_coords = data.get('end_coords')  # [lat, lng]
    distance = data.get('distance', 0)
    
    if not start_location or not end_location:
        return jsonify({'error': 'Brak adresów start/end'}), 400
    
    # Użyj znormalizowanych adresów dla API
    start_for_api = start_location
    end_for_api = end_location
    
    print(f"\n🌐 API Current Offers - tryb TERAZ")
    print(f"   Start: {start_for_api} (coords: {start_coords})")
    print(f"   Cel: {end_for_api} (coords: {end_coords})")
    print(f"   Dystans: {distance} km")
    
    try:
        # Pobierz aktualne oferty z API giełd - przekaż również współrzędne
        offers_data = get_current_offers(
            start_for_api,
            end_for_api,
            distance,
            start_coords=start_coords,
            end_coords=end_coords
        )
        
        return jsonify({
            'success': True,
            'data': offers_data
        })
        
    except Exception as e:
        print(f"❌ Błąd pobierania aktualnych ofert: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'has_data': False,
                'offers': [],
                'message': f'Błąd połączenia z API giełd: {str(e)}'
            }
        }), 500

@app.route('/api/calculate-distance', methods=['POST'])
def calculate_distance():
    """
    Endpoint do obliczania rzeczywistego dystansu drogowego przez AWS Location Service API
    Zwraca dystans w kilometrach, opcjonalnie geometrię trasy, lub fallback do Haversine
    """
    print("\n" + "="*60)
    print("🔵 WYWOŁANO /api/calculate-distance")
    print("="*60)
    
    data = request.json
    print(f"📥 Otrzymane dane: {data}")
    
    start_coords = data.get('start_coords')  # [lat, lng]
    end_coords = data.get('end_coords')      # [lat, lng]
    fallback_distance = data.get('fallback_distance')  # Haversine z frontendu
    include_geometry = data.get('include_geometry', False)  # Czy zwrócić geometrię trasy
    
    if not start_coords or not end_coords:
        print("❌ BŁĄD: Brak współrzędnych")
        return jsonify({'error': 'Brak współrzędnych'}), 400
    
    start_lat, start_lng = start_coords
    end_lat, end_lng = end_coords
    
    print(f"\n📏 Obliczanie dystansu AWS (geometry={include_geometry}):")
    print(f"   Start: [{start_lat}, {start_lng}]")
    print(f"   Cel: [{end_lat}, {end_lng}]")
    print(f"   Fallback distance: {fallback_distance} km")
    print(f"   AWS_LOCATION_API_KEY set: {bool(AWS_LOCATION_API_KEY)}")
    if AWS_LOCATION_API_KEY:
        print(f"   AWS_LOCATION_API_KEY prefix: {AWS_LOCATION_API_KEY[:20]}...")
    print(f"   AWS_REGION: {AWS_REGION}")
    
    # Wywołaj AWS API z możliwością pobrania geometrii
    aws_result = get_aws_route_distance(start_lat, start_lng, end_lat, end_lng, 
                                       return_geometry=include_geometry)
    
    if aws_result is not None:
        # Sukces - użyj dystansu AWS
        response_data = {
            'success': True,
            'distance': aws_result['distance'],
            'method': 'aws',
            'fallback_distance': fallback_distance
        }
        
        # Dodaj geometrię jeśli była pobrana
        if include_geometry and 'geometry' in aws_result:
            response_data['geometry'] = aws_result['geometry']
            response_data['duration'] = aws_result.get('duration', 0)
            print(f"   ✅ SUKCES: Dystans AWS: {aws_result['distance']} km, Punkty: {len(aws_result['geometry'])}")
        else:
            print(f"   ✅ SUKCES: Dystans AWS: {aws_result['distance']} km")
        
        print(f"📤 Zwracam response: method=aws, distance={aws_result['distance']}")
        print("="*60 + "\n")
        return jsonify(response_data)
    else:
        # Błąd AWS - użyj fallback (Haversine)
        print(f"   ⚠️  AWS zwrócił None - używam fallback")
        print(f"   ⚠️  Fallback do Haversine: {fallback_distance} km")
        print(f"📤 Zwracam response: method=haversine_fallback, distance={fallback_distance}")
        print("="*60 + "\n")
        return jsonify({
            'success': True,
            'distance': fallback_distance,
            'method': 'haversine_fallback',
            'message': 'AWS API niedostępny - użyto Haversine'
        })

if __name__ == '__main__':
    # Pobierz port z zmiennej środowiskowej (dla Render) lub użyj 5000 lokalnie
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
