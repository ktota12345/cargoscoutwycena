"""
Skrypt łączący wyniki batch_route_checker z plikiem CSV TRIVIUM.
Dodaje kolumny ze średnimi stawkami, medianami i liczbą ofert dla wszystkich typów pojazdów.
"""

import json
import pandas as pd

# Nazwy plików
INPUT_CSV = 'TRIVIUM PRZETARG 2026(Arkusz1).csv'
OUTPUT_CSV = 'TRIVIUM_PRZETARG_2026_pelne_dane.csv'
RESULTS_JSON = 'route_analysis_20251114_221319.json'

def main():
    print("=" * 80)
    print("MERGE RESULTS TO CSV - PEŁNE DANE (WSZYSTKIE TYPY POJAZDÓW)")
    print("=" * 80)
    
    # Wczytaj CSV
    print(f"\n[LOAD] Wczytuję {INPUT_CSV}...")
    encodings = ['utf-8', 'windows-1250', 'iso-8859-2', 'cp1252']
    df = None
    
    for encoding in encodings:
        try:
            df = pd.read_csv(INPUT_CSV, encoding=encoding, sep=None, engine='python')
            print(f"[OK] Wczytano CSV z kodowaniem: {encoding}")
            break
        except:
            continue
    
    if df is None:
        print("[ERROR] Nie udało się wczytać pliku CSV")
        return
    
    print(f"[OK] Wczytano {len(df)} wierszy")
    
    if 'Lane Name' not in df.columns:
        print("[ERROR] Brak kolumny 'Lane Name' w CSV!")
        return
    
    # Wczytaj wyniki JSON
    print(f"\n[LOAD] Wczytuję {RESULTS_JSON}...")
    with open(RESULTS_JSON, 'r', encoding='utf-8') as f:
        results = json.load(f)
    print(f"[OK] Wczytano {len(results)} tras z JSON")
    
    # Słownik: route_code -> dane
    results_dict = {}
    for result in results:
        route_code = result.get('original_route')
        if route_code:
            results_dict[route_code] = result
    
    print(f"[OK] Przygotowano {len(results_dict)} tras do dopasowania")
    
    # Definicja wszystkich nowych kolumn (57 kolumn!)
    new_columns = [
        'Mapping TimoCom',
        'Mapping TransEU',
        'Dystans [km]',
        
        # TimoCom - Naczepa (9 kolumn)
        'TC Naczepa Avg 7d', 'TC Naczepa Avg 30d', 'TC Naczepa Avg 90d',
        'TC Naczepa Median 7d', 'TC Naczepa Median 30d', 'TC Naczepa Median 90d',
        'TC Naczepa Oferty 7d', 'TC Naczepa Oferty 30d', 'TC Naczepa Oferty 90d',
        
        # TimoCom - Do 3.5t (6 kolumn - brak mediany)
        'TC 3.5t Avg 7d', 'TC 3.5t Avg 30d', 'TC 3.5t Avg 90d',
        'TC 3.5t Oferty 7d', 'TC 3.5t Oferty 30d', 'TC 3.5t Oferty 90d',
        
        # TimoCom - Do 12t (6 kolumn - brak mediany)
        'TC 12t Avg 7d', 'TC 12t Avg 30d', 'TC 12t Avg 90d',
        'TC 12t Oferty 7d', 'TC 12t Oferty 30d', 'TC 12t Oferty 90d',
        
        # Trans.eu - Lorry (9 kolumn)
        'TE Lorry Avg 7d', 'TE Lorry Avg 30d', 'TE Lorry Avg 90d',
        'TE Lorry Median 7d', 'TE Lorry Median 30d', 'TE Lorry Median 90d',
        'TE Lorry Oferty 7d', 'TE Lorry Oferty 30d', 'TE Lorry Oferty 90d',
        
        # Trans.eu - Solo (9 kolumn)
        'TE Solo Avg 7d', 'TE Solo Avg 30d', 'TE Solo Avg 90d',
        'TE Solo Median 7d', 'TE Solo Median 30d', 'TE Solo Median 90d',
        'TE Solo Oferty 7d', 'TE Solo Oferty 30d', 'TE Solo Oferty 90d',
        
        # Trans.eu - Bus (9 kolumn)
        'TE Bus Avg 7d', 'TE Bus Avg 30d', 'TE Bus Avg 90d',
        'TE Bus Median 7d', 'TE Bus Median 30d', 'TE Bus Median 90d',
        'TE Bus Oferty 7d', 'TE Bus Oferty 30d', 'TE Bus Oferty 90d',
        
        # Trans.eu - Double Trailer (9 kolumn)
        'TE DblTrailer Avg 7d', 'TE DblTrailer Avg 30d', 'TE DblTrailer Avg 90d',
        'TE DblTrailer Median 7d', 'TE DblTrailer Median 30d', 'TE DblTrailer Median 90d',
        'TE DblTrailer Oferty 7d', 'TE DblTrailer Oferty 30d', 'TE DblTrailer Oferty 90d',
        
        'Uwagi'
    ]
    
    for col in new_columns:
        df[col] = ''
    
    print(f"[INFO] Dodano {len(new_columns)} nowych kolumn")
    
    # Wypełnij dane
    print("\n[PROCESS] Łączę dane...")
    matched = 0
    
    for idx, row in df.iterrows():
        lane_name = str(row['Lane Name']).strip()
        
        if lane_name not in results_dict:
            df.at[idx, 'Uwagi'] = 'nie znaleziono w analizie'
            continue
        
        matched += 1
        result = results_dict[lane_name]
        
        # Mapping
        df.at[idx, 'Mapping TimoCom'] = f"{result.get('timocom_start', '')}-{result.get('timocom_end', '')}"
        df.at[idx, 'Mapping TransEU'] = f"{result.get('transeu_start', '')}-{result.get('transeu_end', '')}"
        
        # Dystans
        if result.get('distance_km'):
            df.at[idx, 'Dystans [km]'] = result['distance_km']
        
        # Status
        status = result.get('status')
        
        if status == 'too_short':
            df.at[idx, 'Uwagi'] = 'za krótka trasa'
            continue
        elif status == 'mapping_failed':
            df.at[idx, 'Uwagi'] = 'błąd mapowania'
            continue
        elif status == 'error':
            df.at[idx, 'Uwagi'] = f"błąd: {result.get('error', 'nieznany')}"
            continue
        
        # Dane są dostępne
        data = result.get('data', {})
        
        # TimoCom
        timocom = data.get('timocom', {})
        for period in ['7d', '30d', '90d']:
            period_data = timocom.get(period, {})
            
            # Naczepa
            trailer = period_data.get('trailer', {})
            if trailer.get('avg'):
                df.at[idx, f'TC Naczepa Avg {period}'] = round(trailer['avg'], 2)
            if trailer.get('median'):
                df.at[idx, f'TC Naczepa Median {period}'] = round(trailer['median'], 2)
            if trailer.get('offers'):
                df.at[idx, f'TC Naczepa Oferty {period}'] = trailer['offers']
            
            # Do 3.5t
            v35t = period_data.get('vehicle_3_5t', {})
            if v35t.get('avg'):
                df.at[idx, f'TC 3.5t Avg {period}'] = round(v35t['avg'], 2)
            if v35t.get('offers'):
                df.at[idx, f'TC 3.5t Oferty {period}'] = v35t['offers']
            
            # Do 12t
            v12t = period_data.get('vehicle_12t', {})
            if v12t.get('avg'):
                df.at[idx, f'TC 12t Avg {period}'] = round(v12t['avg'], 2)
            if v12t.get('offers'):
                df.at[idx, f'TC 12t Oferty {period}'] = v12t['offers']
        
        # Trans.eu
        transeu = data.get('transeu', {})
        for period in ['7d', '30d', '90d']:
            period_data = transeu.get(period, {})
            
            # Lorry
            lorry = period_data.get('lorry', {})
            if lorry.get('avg'):
                df.at[idx, f'TE Lorry Avg {period}'] = round(lorry['avg'], 2)
            if lorry.get('median'):
                df.at[idx, f'TE Lorry Median {period}'] = round(lorry['median'], 2)
            if lorry.get('records'):
                df.at[idx, f'TE Lorry Oferty {period}'] = lorry['records']
            
            # Solo
            solo = period_data.get('solo', {})
            if solo.get('avg'):
                df.at[idx, f'TE Solo Avg {period}'] = round(solo['avg'], 2)
            if solo.get('median'):
                df.at[idx, f'TE Solo Median {period}'] = round(solo['median'], 2)
            if solo.get('records'):
                df.at[idx, f'TE Solo Oferty {period}'] = solo['records']
            
            # Bus
            bus = period_data.get('bus', {})
            if bus.get('avg'):
                df.at[idx, f'TE Bus Avg {period}'] = round(bus['avg'], 2)
            if bus.get('median'):
                df.at[idx, f'TE Bus Median {period}'] = round(bus['median'], 2)
            if bus.get('records'):
                df.at[idx, f'TE Bus Oferty {period}'] = bus['records']
            
            # Double Trailer
            double = period_data.get('double_trailer', {})
            if double.get('avg'):
                df.at[idx, f'TE DblTrailer Avg {period}'] = round(double['avg'], 2)
            if double.get('median'):
                df.at[idx, f'TE DblTrailer Median {period}'] = round(double['median'], 2)
            if double.get('records'):
                df.at[idx, f'TE DblTrailer Oferty {period}'] = double['records']
    
    print(f"[OK] Dopasowano: {matched} tras")
    
    # Zapisz
    print(f"\n[SAVE] Zapisuję wyniki do {OUTPUT_CSV}...")
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig', sep=';')
    print(f"[OK] Zapisano!")
    
    # Statystyki
    print("\n" + "=" * 80)
    print("STATYSTYKI")
    print("=" * 80)
    print(f"Wierszy w CSV:                {len(df)}")
    print(f"Dopasowanych tras:            {matched}")
    print(f"Za krótkie trasy:             {len(df[df['Uwagi'] == 'za krótka trasa'])}")
    print(f"\nTimoCom:")
    print(f"  Naczepa (z danymi):         {len(df[df['TC Naczepa Avg 7d'] != ''])}")
    print(f"  Do 3.5t (z danymi):         {len(df[df['TC 3.5t Avg 7d'] != ''])}")
    print(f"  Do 12t (z danymi):          {len(df[df['TC 12t Avg 7d'] != ''])}")
    print(f"\nTrans.eu:")
    print(f"  Lorry (z danymi):           {len(df[df['TE Lorry Avg 7d'] != ''])}")
    print(f"  Solo (z danymi):            {len(df[df['TE Solo Avg 7d'] != ''])}")
    print(f"  Bus (z danymi):             {len(df[df['TE Bus Avg 7d'] != ''])}")
    print(f"  Double Trailer (z danymi):  {len(df[df['TE DblTrailer Avg 7d'] != ''])}")
    print(f"\nPlik wyjściowy: {OUTPUT_CSV}")
    print("=" * 80)

if __name__ == '__main__':
    main()
