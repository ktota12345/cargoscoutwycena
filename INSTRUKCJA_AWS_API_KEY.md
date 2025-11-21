# Jak uzyskać AWS Location Service API Key

## Krok 1: Zaloguj się do AWS Console
Otwórz: https://console.aws.amazon.com/

## Krok 2: Przejdź do Amazon Location Service
1. W pasku wyszukiwania wpisz: **"Location Service"**
2. Lub użyj bezpośredniego linku: https://console.aws.amazon.com/location/home

## Krok 3: Utwórz API Key
1. W lewym menu wybierz: **API keys**
   - Lub użyj: https://console.aws.amazon.com/location/home#/api-keys
2. Kliknij przycisk: **Create API key**

## Krok 4: Skonfiguruj API Key
Wypełnij formularz:

### Basic settings:
- **API key name**: `CargoScout-Routes` (lub dowolna nazwa)
- **Description** (opcjonalnie): "API key for route distance calculation"

### Allowed operations:
- ☑️ **Routes** - ZAZNACZ TO!
- ☐ Maps (nie potrzebne)
- ☐ Places (nie potrzebne)

### Allowed resources:
- Wybierz region, np.: **Europe (Frankfurt) - eu-central-1**
- Lub wybierz **All resources** jeśli chcesz większą elastyczność

### Expiration (opcjonalnie):
- **Never expire** - lub ustaw datę wygaśnięcia

## Krok 5: Skopiuj API Key
1. Po utworzeniu, **skopiuj API key** (będzie wyświetlony tylko raz!)
2. Wklej go do pliku `.env`:

```env
AWS_LOCATION_API_KEY="v1.public.ey..."
AWS_REGION="eu-central-1"
```

## Krok 6: Testuj
Uruchom test:
```bash
python test_aws_distance.py
```

## Ważne uwagi
- ⚠️ **API key jest wyświetlany tylko raz** podczas tworzenia
- ⚠️ **Region** w `.env` musi być zgodny z regionem API key
- ⚠️ AWS Location Service ma **limity Free Tier**:
  - 300,000 zapytań/miesiąc GRATIS
  - Potem: ~$0.50 za 1000 zapytań
- 💡 Możesz utworzyć wiele API keys z różnymi uprawnieniami

## Troubleshooting

### Błąd 403 Forbidden
- Sprawdź czy API key jest poprawnie skopiowany
- Upewnij się, że zaznaczyłeś operację **Routes**
- Sprawdź region w `.env`

### Błąd 404 Not Found
- Zły region w `.env` - zmień na region, w którym utworzyłeś API key

### API key nie działa
- API key musi zaczynać się od `v1.public.`
- Upewnij się, że nie ma spacji przed/po kluczu w `.env`
- Sprawdź czy API key nie wygasł
