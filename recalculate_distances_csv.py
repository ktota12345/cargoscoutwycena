"""
Skrypt do przeliczenia dystansów w CSV używając AWS Location Service API
Zastępuje wartości w kolumnie "Dystans [km]" nowymi wartościami z AWS
"""
import json
import os
import pandas as pd
import requests
import time
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe
load_dotenv()

# Konfiguracja AWS
AWS_LOCATION_API_KEY = os.getenv("AWS_LOCATION_API_KEY")
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")

# Konfiguracja
CSV_FILE = "TRIVIUM_PRZETARG_2026_pelne_dane.csv"
OUTPUT_FILE = "TRIVIUM_PRZETARG_2026_pelne_dane_AWS.csv"
CHECKPOINT_FILE = "distance_recalc_checkpoint.json"
DELAY_BETWEEN_REQUESTS = 0.1  # 100ms między requestami aby nie przekroczyć limitów


def load_postal_coordinates():
    """Ładuje współrzędne kodów pocztowych z GeoJSON"""
    with open('package/filtered_postal_codes.geojson', 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    coordinates = {}
    for feature in geojson_data['features']:
        country_code = feature['properties']['country_code']
        postal_code = feature['properties']['postal_code']
        latitude = feature['properties']['latitude']
        longitude = feature['properties']['longitude']
        
        key = f"{country_code}{postal_code}"
        coordinates[key] = (latitude, longitude)
    
    return coordinates


def get_aws_route_distance(start_lat, start_lng, end_lat, end_lng):
    """Wywołuje AWS Location Service API Routes"""
    if not AWS_LOCATION_API_KEY:
        return None
    
    try:
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
            if 'Routes' in data and len(data['Routes']) > 0:
                total_distance = 0
                for leg in data['Routes'][0].get('Legs', []):
                    vehicle_details = leg.get('VehicleLegDetails', {})
                    travel_steps = vehicle_details.get('TravelSteps', [])
                    for step in travel_steps:
                        total_distance += step.get('Distance', 0)
                
                distance_km = total_distance / 1000.0
                return round(distance_km, 2)
        return None
    except:
        return None


def save_checkpoint(processed_indices, checkpoint_file):
    """Zapisuje checkpoint z przetworzonymi indeksami"""
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump({'processed': list(processed_indices)}, f)


def load_checkpoint(checkpoint_file):
    """Ładuje checkpoint"""
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get('processed', []))
    return set()


def main():
    print("=" * 80)
    print("PRZELICZANIE DYSTANSÓW - AWS Location Service API")
    print("=" * 80)
    
    # Sprawdź API key
    if not AWS_LOCATION_API_KEY:
        print("\n❌ BŁĄD: AWS_LOCATION_API_KEY nie jest ustawiony w .env!")
        print("   Dodaj swój API key do pliku .env")
        return
    
    # Wczytaj CSV
    print(f"\n📂 Wczytuję CSV: {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE, sep=';', encoding='utf-8')
    total_rows = len(df)
    print(f"✅ Wczytano {total_rows} tras")
    
    # Wczytaj współrzędne
    print("\n📍 Ładuję współrzędne kodów pocztowych...")
    postal_coords = load_postal_coordinates()
    print(f"✅ Załadowano {len(postal_coords)} kodów pocztowych")
    
    # Wczytaj checkpoint
    processed_indices = load_checkpoint(CHECKPOINT_FILE)
    if processed_indices:
        print(f"\n🔄 Znaleziono checkpoint: {len(processed_indices)} tras już przetworzone")
    
    # Statystyki
    success_count = 0
    failed_count = 0
    skipped_count = len(processed_indices)
    start_time = time.time()
    
    print("\n" + "=" * 80)
    print("ROZPOCZYNAM PRZELICZANIE")
    print("=" * 80)
    print(f"⚠️  Zostanie wykonanych ~{total_rows - len(processed_indices)} zapytań do AWS API")
    print(f"⏱️  Szacowany czas: ~{((total_rows - len(processed_indices)) * 0.5) / 60:.1f} minut")
    print("💾 Checkpoint jest zapisywany co 50 tras\n")
    
    # Dodaj nową kolumnę jeśli nie istnieje
    if 'Dystans AWS [km]' not in df.columns:
        df['Dystans AWS [km]'] = None
    
    # Przetwarzaj każdą trasę
    for idx, row in df.iterrows():
        # Skip jeśli już przetworzono
        if idx in processed_indices:
            continue
        
        # Progress
        processed = len(processed_indices) + success_count + failed_count
        percent = (processed / total_rows) * 100
        elapsed = time.time() - start_time
        if processed > 0:
            eta_seconds = (elapsed / processed) * (total_rows - processed)
            eta_minutes = int(eta_seconds / 60)
            print(f"\r[{processed}/{total_rows}] {percent:.1f}% | Sukces: {success_count} | Błędy: {failed_count} | ETA: {eta_minutes}m", end='', flush=True)
        
        # Pobierz dane trasy
        origin_country = row['Origin Country']
        origin_zip = str(row['Origin 2 Zip']).zfill(2)
        dest_country = row['Destination Country']
        dest_zip = str(row['Destination 2 Zip']).zfill(2)
        
        # Klucze
        start_key = f"{origin_country}{origin_zip}"
        end_key = f"{dest_country}{dest_zip}"
        
        # Sprawdź czy mamy współrzędne
        if start_key not in postal_coords or end_key not in postal_coords:
            failed_count += 1
            processed_indices.add(idx)
            continue
        
        # Pobierz współrzędne
        start_lat, start_lng = postal_coords[start_key]
        end_lat, end_lng = postal_coords[end_key]
        
        # Wywołaj AWS API
        aws_distance = get_aws_route_distance(start_lat, start_lng, end_lat, end_lng)
        
        if aws_distance is not None:
            # Zapisz nowy dystans
            df.at[idx, 'Dystans AWS [km]'] = aws_distance
            success_count += 1
        else:
            failed_count += 1
        
        processed_indices.add(idx)
        
        # Zapisz checkpoint co 50 tras
        if (success_count + failed_count) % 50 == 0:
            save_checkpoint(processed_indices, CHECKPOINT_FILE)
            # Zapisz także częściowy CSV
            df.to_csv(OUTPUT_FILE, sep=';', index=False, encoding='utf-8')
        
        # Delay między requestami
        time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # Finalny progress
    print(f"\r[{total_rows}/{total_rows}] 100.0% | Sukces: {success_count} | Błędy: {failed_count} | ZAKOŃCZONO   ")
    
    # Teraz zastąp starą kolumnę nową
    print("\n" + "=" * 80)
    print("ZASTĘPOWANIE WARTOŚCI")
    print("=" * 80)
    
    # Backup starej kolumny
    df['Dystans Haversine [km]'] = df['Dystans [km]']
    
    # Zastąp AWS wartościami, gdzie są dostępne
    # Gdzie AWS jest None, zostaw starą wartość
    df['Dystans [km]'] = df['Dystans AWS [km]'].combine_first(df['Dystans [km]'])
    
    # Usuń kolumnę tymczasową
    df = df.drop(columns=['Dystans AWS [km]'])
    
    # Zapisz wynik
    print(f"\n💾 Zapisuję wynik do: {OUTPUT_FILE}...")
    df.to_csv(OUTPUT_FILE, sep=';', index=False, encoding='utf-8')
    
    # Usuń checkpoint
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        print(f"✅ Usunięto checkpoint")
    
    # Statystyki końcowe
    elapsed_total = time.time() - start_time
    print("\n" + "=" * 80)
    print("STATYSTYKI")
    print("=" * 80)
    print(f"✅ Sukces:        {success_count} tras")
    print(f"❌ Błędy:         {failed_count} tras")
    print(f"⏭️  Pominięto:     {skipped_count} tras (z checkpoint)")
    print(f"⏱️  Czas:          {elapsed_total / 60:.1f} minut")
    print(f"📊 Średni czas:   {(elapsed_total / (success_count + failed_count)):.2f}s/trasa" if (success_count + failed_count) > 0 else "")
    print(f"\n📁 Plik wyjściowy: {OUTPUT_FILE}")
    print(f"📝 Stara kolumna zachowana jako: 'Dystans Haversine [km]'")
    print(f"📝 Nowa kolumna:                 'Dystans [km]' (z AWS)")
    print("\n✅ Gotowe!")


if __name__ == "__main__":
    main()
