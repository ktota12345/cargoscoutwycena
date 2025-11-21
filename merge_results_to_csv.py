"""
Skrypt łączący wyniki batch_route_checker z plikiem CSV TRIVIUM.
Dodaje kolumny ze średnimi stawkami i liczbą ofert.
"""

import json
import pandas as pd
import sys

# Nazwy plików
INPUT_CSV = 'TRIVIUM PRZETARG 2026(Arkusz1).csv'
OUTPUT_CSV = 'TRIVIUM_PRZETARG_2026_z_danymi.csv'
RESULTS_JSON = 'route_analysis_20251114_182948.json'

def main():
    print("=" * 80)
    print("MERGE RESULTS TO CSV")
    print("=" * 80)
    
    # Wczytaj CSV z automatycznym wykrywaniem separatora i kodowania
    print(f"\n[LOAD] Wczytuję {INPUT_CSV}...")
    
    # Próbuj różne kodowania
    encodings = ['utf-8', 'windows-1250', 'iso-8859-2', 'cp1252']
    df = None
    
    for encoding in encodings:
        try:
            df = pd.read_csv(INPUT_CSV, encoding=encoding, sep=None, engine='python')
            print(f"[OK] Wczytano CSV z kodowaniem: {encoding}")
            break
        except Exception as e:
            continue
    
    if df is None:
        print("[ERROR] Nie udało się wczytać pliku CSV")
        return
    
    print(f"[OK] Wczytano {len(df)} wierszy")
    print(f"[INFO] Kolumny w CSV: {list(df.columns)}")
    
    # Sprawdź czy jest kolumna Lane Name
    if 'Lane Name' not in df.columns:
        print("[ERROR] Brak kolumny 'Lane Name' w CSV!")
        print("[INFO] Dostępne kolumny:", list(df.columns))
        return
    
    # Wczytaj wyniki JSON
    print(f"\n[LOAD] Wczytuję {RESULTS_JSON}...")
    with open(RESULTS_JSON, 'r', encoding='utf-8') as f:
        results = json.load(f)
    print(f"[OK] Wczytano {len(results)} tras z JSON")
    
    # Stwórz słownik: route_code -> dane
    results_dict = {}
    for result in results:
        route_code = result.get('original_route')
        if route_code:
            results_dict[route_code] = result
    
    print(f"[OK] Przygotowano {len(results_dict)} tras do dopasowania")
    
    # Dodaj nowe kolumny
    new_columns = [
        'Mapping TimoCom',
        'Mapping TransEU',
        'Dystans [km]',
        'TimoCom 7d [EUR/km]',
        'TimoCom 30d [EUR/km]',
        'TimoCom 90d [EUR/km]',
        'TimoCom 7d oferty',
        'TimoCom 30d oferty',
        'TimoCom 90d oferty',
        'TransEU 7d [EUR/km]',
        'TransEU 30d [EUR/km]',
        'TransEU 90d [EUR/km]',
        'Uwagi'
    ]
    
    for col in new_columns:
        df[col] = ''
    
    # Wypełnij dane
    print("\n[PROCESS] Łączę dane...")
    matched = 0
    not_matched = 0
    
    for idx, row in df.iterrows():
        lane_name = str(row['Lane Name']).strip()
        
        if lane_name in results_dict:
            matched += 1
            result = results_dict[lane_name]
            
            # Mapping
            df.at[idx, 'Mapping TimoCom'] = f"{result.get('timocom_start', '')}-{result.get('timocom_end', '')}"
            df.at[idx, 'Mapping TransEU'] = f"{result.get('transeu_start', '')}-{result.get('transeu_end', '')}"
            
            # Dystans
            if result.get('distance_km'):
                df.at[idx, 'Dystans [km]'] = result['distance_km']
            
            # Status i uwagi
            status = result.get('status')
            
            if status == 'too_short':
                df.at[idx, 'Uwagi'] = 'za krótka trasa'
            elif status == 'mapping_failed':
                df.at[idx, 'Uwagi'] = 'błąd mapowania'
            elif status == 'error':
                df.at[idx, 'Uwagi'] = f"błąd: {result.get('error', 'nieznany')}"
            elif status in ['success', 'cached']:
                # Dane są dostępne
                data = result.get('data', {})
                
                # TimoCom
                timocom = data.get('timocom', {})
                for period in ['7d', '30d', '90d']:
                    period_data = timocom.get(period, {})
                    if period_data.get('has_data'):
                        # Średnia stawka
                        rate = period_data.get('avg_rate_per_km')
                        if rate:
                            df.at[idx, f'TimoCom {period} [EUR/km]'] = round(rate, 2)
                        
                        # Liczba ofert
                        offers = period_data.get('total_offers')
                        if offers:
                            df.at[idx, f'TimoCom {period} oferty'] = offers
                
                # TransEU
                transeu = data.get('transeu', {})
                for period in ['7d', '30d', '90d']:
                    period_data = transeu.get(period, {})
                    if period_data.get('has_data'):
                        # Średnia stawka
                        rate = period_data.get('avg_rate_per_km')
                        if rate:
                            df.at[idx, f'TransEU {period} [EUR/km]'] = round(rate, 2)
                
                # Sprawdź czy są jakieś dane
                has_any_data = False
                for col in ['TimoCom 7d [EUR/km]', 'TimoCom 30d [EUR/km]', 'TimoCom 90d [EUR/km]',
                           'TransEU 7d [EUR/km]', 'TransEU 30d [EUR/km]', 'TransEU 90d [EUR/km]']:
                    if df.at[idx, col] != '':
                        has_any_data = True
                        break
                
                if not has_any_data:
                    df.at[idx, 'Uwagi'] = 'brak danych historycznych'
        else:
            not_matched += 1
            df.at[idx, 'Uwagi'] = 'nie znaleziono w analizie'
    
    print(f"[OK] Dopasowano: {matched} tras")
    print(f"[WARN] Nie dopasowano: {not_matched} tras")
    
    # Zapisz
    print(f"\n[SAVE] Zapisuję wyniki do {OUTPUT_CSV}...")
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig', sep=';')
    print(f"[OK] Zapisano!")
    
    # Statystyki
    print("\n" + "=" * 80)
    print("STATYSTYKI")
    print("=" * 80)
    print(f"Wierszy w CSV:          {len(df)}")
    print(f"Dopasowanych tras:      {matched}")
    print(f"Nie dopasowanych:       {not_matched}")
    print(f"Za krótkie trasy:       {len(df[df['Uwagi'] == 'za krótka trasa'])}")
    print(f"Z danymi TimoCom:       {len(df[df['TimoCom 7d [EUR/km]'] != ''])}")
    print(f"Z danymi TransEU:       {len(df[df['TransEU 7d [EUR/km]'] != ''])}")
    print(f"\nPlik wyjściowy: {OUTPUT_CSV}")
    print("=" * 80)

if __name__ == '__main__':
    main()
