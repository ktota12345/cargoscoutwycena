# Opis Kolumn w Pliku TRIVIUM_PRZETARG_2026_pelne_dane.csv

## 📋 Ogólne Informacje

Plik zawiera **61 nowych kolumn** z danymi historycznymi z giełd TimoCom i Trans.eu.
Dane są w podziale na:
- **3 przedziały czasowe**: 7, 30, 90 dni
- **7 typów pojazdów**: 3 dla TimoCom + 4 dla Trans.eu
- **3 metryki**: średnia cena, mediana ceny (gdzie dostępna), liczba ofert

---

## 🗺️ Kolumny Mapowania

### `Mapping TimoCom`
**Format:** `XX-YY` (np. `37-83`)
**Opis:** Kody bazowych regionów TimoCom, na które została zmapowana oryginalna trasa
- XX = region startowy (ID regionu TimoCom)
- YY = region docelowy (ID regionu TimoCom)

### `Mapping TransEU`
**Format:** `XX-YY` (np. `106-114`)
**Opis:** Kody bazowych regionów Trans.eu, na które została zmapowana oryginalna trasa
- XX = region startowy (ID regionu Trans.eu)
- YY = region docelowy (ID regionu Trans.eu)

### `Dystans [km]`
**Format:** Liczba (np. `453.2`)
**Opis:** Obliczony dystans w kilometrach między centrami zmapowanych regionów (wzór Haversine)

---

## 🚛 TimoCom - Naczepa (Trailer)

Standard TIR z naczepą - najczęstszy typ transportu dalekobieżnego.

### Średnie Ceny (EUR/km)
- `TC Naczepa Avg 7d` - Średnia cena za km z ostatnich 7 dni
- `TC Naczepa Avg 30d` - Średnia cena za km z ostatnich 30 dni
- `TC Naczepa Avg 90d` - Średnia cena za km z ostatnich 90 dni

### Mediany Cen (EUR/km)
- `TC Naczepa Median 7d` - Mediana ceny za km z ostatnich 7 dni
- `TC Naczepa Median 30d` - Mediana ceny za km z ostatnich 30 dni
- `TC Naczepa Median 90d` - Mediana ceny za km z ostatnich 90 dni

### Liczba Ofert
- `TC Naczepa Oferty 7d` - Całkowita liczba ofert z ostatnich 7 dni
- `TC Naczepa Oferty 30d` - Całkowita liczba ofert z ostatnich 30 dni
- `TC Naczepa Oferty 90d` - Całkowita liczba ofert z ostatnich 90 dni

---

## 🚐 TimoCom - Do 3.5t

Pojazdy dostawcze do 3.5 tony (tzw. "busy").

### Średnie Ceny (EUR/km)
- `TC 3.5t Avg 7d` - Średnia cena za km z ostatnich 7 dni
- `TC 3.5t Avg 30d` - Średnia cena za km z ostatnich 30 dni
- `TC 3.5t Avg 90d` - Średnia cena za km z ostatnich 90 dni

### Liczba Ofert
- `TC 3.5t Oferty 7d` - Całkowita liczba ofert z ostatnich 7 dni
- `TC 3.5t Oferty 30d` - Całkowita liczba ofert z ostatnich 30 dni
- `TC 3.5t Oferty 90d` - Całkowita liczba ofert z ostatnich 90 dni

**UWAGA:** Brak kolumn z medianą - TimoCom nie udostępnia mediany dla tego typu pojazdu.

---

## 🚚 TimoCom - Do 12t

Średnie ciężarówki do 12 ton.

### Średnie Ceny (EUR/km)
- `TC 12t Avg 7d` - Średnia cena za km z ostatnich 7 dni
- `TC 12t Avg 30d` - Średnia cena za km z ostatnich 30 dni
- `TC 12t Avg 90d` - Średnia cena za km z ostatnich 90 dni

### Liczba Ofert
- `TC 12t Oferty 7d` - Całkowita liczba ofert z ostatnich 7 dni
- `TC 12t Oferty 30d` - Całkowita liczba ofert z ostatnich 30 dni
- `TC 12t Oferty 90d` - Całkowita liczba ofert z ostatnich 90 dni

**UWAGA:** Brak kolumn z medianą - TimoCom nie udostępnia mediany dla tego typu pojazdu.

---

## 🚛 Trans.eu - Lorry

Ciężarówka z naczepą - odpowiednik naczepy z TimoCom.

### Średnie Ceny (EUR/km)
- `TE Lorry Avg 7d` - Średnia cena za km z ostatnich 7 dni
- `TE Lorry Avg 30d` - Średnia cena za km z ostatnich 30 dni
- `TE Lorry Avg 90d` - Średnia cena za km z ostatnich 90 dni

### Mediany Cen (EUR/km)
- `TE Lorry Median 7d` - Mediana ceny za km z ostatnich 7 dni
- `TE Lorry Median 30d` - Mediana ceny za km z ostatnich 30 dni
- `TE Lorry Median 90d` - Mediana ceny za km z ostatnich 90 dni

### Liczba Ofert
- `TE Lorry Oferty 7d` - Liczba rekordów z ostatnich 7 dni
- `TE Lorry Oferty 30d` - Liczba rekordów z ostatnich 30 dni
- `TE Lorry Oferty 90d` - Liczba rekordów z ostatnich 90 dni

---

## 🚐 Trans.eu - Solo

Samochód ciężarowy bez naczepy.

### Średnie Ceny (EUR/km)
- `TE Solo Avg 7d` - Średnia cena za km z ostatnich 7 dni
- `TE Solo Avg 30d` - Średnia cena za km z ostatnich 30 dni
- `TE Solo Avg 90d` - Średnia cena za km z ostatnich 90 dni

### Mediany Cen (EUR/km)
- `TE Solo Median 7d` - Mediana ceny za km z ostatnich 7 dni
- `TE Solo Median 30d` - Mediana ceny za km z ostatnich 30 dni
- `TE Solo Median 90d` - Mediana ceny za km z ostatnich 90 dni

### Liczba Ofert
- `TE Solo Oferty 7d` - Liczba rekordów z ostatnich 7 dni
- `TE Solo Oferty 30d` - Liczba rekordów z ostatnich 30 dni
- `TE Solo Oferty 90d` - Liczba rekordów z ostatnich 90 dni

**UWAGA:** W aktualnej bazie danych brak ofert dla tego typu pojazdu.

---

## 🚌 Trans.eu - Bus

Autobusy.

### Średnie Ceny (EUR/km)
- `TE Bus Avg 7d` - Średnia cena za km z ostatnich 7 dni
- `TE Bus Avg 30d` - Średnia cena za km z ostatnich 30 dni
- `TE Bus Avg 90d` - Średnia cena za km z ostatnich 90 dni

### Mediany Cen (EUR/km)
- `TE Bus Median 7d` - Mediana ceny za km z ostatnich 7 dni
- `TE Bus Median 30d` - Mediana ceny za km z ostatnich 30 dni
- `TE Bus Median 90d` - Mediana ceny za km z ostatnich 90 dni

### Liczba Ofert
- `TE Bus Oferty 7d` - Liczba rekordów z ostatnich 7 dni
- `TE Bus Oferty 30d` - Liczba rekordów z ostatnich 30 dni
- `TE Bus Oferty 90d` - Liczba rekordów z ostatnich 90 dni

**UWAGA:** W aktualnej bazie danych brak ofert dla tego typu pojazdu.

---

## 🚛🚛 Trans.eu - Double Trailer

Podwójna naczepa (road train).

### Średnie Ceny (EUR/km)
- `TE DblTrailer Avg 7d` - Średnia cena za km z ostatnich 7 dni
- `TE DblTrailer Avg 30d` - Średnia cena za km z ostatnich 30 dni
- `TE DblTrailer Avg 90d` - Średnia cena za km z ostatnich 90 dni

### Mediany Cen (EUR/km)
- `TE DblTrailer Median 7d` - Mediana ceny za km z ostatnich 7 dni
- `TE DblTrailer Median 30d` - Mediana ceny za km z ostatnich 30 dni
- `TE DblTrailer Median 90d` - Mediana ceny za km z ostatnich 90 dni

### Liczba Ofert
- `TE DblTrailer Oferty 7d` - Liczba rekordów z ostatnich 7 dni
- `TE DblTrailer Oferty 30d` - Liczba rekordów z ostatnich 30 dni
- `TE DblTrailer Oferty 90d` - Liczba rekordów z ostatnich 90 dni

**UWAGA:** W aktualnej bazie danych brak ofert dla tego typu pojazdu.

---

## ⚠️ Kolumna Uwagi

### `Uwagi`
**Możliwe wartości:**
- **(puste)** - Trasa przetworzona poprawnie, dane dostępne
- `za krótka trasa` - Dystans < 150 km (takie trasy nie są w bazie)
- `błąd mapowania` - Nie udało się zmapować kodów pocztowych na regiony
- `brak danych historycznych` - Mapowanie OK, ale brak ofert w bazie dla tej trasy
- `nie znaleziono w analizie` - Trasa z CSV nie została znaleziona w pliku z wynikami

---

## 📊 Podsumowanie

**Łącznie kolumn:** 61 (3 mapowanie + 21 TimoCom + 36 Trans.eu + 1 uwagi)

**Format pliku:**
- Separator: średnik (`;`)
- Kodowanie: UTF-8 with BOM (UTF-8-sig)
- Gotowy do otwarcia w Excel

**Wartości puste:** Jeśli kolumna jest pusta, oznacza to brak danych dla danego typu pojazdu w danym okresie.

**Rekomendacje:**
- Dla standardowych tras TIR: używaj `TC Naczepa` lub `TE Lorry`
- Dla dostawczych: używaj `TC 3.5t`
- Mediana jest bardziej odporna na wartości odstające niż średnia
- Im dłuższy okres (90d), tym bardziej wiarygodne dane, ale mniej aktualne
