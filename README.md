# Wyceniarka Tras Transportowych

Narzędzie webowe dla spedytorów do wyceny tras transportowych z wizualizacją na mapie, analizą stawek rynkowych i historycznych oraz sugestiami przewoźników.

## Funkcjonalności

- 📍 **Wyszukiwanie tras** - Wprowadzenie lokalizacji początkowej i końcowej
- 🗺️ **Wizualizacja na mapie** - Interaktywna mapa z wyznaczoną trasą
- 💰 **Stawki giełdowe** - Średnie stawki z platform transportowych (Trans.eu, TimoCom, itp.)
- 📊 **Stawki historyczne** - Analiza historycznych zleceń firmy na danym kierunku
- 🛣️ **Opłaty drogowe** - Automatyczne wyliczenie opłat drogowych (e-TOLL, Toll Collect, itp.)
- 🚚 **Sugerowani przewoźnicy** - Lista przewoźników historycznych i z giełd
- 💵 **Podsumowanie kosztów** - Kompleksowe zestawienie wszystkich kosztów

## Struktura projektu

```
wyceniarka/
│
├── app.py                 # Główna aplikacja Flask
├── requirements.txt       # Zależności Python
├── README.md             # Dokumentacja
│
├── templates/
│   └── index.html        # Szablon strony głównej
│
└── static/
    ├── css/
    │   └── style.css     # Style CSS
    └── js/
        └── main.js       # Logika JavaScript
```

## Instalacja i uruchomienie lokalnie

### Wymagania
- Python 3.8+
- pip

### Kroki instalacji

1. **Zainstaluj zależności:**
```bash
pip install -r requirements.txt
```

2. **Uruchom aplikację:**
```bash
python app.py
```

3. **Otwórz przeglądarkę:**
```
http://localhost:5000
```

## Użytkowanie

1. Wprowadź lokalizację początkową (np. "Warszawa")
2. Wprowadź lokalizację końcową (np. "Berlin")
3. Kliknij przycisk "Wyceń"
4. Przeglądaj wyniki:
   - Wizualizację trasy na mapie
   - Stawki z giełd transportowych
   - Historyczne stawki firmy (jeśli dostępne)
   - Opłaty drogowe
   - Sugerowanych przewoźników

### Przykładowe lokalizacje do testowania
- Warszawa, Kraków, Poznań, Wrocław, Gdańsk, Katowice, Łódź, Szczecin
- Berlin, Praga, Wiedeń, Budapeszt

## Dane przykładowe (prototyp)

Aktualnie aplikacja działa z **danymi przykładowymi** (losowymi) do celów testowych:
- ✅ Stawki giełdowe - dane losowe
- ✅ Stawki historyczne - dane losowe
- ✅ Opłaty drogowe - dane szacunkowe
- ✅ Przewoźnicy - dane przykładowe

## Integracja z rzeczywistymi źródłami danych (TODO)

### 1. Dane giełdowe
W przyszłości do podłączenia:
- API Trans.eu
- API TimoCom
- API Teleroute
- API Transporeon

### 2. Dane historyczne firmy
Integracja z Microsoft SQL Server:
- Connection string do bazy firmowej
- Query do pobierania historycznych zleceń
- Filtrowanie po trasach

### 3. Obliczanie opłat drogowych
- Integracja z API systemu e-TOLL (Polska)
- API Toll Collect (Niemcy)
- Inne systemy europejskie

### 4. Obliczanie tras
- Google Maps Directions API
- OpenRouteService API
- Mapbox API

## Deployment na Render

### Przygotowanie

1. Utwórz plik `render.yaml` (opcjonalnie)
2. Upewnij się że `gunicorn` jest w `requirements.txt`

### Konfiguracja na Render.com

1. Połącz repozytorium GitHub z Render
2. Utwórz nowy Web Service
3. Ustaw następujące parametry:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Environment:** Python 3

4. Dodaj zmienne środowiskowe (gdy będą potrzebne):
   - `DATABASE_URL` - connection string do MS SQL
   - `TRANS_EU_API_KEY` - klucz API Trans.eu
   - itd.

## Technologie

- **Backend:** Flask (Python)
- **Frontend:** HTML5, CSS3, JavaScript
- **Mapa:** Leaflet.js + OpenStreetMap
- **UI Framework:** Bootstrap 5
- **Ikony:** Font Awesome 6

## Rozwój aplikacji

### Kolejne kroki:
1. ✅ Prototyp z danymi przykładowymi
2. ⏳ Integracja z API giełd transportowych
3. ⏳ Połączenie z bazą danych firmową (MS SQL Server)
4. ⏳ Rzeczywiste obliczanie opłat drogowych
5. ⏳ Zaawansowane filtry i raportowanie
6. ⏳ Eksport wyników do PDF/Excel
7. ⏳ System autoryzacji użytkowników (opcjonalnie)

## Uwagi

- Aplikacja nie wymaga logowania (zgodnie z wymaganiami)
- Dane są generowane losowo dla celów demonstracyjnych
- Interface jest w języku polskim
- Responsywny design - działa na urządzeniach mobilnych

## Licencja

Projekt wewnętrzny firmy.
