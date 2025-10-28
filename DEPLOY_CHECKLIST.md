# ✅ Checklist Deploy - Render

## Przed deployem

### 1. Sprawdź pliki konfiguracyjne
- [x] `requirements.txt` - zależności Python
- [x] `runtime.txt` - wersja Python (3.11.7)
- [x] `render.yaml` - konfiguracja Render
- [x] `.gitignore` - folder `package/` jest ignorowany
- [x] `app.py` - używa `PORT` ze zmiennej środowiskowej

### 2. Sprawdź pliki danych w `static/data/`
```bash
# Uruchom w terminalu:
ls -lh static/data/

# Powinny być:
# voronoi_regions.geojson (~2MB)
# postal_code_to_region_transeu.json (~100KB)
# filtered_postal_codes.geojson (~457KB)
```

### 3. Test lokalny
```bash
# Uruchom aplikację:
python app.py

# Sprawdź w przeglądarce:
# http://localhost:5000
```

---

## Inicjalizacja Git

```bash
cd c:\Users\konra\Documents\wyceniarka

# Inicjalizacja (jeśli jeszcze nie zrobione)
git init

# Dodaj wszystkie pliki
git add .

# Pierwszy commit
git commit -m "Initial commit - Wyceniarka tras transportowych v1.0"

# Sprawdź status
git status
```

---

## Utwórz repozytorium GitHub

1. Przejdź na https://github.com/new
2. Nazwa repozytorium: `wyceniarka-tras`
3. Opis: `Aplikacja do wyceny tras transportowych`
4. **Public** lub **Private** (według preferencji)
5. **NIE** zaznaczaj: "Add README", ".gitignore", "license"
6. Kliknij **"Create repository"**

---

## Podłącz i wypchnij kod

```bash
# Dodaj zdalny origin (ZMIEŃ na swój URL!)
git remote add origin https://github.com/TWOJA_NAZWA/wyceniarka-tras.git

# Zmień branch na main
git branch -M main

# Wypchnij kod
git push -u origin main
```

---

## Deploy na Render

### Opcja A: Blueprint (ZALECANA - szybsza)

1. Zaloguj się na https://dashboard.render.com
2. Kliknij **"New +"** → **"Blueprint"**
3. Kliknij **"Connect a repository"**
4. Wybierz `wyceniarka-tras`
5. Render wykryje `render.yaml`
6. Kliknij **"Apply"**
7. ⏳ Poczekaj 3-5 minut

### Opcja B: Web Service (ręczna)

1. Zaloguj się na https://dashboard.render.com
2. Kliknij **"New +"** → **"Web Service"**
3. Kliknij **"Connect a repository"**
4. Wybierz `wyceniarka-tras`
5. Konfiguracja:
   - **Name:** `wyceniarka`
   - **Region:** Frankfurt (Europe)
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** `Free`
6. Kliknij **"Create Web Service"**
7. ⏳ Poczekaj 3-5 minut

---

## Weryfikacja

Po zakończeniu deployu:

### 1. Sprawdź URL
```
https://wyceniarka-XXXXX.onrender.com
```

### 2. Test funkcjonalności

#### Test 1: Strona główna
- [ ] Strona ładuje się poprawnie
- [ ] Wszystkie style CSS załadowane
- [ ] Brak błędów w konsoli (F12)

#### Test 2: Wyszukiwanie trasy
- [ ] Wpisz: `PL50340` → `DE10115`
- [ ] Kliknij "Wyceń"
- [ ] Wyniki się wyświetlają
- [ ] Mapa pokazuje trasę

#### Test 3: Regiony Voronoi
- [ ] Na mapie widoczne półprzezroczyste regiony
- [ ] Precyzyjne znaczniki A i B
- [ ] Linia trasy między punktami

#### Test 4: Przyciski dni
- [ ] Kliknij "30 dni" - dane się zmieniają
- [ ] Kliknij "90 dni" - dane się zmieniają
- [ ] Kliknij "7 dni" - powrót do pierwotnych danych

#### Test 5: Tryb "teraz"
- [ ] Kliknij "⚡ teraz"
- [ ] Pokazuje się pasek postępu
- [ ] Po 8 sekundach dane są widoczne
- [ ] Mapa pokazuje okręgi 100km
- [ ] Drugie kliknięcie "teraz" - natychmiastowe (bez paska)

#### Test 6: Autocomplete
- [ ] Wpisz "PL5" w pole startu
- [ ] Pokazują się sugestie
- [ ] Wybór z listy działa

---

## Problemy i rozwiązania

### ❌ Błąd 404 na dane GeoJSON

**Przyczyna:** Pliki nie zostały dodane do git

**Rozwiązanie:**
```bash
git add static/data/
git commit -m "Add data files"
git push origin main
```

### ❌ Aplikacja nie startuje

**Sprawdź logi:**
1. Render Dashboard → Twoja aplikacja
2. Zakładka "Logs"
3. Szukaj błędów

**Typowe problemy:**
- Brak `gunicorn` w requirements.txt
- Błąd w `app.py`
- Nieprawidłowy `PORT`

### ❌ Cold start trwa długo

**To normalne na Free tier:**
- Pierwsze uruchomienie: ~30 sekund
- Po 15 minutach nieaktywności aplikacja "śpi"
- Następne uruchomienie znów ~30 sekund

**Rozwiązanie:** Upgrade do płatnego planu ($7/miesiąc)

---

## 🎉 Gotowe!

Twoja aplikacja jest teraz online!

**Następne kroki:**
1. Udostępnij URL klientom
2. Zbierz feedback
3. Dodaj własną domenę (opcjonalnie)
4. Monitoruj logi na Render

---

## Aktualizacje

Aby zaktualizować aplikację:

```bash
# Wprowadź zmiany w kodzie
git add .
git commit -m "Opis zmian"
git push origin main

# Render automatycznie zrobi redeploy (2-3 minuty)
```

---

## 📞 Pomoc

Jeśli coś nie działa:
1. Sprawdź logi na Render Dashboard
2. Zobacz `README_DEPLOY.md` dla szczegółów
3. [Dokumentacja Render](https://render.com/docs/deploy-flask)
