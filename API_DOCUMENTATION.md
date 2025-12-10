# API Wyceny Tras Transportowych - Dokumentacja dla Developera

## 🌐 Podstawowe Informacje

**Base URL:** `https://api.twojadomena.com` (lub localhost:5000 dla development)

**Wersja API:** 2.3.0

**Format danych:** JSON

**Autentykacja:** API Key w nagłówku

---

## 🔐 Autentykacja

Każde żądanie musi zawierać nagłówek z kluczem API:

```http
X-API-Key: twoj_klucz_api
```

**Przykład (Python):**
```python
headers = {
    'X-API-Key': '0aa1a2a087a201d6ab4d4f25979779f3',
    'Content-Type': 'application/json'
}
```

---

## 📍 Endpoint: `/api/route-pricing`

**Metoda:** `POST`

**Rate Limit:** 5 requestów na minutę

**Opis:** Zwraca średnie stawki transportowe EUR/km dla danej trasy z trzech źródeł:
- **TimoCom** (giełda, ostatnie 30 dni)
- **Trans.eu** (giełda, ostatnie 30 dni)  
- **Dane historyczne firmowe** (ostatnie 6 miesięcy z podziałem FTL/LTL)

---

## 📥 Request Format

### Body (JSON):

```json
{
  "start_postal_code": "PL20",
  "end_postal_code": "DE49",
  "dystans": 850
}
```

### Parametry:

| Parametr | Typ | Wymagany | Opis | Przykład |
|----------|-----|----------|------|----------|
| `start_postal_code` | string | ✅ TAK | Kod pocztowy startu (ISO kraj + cyfry) | `"PL20"`, `"DE49"` |
| `end_postal_code` | string | ✅ TAK | Kod pocztowy celu (ISO kraj + cyfry) | `"FR75"`, `"IT20"` |
| `dystans` | number | ✅ TAK | Dystans trasy w kilometrach | `850` |

**Format kodu pocztowego:** 
- 2 litery (kod kraju ISO)
- 1-5 cyfr (kod regionu)
- Pattern: `^[A-Z]{2}\d{1,5}$`

---

## 📤 Response Format

### Sukces (200):

```json
{
  "success": true,
  "data": {
    "start_postal_code": "PL20",
    "end_postal_code": "DE49",
    "start_region_id": 135,
    "end_region_id": 98,
    "pricing": {
      "timocom": {
        "30d": {
          "avg_price_per_km": {
            "solo": 0.92,
            "trailer": 0.85,
            "mega_trailer": 0.88
          },
          "median_price_per_km": {
            "solo": 0.89,
            "trailer": 0.82,
            "mega_trailer": 0.86
          },
          "total_offers": 1245,
          "days_with_data": 28
        }
      },
      "transeu": {
        "30d": {
          "avg_price_per_km": {
            "lorry": 0.87
          },
          "median_price_per_km": {
            "lorry": 0.84
          },
          "total_offers": 9240,
          "days_with_data": 28
        }
      },
      "historical": {
        "180d": {
          "FTL": {
            "avg_price_per_km": {
              "client": 0.95,
              "carrier": 0.85
            },
            "median_price_per_km": {
              "client": 0.92,
              "carrier": 0.83
            },
            "avg_amounts": {
              "client": 850.50,
              "carrier": 750.00
            },
            "avg_distance": 900.5,
            "total_orders": 25,
            "days_with_data": 28,
            "top_carriers": [
              {
                "carrier_id": 123,
                "carrier_name": "TRANS-POL SP. Z O.O.",
                "order_count": 15,
                "avg_client_price_per_km": 0.98,
                "avg_carrier_price_per_km": 0.88,
                "avg_client_amount": 880.00,
                "avg_carrier_amount": 790.00
              }
            ]
          },
          "LTL": {
            "avg_price_per_km": {
              "client": 1.15,
              "carrier": 1.05
            },
            "median_price_per_km": {
              "client": 1.12,
              "carrier": 1.03
            },
            "avg_amounts": {
              "client": 450.00,
              "carrier": 380.00
            },
            "avg_distance": 400.0,
            "total_orders": 20,
            "days_with_data": 25,
            "top_carriers": [
              {
                "carrier_id": 456,
                "carrier_name": "EXPRESS-TRANS",
                "order_count": 10,
                "avg_client_price_per_km": 1.18,
                "avg_carrier_price_per_km": 1.08,
                "avg_client_amount": 480.00,
                "avg_carrier_amount": 410.00
              }
            ]
          }
        }
      }
    },
    "currency": "EUR",
    "unit": "EUR/km",
    "data_sources": {
      "timocom": true,
      "transeu": true,
      "historical": true
    }
  }
}
```

---

## 📊 Struktura Odpowiedzi - Szczegółowy Opis

### Sekcja `pricing.timocom.30d`

**Źródło:** Giełda TimoCom (ostatnie 30 dni)

| Pole | Typ | Opis |
|------|-----|------|
| `avg_price_per_km.solo` | number/null | Średnia stawka solo (samochód bez naczepy) |
| `avg_price_per_km.trailer` | number/null | Średnia stawka z naczepą standardową |
| `avg_price_per_km.mega_trailer` | number/null | Średnia stawka z mega-naczepą |
| `median_price_per_km.*` | number/null | Mediany stawek (analogicznie jak avg) |
| `total_offers` | integer | Łączna liczba ofert w okresie |
| `days_with_data` | integer | Liczba dni z danymi w okresie |

**Uwaga:** Jeśli nie ma danych dla danego typu pojazdu, wartość będzie `null`.

---

### Sekcja `pricing.transeu.30d`

**Źródło:** Giełda Trans.eu (ostatnie 30 dni)

| Pole | Typ | Opis |
|------|-----|------|
| `avg_price_per_km.lorry` | number/null | Średnia stawka dla ciężarówki |
| `median_price_per_km.lorry` | number/null | Mediana stawki |
| `total_offers` | integer | Łączna liczba ofert |
| `days_with_data` | integer | Liczba dni z danymi |

---

### Sekcja `pricing.historical.180d`

**Źródło:** Firmowe zlecenia historyczne (ostatnie 6 miesięcy)

**Podział:** FTL i LTL (każdy typ ma osobne statystyki)

#### FTL (Full Truck Load - Pełne ładunki)

| Pole | Typ | Opis |
|------|-----|------|
| `avg_price_per_km.client` | number/null | Średnia cena sprzedaży (kwota dla klienta) |
| `avg_price_per_km.carrier` | number/null | Średni koszt realizacji (kwota dla przewoźnika) |
| `median_price_per_km.client` | number/null | Mediana ceny sprzedaży |
| `median_price_per_km.carrier` | number/null | Mediana kosztu realizacji |
| `avg_amounts.client` | number/null | Średnia kwota sprzedaży za zlecenie (całkowita) |
| `avg_amounts.carrier` | number/null | Średni koszt realizacji za zlecenie (całkowity) |
| `avg_distance` | number/null | Średni dystans zleceń w km |
| `total_orders` | integer | Liczba zleceń |
| `days_with_data` | integer | Liczba dni z danymi |
| `top_carriers` | array | Top 4 przewoźników (patrz poniżej) |

#### LTL (Less Than Truckload - Ładunki częściowe)

Struktura identyczna jak FTL, ale dane dla ładunków częściowych.

**Uwaga:** Stawki LTL zazwyczaj wyższe za km, ale niższe kwoty całkowite.

---

### Struktura `top_carriers`

Każdy przewoźnik w tablicy `top_carriers` ma strukturę:

```json
{
  "carrier_id": 123,
  "carrier_name": "TRANS-POL SP. Z O.O.",
  "order_count": 15,
  "avg_client_price_per_km": 0.98,
  "avg_carrier_price_per_km": 0.88,
  "avg_client_amount": 880.00,
  "avg_carrier_amount": 790.00
}
```

| Pole | Typ | Opis |
|------|-----|------|
| `carrier_id` | integer | ID przewoźnika w systemie |
| `carrier_name` | string | Nazwa firmy przewozowej |
| `order_count` | integer | Liczba zleceń wykonanych na tej trasie |
| `avg_client_price_per_km` | number/null | Średnia cena sprzedaży za km dla tego przewoźnika |
| `avg_carrier_price_per_km` | number/null | Średni koszt realizacji za km |
| `avg_client_amount` | number/null | Średnia kwota sprzedaży za zlecenie |
| `avg_carrier_amount` | number/null | Średni koszt realizacji za zlecenie |

**Maksymalna liczba:** 4 przewoźników dla FTL + 4 dla LTL (łącznie 8)

---

## ⚠️ Błędy

### 400 Bad Request

```json
{
  "success": false,
  "error": "Nieprawidłowe dane wejściowe"
}
```

**Przyczyny:**
- Brak wymaganych parametrów
- Nieprawidłowy format kodu pocztowego
- Dystans ≤ 0

### 401 Unauthorized

```json
{
  "success": false,
  "error": "Brak lub nieprawidłowy klucz API"
}
```

**Przyczyna:** Brak nagłówka `X-API-Key` lub nieprawidłowy klucz.

### 404 Not Found

```json
{
  "success": false,
  "error": "Brak danych dla trasy PL20 -> DE49",
  "message": "Nie znaleziono danych cenowych w bazie dla tej trasy"
}
```

**Przyczyna:** Brak danych w żadnym ze źródeł (giełdy + historia) dla tej trasy.

### 429 Too Many Requests

```json
{
  "success": false,
  "error": "Przekroczono limit żądań"
}
```

**Przyczyna:** Przekroczono limit 5 requestów/minutę.

### 500 Internal Server Error

```json
{
  "success": false,
  "error": "Błąd serwera"
}
```

**Przyczyna:** Wewnętrzny błąd serwera (problem z bazą danych itp.)

---

## 🎯 Najlepsze Praktyki dla GUI

### 1. **Obsługa Brakujących Danych**

Nie wszystkie źródła zawsze mają dane. Sprawdzaj sekcję `data_sources`:

```javascript
if (response.data.data_sources.timocom) {
  // Pokaż dane z TimoCom
}
if (response.data.data_sources.historical) {
  // Pokaż dane historyczne
}
```

### 2. **Null Values**

Poszczególne ceny mogą być `null`:

```javascript
const price = response.data.pricing.timocom['30d'].avg_price_per_km.solo;
if (price !== null) {
  displayPrice(price);
} else {
  displayNoData();
}
```

### 3. **Wyświetlanie Danych Historycznych**

Zawsze sprawdzaj czy FTL/LTL istnieją:

```javascript
const historical = response.data.pricing.historical['180d'];
if (historical.FTL) {
  displayFTL(historical.FTL);
}
if (historical.LTL) {
  displayLTL(historical.LTL);
}
```

### 4. **Różnica Client vs Carrier**

W danych historycznych:
- **`client`** = cena sprzedaży (przychód firmy)
- **`carrier`** = koszt realizacji (wydatek firmy)
- **Marża** = `client - carrier`

```javascript
const margin = historical.FTL.avg_price_per_km.client - 
               historical.FTL.avg_price_per_km.carrier;
const marginPercent = (margin / historical.FTL.avg_price_per_km.client) * 100;
```

### 5. **FTL vs LTL**

- **FTL** - Pełny ładunek (Full Truck Load)
  - Niższe stawki za km
  - Wyższe kwoty całkowite
  - Dłuższe dystanse
  
- **LTL** - Ładunek częściowy (Less Than Truckload)
  - Wyższe stawki za km
  - Niższe kwoty całkowite
  - Krótsze dystanse

---

## 📝 Przykładowy Kod Integracji

### Python:

```python
import requests

API_URL = "https://api.twojadomena.com/api/route-pricing"
API_KEY = "0aa1a2a087a201d6ab4d4f25979779f3"

def get_route_pricing(start_code, end_code, distance):
    headers = {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'start_postal_code': start_code,
        'end_postal_code': end_code,
        'dystans': distance
    }
    
    response = requests.post(API_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

# Użycie
result = get_route_pricing("PL20", "DE49", 850)
if result and result['success']:
    pricing = result['data']['pricing']
    
    # TimoCom
    if 'timocom' in pricing:
        timocom = pricing['timocom']['30d']
        print(f"TimoCom trailer: {timocom['avg_price_per_km']['trailer']} EUR/km")
    
    # Dane historyczne FTL
    if 'historical' in pricing:
        ftl = pricing['historical']['180d'].get('FTL')
        if ftl:
            print(f"Historical FTL client: {ftl['avg_price_per_km']['client']} EUR/km")
            print(f"Top carriers: {len(ftl['top_carriers'])}")
```

### JavaScript (React/Vue):

```javascript
const API_URL = 'https://api.twojadomena.com/api/route-pricing';
const API_KEY = '0aa1a2a087a201d6ab4d4f25979779f3';

async function getRoutePricing(startCode, endCode, distance) {
  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'X-API-Key': API_KEY,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        start_postal_code: startCode,
        end_postal_code: endCode,
        dystans: distance
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
    
  } catch (error) {
    console.error('Error fetching pricing:', error);
    return null;
  }
}

// Użycie
getRoutePricing('PL20', 'DE49', 850).then(result => {
  if (result?.success) {
    const pricing = result.data.pricing;
    
    // Wyświetl dane TimoCom
    if (pricing.timocom) {
      console.log('TimoCom data available');
    }
    
    // Wyświetl dane historyczne
    if (pricing.historical?.['180d']?.FTL) {
      const ftl = pricing.historical['180d'].FTL;
      console.log(`FTL avg price: ${ftl.avg_price_per_km.client} EUR/km`);
      console.log(`Top carriers: ${ftl.top_carriers.length}`);
    }
  }
});
```

---

## 🔄 Okresy Danych

| Źródło | Okres | Opis |
|--------|-------|------|
| TimoCom | 30 dni | Giełda transportowa |
| Trans.eu | 30 dni | Giełda transportowa |
| Historical | 180 dni (6 miesięcy) | Firmowe zlecenia z podziałem FTL/LTL |

---

## 🚫 Wykluczenia w Danych Historycznych

Dane historyczne **NIE zawierają**:
- Zleceń klienta Motiva (clientId = 1)
- Tras krótszych niż 500 km (≤ 499 km)
- Zleceń niezakończonych (status != 'Z')
- Outlierów (cena > 5 EUR/km)

---

## 📧 Kontakt / Support

W razie pytań lub problemów z API, skontaktuj się z zespołem technicznym.

---

## 📜 Changelog

**v2.3.0** (2025-12-10)
- Dodano podział danych historycznych na FTL i LTL
- Dodano top 4 przewoźników dla każdego typu ładunku
- Zmiana okresu danych historycznych z 30 na 180 dni
- Dodano filtry: wykluczenie Motiva, min 500 km

**v2.2.0**
- Dodano dane historyczne firmowe

**v2.1.0**
- Integracja Trans.eu

**v2.0.0**
- Pierwsza wersja z TimoCom
