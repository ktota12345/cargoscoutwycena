# Trans.eu - Kopiowanie tokenu z istniejącej aplikacji

Jeśli aplikacja już działa na `freightfusion.eu`, możesz skopiować token zamiast robić nowy OAuth flow.

## Krok 1: Znajdź token na serwerze produkcyjnym

Na serwerze freightfusion.eu, token prawdopodobnie jest w:
- Pliku `.transeu_tokens.json` w katalogu aplikacji
- Lub w bazie danych
- Lub w pamięci cache

## Krok 2: Skopiuj format tokenu

Token powinien wyglądać tak:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "def502007e8a1c8f3d2b1a9e...",
  "expires_at": 1699887234.567
}
```

## Krok 3: Zapisz token lokalnie

Utwórz plik:
```
C:\Users\konra\Documents\wyceniarka\.transeu_tokens.json
```

I wklej skopiowany token.

## Krok 4: Restart aplikacji

```bash
python app.py
```

Token powinien zostać automatycznie załadowany i odświeżony gdy wygaśnie.

---

**UWAGA:** Token jest ważny tylko przez ~1 godzinę, ale refresh_token pozwala go odnawiać automatycznie przez ~30 dni.
