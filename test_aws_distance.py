"""
Test AWS Location Service API dla pierwszych 3 tras z CSV
Używa HTTP requests z API key
"""
import json
import os
import pandas as pd
import requests
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe
load_dotenv()

# Konfiguracja AWS
AWS_LOCATION_API_KEY = os.getenv("AWS_LOCATION_API_KEY")
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")


def load_postal_coordinates():
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


def get_aws_route_distance(start_lat, start_lng, end_lat, end_lng):
    """
    Wywołuje AWS Location Service Routes API aby obliczyć rzeczywisty dystans drogowy.
    Zwraca dystans w kilometrach lub None w przypadku błędu.
    """
    if not AWS_LOCATION_API_KEY:
        print("   ❌ AWS_LOCATION_API_KEY nie jest ustawiony w .env")
        return None
    
    try:
        print(f"   🌐 Wywołuję AWS Location Service...")
        print(f"      Origin: [{start_lng}, {start_lat}]")
        print(f"      Destination: [{end_lng}, {end_lat}]")
        
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
        
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            # Pobierz dystans z pierwszej trasy
            # AWS zwraca dystans w metrach w TravelSteps
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
            else:
                print(f"   ❌ Brak tras w odpowiedzi AWS")
                return None
        else:
            print(f"   ❌ AWS API ERROR: Status {response.status_code}")
            print(f"      Response: {response.text[:500]}")
            return None
            
    except requests.exceptions.Timeout:
        print("   ❌ AWS API ERROR: Timeout")
        return None
    except Exception as e:
        print(f"   ❌ AWS API ERROR: {str(e)}")
        return None


def main():
    print("=" * 80)
    print("TEST AWS LOCATION SERVICE API - PIERWSZE 3 TRASY")
    print("=" * 80)
    
    # Wczytaj CSV z ustawionym separatorem i kodowaniem
    print("\n📂 Wczytuję CSV...")
    df = pd.read_csv('TRIVIUM_PRZETARG_2026_pelne_dane.csv', 
                     sep=';', 
                     encoding='utf-8',
                     nrows=3)  # Tylko pierwsze 3 wiersze
    
    print(f"✅ Wczytano {len(df)} tras\n")
    
    # Wczytaj współrzędne
    print("📍 Ładuję współrzędne kodów pocztowych...")
    postal_coords = load_postal_coordinates()
    print(f"✅ Załadowano {len(postal_coords)} kodów pocztowych\n")
    
    # Przetwórz każdą trasę
    print("=" * 80)
    print("PORÓWNANIE DYSTANSÓW")
    print("=" * 80)
    
    for idx, row in df.iterrows():
        lane_name = row['Lane Name']
        origin_country = row['Origin Country']
        origin_zip = str(row['Origin 2 Zip']).zfill(2)  # Dopełnij zerami do 2 cyfr
        dest_country = row['Destination Country']
        dest_zip = str(row['Destination 2 Zip']).zfill(2)
        old_distance = row['Dystans [km]']
        
        print(f"\n🚛 TRASA #{idx + 1}: {lane_name}")
        print(f"   Początek: {origin_country}{origin_zip}")
        print(f"   Koniec:   {dest_country}{dest_zip}")
        print(f"   📊 STARY DYSTANS (Haversine): {old_distance} km")
        
        # Pobierz współrzędne
        start_key = f"{origin_country}{origin_zip}"
        end_key = f"{dest_country}{dest_zip}"
        
        if start_key not in postal_coords:
            print(f"   ⚠️  Brak współrzędnych dla {start_key}")
            continue
            
        if end_key not in postal_coords:
            print(f"   ⚠️  Brak współrzędnych dla {end_key}")
            continue
        
        start_lat, start_lng = postal_coords[start_key]
        end_lat, end_lng = postal_coords[end_key]
        
        # Wywołaj AWS API
        new_distance = get_aws_route_distance(start_lat, start_lng, end_lat, end_lng)
        
        if new_distance:
            difference = new_distance - old_distance
            percent_diff = (difference / old_distance) * 100 if old_distance > 0 else 0
            
            print(f"   ✅ NOWY DYSTANS (AWS API):    {new_distance} km")
            print(f"   📈 RÓŻNICA: {difference:+.2f} km ({percent_diff:+.1f}%)")
            
            if abs(percent_diff) > 10:
                print(f"   ⚠️  Znacząca różnica > 10%!")
        else:
            print(f"   ❌ Nie udało się obliczyć dystansu przez AWS API")
        
        print("-" * 80)
    
    print("\n✅ Test zakończony!")


if __name__ == "__main__":
    main()
