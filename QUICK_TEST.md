# 🚀 Szybki Test - System Wyszukiwania Kodów Pocztowych

## 1. Uruchom aplikację

```bash
cd c:\Users\konra\Documents\wyceniarka
python app.py
```

Poczekaj na komunikat:
```
* Running on http://0.0.0.0:5000
* Running on http://127.0.0.1:5000
```

---

## 2. Otwórz w przeglądarce

```
http://localhost:5000
```

---

## 3. Testuj funkcjonalność

### ✅ Test 1: Trasa krajowa (Polska)
1. W polu "Lokalizacja początkowa" wpisz: **PL50**
2. Pojawi się sugestia: **PL-50** (Wrocław)
3. Kliknij aby wybrać
4. W polu "Lokalizacja końcowa" wpisz: **PL00**
5. Pojawi się sugestia: **PL-00** (Warszawa)
6. Kliknij "Wyceń"

**Oczekiwany rezultat:**
- Mapa pokazuje dwa regiony (zielony i czarny)
- Przerywana linia łączy oba regiony
- Odległość: ~300-350 km

---

### ✅ Test 2: Trasa międzynarodowa
1. Lokalizacja początkowa: **PL30** (Kraków)
2. Lokalizacja końcowa: **DE10** (Berlin)
3. Kliknij "Wyceń"

**Oczekiwany rezultat:**
- Mapa pokazuje trasę Polska → Niemcy
- Odległość: ~500-600 km

---

### ✅ Test 3: Autocomplete z wyszukiwaniem
1. W polu wpisz tylko: **PL**
2. Pojawi się lista wszystkich regionów Polski
3. Użyj strzałek ↑ ↓ do nawigacji
4. Naciśnij **Enter** aby wybrać

---

### ✅ Test 4: Różne kraje
Przetestuj różne kombinacje:

| Start | Koniec | Kraj Start → Kraj Koniec |
|-------|--------|--------------------------|
| PL50 | DE10 | Polska → Niemcy |
| FR75 | ES28 | Francja → Hiszpania |
| IT00 | AT10 | Włochy → Austria |
| NL10 | BE10 | Holandia → Belgia |
| CZ10 | SK80 | Czechy → Słowacja |

---

## 4. Sprawdź konsolę przeglądarki (F12)

Po załadowaniu strony powinieneś zobaczyć:

```
Inicjalizacja PostalCodeSearch...
Ładowanie regionów z /static/data/voronoi_regions.geojson...
✓ Załadowano 250 regionów
Ładowanie mapowania z /static/data/postal_code_to_region_transeu.json...
✓ Załadowano mapowanie 9000 kodów pocztowych
✓ PostalCodeSearch zainicjalizowany pomyślnie
✓ Załadowano 250 regionów w 30 krajach
```

---

## 5. Funkcje do przetestowania

### Autocomplete:
- ✅ Wpisz kod i czekaj na sugestie
- ✅ Kliknij aby wybrać
- ✅ Użyj klawiatury (strzałki + Enter)

### Wizualizacja:
- ✅ Sprawdź czy regiony są widoczne na mapie
- ✅ Kliknij w regiony aby zobaczyć popup
- ✅ Sprawdź czy linia łączy oba regiony

### Obliczanie:
- ✅ Sprawdź czy odległość ma sens
- ✅ Sprawdź czy stawki są wyliczone
- ✅ Sprawdź opłaty drogowe

---

## 🐛 Rozwiązywanie problemów

### Problem: Brak sugestii autocomplete
**Rozwiązanie:**
1. Otwórz konsolę przeglądarki (F12)
2. Sprawdź czy są błędy
3. Sprawdź czy pliki się załadowały:
   - `voronoi_regions.geojson`
   - `postal_code_to_region_transeu.json`

### Problem: "Nie można znaleźć regionów"
**Rozwiązanie:**
- Upewnij się że używasz formatu: **2 litery + cyfry** (np. PL50, nie "Wrocław")
- Sprawdź wielkość liter (powinno działać bez względu na wielkość)

### Problem: Mapa nie pokazuje regionów
**Rozwiązanie:**
1. Sprawdź czy Turf.js się załadował
2. Sprawdź czy Leaflet działa poprawnie
3. Odśwież stronę (Ctrl + F5)

### Problem: Błąd 404 dla plików danych
**Rozwiązanie:**
```bash
# Sprawdź czy pliki istnieją:
dir static\data

# Powinny być:
# - postal_code_to_region_transeu.json (152 KB)
# - voronoi_regions.geojson (154 KB)
```

---

## 📊 Kody przykładowe do testów

### Polska:
- PL00 - Warszawa
- PL30 - Kraków  
- PL50 - Wrocław
- PL60 - Poznań
- PL80 - Gdańsk
- PL90 - Katowice

### Niemcy:
- DE10 - Berlin
- DE20 - Hamburg
- DE40 - Düsseldorf
- DE80 - München (Monachium)

### Inne kraje:
- FR75 - Paris (Paryż)
- ES28 - Madrid (Madryt)
- IT00 - Roma (Rzym)
- AT10 - Wien (Wiedeń)
- CZ10 - Praha (Praga)
- NL10 - Amsterdam
- BE10 - Bruxelles (Bruksela)

---

## ✅ Checklist Testów

- [ ] Aplikacja uruchamia się bez błędów
- [ ] Strona ładuje się poprawnie
- [ ] Konsola pokazuje komunikaty o inicjalizacji
- [ ] Autocomplete pokazuje sugestie
- [ ] Można wybrać region z listy
- [ ] Formularz wysyła dane
- [ ] Mapa pokazuje regiony
- [ ] Odległość jest obliczona
- [ ] Wyniki są wyświetlone

---

## 🎯 Kolejne kroki po testach

Jeśli wszystko działa:
1. ✅ System jest gotowy do użycia
2. 📝 Możesz dodać więcej regionów (Timocom)
3. 🚀 Można wdrożyć na produkcję

Jeśli są problemy:
1. 🐛 Sprawdź konsolę przeglądarki
2. 📋 Sprawdź logi Flask
3. 📧 Zgłoś błędy

---

*Dokument testowy - System Postal Code Search v1.0*
