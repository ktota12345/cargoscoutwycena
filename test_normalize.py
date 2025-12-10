import re

def normalize_postal_code(postal_code):
    if not postal_code:
        return None
    
    cleaned = postal_code.upper().replace(' ', '').replace('-', '')
    match = re.match(r'^([A-Z]{2})(\d{2})', cleaned)
    
    if match:
        country_code = match.group(1)
        first_two_digits = match.group(2)
        return f"{country_code}{first_two_digits}"
    
    return postal_code

# Testy
test_cases = [
    "PL20",
    "DE49",
    "PL20-123",
    "DE 49876",
    "FR75001",
    "pl20",
    "de49"
]

print("Testy normalizacji kodów pocztowych:")
print("-" * 40)
for code in test_cases:
    normalized = normalize_postal_code(code)
    print(f"{code:20} -> {normalized}")
