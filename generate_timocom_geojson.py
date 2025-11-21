"""
Skrypt generujący plik GeoJSON z punktami TimoCom
Tworzy prosty punktowy GeoJSON (później można dodać regiony Voronoi)
"""

import csv
import json
from pathlib import Path

def generate_timocom_geojson():
    """Generuje plik GeoJSON z punktami TimoCom"""
    
    # Wczytaj dane z CSV
    csv_path = Path(__file__).parent / 'timo_centers.csv'
    
    features = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Utwórz feature GeoJSON dla każdego punktu
            feature = {
                "type": "Feature",
                "properties": {
                    "id": int(row['id']),
                    "type": row['type'],
                    "city_name": row['city_name'],
                    "latitude": float(row['latitude']),
                    "longitude": float(row['longitude']),
                    "country": row['country'],
                    "postal_code": row['postal_code'],
                    "country_code": row['country']
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row['longitude']), float(row['latitude'])]
                }
            }
            features.append(feature)
    
    print(f"Wygenerowano {len(features)} punktów TimoCom")
    
    # Utwórz GeoJSON FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "name": "timocom_regions",
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
            }
        },
        "features": features
    }
    
    # Zapisz do pliku
    output_path = Path(__file__).parent / 'static' / 'data' / 'timocom_regions.geojson'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)
    
    print(f"Zapisano GeoJSON do: {output_path}")
    print(f"\nPrzykładowe punkty:")
    for feature in features[:5]:
        props = feature['properties']
        print(f"  ID {props['id']}: {props['city_name']} ({props['country']}) - {props['postal_code']}")

if __name__ == '__main__':
    generate_timocom_geojson()
