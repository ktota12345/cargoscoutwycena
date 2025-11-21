"""
Analiza nietypowych przypadków różnic w dystansach
- Duże różnice procentowe
- Podejrzenia błędów w danych
- Trasy przez promy/wodę
"""
import pandas as pd
import numpy as np
import json

CSV_FILE = "TRIVIUM_PRZETARG_2026_pelne_dane_AWS.csv"
POSTAL_COORDS_FILE = "package/filtered_postal_codes.geojson"

def load_postal_coordinates():
    """Ładuje współrzędne do weryfikacji"""
    with open(POSTAL_COORDS_FILE, 'r', encoding='utf-8') as f:
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


def haversine_check(lat1, lon1, lat2, lon2):
    """Oblicz dystans Haversine dla weryfikacji"""
    from math import radians, cos, sin, asin, sqrt
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r


def main():
    print("=" * 100)
    print("ANALIZA NIETYPOWYCH PRZYPADKÓW")
    print("=" * 100)
    
    # Wczytaj dane
    print(f"\n📂 Wczytuję: {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE, sep=';', encoding='utf-8')
    
    print(f"📍 Ładuję współrzędne...")
    postal_coords = load_postal_coordinates()
    
    # Kolumny
    aws_col = 'Dystans [km]'
    haversine_col = 'Dystans Haversine [km]'
    
    # Filtruj tylko te z obydwoma wartościami
    df_valid = df[(df[aws_col].notna()) & (df[haversine_col].notna())].copy()
    df_valid['Różnica [km]'] = df_valid[haversine_col] - df_valid[aws_col]
    df_valid['Różnica [%]'] = ((df_valid[haversine_col] - df_valid[aws_col]) / df_valid[haversine_col] * 100)
    
    # Dodaj współrzędne dla weryfikacji
    df_valid['Origin_Key'] = df_valid['Origin Country'] + df_valid['Origin 2 Zip'].astype(str).str.zfill(2)
    df_valid['Dest_Key'] = df_valid['Destination Country'] + df_valid['Destination 2 Zip'].astype(str).str.zfill(2)
    
    # Pobierz współrzędne
    df_valid['Origin_Coords'] = df_valid['Origin_Key'].map(postal_coords)
    df_valid['Dest_Coords'] = df_valid['Dest_Key'].map(postal_coords)
    
    # Oblicz Haversine dla weryfikacji
    def calc_haversine_row(row):
        try:
            if row['Origin_Coords'] and row['Dest_Coords']:
                if isinstance(row['Origin_Coords'], tuple) and isinstance(row['Dest_Coords'], tuple):
                    lat1, lon1 = row['Origin_Coords']
                    lat2, lon2 = row['Dest_Coords']
                    return haversine_check(lat1, lon1, lat2, lon2)
        except:
            pass
        return None
    
    df_valid['Haversine_Check'] = df_valid.apply(calc_haversine_row, axis=1)
    df_valid['Haversine_Mismatch'] = abs(df_valid[haversine_col] - df_valid['Haversine_Check'].fillna(0))
    
    print(f"✅ Przeanalizowano {len(df_valid)} tras")
    
    # ========== KATEGORIA 1: AWS ZNACZNIE KRÓTSZY (>30%) ==========
    print("\n" + "=" * 100)
    print("KATEGORIA 1: AWS ZNACZNIE KRÓTSZY (>30% różnicy)")
    print("Możliwe przyczyny: błąd w danych Haversine, złe mapowanie współrzędnych")
    print("=" * 100)
    
    aws_much_shorter = df_valid[df_valid['Różnica [%]'] > 30].sort_values('Różnica [%]', ascending=False)
    
    print(f"\n🔍 Znaleziono {len(aws_much_shorter)} tras\n")
    print(f"{'#':<4} {'Trasa':<15} {'Origin':<8} {'Dest':<8} {'Haver':<8} {'AWS':<8} {'Różn.':<10} {'%':<8} {'Haver.Check':<12}")
    print("-" * 100)
    
    for idx, (i, row) in enumerate(aws_much_shorter.head(50).iterrows(), 1):
        haver_check = row['Haversine_Check'] if pd.notna(row['Haversine_Check']) else 0
        mismatch = row['Haversine_Mismatch'] if pd.notna(row['Haversine_Mismatch']) else 0
        warning = " ⚠️ BŁĄD" if mismatch > 50 else ""
        
        print(f"{idx:<4} {row['Lane Name']:<15} "
              f"{row['Origin_Key']:<8} {row['Dest_Key']:<8} "
              f"{row[haversine_col]:>7.0f} {row[aws_col]:>7.0f} "
              f"{row['Różnica [km]']:>9.0f} km {row['Różnica [%]']:>6.1f}% "
              f"{haver_check:>7.0f} km{warning}")
    
    # ========== KATEGORIA 2: AWS ZNACZNIE DŁUŻSZY (>50%) ==========
    print("\n" + "=" * 100)
    print("KATEGORIA 2: AWS ZNACZNIE DŁUŻSZY (>50% różnicy)")
    print("Możliwe przyczyny: promy, objazdy przez góry/wody, brak bezpośrednich połączeń")
    print("=" * 100)
    
    aws_much_longer = df_valid[df_valid['Różnica [%]'] < -50].sort_values('Różnica [%]')
    
    print(f"\n🔍 Znaleziono {len(aws_much_longer)} tras\n")
    print(f"{'#':<4} {'Trasa':<15} {'Origin':<8} {'Dest':<8} {'Haver':<8} {'AWS':<8} {'Różn.':<10} {'%':<8} {'Typ':<15}")
    print("-" * 100)
    
    # Identyfikuj typ nietypowości
    def identify_route_type(row):
        origin = row['Origin Country']
        dest = row['Destination Country']
        
        # Kraje wymagające promu
        island_countries = ['GB', 'IE', 'IS', 'CY', 'MT']
        water_crossing = ['ES-GB', 'FR-GB', 'DK-SE', 'DK-NO', 'PL-SE']
        
        if origin in island_countries or dest in island_countries:
            return "🚢 Prom/Wyspa"
        if f"{origin}-{dest}" in water_crossing or f"{dest}-{origin}" in water_crossing:
            return "🚢 Przeprawa wodna"
        if origin != dest and abs(row['Różnica [%]']) > 100:
            return "🏔️ Góry/Objazd"
        return "❓ Nieznane"
    
    aws_much_longer['Route_Type'] = aws_much_longer.apply(identify_route_type, axis=1)
    
    for idx, (i, row) in enumerate(aws_much_longer.head(50).iterrows(), 1):
        print(f"{idx:<4} {row['Lane Name']:<15} "
              f"{row['Origin_Key']:<8} {row['Dest_Key']:<8} "
              f"{row[haversine_col]:>7.0f} {row[aws_col]:>7.0f} "
              f"{row['Różnica [km]']:>9.0f} km {row['Różnica [%]']:>6.1f}% "
              f"{row['Route_Type']:<15}")
    
    # ========== KATEGORIA 3: BŁĘDY W DANYCH HAVERSINE ==========
    print("\n" + "=" * 100)
    print("KATEGORIA 3: PODEJRZENIA BŁĘDÓW W DANYCH HAVERSINE")
    print("Haversine w CSV różni się >50km od przeliczonego Haversine")
    print("=" * 100)
    
    haversine_errors = df_valid[df_valid['Haversine_Mismatch'] > 50].sort_values('Haversine_Mismatch', ascending=False)
    
    print(f"\n🔍 Znaleziono {len(haversine_errors)} tras z błędami\n")
    print(f"{'#':<4} {'Trasa':<15} {'Origin':<8} {'Dest':<8} {'CSV Haver':<10} {'Check Haver':<12} {'Różn.':<10}")
    print("-" * 100)
    
    for idx, (i, row) in enumerate(haversine_errors.head(30).iterrows(), 1):
        haver_check = row['Haversine_Check'] if pd.notna(row['Haversine_Check']) else 0
        mismatch = row['Haversine_Mismatch'] if pd.notna(row['Haversine_Mismatch']) else 0
        
        print(f"{idx:<4} {row['Lane Name']:<15} "
              f"{row['Origin_Key']:<8} {row['Dest_Key']:<8} "
              f"{row[haversine_col]:>9.0f} km {haver_check:>11.0f} km "
              f"{mismatch:>9.0f} km")
    
    # ========== KATEGORIA 4: EKSTREMALNE PRZYPADKI ==========
    print("\n" + "=" * 100)
    print("KATEGORIA 4: EKSTREMALNE PRZYPADKI")
    print("Bezwzględna różnica >500 km")
    print("=" * 100)
    
    extreme_cases = df_valid[abs(df_valid['Różnica [km]']) > 500].sort_values('Różnica [km]', key=abs, ascending=False)
    
    print(f"\n🔍 Znaleziono {len(extreme_cases)} ekstremalnych tras\n")
    print(f"{'#':<4} {'Trasa':<15} {'Origin':<8} {'Dest':<8} {'Haver':<8} {'AWS':<8} {'Różn.':<10} {'%':<8} {'Typ':<15}")
    print("-" * 100)
    
    extreme_cases['Route_Type'] = extreme_cases.apply(identify_route_type, axis=1)
    
    for idx, (i, row) in enumerate(extreme_cases.iterrows(), 1):
        print(f"{idx:<4} {row['Lane Name']:<15} "
              f"{row['Origin_Key']:<8} {row['Dest_Key']:<8} "
              f"{row[haversine_col]:>7.0f} {row[aws_col]:>7.0f} "
              f"{row['Różnica [km]']:>9.0f} km {row['Różnica [%]']:>6.1f}% "
              f"{row['Route_Type']:<15}")
    
    # ========== PODSUMOWANIE ==========
    print("\n" + "=" * 100)
    print("PODSUMOWANIE NIETYPOWYCH PRZYPADKÓW")
    print("=" * 100)
    
    total_unusual = len(df_valid[abs(df_valid['Różnica [%]']) > 30])
    
    print(f"\n📊 Statystyki:")
    print(f"   AWS >30% krótszy:           {len(aws_much_shorter):4d} tras ({len(aws_much_shorter)/len(df_valid)*100:.1f}%)")
    print(f"   AWS >50% dłuższy:           {len(aws_much_longer):4d} tras ({len(aws_much_longer)/len(df_valid)*100:.1f}%)")
    print(f"   Błędy w Haversine (>50km):  {len(haversine_errors):4d} tras ({len(haversine_errors)/len(df_valid)*100:.1f}%)")
    print(f"   Różnica >500 km:            {len(extreme_cases):4d} tras ({len(extreme_cases)/len(df_valid)*100:.1f}%)")
    print(f"   RAZEM nietypowe (>30%):     {total_unusual:4d} tras ({total_unusual/len(df_valid)*100:.1f}%)")
    
    # Analiza po krajach
    print("\n" + "=" * 100)
    print("NAJCZĘSTSZE NIETYPOWE POŁĄCZENIA (TOP 20)")
    print("=" * 100)
    
    unusual_routes = df_valid[abs(df_valid['Różnica [%]']) > 30].copy()
    unusual_routes['Route_Pair'] = unusual_routes['Origin Country'] + '-' + unusual_routes['Destination Country']
    route_counts = unusual_routes['Route_Pair'].value_counts()
    
    print(f"\n{'#':<4} {'Połączenie':<12} {'Liczba tras':<15} {'Średnia różnica':<20}")
    print("-" * 60)
    
    for idx, (route_pair, count) in enumerate(route_counts.head(20).items(), 1):
        subset = unusual_routes[unusual_routes['Route_Pair'] == route_pair]
        avg_diff = subset['Różnica [%]'].mean()
        print(f"{idx:<4} {route_pair:<12} {count:>10d} tras {avg_diff:>15.1f}%")
    
    # Zapisz raporty
    print("\n" + "=" * 100)
    print("ZAPIS RAPORTÓW")
    print("=" * 100)
    
    # Raport 1: AWS krótszy
    aws_much_shorter.to_csv('unusual_aws_shorter.csv', sep=';', index=False, encoding='utf-8')
    print(f"✅ unusual_aws_shorter.csv - {len(aws_much_shorter)} tras gdzie AWS >30% krótszy")
    
    # Raport 2: AWS dłuższy
    aws_much_longer.to_csv('unusual_aws_longer.csv', sep=';', index=False, encoding='utf-8')
    print(f"✅ unusual_aws_longer.csv - {len(aws_much_longer)} tras gdzie AWS >50% dłuższy")
    
    # Raport 3: Błędy Haversine
    haversine_errors.to_csv('unusual_haversine_errors.csv', sep=';', index=False, encoding='utf-8')
    print(f"✅ unusual_haversine_errors.csv - {len(haversine_errors)} tras z błędami w Haversine")
    
    # Raport 4: Wszystkie nietypowe
    unusual_all = df_valid[abs(df_valid['Różnica [%]']) > 30].sort_values('Różnica [%]', key=abs, ascending=False)
    unusual_all.to_csv('unusual_all_cases.csv', sep=';', index=False, encoding='utf-8')
    print(f"✅ unusual_all_cases.csv - {len(unusual_all)} wszystkich nietypowych tras")
    
    print("\n✅ Analiza zakończona!")


if __name__ == "__main__":
    main()
