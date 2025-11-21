"""
Skrypt generujący mapowanie kodów pocztowych na ID regionów TimoCom
Analogicznie jak postal_code_to_region_transeu.json
"""

import csv
import json
from pathlib import Path

def generate_timocom_mapping():
    """Generuje plik JSON mapujący kody pocztowe na ID TimoCom"""
    
    # Wczytaj dane z CSV
    timo_centers = []
    csv_path = Path(__file__).parent / 'timo_centers.csv'
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            timo_centers.append({
                'id': int(row['id']),
                'country': row['country'],
                'postal_code': row['postal_code'],
                'city_name': row['city_name'],
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude'])
            })
    
    print(f"Wczytano {len(timo_centers)} punktów TimoCom")
    
    # Generuj mapowanie kodów pocztowych
    postal_mapping = {}
    
    for center in timo_centers:
        country = center['country']
        postal_code = center['postal_code']
        
        # Generuj klucze mapowania - różne poziomy szczegółowości
        # Np. dla "8500" w PT: PT85, PT850, PT8500
        
        if len(postal_code) >= 2:
            # Podstawowy klucz: kraj + pierwsze 2 cyfry
            key = f"{country}{postal_code[:2]}"
            if key not in postal_mapping:
                postal_mapping[key] = {
                    'region_id': center['id'],
                    'distance_km': 0.0
                }
        
        if len(postal_code) >= 3:
            # Rozszerzony klucz: kraj + pierwsze 3 cyfry
            key = f"{country}{postal_code[:3]}"
            if key not in postal_mapping:
                postal_mapping[key] = {
                    'region_id': center['id'],
                    'distance_km': 0.0
                }
        
        if len(postal_code) >= 4:
            # Pełny klucz: kraj + pierwsze 4 cyfry
            key = f"{country}{postal_code[:4]}"
            if key not in postal_mapping:
                postal_mapping[key] = {
                    'region_id': center['id'],
                    'distance_km': 0.0
                }
        
        # Dodaj też pełny kod pocztowy bez separatorów
        full_code = postal_code.replace('-', '').replace(' ', '')
        if full_code:
            key = f"{country}{full_code}"
            if key not in postal_mapping:
                postal_mapping[key] = {
                    'region_id': center['id'],
                    'distance_km': 0.0
                }
    
    print(f"Wygenerowano {len(postal_mapping)} mapowań kodów pocztowych")
    
    # Zapisz do pliku JSON
    output_path = Path(__file__).parent / 'static' / 'data' / 'postal_code_to_region_timocom.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(postal_mapping, f, indent=2, ensure_ascii=False)
    
    print(f"Zapisano mapowanie do: {output_path}")
    
    # Wyświetl przykłady
    print("\nPrzykładowe mapowania:")
    for i, (key, value) in enumerate(list(postal_mapping.items())[:10]):
        print(f"  {key} -> region_id: {value['region_id']}")

if __name__ == '__main__':
    generate_timocom_mapping()
