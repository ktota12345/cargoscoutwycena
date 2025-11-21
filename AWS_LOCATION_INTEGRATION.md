# Integracja AWS Location Service API Routes

## Opis zmian

Skrypt `batch_route_checker.py` został zmodyfikowany aby obliczać dystanse tras używając **AWS Location Service API Routes** zamiast wzoru Haversine.

## Kluczowe zmiany

### 1. Nowa funkcja: `get_aws_route_distance()`
- Wywołuje AWS Location Service API Routes
- Oblicza rzeczywisty dystans drogowy (nie w linii prostej)
- Używa trybu `TravelMode: "Truck"` odpowiedniego dla transportu ciężarowego
- Zwraca dystans w kilometrach
- Ma wbudowany mechanizm fallback do wzoru Haversine w przypadku błędu API

### 2. Nowa funkcja: `load_postal_coordinates()`
- Ładuje współrzędne z pliku `package/filtered_postal_codes.geojson`
- Zwraca dict z kluczami w formacie `{country_code}{postal_code}` (np. "PL50", "DE10")
- Współrzędne są używane do wywołań AWS API

### 3. Zmodyfikowana funkcja: `process_single_route()`
- Używa `postal_coords` zamiast `region_coords`
- Wywołuje `get_aws_route_distance()` dla obliczenia dystansu
- W przypadku błędu AWS API, używa wzoru Haversine jako fallback
- Dodaje pole `distance_method: 'haversine_fallback'` gdy używa fallback

### 4. Zmodyfikowana funkcja: `process_routes()`
- Przyjmuje `postal_coords` zamiast `region_coords`
- Dla optymalizacji batch queries nadal używa Haversine do szybkiego filtrowania
- Dokładny dystans AWS jest obliczany dla każdej trasy w `process_single_route()`

## Konfiguracja

### 1. Utwórz API Key w AWS Location Service

1. Zaloguj się do [AWS Console](https://console.aws.amazon.com/)
2. Przejdź do: **Amazon Location Service** → **API keys**
   - Link bezpośredni: https://console.aws.amazon.com/location/home#/api-keys
3. Kliknij **Create API key**
4. Skonfiguruj API key:
   - **Name**: np. "CargoScout-Routes"
   - **Allowed operations**: Zaznacz **Routes**
   - **Allowed resources**: Wybierz region i opcje
5. Skopiuj wygenerowany API key

### 2. Dodaj API Key do .env

Otwórz plik `.env` i wklej swój API key:

```bash
AWS_LOCATION_API_KEY="twój-api-key-tutaj"
AWS_REGION="eu-central-1"
```

**Ważne**: Region musi być zgodny z regionem, w którym utworzyłeś API key.

### 3. Zainstaluj wymagane biblioteki
```bash
pip install requests pandas
```

## Struktura danych wejściowych

### Plik: `package/filtered_postal_codes.geojson`
Format GeoJSON FeatureCollection z właściwościami:
- `country_code`: Kod kraju (np. "PL", "DE")
- `postal_code`: Pierwsze 2 cyfry kodu pocztowego (np. "50", "10")
- `latitude`: Szerokość geograficzna
- `longitude`: Długość geograficzna

Przykład:
```json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [16.9252, 52.4064]
  },
  "properties": {
    "country_code": "PL",
    "postal_code": "60",
    "latitude": 52.4064,
    "longitude": 16.9252,
    "accuracy": 1
  }
}
```

## AWS Location Service API

### Endpoint
```
POST https://routes.geo.{region}.amazonaws.com/v2/routes?key={API_KEY}
```

### Sposób wywołania
Skrypt używa **HTTP POST request** z API key przekazywanym w URL:

```python
import requests

url = f"https://routes.geo.{AWS_REGION}.amazonaws.com/v2/routes?key={AWS_LOCATION_API_KEY}"

headers = {
    "Content-Type": "application/json"
}

payload = {
    "Origin": [longitude, latitude],
    "Destination": [longitude, latitude],
    "TravelMode": "Truck",
    "OptimizeRoutingFor": "FastestRoute"
}

response = requests.post(url, json=payload, headers=headers, timeout=10)
```

### Parametry
- `Origin`: [longitude, latitude] - współrzędne punktu startowego
- `Destination`: [longitude, latitude] - współrzędne punktu docelowego
- `TravelMode`: "Truck" - tryb transportu (uwzględnia ograniczenia dla ciężarówek)
- `OptimizeRoutingFor`: "FastestRoute" - optymalizacja dla najszybszej trasy

### Response
API zwraca dane w formacie JSON z trasą w `Routes[0]`. Dystans jest w metrach i składa się z sumy dystansów ze wszystkich `TravelSteps` w każdym `Leg`:

```json
{
  "Routes": [{
    "Legs": [{
      "VehicleLegDetails": {
        "TravelSteps": [
          {"Distance": 1288},
          {"Distance": 262},
          ...
        ]
      }
    }]
  }]
}
```

Dystans jest konwertowany z metrów na kilometry.

## Zalety nowego rozwiązania

1. **Rzeczywiste dystanse drogowe** - zamiast dystansu w linii prostej
2. **Tryb ciężarowy** - uwzględnia ograniczenia dla ciężarówek
3. **Dokładniejsze wyceny** - bazują na rzeczywistych trasach
4. **Fallback mechanism** - w razie błędu API używany jest Haversine
5. **Współrzędne rzeczywistych adresów** - nie punktów bazowych regionów

## Limity i uwagi

- AWS API ma limity wywołań - monitoruj użycie
- Timeout ustawiony na 10 sekund dla każdego wywołania
- W przypadku problemów z API, skrypt automatycznie używa fallback do Haversine
- Dla batch queries (filtrowanie tras przed pobraniem danych) używany jest Haversine dla optymalizacji
- Dokładne dystanse AWS są obliczane dla każdej trasy podczas przetwarzania

## Testowanie

Uruchom skrypt w trybie testowym (pierwsze 10 tras):
```python
# W pliku batch_route_checker.py zmień:
TEST_MODE = True
```

Następnie uruchom:
```bash
python batch_route_checker.py
```

Sprawdź w wyniku czy dystanse są obliczane przez AWS API i czy mechanizm fallback działa poprawnie w przypadku błędów.
