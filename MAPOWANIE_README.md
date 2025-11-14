# System Mapowania Kodów Pocztowych na Regiony Giełd

## Przegląd

Aplikacja używa dwóch systemów regionów:
- **Trans.eu** - 251 regionów (plik źródłowy: `voronoi_regions.geojson`)
- **TimoCom** - 97 punktów (plik źródłowy: `timo_centers.csv`)

## Struktura Plików

### Pliki Danych

```
static/data/
├── voronoi_regions.geojson                    # Regiony Trans.eu (251 regionów)
├── timocom_regions.geojson                    # Punkty TimoCom (97 punktów)
├── postal_code_to_region_transeu.json         # Mapowanie kodów pocztowych -> Trans.eu ID
├── postal_code_to_region_timocom.json         # Mapowanie kodów pocztowych -> TimoCom ID
└── transeu_to_timocom_mapping.json            # Mapowanie Trans.eu ID -> TimoCom ID
```

### Skrypty Generujące

```
generate_timocom_mapping.py                    # Generuje postal_code_to_region_timocom.json
generate_timocom_geojson.py                    # Generuje timocom_regions.geojson
generate_transeu_timocom_mapping.py            # Generuje transeu_to_timocom_mapping.json
```

## Przepływ Danych

### 1. Frontend (JavaScript)

```
Kod pocztowy (np. PL50-123)
    ↓
normalizePostalCode() → PL50
    ↓
postal_code_to_region_transeu.json
    ↓
Trans.eu Region ID (np. 135)
    ↓
Wysłanie do API: start_region_id=135
```

### 2. Backend (Python)

```
Trans.eu ID (135)
    ↓
map_transeu_to_timocom_id()
    ↓
transeu_to_timocom_mapping.json
    ↓
TimoCom ID (np. 40)
    ↓
Zapytanie do bazy: SELECT ... WHERE starting_id = 40
```

## Mapowanie Trans.eu → TimoCom

Mapowanie opiera się na:
- **Odległości geograficznej** między punktami
- **Priorytecie dla tego samego kraju** (odległość × 0.5)

Przykład:
```json
{
  "135": {
    "timocom_id": 40,
    "distance_km": 15.5,
    "trans_country": "PL",
    "trans_city": "Wrocław"
  }
}
```

## Statystyki Mapowania

- **Regiony Trans.eu**: 251
- **Punkty TimoCom**: 97
- **Średnia odległość mapowania**: ~57 km
- **Maksymalna odległość**: ~186 km

## Regeneracja Plików

### Krok 1: Mapowanie kodów pocztowych TimoCom
```bash
python generate_timocom_mapping.py
```
Generuje: `static/data/postal_code_to_region_timocom.json`

### Krok 2: GeoJSON punktów TimoCom
```bash
python generate_timocom_geojson.py
```
Generuje: `static/data/timocom_regions.geojson`

### Krok 3: Mapowanie Trans.eu → TimoCom
```bash
python generate_transeu_timocom_mapping.py
```
Generuje: `static/data/transeu_to_timocom_mapping.json`

## Użycie w Aplikacji

### Backend - Funkcje Mapowania

```python
# Mapowanie Trans.eu ID na TimoCom ID
timocom_id = map_transeu_to_timocom_id(transeu_id)

# Pobieranie danych z TimoCom
timocom_data = get_timocom_data(start_region_id, end_region_id, distance, days)

# Agregacja danych z różnych giełd
all_data = get_aggregated_exchange_data(start_region_id, end_region_id, distance, days)
```

### Frontend - PostalCodeSearch

```javascript
// Inicjalizacja z mapowaniem Trans.eu
postalSearch.initialize(
    '/static/data/voronoi_regions.geojson',
    '/static/data/postal_code_to_region_transeu.json'
);

// Wyszukiwanie regionu po kodzie pocztowym
const region = postalSearch.findRegionByPostalCode('PL50-340');
// region.id = Trans.eu ID
```

## Logowanie

Aplikacja loguje proces mapowania w konsoli:

```
✓ Załadowano mapowanie Trans.eu -> TimoCom (251 regionów)
📊 Pobieranie danych z bazy dla regionów: 135 -> 40
🔄 Mapowanie: Trans.eu [135 -> 40] → TimoCom [78 -> 79]
✓ Pobrano dane TimoCom z bazy: 15 rekordów, średnia stawka: 0.52 EUR/km
```

## Rozszerzenia

### Dodanie nowej giełdy

1. Przygotuj plik CSV z punktami
2. Stwórz skrypt generujący mapowanie
3. Dodaj funkcję `get_[gielda]_data()` w `app.py`
4. Dodaj do agregacji w `get_aggregated_exchange_data()`

### Aktualizacja punktów TimoCom

1. Zaktualizuj plik `timo_centers.csv`
2. Uruchom wszystkie 3 skrypty generujące
3. Zrestartuj aplikację
