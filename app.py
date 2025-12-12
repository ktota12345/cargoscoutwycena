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
    
    # Normalizuj kody
    normalized_start = normalize_postal_code(start_location)
    normalized_end = normalize_postal_code(end_location)
    
    print(f"📝 {start_location} -> {normalized_start}, {end_location} -> {normalized_end}")
    
    if not normalized_start or not normalized_end:
        return jsonify({
            'error': 'Nieprawidłowy format kodów pocztowych',
            'message': 'Użyj formatu: <KRAJ><CYFRY> np. PL20, DE49'
        }), 400
    
    if not BACKEND_API_URL or not BACKEND_API_KEY:
        return jsonify({
            'error': 'Brak konfiguracji Backend API',
            'message': 'Ustaw API_URL i API_KEY w .env'
        }), 500
    
    # Wywołaj Backend API
    try:
        print(f"🌐 Backend API: {normalized_start} -> {normalized_end}")
        
        response = requests.post(
            BACKEND_API_URL,
            json={
                'start_postal_code': normalized_start,
                'end_postal_code': normalized_end
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
                route_distance_data = backend_data.get('route_distance', {})
                
                # Użyj dystansu z API
                actual_distance = route_distance_data.get('distance_km', 0)
                
                # Przygotuj odpowiedź
                result = {
                    'distance': actual_distance,
                    'start_location': start_location,
                    'end_location': end_location,
                    'start_coords': data.get('start_coords'),
                    'end_coords': data.get('end_coords'),
                    'route': {
                        'start': data.get('start_coords', [52.0, 19.0]),
                        'end': data.get('end_coords', [50.0, 20.0]),
                        'route': []
                    },
                    # Dane z API
                    'exchange_rates': transform_to_ui_format(pricing, actual_distance, 30),
                    'exchange_rates_by_days': {
                        '7': transform_to_ui_format(pricing, actual_distance, 7),
                        '30': transform_to_ui_format(pricing, actual_distance, 30),
                        '90': transform_to_ui_format(pricing, actual_distance, 90)
                    },
                    'historical_rates': transform_historical(pricing),
                    'historical_rates_by_days': {
                        '7': transform_historical(pricing),
                        '30': transform_historical(pricing),
                        '90': transform_historical(pricing)
                    },
                    'historical_orders': get_all_historical_orders(backend_data),
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


def get_all_historical_orders(backend_data):
    """Pobierz wszystkie zlecenia historyczne z API"""
    # Zlecenia są w pricing.historical.180d.orders
    pricing = backend_data.get('pricing', {})
    historical = pricing.get('historical', {})
    period_180d = historical.get('180d', {})
    orders = period_180d.get('orders', [])
    
    print(f"📦 Orders znalezione: {len(orders) if orders else 0}")
    
    if not orders:
        return []
    
    # Przekształć zlecenia do formatu UI
    result = []
    for order in orders:
        # Formatuj datę do yyyy-mm-dd
        order_date = order.get('order_date', '')
        if order_date and 'T' in order_date:
            order_date = order_date.split('T')[0]  # Weź tylko część przed 'T'
        elif order_date and ' ' in order_date:
            order_date = order_date.split(' ')[0]  # Weź tylko część przed spacją
        
        result.append({
            'date': order_date,
            'carrier': order.get('carrier_name'),
            'type': order.get('order_type'),  # FTL lub LTL
            'cargo_type': order.get('cargo_type'),
            'rate_per_km': order.get('carrier_price_per_km'),
            'amount': order.get('carrier_amount'),
            'currency': order.get('carrier_currency', 'EUR'),
            'distance': order.get('route_distance') or order.get('distance'),
            'carrier_email': order.get('carrier_email'),
            'carrier_contact': order.get('carrier_contact')
        })
    
    print(f"✅ Przekształcono {len(result)} zleceń")
    return result


def transform_to_ui_format(pricing, distance, days):
    """Przekształć dane giełd z API do formatu UI"""
    period_key = f"{days}d"
    offers = []
    
    # API zwraca: 3_5t, 12t, trailer
    # Pokazujemy wszystkie typy
    
    # TimoCom
    timocom = pricing.get('timocom', {}).get(period_key, {})
    if timocom.get('avg_price_per_km'):
        avg_prices = timocom['avg_price_per_km']
        total_offers = timocom.get('total_offers', 0)
        offers_by_type = timocom.get('offers_by_vehicle_type', {})
        total_prices = timocom.get('total_price', {})
        
        # 3.5t
        if avg_prices.get('3_5t'):
            offers.append({
                'exchange': 'TimoCom',
                'vehicle_type': 'Do 3.5t',
                'rate_per_km': avg_prices['3_5t'],
                'total_price': total_prices.get('3_5t'),
                'currency': 'EUR',
                'has_data': True,
                'total_offers_sum': offers_by_type.get('3_5t', 0)
            })
        
        # 12t
        if avg_prices.get('12t'):
            offers.append({
                'exchange': 'TimoCom',
                'vehicle_type': 'Do 12t',
                'rate_per_km': avg_prices['12t'],
                'total_price': total_prices.get('12t'),
                'currency': 'EUR',
                'has_data': True,
                'total_offers_sum': offers_by_type.get('12t', 0)
            })
        
        # Naczepa (trailer)
        if avg_prices.get('trailer'):
            offers.append({
                'exchange': 'TimoCom',
                'vehicle_type': 'Naczepa',
                'rate_per_km': avg_prices['trailer'],
                'total_price': total_prices.get('trailer'),
                'currency': 'EUR',
                'has_data': True,
                'total_offers_sum': offers_by_type.get('trailer', 0)
            })
    
    # Trans.eu
    transeu = pricing.get('transeu', {}).get(period_key, {})
    if transeu.get('avg_price_per_km', {}).get('lorry'):
        offers.append({
            'exchange': 'Trans.eu',
            'vehicle_type': 'Lorry',
            'rate_per_km': transeu['avg_price_per_km']['lorry'],
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
    """Przekształć dane historyczne z API - osobno FTL i LTL"""
    historical = pricing.get('historical', {}).get('180d', {})
    ftl = historical.get('FTL')
    ltl = historical.get('LTL')
    
    result = {
        'has_data': False,
        'ftl': {'has_data': False, 'avg_rate_per_km': None, 'avg_amount': None, 'carriers': []},
        'ltl': {'has_data': False, 'avg_rate_per_km': None, 'avg_amount': None, 'carriers': []}
    }
    
    # FTL
    if ftl:
        ftl_carriers = []
        if ftl.get('top_carriers'):
            for c in ftl['top_carriers']:
                ftl_carriers.append({
                    'carrier': c.get('carrier_name'),
                    'rate_per_km': c.get('avg_carrier_price_per_km'),
                    'total_price': c.get('avg_carrier_amount'),
                    'currency': c.get('carrier_currency', 'EUR'),
                    'order_count': c.get('order_count', 0)
                })
        
        result['ftl'] = {
            'has_data': True,
            'avg_rate_per_km': ftl.get('avg_price_per_km', {}).get('carrier'),
            'avg_amount': ftl.get('total_price', {}).get('carrier'),  # Użyj total_price z API
            'carriers': ftl_carriers
        }
        result['has_data'] = True
    
    # LTL
    if ltl:
        ltl_carriers = []
        if ltl.get('top_carriers'):
            for c in ltl['top_carriers']:
                ltl_carriers.append({
                    'carrier': c.get('carrier_name'),
                    'rate_per_km': c.get('avg_carrier_price_per_km'),
                    'total_price': c.get('avg_carrier_amount'),
                    'currency': c.get('carrier_currency', 'EUR'),
                    'order_count': c.get('order_count', 0)
                })
        
        result['ltl'] = {
            'has_data': True,
            'avg_rate_per_km': ltl.get('avg_price_per_km', {}).get('carrier'),
            'avg_amount': ltl.get('total_price', {}).get('carrier'),  # Użyj total_price z API
            'carriers': ltl_carriers
        }
        result['has_data'] = True
    
    return result


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
