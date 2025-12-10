"""
Cargo Scout Wycena - UI Frontend
Prosty frontend - tylko normalizuje kody pocztowe i wywołuje Backend API
"""
from flask import Flask, render_template, jsonify, request
import os
import re
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)

# Konfiguracja Backend API
BACKEND_API_URL = os.getenv("API_URL")
BACKEND_API_KEY = os.getenv("API_KEY")

# AWS dla dystansu
AWS_LOCATION_API_KEY = os.getenv("AWS_LOCATION_API_KEY")
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")


def normalize_postal_code(postal_code):
    """
    Normalizuje kod pocztowy do formatu: <KOD_KRAJU><2_CYFRY>
    PL20-123 -> PL20, DE49876 -> DE49
    """
    if not postal_code:
        return None
    
    cleaned = str(postal_code).upper().replace(' ', '').replace('-', '')
    match = re.match(r'^([A-Z]{2})(\d{2})', cleaned)
    
    if match:
        return f"{match.group(1)}{match.group(2)}"
    
    return None


@app.route('/')
def index():
    """Strona główna"""
    return render_template('index.html')


@app.route('/api/calculate', methods=['POST'])
def calculate_route():
    """
    Prosty proxy do Backend API
    1. Normalizuje kody pocztowe (PL20, DE49)
    2. Wywołuje Backend API
    3. Zwraca odpowiedź
    """
    data = request.json
    
    start_location = data.get('start_location', '')
    end_location = data.get('end_location', '')
    calculated_distance = data.get('calculated_distance')
    vehicle_type = data.get('vehicle_type', 'naczepa')
    body_type = data.get('body_type', 'standard')
    
    # Normalizuj kody
    normalized_start = normalize_postal_code(start_location)
    normalized_end = normalize_postal_code(end_location)
    
    print(f"📝 {start_location} -> {normalized_start}, {end_location} -> {normalized_end}")
    print(f"🚛 Typ: {vehicle_type}, Nadwozie: {body_type}")
    
    if not normalized_start or not normalized_end:
        return jsonify({
            'error': 'Nieprawidłowy format kodów pocztowych',
            'message': 'Użyj formatu: <KRAJ><CYFRY> np. PL20, DE49'
        }), 400
    
    if not calculated_distance:
        return jsonify({'error': 'Brak dystansu'}), 400
    
    if not BACKEND_API_URL or not BACKEND_API_KEY:
        return jsonify({
            'error': 'Brak konfiguracji Backend API',
            'message': 'Ustaw API_URL i API_KEY w .env'
        }), 500
    
    # Wywołaj Backend API
    try:
        print(f"🌐 Backend API: {normalized_start} -> {normalized_end}, {calculated_distance} km")
        
        response = requests.post(
            BACKEND_API_URL,
            json={
                'start_postal_code': normalized_start,
                'end_postal_code': normalized_end,
                'dystans': calculated_distance
            },
            headers={
                'X-API-Key': BACKEND_API_KEY,
                'Content-Type': 'application/json'
            },
            timeout=30
        )
        
        print(f"📥 Status: {response.status_code}")
        
        if response.status_code == 200:
            api_data = response.json()
            
            if api_data.get('success'):
                # Przekształć do formatu UI
                backend_data = api_data.get('data', {})
                pricing = backend_data.get('pricing', {})
                
                # Przygotuj odpowiedź
                result = {
                    'distance': calculated_distance,
                    'start_location': start_location,
                    'end_location': end_location,
                    'vehicle_type': vehicle_type,
                    'body_type': body_type,
                    'start_coords': data.get('start_coords'),
                    'end_coords': data.get('end_coords'),
                    'route': {
                        'start': data.get('start_coords', [52.0, 19.0]),
                        'end': data.get('end_coords', [50.0, 20.0]),
                        'route': []
                    },
                    # Dane z API - filtrowane według typu samochodu
                    'exchange_rates': transform_to_ui_format(pricing, calculated_distance, 30, vehicle_type, body_type),
                    'exchange_rates_by_days': {
                        '7': transform_to_ui_format(pricing, calculated_distance, 7, vehicle_type, body_type),
                        '30': transform_to_ui_format(pricing, calculated_distance, 30, vehicle_type, body_type),
                        '90': transform_to_ui_format(pricing, calculated_distance, 90, vehicle_type, body_type)
                    },
                    'historical_rates': transform_historical(pricing),
                    'historical_rates_by_days': {
                        '7': transform_historical(pricing),
                        '30': transform_historical(pricing),
                        '90': transform_historical(pricing)
                    },
                    'tolls': {'estimated': 0, 'currency': 'EUR'},
                    'suggested_carriers': [],
                    '_api_response': backend_data  # Debug
                }
                
                return jsonify(result)
            else:
                return jsonify(api_data), 400
        else:
            return jsonify({
                'error': f'Backend API error: {response.status_code}',
                'message': response.text
            }), response.status_code
            
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Backend API timeout'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': f'Nie można połączyć z {BACKEND_API_URL}'}), 503
    except Exception as e:
        print(f"❌ {e}")
        return jsonify({'error': str(e)}), 500


def transform_to_ui_format(pricing, distance, days, vehicle_type='naczepa', body_type='standard'):
    """Przekształć dane giełd z API do formatu UI - filtrowane według typu samochodu"""
    period_key = f"{days}d"
    offers = []
    
    # Mapowanie typu samochodu na klucze API
    # solo -> solo
    # naczepa + standard -> trailer
    # naczepa + mega/jumbo -> mega_trailer
    # bus, zestaw -> pokaż wszystkie
    
    # TimoCom
    timocom = pricing.get('timocom', {}).get(period_key, {})
    if timocom.get('avg_price_per_km'):
        # Solo
        if vehicle_type == 'solo' and timocom['avg_price_per_km'].get('solo'):
            offers.append({
                'exchange': 'TimoCom',
                'vehicle_type': 'Solo',
                'rate_per_km': timocom['avg_price_per_km']['solo'],
                'total_price': round(timocom['avg_price_per_km']['solo'] * distance, 2),
                'currency': 'EUR',
                'has_data': True,
                'total_offers_sum': timocom.get('total_offers', 0)
            })
        
        # Naczepa Standard
        if vehicle_type == 'naczepa' and body_type == 'standard' and timocom['avg_price_per_km'].get('trailer'):
            offers.append({
                'exchange': 'TimoCom',
                'vehicle_type': 'Naczepa Standard',
                'rate_per_km': timocom['avg_price_per_km']['trailer'],
                'total_price': round(timocom['avg_price_per_km']['trailer'] * distance, 2),
                'currency': 'EUR',
                'has_data': True,
                'total_offers_sum': timocom.get('total_offers', 0)
            })
        
        # Naczepa Mega/Jumbo
        if vehicle_type == 'naczepa' and body_type in ['mega', 'jumbo'] and timocom['avg_price_per_km'].get('mega_trailer'):
            offers.append({
                'exchange': 'TimoCom',
                'vehicle_type': f'Naczepa {body_type.capitalize()}',
                'rate_per_km': timocom['avg_price_per_km']['mega_trailer'],
                'total_price': round(timocom['avg_price_per_km']['mega_trailer'] * distance, 2),
                'currency': 'EUR',
                'has_data': True,
                'total_offers_sum': timocom.get('total_offers', 0)
            })
        
        # Bus, Zestaw - pokaż trailer jako domyślny
        if vehicle_type in ['bus', 'zestaw'] and timocom['avg_price_per_km'].get('trailer'):
            offers.append({
                'exchange': 'TimoCom',
                'vehicle_type': 'Naczepa',
                'rate_per_km': timocom['avg_price_per_km']['trailer'],
                'total_price': round(timocom['avg_price_per_km']['trailer'] * distance, 2),
                'currency': 'EUR',
                'has_data': True,
                'total_offers_sum': timocom.get('total_offers', 0)
            })
    
    # Trans.eu
    transeu = pricing.get('transeu', {}).get(period_key, {})
    if transeu.get('avg_price_per_km', {}).get('lorry'):
        offers.append({
            'exchange': 'Trans.eu',
            'vehicle_type': 'Lorry',
            'rate_per_km': transeu['avg_price_per_km']['lorry'],
            'total_price': round(transeu['avg_price_per_km']['lorry'] * distance, 2),
            'currency': 'EUR',
            'has_data': True,
            'total_offers_sum': transeu.get('total_offers', 0)
        })
    
    if not offers:
        offers = [
            {'exchange': 'TimoCom', 'has_data': False, 'rate_per_km': None},
            {'exchange': 'Trans.eu', 'has_data': False, 'rate_per_km': None}
        ]
    
    rates = [o['rate_per_km'] for o in offers if o.get('has_data') and o.get('rate_per_km')]
    
    return {
        'has_data': len(rates) > 0,
        'offers': offers,
        'average_rate_per_km': round(sum(rates) / len(rates), 2) if rates else None,
        'days': days
    }


def transform_historical(pricing):
    """Przekształć dane historyczne z API"""
    historical = pricing.get('historical', {}).get('180d', {})
    ftl = historical.get('FTL')
    ltl = historical.get('LTL')
    
    if not ftl and not ltl:
        return {'has_data': False, 'orders': []}
    
    orders = []
    
    if ftl and ftl.get('top_carriers'):
        for c in ftl['top_carriers']:
            orders.append({
                'carrier': c.get('carrier_name'),
                'rate_per_km': c.get('avg_carrier_price_per_km'),
                'total_price': c.get('avg_carrier_amount'),
                'type': 'FTL',
                'order_count': c.get('order_count', 0)
            })
    
    if ltl and ltl.get('top_carriers'):
        for c in ltl['top_carriers']:
            orders.append({
                'carrier': c.get('carrier_name'),
                'rate_per_km': c.get('avg_carrier_price_per_km'),
                'total_price': c.get('avg_carrier_amount'),
                'type': 'LTL',
                'order_count': c.get('order_count', 0)
            })
    
    rates = [o['rate_per_km'] for o in orders if o.get('rate_per_km')]
    
    return {
        'has_data': True,
        'orders': orders,
        'average_rate_per_km': round(sum(rates) / len(rates), 2) if rates else None
    }


@app.route('/api/calculate-distance', methods=['POST'])
def calculate_distance():
    """AWS Location Service - obliczanie dystansu"""
    data = request.json
    start_coords = data.get('start_coords')
    end_coords = data.get('end_coords')
    
    if not start_coords or not end_coords or not AWS_LOCATION_API_KEY:
        return jsonify({'success': False, 'error': 'Brak danych lub konfiguracji'}), 400
    
    try:
        url = f"https://routes.geo.{AWS_REGION}.amazonaws.com/routes/v0/calculators/CargoScoutCalculator/calculate/route"
        
        response = requests.post(
            url,
            json={
                'Origin': {'Position': [start_coords[1], start_coords[0]]},
                'Destination': {'Position': [end_coords[1], end_coords[0]]},
                'TravelMode': 'Truck'
            },
            headers={
                'Content-Type': 'application/json',
                'X-Amz-Api-Key': AWS_LOCATION_API_KEY
            },
            timeout=30
        )
        
        if response.status_code == 200:
            aws_data = response.json()
            distance_km = aws_data.get('Summary', {}).get('Distance', 0) / 1000
            
            return jsonify({
                'success': True,
                'distance': round(distance_km, 2),
                'method': 'aws'
            })
        else:
            return jsonify({'success': False, 'error': 'AWS error'}), response.status_code
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Cargo Scout UI - Port {port}")
    print(f"🔗 Backend API: {BACKEND_API_URL}")
    app.run(debug=True, host='0.0.0.0', port=port)
