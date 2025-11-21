import json

with open('route_analysis_20251114_182948.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 80)
print("SPRAWDZENIE MAPOWANIA")
print("=" * 80)

# Przykłady
print("\nPrzykładowe mapowania (pierwsze 10 tras):")
for r in data[:10]:
    route = r.get('original_route', 'N/A')
    timo_start = r.get('timocom_start', 'BRAK')
    timo_end = r.get('timocom_end', 'BRAK')
    trans_start = r.get('transeu_start', 'BRAK')
    trans_end = r.get('transeu_end', 'BRAK')
    
    print(f"  {route:15} | TimoCom: {timo_start:4} -> {timo_end:4} | Trans.eu: {trans_start:4} -> {trans_end:4}")

# Statystyki
no_transeu = sum(1 for r in data if not r.get('transeu_start') or not r.get('transeu_end'))
no_timocom = sum(1 for r in data if not r.get('timocom_start') or not r.get('timocom_end'))

print("\n" + "=" * 80)
print("STATYSTYKI MAPOWANIA")
print("=" * 80)
print(f"Łącznie tras:                {len(data)}")
print(f"❌ Tras BEZ mapowania Trans.eu: {no_transeu}")
print(f"❌ Tras BEZ mapowania TimoCom:  {no_timocom}")
print(f"✅ Tras z mapowaniem Trans.eu:  {len(data) - no_transeu}")
print(f"✅ Tras z mapowaniem TimoCom:   {len(data) - no_timocom}")

# Sprawdź ile tras ma dane w Trans.eu
with_transeu_data = 0
for r in data:
    if r.get('status') in ['success', 'cached']:
        data_obj = r.get('data', {})
        transeu = data_obj.get('transeu', {})
        for period in ['7d', '30d', '90d']:
            if transeu.get(period, {}).get('has_data'):
                with_transeu_data += 1
                break

print(f"\n✅ Tras z DANYMI Trans.eu:       {with_transeu_data}")
print("=" * 80)
