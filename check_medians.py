import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST'),
    port=os.getenv('POSTGRES_PORT'),
    user=os.getenv('POSTGRES_USER'),
    password=os.getenv('POSTGRES_PASSWORD'),
    dbname=os.getenv('POSTGRES_DB')
)

cur = conn.cursor()

print("=" * 80)
print("SPRAWDZENIE KOLUMN Z MEDIANĄ I ŚREDNIĄ")
print("=" * 80)

print("\n### TimoCom (public.offers) ###")
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'public'
      AND table_name = 'offers' 
      AND (column_name LIKE '%median%' OR column_name LIKE '%avg%')
      AND column_name LIKE '%price%km%'
    ORDER BY column_name
""")
print("\nKolumny:")
for row in cur.fetchall():
    col = row[0]
    if 'trailer' in col and ('median' in col or 'avg' in col) and 'low_filter' not in col and 'premium' not in col:
        print(f"  ✓ {col}")
    elif ('3_5_t' in col or '12_t' in col) and ('median' in col or 'avg' in col) and 'low_filter' not in col and 'premium' not in col:
        print(f"  ✓ {col}")

print("\n### Trans.eu (public.OffersTransEU) ###")
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'public'
      AND table_name = 'OffersTransEU' 
      AND (column_name LIKE '%median%' OR column_name LIKE '%avg%')
      AND column_name LIKE '%price%km%'
    ORDER BY column_name
""")
print("\nKolumny:")
for row in cur.fetchall():
    col = row[0]
    if ('lorry' in col or 'solo' in col or 'bus' in col or 'double_trailer' in col) and ('median' in col or 'avg' in col) and 'low_filter' not in col and 'premium' not in col:
        print(f"  ✓ {col}")

cur.close()
conn.close()
print("\n" + "=" * 80)
