# 🚀 Deploy na Render - Instrukcja

## 📋 Wymagania wstępne

1. Konto na [Render.com](https://render.com)
2. Repozytorium Git (GitHub, GitLab, lub Bitbucket)

---

## 🔧 Przygotowanie projektu

### 1. Inicjalizacja repozytorium Git (jeśli jeszcze nie zrobione)

```bash
cd c:\Users\konra\Documents\wyceniarka
git init
git add .
git commit -m "Initial commit - Wyceniarka tras transportowych"
```

### 2. Utwórz repozytorium na GitHub/GitLab

1. Przejdź na [GitHub](https://github.com/new)
2. Utwórz nowe repozytorium (np. `wyceniarka-tras`)
3. **NIE** inicjalizuj z README, .gitignore lub licencją

### 3. Podłącz lokalne repozytorium do zdalnego

```bash
git remote add origin https://github.com/TWOJA_NAZWA/wyceniarka-tras.git
git branch -M main
git push -u origin main
```

---

## 🌐 Deploy na Render

### Metoda 1: Blueprint (zalecana)

1. Zaloguj się na [Render Dashboard](https://dashboard.render.com)
2. Kliknij **"New +"** → **"Blueprint"**
3. Połącz swoje repozytorium GitHub/GitLab
4. Wybierz repozytorium `wyceniarka-tras`
5. Render automatycznie wykryje `render.yaml` i skonfiguruje deployment
6. Kliknij **"Apply"**
7. Poczekaj ~3-5 minut na deployment

### Metoda 2: Web Service (ręczna)

1. Zaloguj się na [Render Dashboard](https://dashboard.render.com)
2. Kliknij **"New +"** → **"Web Service"**
3. Połącz repozytorium
4. Skonfiguruj:
   - **Name:** `wyceniarka`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** `Free`
5. Kliknij **"Create Web Service"**

---

## ✅ Sprawdzenie deployu

Po zakończeniu deployu:

1. Render wyświetli URL: `https://wyceniarka-XXXXX.onrender.com`
2. Kliknij w URL lub otwórz w przeglądarce
3. Aplikacja powinna się załadować w ~30 sekund (cold start na free tier)

### Test funkcjonalności:

1. ✅ Strona główna ładuje się poprawnie
2. ✅ Wpisz trasę: `PL50-340` → `DE10115`
3. ✅ Kliknij "Wyceń"
4. ✅ Sprawdź mapę z regionami Voronoi
5. ✅ Kliknij "⚡ teraz" i sprawdź okręgi 100km

---

## 📦 Pliki potrzebne do deployu

✅ Już przygotowane:

- `app.py` - główna aplikacja Flask (z obsługą PORT)
- `requirements.txt` - zależności Python
- `runtime.txt` - wersja Python (3.11.7)
- `render.yaml` - konfiguracja Render
- `.gitignore` - ignorowane pliki (w tym `package/`)
- `templates/` - szablony HTML
- `static/` - pliki statyczne (CSS, JS, dane)

---

## 🔥 Ważne uwagi

### 1. Folder `package/` NIE jest deployowany
- Zawiera tylko pliki źródłowe z innego projektu
- Jest w `.gitignore`
- Nie jest potrzebny na produkcji

### 2. Dane są w `static/data/`
- ✅ `voronoi_regions.geojson` (~2MB)
- ✅ `postal_code_to_region_transeu.json` (~100KB)
- ✅ `filtered_postal_codes.geojson` (~457KB)

### 3. Free tier Render
- Aplikacja "śpi" po 15 min nieaktywności
- Pierwsze uruchomienie może trwać ~30 sekund (cold start)
- Wystarczające dla testów i małego ruchu

---

## 🔄 Aktualizacja aplikacji

Po wprowadzeniu zmian w kodzie:

```bash
git add .
git commit -m "Opis zmian"
git push origin main
```

Render automatycznie wykryje zmiany i zrobi redeploy (~2-3 minuty).

---

## 🐛 Rozwiązywanie problemów

### Aplikacja nie startuje?

1. Sprawdź logi na Render Dashboard
2. Upewnij się, że wszystkie pliki są w repo:
   ```bash
   git status
   git push origin main
   ```

### 404 na plikach statycznych?

Sprawdź czy `static/data/` są w repozytorium:
```bash
git ls-files static/data/
```

Powinny być:
- `static/data/voronoi_regions.geojson`
- `static/data/postal_code_to_region_transeu.json`
- `static/data/filtered_postal_codes.geojson`

### Błąd importu?

Sprawdź `requirements.txt`:
```bash
cat requirements.txt
```

---

## 📊 Monitoring

Na Render Dashboard możesz:
- ✅ Zobacz logi aplikacji
- ✅ Sprawdzić użycie zasobów
- ✅ Ustawić custom domain
- ✅ Dodać zmienne środowiskowe

---

## 🎉 Gotowe!

Twoja aplikacja jest teraz dostępna online pod adresem:
```
https://wyceniarka-XXXXX.onrender.com
```

Możesz ją udostępnić klientom lub użytkownikom! 🚚💰

---

## 📞 Wsparcie

- [Dokumentacja Render](https://render.com/docs)
- [Render Community](https://community.render.com)
- [GitHub Issues](https://github.com/TWOJA_NAZWA/wyceniarka-tras/issues)
