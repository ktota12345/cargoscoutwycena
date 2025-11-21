"""
Analiza różnic między dystansami obliczonymi różnymi metodami:
- Haversine (dystans w linii prostej)
- AWS Location Service API (rzeczywisty dystans drogowy dla ciężarówek)
"""
import pandas as pd
import numpy as np

CSV_FILE = "TRIVIUM_PRZETARG_2026_pelne_dane_AWS.csv"

def main():
    print("=" * 80)
    print("ANALIZA RÓŻNIC MIĘDZY DYSTANSAMI")
    print("=" * 80)
    
    # Wczytaj CSV
    print(f"\n📂 Wczytuję: {CSV_FILE}...")
    df = pd.read_csv(CSV_FILE, sep=';', encoding='utf-8')
    print(f"✅ Wczytano {len(df)} tras")
    
    # Kolumny
    aws_col = 'Dystans [km]'
    haversine_col = 'Dystans Haversine [km]'
    
    # Filtruj tylko te, które mają obie wartości
    df_valid = df[(df[aws_col].notna()) & (df[haversine_col].notna())].copy()
    print(f"✅ {len(df_valid)} tras z obydwoma dystansami")
    
    # Oblicz różnice
    df_valid['Różnica [km]'] = df_valid[haversine_col] - df_valid[aws_col]
    df_valid['Różnica [%]'] = ((df_valid[haversine_col] - df_valid[aws_col]) / df_valid[haversine_col] * 100)
    df_valid['Różnica Bezwzględna [km]'] = df_valid['Różnica [km]'].abs()
    
    print("\n" + "=" * 80)
    print("STATYSTYKI OGÓLNE")
    print("=" * 80)
    
    # Podstawowe statystyki
    print(f"\n📊 Dystans Haversine (w linii prostej):")
    print(f"   Średnia:  {df_valid[haversine_col].mean():.2f} km")
    print(f"   Mediana:  {df_valid[haversine_col].median():.2f} km")
    print(f"   Min:      {df_valid[haversine_col].min():.2f} km")
    print(f"   Max:      {df_valid[haversine_col].max():.2f} km")
    
    print(f"\n📊 Dystans AWS (rzeczywisty drogowy):")
    print(f"   Średnia:  {df_valid[aws_col].mean():.2f} km")
    print(f"   Mediana:  {df_valid[aws_col].median():.2f} km")
    print(f"   Min:      {df_valid[aws_col].min():.2f} km")
    print(f"   Max:      {df_valid[aws_col].max():.2f} km")
    
    print("\n" + "=" * 80)
    print("ANALIZA RÓŻNIC")
    print("=" * 80)
    
    # Różnice w kilometrach
    print(f"\n📏 Różnica w kilometrach (Haversine - AWS):")
    print(f"   Średnia:         {df_valid['Różnica [km]'].mean():.2f} km")
    print(f"   Mediana:         {df_valid['Różnica [km]'].median():.2f} km")
    print(f"   Odchylenie std:  {df_valid['Różnica [km]'].std():.2f} km")
    print(f"   Min (AWS dłuższy): {df_valid['Różnica [km]'].min():.2f} km")
    print(f"   Max (Haversine dłuższy): {df_valid['Różnica [km]'].max():.2f} km")
    
    # Różnice w procentach
    print(f"\n📈 Różnica w procentach:")
    print(f"   Średnia:         {df_valid['Różnica [%]'].mean():.2f}%")
    print(f"   Mediana:         {df_valid['Różnica [%]'].median():.2f}%")
    print(f"   Odchylenie std:  {df_valid['Różnica [%]'].std():.2f}%")
    print(f"   Min:             {df_valid['Różnica [%]'].min():.2f}%")
    print(f"   Max:             {df_valid['Różnica [%]'].max():.2f}%")
    
    # Kategorie różnic
    print("\n" + "=" * 80)
    print("KATEGORIE RÓŻNIC PROCENTOWYCH")
    print("=" * 80)
    
    categories = [
        ("AWS krótszy o >50%", df_valid['Różnica [%]'] > 50),
        ("AWS krótszy o 30-50%", (df_valid['Różnica [%]'] > 30) & (df_valid['Różnica [%]'] <= 50)),
        ("AWS krótszy o 20-30%", (df_valid['Różnica [%]'] > 20) & (df_valid['Różnica [%]'] <= 30)),
        ("AWS krótszy o 10-20%", (df_valid['Różnica [%]'] > 10) & (df_valid['Różnica [%]'] <= 20)),
        ("AWS krótszy o 5-10%", (df_valid['Różnica [%]'] > 5) & (df_valid['Różnica [%]'] <= 10)),
        ("Podobne (±5%)", (df_valid['Różnica [%]'] >= -5) & (df_valid['Różnica [%]'] <= 5)),
        ("AWS dłuższy o 5-10%", (df_valid['Różnica [%]'] < -5) & (df_valid['Różnica [%]'] >= -10)),
        ("AWS dłuższy o >10%", df_valid['Różnica [%]'] < -10),
    ]
    
    for label, condition in categories:
        count = condition.sum()
        percent = (count / len(df_valid)) * 100
        print(f"   {label:30s} {count:5d} tras ({percent:5.1f}%)")
    
    # Kierunek różnic
    print("\n" + "=" * 80)
    print("KIERUNEK RÓŻNIC")
    print("=" * 80)
    
    aws_shorter = (df_valid['Różnica [km]'] > 0).sum()
    aws_longer = (df_valid['Różnica [km]'] < 0).sum()
    similar = (df_valid['Różnica [km]'] == 0).sum()
    
    print(f"   🟢 AWS krótszy niż Haversine:  {aws_shorter:5d} tras ({aws_shorter/len(df_valid)*100:.1f}%)")
    print(f"   🔴 AWS dłuższy niż Haversine:  {aws_longer:5d} tras ({aws_longer/len(df_valid)*100:.1f}%)")
    print(f"   🟡 Identyczne:                 {similar:5d} tras ({similar/len(df_valid)*100:.1f}%)")
    
    # Top 20 największych różnic
    print("\n" + "=" * 80)
    print("TOP 20 NAJWIĘKSZYCH RÓŻNIC (Haversine był dużo dłuższy)")
    print("=" * 80)
    
    top_diff = df_valid.nlargest(20, 'Różnica [km]')[
        ['Lane Name', 'Origin Country', 'Origin 2 Zip', 'Destination Country', 'Destination 2 Zip',
         haversine_col, aws_col, 'Różnica [km]', 'Różnica [%]']
    ]
    
    print(f"\n{'#':<4} {'Trasa':<12} {'Haver.':<8} {'AWS':<8} {'Różnica':<10} {'%':<8}")
    print("-" * 60)
    for idx, (i, row) in enumerate(top_diff.iterrows(), 1):
        print(f"{idx:<4} {row['Lane Name']:<12} {row[haversine_col]:>7.0f} {row[aws_col]:>7.0f} "
              f"{row['Różnica [km]']:>9.0f} km {row['Różnica [%]']:>6.1f}%")
    
    # Top 10 tras gdzie AWS był dłuższy
    print("\n" + "=" * 80)
    print("TOP 10 TRAS GDZIE AWS BYŁ DŁUŻSZY (nietypowe przypadki)")
    print("=" * 80)
    
    aws_longer_df = df_valid[df_valid['Różnica [km]'] < 0].copy()
    if len(aws_longer_df) > 0:
        top_longer = aws_longer_df.nsmallest(10, 'Różnica [km]')[
            ['Lane Name', 'Origin Country', 'Origin 2 Zip', 'Destination Country', 'Destination 2 Zip',
             haversine_col, aws_col, 'Różnica [km]', 'Różnica [%]']
        ]
        
        print(f"\n{'#':<4} {'Trasa':<12} {'Haver.':<8} {'AWS':<8} {'Różnica':<10} {'%':<8}")
        print("-" * 60)
        for idx, (i, row) in enumerate(top_longer.iterrows(), 1):
            print(f"{idx:<4} {row['Lane Name']:<12} {row[haversine_col]:>7.0f} {row[aws_col]:>7.0f} "
                  f"{row['Różnica [km]']:>9.0f} km {row['Różnica [%]']:>6.1f}%")
    else:
        print("   Brak tras gdzie AWS był dłuższy")
    
    # Analiza po typach tras (krótkie, średnie, długie)
    print("\n" + "=" * 80)
    print("ANALIZA WG DŁUGOŚCI TRASY")
    print("=" * 80)
    
    distance_ranges = [
        ("Bardzo krótkie (<300 km)", df_valid[haversine_col] < 300),
        ("Krótkie (300-600 km)", (df_valid[haversine_col] >= 300) & (df_valid[haversine_col] < 600)),
        ("Średnie (600-1000 km)", (df_valid[haversine_col] >= 600) & (df_valid[haversine_col] < 1000)),
        ("Długie (1000-1500 km)", (df_valid[haversine_col] >= 1000) & (df_valid[haversine_col] < 1500)),
        ("Bardzo długie (>1500 km)", df_valid[haversine_col] >= 1500),
    ]
    
    for label, condition in distance_ranges:
        subset = df_valid[condition]
        if len(subset) > 0:
            avg_diff_km = subset['Różnica [km]'].mean()
            avg_diff_pct = subset['Różnica [%]'].mean()
            count = len(subset)
            print(f"\n   {label}")
            print(f"      Liczba tras:        {count}")
            print(f"      Średnia różnica:    {avg_diff_km:.2f} km ({avg_diff_pct:.1f}%)")
            print(f"      Mediana różnicy:    {subset['Różnica [km]'].median():.2f} km")
    
    # Zapisz szczegółowy raport
    print("\n" + "=" * 80)
    print("ZAPIS SZCZEGÓŁOWEGO RAPORTU")
    print("=" * 80)
    
    output_file = "distance_comparison_report.csv"
    df_report = df_valid[[
        'Lane Name', 'Origin Country', 'Origin 2 Zip', 'Destination Country', 'Destination 2 Zip',
        haversine_col, aws_col, 'Różnica [km]', 'Różnica [%]'
    ]].copy()
    
    # Sortuj po największej różnicy procentowej
    df_report = df_report.sort_values('Różnica [%]', ascending=False)
    df_report.to_csv(output_file, sep=';', index=False, encoding='utf-8')
    
    print(f"\n✅ Zapisano szczegółowy raport: {output_file}")
    print(f"   Zawiera {len(df_report)} tras z porównaniem dystansów")
    
    print("\n" + "=" * 80)
    print("WNIOSKI")
    print("=" * 80)
    
    avg_diff = df_valid['Różnica [%]'].mean()
    if avg_diff > 0:
        print(f"\n✅ Dystanse AWS są średnio o {avg_diff:.1f}% KRÓTSZE niż Haversine")
        print(f"   To oznacza, że Haversine ZAWYŻAŁ dystanse")
    else:
        print(f"\n⚠️  Dystanse AWS są średnio o {abs(avg_diff):.1f}% DŁUŻSZE niż Haversine")
    
    significant = (df_valid['Różnica Bezwzględna [km]'] > 50).sum()
    print(f"\n📊 {significant} tras ({significant/len(df_valid)*100:.1f}%) ma różnicę >50 km")
    
    print("\n✅ Analiza zakończona!")


if __name__ == "__main__":
    main()
