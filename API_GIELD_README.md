# Integracja z API Giełd - Tryb "Teraz"

## Przegląd

W trybie "teraz" aplikacja pobiera **aktualne oferty na żywo** z API giełd transportowych (TimoCom i Trans.eu) używając **realnych adresów** wpisanych przez użytkownika, zamiast mapowania na ID regionów.

## Architektura

### Przepływ danych

```
Użytkownik wpisuje: "50-340, Wrocław" → "08034, Barcelona"
    ↓
Tryb "TERAZ" (przycisk)
    ↓
Frontend: POST /api/current-offers
    {
        "start_location": "50-340, Wrocław, Poland",
        "end_location": "08034, Barcelona, Spain",
        "distance": 1500
    }
    ↓
Backend: freight_api.py
    ├─ TimocomAPI.search_freight_offers()
    │   └─ POST https://api.timocom.com/freight-exchange/3/freight-offers/search
    │       Headers: Authorization: Basic [credentials]
    │
    └─ TranseuAPI.search_freight_offers()
        └─ POST https://api.trans.eu/api/rest/v1/loads/search
            Headers: Authorization: Bearer [API_KEY]
    ↓
Agregacja wyników z obu giełd
    ↓
Frontend: Wyświetlenie aktualnych ofert
```

## Konfiguracja

### 1. Credentials w pliku `.env`

Skopiuj `.env.example` do `.env` i wypełnij:

```bash
# API TimoCom (dla trybu "teraz")
TIMOCOM_USERNAME=Janta
TIMOCOM_PASSWORD=1tae17kpS5m4NaMYhSvYdw
TIMOCOM_API_URL=https://api.timocom.com

# API Trans.eu (dla trybu "teraz")
TRANSEU_API_KEY=5d7a5d98b726a400012bbb8a6ab03b01b9a9403fbda18b6478d98264
TRANSEU_CLIENT_ID=de92025f-9afc-4d75-8e5e-23b6335ce8b3
TRANSEU_CLIENT_SECRET=zahx6eiVoo5lae9Uyaith6Doiez9Iewe
```

### 2. Instalacja zależności

```bash
pip install -r requirements.txt
```

Dodano: `requests==2.31.0`

### 3. Uruchomienie

```bash
python app.py
```

## Pliki

### Backend

- **`freight_api.py`** - Główny moduł komunikacji z API
  - `TimocomAPI` - Klient API TimoCom
  - `TranseuAPI` - Klient API Trans.eu
  - `get_current_offers()` - Funkcja agregująca wyniki

- **`app.py`** - Endpoint Flask
  - `POST /api/current-offers` - Pobiera aktualne oferty

### Frontend

- **`static/js/main.js`**
  - `handleNowMode()` - Obsługa trybu "teraz"
  - Wywołuje `/api/current-offers` z realnymi adresami

## API TimoCom

### Endpoint
```
POST https://api.timocom.com/freight-exchange/3/freight-offers/search
```

### Autoryzacja
```
Authorization: Basic base64(username:password)
```

### Request Body
```json
{
  "origin": {
    "location": "50-340, Wrocław, Poland"
  },
  "destination": {
    "location": "08034, Barcelona, Spain"
  },
  "paging": {
    "page": 1,
    "limit": 30
  }
}
```

### Response
```json
{
  "payload": [
    {
      "id": "123456",
      "price": 2500,
      "pricePerKm": 1.20,
      "currency": "EUR",
      "vehicleType": "Trailer",
      "loadingDate": "2025-11-15"
    }
  ]
}
```

## API Trans.eu

### Endpoint
```
POST https://api.trans.eu/api/rest/v1/loads/search
```

### Autoryzacja
```
Authorization: Bearer {API_KEY}
```

### Request Body
```json
{
  "loading_place": "50-340, Wrocław, Poland",
  "unloading_place": "08034, Barcelona, Spain",
  "limit": 30
}
```

## Różnice: Tryb "Teraz" vs Tryby Historyczne

| Aspekt | Tryby 7/30/90 dni | Tryb "Teraz" |
|--------|-------------------|--------------|
| **Źródło danych** | Baza PostgreSQL (agregowane) | API giełd (live) |
| **Mapowanie** | Trans.eu ID → TimoCom ID → SQL | Bezpośrednie adresy → API |
| **Dane** | Średnie historyczne | Aktualne oferty |
| **Liczba ofert** | `number_of_offers_total` z bazy | Rzeczywista liczba z API |
| **Opóźnienie** | ~0ms (z bazy) | ~2-5s (wywołania API) |
| **Cache** | Nie (zawsze świeże z bazy) | Możliwy (5 min TTL) |

## Obsługa błędów

### Backend

```python
try:
    offers_data = get_current_offers(start, end, distance)
except Exception as e:
    return jsonify({
        'success': False,
        'error': str(e),
        'data': {'has_data': False, 'message': 'Błąd API'}
    })
```

### Frontend

```javascript
try {
    const response = await fetch('/api/current-offers', ...);
    if (result.success && result.data.has_data) {
        // Wyświetl aktualne oferty
    } else {
        // Fallback - użyj danych historycznych
        updateRatesForSelectedDays(7);
    }
} catch (error) {
    console.error('Błąd API:', error);
    // Fallback
}
```

## Testowanie

### Test backendu (Python)

```bash
python
>>> from freight_api import get_current_offers
>>> result = get_current_offers("50-340, Wrocław, Poland", "08034, Barcelona, Spain", 1500)
>>> print(result)
```

### Test endpointu (curl)

```bash
curl -X POST http://localhost:5000/api/current-offers \
  -H "Content-Type: application/json" \
  -d '{
    "start_location": "50-340, Wrocław, Poland",
    "end_location": "08034, Barcelona, Spain",
    "distance": 1500
  }'
```

### Test frontend

1. Uruchom aplikację: `python app.py`
2. Otwórz: `http://localhost:5000`
3. Wpisz trasę
4. Kliknij przycisk **"teraz"**
5. Sprawdź konsole przeglądarki (F12) i terminal

## Logi

### Backend (terminal)
```
🌐 API Current Offers - tryb TERAZ
   Start: 50-340, Wrocław, Poland
   Cel: 08034, Barcelona, Spain
   Dystans: 1500 km

🔄 TimoCom API: Zapytanie 50-340, Wrocław, Poland -> 08034, Barcelona, Spain
✓ TimoCom: Znaleziono 15 ofert

🔄 Trans.eu API: Zapytanie 50-340, Wrocław, Poland -> 08034, Barcelona, Spain
✓ Trans.eu: Znaleziono 8 ofert

✓ Pobrano łącznie 23 aktualnych ofert
   TimoCom: 15 ofert
   Trans.eu: 8 ofert
   Średnia stawka: 1.12 EUR/km
```

### Frontend (konsola przeglądarki)
```
📊 Tryb "teraz" - pobieranie aktualnych ofert z API...
✓ Pobrano aktualne oferty z API giełd: Object { has_data: true, offers: Array(23), ... }
```

## Rozszerzenia

### Dodanie cache'owania

W `freight_api.py` można dodać cache (np. Redis):

```python
import redis
import json
import hashlib

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_current_offers_cached(start, end, distance):
    cache_key = f"offers:{hashlib.md5(f'{start}:{end}'.encode()).hexdigest()}"
    
    # Sprawdź cache (TTL 5 minut)
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Pobierz z API
    result = get_current_offers(start, end, distance)
    
    # Zapisz do cache
    redis_client.setex(cache_key, 300, json.dumps(result))
    
    return result
```

### Dodanie paginacji

Dla dużej liczby wyników:

```python
def search_freight_offers(self, start, end, limit=30, page=1):
    payload = {
        "paging": {"page": page, "limit": limit}
    }
    # ...
```

## Troubleshooting

### Błąd: "Brak credentials"
- Sprawdź plik `.env`
- Upewnij się że `load_dotenv()` jest wywołane

### Błąd: "HTTP 401 Unauthorized"
- Sprawdź poprawność username/password (TimoCom)
- Sprawdź ważność API key (Trans.eu)

### Brak ofert
- API może nie mieć ofert dla danej trasy
- Sprawdź format adresów (powinny być pełne z krajem)

### Timeout
- Zwiększ timeout w `requests.post(..., timeout=15)`
- Sprawdź połączenie internetowe
