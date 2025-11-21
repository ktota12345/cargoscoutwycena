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
print("KOLUMNY Z CENAMI W BAZACH")
print("=" * 80)

print("\nTimoCom (public.offers) - kolumny z 'price' i 'km':")
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'public'
      AND table_name = 'offers' 
      AND column_name LIKE '%price%km%'
    ORDER BY column_name
""")
for row in cur.fetchall():
    print(f"  - {row[0]}")

print("\nTrans.eu (public.OffersTransEU) - kolumny z 'price' i 'km':")
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_schema = 'public'
      AND table_name = 'OffersTransEU' 
      AND column_name LIKE '%price%km%'
    ORDER BY column_name
""")
for row in cur.fetchall():
    print(f"  - {row[0]}")

cur.close()
conn.close()
print("=" * 80)
