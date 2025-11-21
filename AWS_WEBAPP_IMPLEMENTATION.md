# AWS Location Service - Implementacja w aplikacji webowej

## ✅ Zaimplementowano

Aplikacja webowa teraz używa **AWS Location Service API Routes** do obliczania rzeczywistych dystansów drogowych zamiast prostego wzoru Haversine.

## 🔧 Zmiany w kodzie

### 1. Backend (Flask) - `app.py`

#### Dodane importy i konfiguracja:
```python
import requests
from typing import Optional

# Konfiguracja AWS Location Service
AWS_LOCATION_API_KEY = os.getenv("AWS_LOCATION_API_KEY")
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
```

#### Nowa funkcja: `get_aws_route_distance()`
- Wywołuje AWS Location Service Routes API
- Zwraca rzeczywisty dystans drogowy w km
- Uwzględnia tryb `Truck` (ograniczenia dla ciężarówek)
- Timeout: 15 sekund
- Fallback do `None` jeśli błąd

#### Nowy endpoint: `/api/calculate-distance` (POST)
**Parametry wejściowe:**
```json
{
  "start_coords": [lat, lng],
  "end_coords": [lat, lng],
  "fallback_distance": 1234  // Haversine z frontendu
}
```

**Odpowiedź:**
```json
{
  "success": true,
  "distance": 1456.78,
  "method": "aws",  // lub "haversine_fallback"
  "fallback_distance": 1234
}
```

#### Zaktualizowany endpoint: `/api/calculate`
Dodane pola w odpowiedzi:
- `distance_method`: `"aws"`, `"haversine"` lub `"haversine_fallback"`
- `haversine_distance`: Oryginalny dystans Haversine (dla porównania)

### 2. Frontend (JavaScript) - `main.js`

#### Nowa logika obliczania dystansu:

1. **Krok 1**: Oblicz dystans Haversine (fallback)
   ```javascript
   const haversineDistance = turf.distance(startCoords, endCoords);
   ```

2. **Krok 2**: Wywołaj AWS API
   ```javascript
   const distanceResponse = await fetch('/api/calculate-distance', {
       method: 'POST',
       body: JSON.stringify({
           start_coords: [lat, lng],
           end_coords: [lat, lng],
           fallback_distance: haversineDistance
       })
   });
   ```

3. **Krok 3**: Użyj AWS dystansu jeśli dostępny, w przeciwnym razie Haversine
   ```javascript
   if (distanceData.method === 'aws') {
       distance = distanceData.distance;  // AWS API
   } else {
       distance = haversineDistance;      // Fallback
   }
   ```

#### Dodane do zapytania `/api/calculate`:
```javascript
{
    calculated_distance: Math.round(distance),
    distance_method: distanceMethod,        // 'aws' | 'haversine' | 'haversine_fallback'
    haversine_distance: Math.round(haversineDistance)
}
```

### 3. Interfejs użytkownika - `index.html`

#### Dodany badge obok dystansu:
```html
<strong>Dystans:</strong> 
<span id="infoDistance"></span> km 
<span id="distanceMethodBadge" class="badge"></span>
```

#### Funkcja `displayRouteInfo()` aktualizowana o badge:
- 🟢 **AWS API** (zielony) - rzeczywisty dystans z AWS
- 🟡 **Haversine (fallback)** (żółty) - AWS niedostępny
- ⚪ **Haversine** (szary) - stara metoda

## 🎯 Jak to działa

### Przepływ danych:

```
1. Użytkownik wpisuje trasę (np. PL50 → DE10)
   ↓
2. Frontend oblicza Haversine (dystans w linii prostej)
   ↓
3. Frontend wywołuje /api/calculate-distance z współrzędnymi
   ↓
4. Backend wywołuje AWS Location Service API Routes
   ↓
5. AWS zwraca rzeczywisty dystans drogowy (TravelMode: Truck)
   ↓
6. Frontend używa AWS dystansu do obliczeń
   ↓
7. Badge pokazuje metodę ("AWS API" lub "Haversine fallback")
```

### Fallback mechanism:

```
AWS API dostępny?
├─ TAK  → Użyj AWS dystansu (dokładny, uwzględnia drogi)
└─ NIE  → Użyj Haversine (w linii prostej)
```

## 📊 Różnice w dystansach

Na podstawie analizy 1429 tras:

| Typ trasy | Średnia różnica | Przykłady |
|-----------|----------------|-----------|
| **Krótkie (<300 km)** | AWS +38% dłuższy | Trasy wewnętrzne DE/FR |
| **Średnie (300-1000 km)** | AWS +21-23% dłuższy | Większość tras międzynarodowych |
| **Długie (>1000 km)** | AWS +25% dłuższy | Trasy dalekie |
| **Przez promy** | AWS +100-200% dłuższy | GB, Skandynawia |
| **Przez góry** | AWS +50-100% dłuższy | Alpy, Pireneje |

### Przykłady różnic:

- **NL89 → CZ50**: Haversine 996 km → AWS **956 km** (-4%)
- **FR29 → ES36**: Haversine 574 km → AWS **1538 km** (+168%) 🚢 Prom
- **DE50 → DE56**: Haversine 398 km → AWS **109 km** (-73%) ⚠️ Błąd mapowania

## 🔑 Konfiguracja

### Wymagane zmienne w `.env`:

```bash
AWS_LOCATION_API_KEY="v1.public.ey..."
AWS_REGION="eu-central-1"
```

### Jak uzyskać API key:

1. AWS Console → **Amazon Location Service**
2. **API keys** → **Create API key**
3. Nazwa: "CargoScout-Routes"
4. **Allowed operations**: ☑️ **Routes**
5. Region: **eu-central-1** (lub inny)
6. Skopiuj API key i wklej do `.env`

Szczegółowe instrukcje: `INSTRUKCJA_AWS_API_KEY.md`

## 💡 Zalety nowego rozwiązania

1. ✅ **Rzeczywiste dystanse drogowe** - nie w linii prostej
2. ✅ **Tryb ciężarowy** - uwzględnia ograniczenia dla TIR-ów
3. ✅ **Dokładniejsze wyceny** - bazują na faktycznych trasach
4. ✅ **Fallback mechanism** - działa nawet jeśli AWS niedostępny
5. ✅ **Przejrzystość** - badge pokazuje użytą metodę
6. ✅ **Porównanie** - zachowuje Haversine do analizy

## 🧪 Testowanie

### Test lokalny:

1. Upewnij się, że AWS API key jest w `.env`
2. Uruchom aplikację: `python app.py`
3. Otwórz: http://localhost:5000
4. Wpisz trasę (np. `PL50` → `DE10`)
5. Sprawdź badge obok dystansu:
   - 🟢 **AWS API** = sukces
   - 🟡 **Haversine (fallback)** = AWS niedostępny

### Konsola przeglądarki:

```
📏 Odległość Haversine: 1234 km
🌐 Wywołuję AWS Location Service API...
✅ Dystans AWS (rzeczywisty drogowy): 1456 km
```

### Konsola serwera:

```
📏 Obliczanie dystansu AWS:
   Start: [52.4064, 16.9252]
   Cel: [50.0647, 19.9450]
[AWS] ✓ Dystans AWS: 456.78 km
```

## 📈 Metryki AWS

### Limity Free Tier:
- **300,000 zapytań/miesiąc** GRATIS
- Potem: ~$0.50 za 1000 zapytań

### Optymalizacja:
- Timeout: 15s (szybka odpowiedź lub fallback)
- Cache możliwy w przyszłości (brak w obecnej wersji)
- Fallback zapobiega błędom jeśli AWS niedostępny

## 🔄 Przyszłe ulepszenia

### Możliwe rozszerzenia:

1. **Cache dystansów** (Redis/DB)
   - Zapisuj obliczone dystanse AWS
   - Zmniejsz liczbę zapytań do API

2. **Batch processing**
   - Oblicz dystanse dla wielu tras naraz
   - Efektywniejsze wykorzystanie API

3. **Porównanie z historią**
   - Pokaż różnicę AWS vs Haversine dla danej trasy
   - Statystyki dokładności

4. **Wybór użytkownika**
   - Pozwól użytkownikowi wybrać metodę
   - Toggle AWS / Haversine w interfejsie

## 📝 Changelog

### v1.0 - Integracja AWS Location Service
- ✅ Endpoint `/api/calculate-distance`
- ✅ Funkcja `get_aws_route_distance()`
- ✅ Frontend: wywołanie AWS API
- ✅ Badge z metodą obliczania
- ✅ Fallback mechanism
- ✅ Dokumentacja

## 🐛 Znane problemy

1. **Timeout 15s** może być za krótki dla bardzo długich tras
   - Rozwiązanie: zwiększyć timeout lub async processing

2. **Brak cache** - każde wyszukiwanie = zapytanie AWS
   - Rozwiązanie: dodać Redis lub DB cache

3. **Free tier limit** - 300k/miesiąc
   - Rozwiązanie: monitorować użycie, dodać cache

## 📚 Powiązane pliki

- `app.py` - Backend (Flask)
- `static/js/main.js` - Frontend (JavaScript)
- `templates/index.html` - Interfejs
- `AWS_LOCATION_INTEGRATION.md` - Integracja batch script
- `INSTRUKCJA_AWS_API_KEY.md` - Jak uzyskać API key

## ✨ Gotowe!

Aplikacja webowa jest w pełni zintegrowana z AWS Location Service API Routes. Dystanse są teraz obliczane na podstawie rzeczywistych dróg z uwzględnieniem ograniczeń dla ciężarówek.
