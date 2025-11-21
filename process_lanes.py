import pandas as pd
import json

# Lista potencjalnych kodowań do sprawdzenia
encodings = ['utf-8', 'latin-1', 'windows-1250', 'iso-8859-2']
# Lista potencjalnych separatorów
separators = [',', ';']

file_path = 'TRIVIUM PRZETARG 2026(Arkusz1).csv'
df = None

# Pętla próbująca odczytać plik z różnymi kodowaniami i separatorami
for encoding in encodings:
    for sep in separators:
        try:
            df = pd.read_csv(file_path, encoding=encoding, sep=sep)
            print(f"Plik wczytany poprawnie z kodowaniem '{encoding}' i separatorem '{sep}'")
            break  # Jeśli się uda, przerwij pętlę separatorów
        except Exception as e:
            print(f"Nieudana próba z kodowaniem '{encoding}' i separatorem '{sep}': {e}")
            continue
    if df is not None:
        break # Jeśli się uda, przerwij pętlę kodowań

# Jeśli plik został wczytany pomyślnie
if df is not None:
    # Sprawdzenie, czy kolumna 'Lane Name' istnieje
    if 'Lane Name' in df.columns:
        # Wyodrębnienie unikalnych wartości z kolumny 'Lane Name'
        unique_lanes = df['Lane Name'].unique().tolist()

        # Definiowanie ścieżki do pliku wyjściowego
        output_path = 'unikalne_trasy.json'

        # Zapisywanie unikalnych tras do pliku JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(unique_lanes, f, ensure_ascii=False, indent=4)

        print(f"Znaleziono {len(unique_lanes)} unikalnych tras.")
        print(f"Unikalne trasy zostały zapisane w pliku '{output_path}'.")
    else:
        print("Błąd: Kolumna 'Lane Name' nie została znaleziona w pliku CSV.")
        print("Dostępne kolumny:", df.columns.tolist())
else:
    print("Nie udało się odczytać pliku CSV z żadnym z testowanych kodowań i separatorów.")
