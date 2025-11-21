# Trans.eu OAuth2 - Konfiguracja

## Przegląd

Trans.eu API wymaga autoryzacji OAuth2 (Authorization Code Grant Flow) zamiast prostego API key. Zaimplementowany system automatycznie odświeża tokeny i zapisuje je lokalnie.

## Wymagane dane (już masz w `.env`)

```bash
TRANSEU_API_KEY=5d7a5d98b726a400012bbb8a6ab03b01b9a9403fbda18b6478d98264
TRANSEU_CLIENT_ID=de92025f-9afc-4d75-8e5e-23b6335ce8b3
TRANSEU_CLIENT_SECRET=zahx6eiVoo5lae9Uyaith6Doiez9Iewe
TRANSEU_REDIRECT_URI=http://localhost:5000/callback/transeu
```

**Uwaga:** `TRANSEU_API_KEY` jest używany jako header `Api-key` w OAuth flow (nowa platforma Trans.eu)

## Kroki konfiguracji

### 1. Uruchom aplikację

```bash
python app.py
```

Aplikacja działa na: `http://localhost:5000`

### 2. Sprawdź status autoryzacji

Otwórz w przeglądarce:
```
http://localhost:5000/api/oauth/transeu/status
```

Odpowiedź:
```json
{
  "authorized": false,
  "authorization_url": "https://auth.system.trans.eu/oauth2/authorize?..."
}
```

### 3. Rozpocznij autoryzację OAuth

**Opcja A: Przez przeglądarkę (najprostsze)**

```
http://localhost:5000/oauth/transeu/authorize
```

**Opcja B: Przez skrypt Python**

```bash
python transeu_oauth.py
```

### 4. Zaloguj się do Trans.eu

1. Zostaniesz przekierowany na stronę logowania Trans.eu
2. Zaloguj się swoim kontem Trans.eu
3. Zatwierdź uprawnienia dla aplikacji (scope: `offers.loads.manage`)

### 5. Callback i zapisanie tokenu

Po zatwierdzeniu zostaniesz przekierowany na:
```
http://localhost:5000/callback/transeu?code=AUTHORIZATION_CODE&state=...
```

System automatycznie:
- Wymieni `code` na `access_token` i `refresh_token`
- Zapisze tokeny do pliku `.transeu_tokens.json`
- Wyświetli komunikat sukcesu

### 6. Weryfikacja

Sprawdź ponownie status:
```
http://localhost:5000/api/oauth/transeu/status
```

Odpowiedź:
```json
{
  "authorized": true,
  "expires_in": 3600,
  "expires_in_minutes": 60.0
}
```

## Automatyczne odświeżanie tokenu

System automatycznie:
- Sprawdza ważność tokenu przed każdym zapytaniem
- Odświeża token gdy wygasa (za pomocą `refresh_token`)
- Zapisuje nowy token do pliku

**Nie musisz nic robić ręcznie!**

## Struktura plików

### `.transeu_tokens.json` (tworzony automatycznie)

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "def502007e8a1c8f3d2b1a9e...",
  "expires_at": 1699887234.567
}
```

**Ważne:** Dodaj ten plik do `.gitignore`!

```bash
echo ".transeu_tokens.json" >> .gitignore
```

## Testowanie API

### Test z terminala

```python
from freight_api import TranseuAPI

api = TranseuAPI()

result = api.search_freight_offers(
    start_location="50-340 Wrocław, Poland",
    end_location="50667 Köln, Germany",
    limit=10
)

print(result)
```

### Test przez aplikację

1. Uruchom aplikację: `python app.py`
2. Wpisz trasę (np. Wrocław → Köln)
3. Kliknij przycisk **"teraz"**
4. Sprawdź logi:

```
🌐 API Current Offers - tryb TERAZ
   Start: 50-340 Wrocław, Poland (raw: pl00)
   Cel: 50667 Köln, Germany (raw: de50)

🔄 TimoCom API: Zapytanie...
✓ TimoCom: Znaleziono 15 ofert

🔄 Trans.eu API: Zapytanie...
✓ Trans.eu: Znaleziono 8 ofert

✓ Pobrano łącznie 23 aktualnych ofert
```

## Troubleshooting

### Błąd: "Brak ważnego tokenu OAuth"

**Rozwiązanie:** Przejdź przez proces autoryzacji ponownie:
```
http://localhost:5000/oauth/transeu/authorize
```

### Błąd: "redirect_uri mismatch"

**Przyczyna:** Redirect URI w aplikacji Trans.eu nie zgadza się z tym w `.env`

**Rozwiązanie:**
1. Zaloguj się do panelu Trans.eu dla developerów
2. Sprawdź ustawienia aplikacji OAuth
3. Ustaw redirect URI na: `http://localhost:5000/callback/transeu`

### Błąd: "invalid_client"

**Przyczyna:** Nieprawidłowy CLIENT_ID lub CLIENT_SECRET

**Rozwiązanie:** Sprawdź dane w pliku `.env`

### Token wygasa zbyt często

**Info:** Access token Trans.eu zwykle wygasa po 1 godzinie, ale jest automatycznie odświeżany.

Jeśli widzisz częste odświeżanie:
```
✓ Odświeżono access token Trans.eu
```

To normalne zachowanie - nie wymaga działania.

### Usunięcie autoryzacji

Usuń plik z tokenami:
```bash
rm .transeu_tokens.json
```

Następnie przejdź przez proces autoryzacji ponownie.

## Endpointy OAuth w aplikacji

| Endpoint | Opis |
|----------|------|
| `GET /oauth/transeu/authorize` | Przekierowanie do Trans.eu login |
| `GET /callback/transeu` | Callback po autoryzacji |
| `GET /api/oauth/transeu/status` | Status autoryzacji (JSON) |

## Zakres uprawnień (scopes)

Aplikacja żąda zakresu:
```
offers.loads.manage
```

To pozwala na:
- Wyszukiwanie ofert ładunków
- Przeglądanie szczegółów ofert
- (Potencjalnie) tworzenie/edycję ofert

## Bezpieczeństwo

### Best practices:

1. **Nie commituj tokenów do Git:**
   ```bash
   echo ".transeu_tokens.json" >> .gitignore
   ```

2. **Nie udostępniaj CLIENT_SECRET:**
   - Przechowuj w `.env`
   - Dodaj `.env` do `.gitignore`

3. **HTTPS w produkcji:**
   - Lokalnie: `http://localhost:5000` jest OK
   - Produkcja: WYMAGANE `https://`

4. **State parameter:**
   - System używa state dla ochrony CSRF
   - Nie wyłączaj tego!

## Przepływ OAuth2 (szczegóły techniczne)

```
1. Użytkownik → /oauth/transeu/authorize
                ↓
2. Przekierowanie → https://auth.platform.trans.eu/oauth2/auth
                    ?client_id=...
                    &redirect_uri=http://localhost:5000/callback/transeu
                    &response_type=code
                    &scope=offers.loads.manage
                ↓
3. Użytkownik loguje się i zatwierdza
                ↓
4. Trans.eu → http://localhost:5000/callback/transeu?code=AUTH_CODE
                ↓
5. Backend → POST https://api.platform.trans.eu/ext/auth-api/accounts/token
             Headers: 
               Content-Type: application/x-www-form-urlencoded
               Api-key: {TRANSEU_API_KEY}
             Body: {
               "grant_type": "authorization_code",
               "code": "AUTH_CODE",
               "client_id": "...",
               "client_secret": "..."
             }
                ↓
6. Trans.eu → {
                "access_token": "...",
                "refresh_token": "...",
                "expires_in": 3600
              }
                ↓
7. Backend zapisuje tokeny → .transeu_tokens.json
```

## Odświeżanie tokenu

```
1. API call → Sprawdź czy token ważny
                ↓
2. Nie ważny → POST https://api.platform.trans.eu/ext/auth-api/accounts/token
               Headers: 
                 Content-Type: application/x-www-form-urlencoded
                 Api-key: {TRANSEU_API_KEY}
               Body: {
                 "grant_type": "refresh_token",
                 "refresh_token": "...",
                 "client_id": "...",
                 "client_secret": "..."
               }
                ↓
3. Trans.eu → {
                "access_token": "NEW_TOKEN",
                "refresh_token": "NEW_REFRESH",
                "expires_in": 3600
              }
                ↓
4. Zapisz nowe tokeny → Kontynuuj API call
```

## Monitoring

### Sprawdź logi aplikacji:

```bash
python app.py
```

Będziesz widział:
```
✓ Załadowano tokeny Trans.eu z pliku
✓ Odświeżono access token Trans.eu
🔄 Trans.eu API: Zapytanie 50-340 Wrocław, Poland -> 50667 Köln, Germany
✓ Trans.eu: Znaleziono 8 ofert
```

### Sprawdź plik tokenów:

```bash
cat .transeu_tokens.json
```

## Pytania?

Sprawdź:
- Dokumentację Trans.eu API: https://api-docs.trans.eu/
- OAuth2 RFC: https://oauth.net/2/

## Podsumowanie

1. ✅ Masz już CLIENT_ID i CLIENT_SECRET w `.env`
2. ✅ Uruchom aplikację: `python app.py`
3. ✅ Otwórz: `http://localhost:5000/oauth/transeu/authorize`
4. ✅ Zaloguj się i zatwierdź
5. ✅ Gotowe! Tokeny są automatycznie zarządzane

**Trans.eu API będzie teraz działać w trybie "teraz"!** 🚀
