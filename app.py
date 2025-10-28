from flask import Flask, render_template, request, jsonify
import random
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Funkcja do generowania przykładowych współrzędnych trasy
def generate_route_coordinates(start_location, end_location):
    """Generuje przykładowe współrzędne trasy między lokalizacjami"""
    # Przykładowe współrzędne dla polskich miast
    cities = {
        'warszawa': [52.2297, 21.0122],
        'kraków': [50.0647, 19.9450],
        'poznań': [52.4064, 16.9252],
        'wrocław': [51.1079, 17.0385],
        'gdańsk': [54.3520, 18.6466],
        'katowice': [50.2649, 19.0238],
        'łódź': [51.7592, 19.4560],
        'szczecin': [53.4285, 14.5528],
        'berlin': [52.5200, 13.4050],
        'praga': [50.0755, 14.4378],
        'wiedeń': [48.2082, 16.3738],
        'budapeszt': [47.4979, 19.0402]
    }
    
    start_coords = cities.get(start_location.lower(), [52.0, 19.0])
    end_coords = cities.get(end_location.lower(), [50.0, 20.0])
    
    # Generowanie punktów pośrednich dla płynniejszej trasy
    route_points = [start_coords]
    steps = 5
    for i in range(1, steps):
        lat = start_coords[0] + (end_coords[0] - start_coords[0]) * i / steps
        lng = start_coords[1] + (end_coords[1] - start_coords[1]) * i / steps
        # Dodanie małego losowego odchylenia dla bardziej realistycznej trasy
        lat += random.uniform(-0.2, 0.2)
        lng += random.uniform(-0.2, 0.2)
        route_points.append([lat, lng])
    route_points.append(end_coords)
    
    return {
        'start': start_coords,
        'end': end_coords,
        'route': route_points
    }

# Funkcja do generowania przykładowych danych giełdowych
def generate_exchange_data(distance, days=7):
    """Generuje przykładowe dane ze stawkami giełdowymi dla określonej liczby dni"""
    base_rate = random.uniform(0.40, 0.55)  # EUR za km
    
    exchanges = ['Trans.eu', 'TimoCom', 'Teleroute', 'Transporeon']
    offers = []
    
    # Generuj po jednej ofercie dla każdej giełdy (bez duplikatów)
    for exchange in exchanges:
        rate_per_km = base_rate + random.uniform(-0.3, 0.3)
        total_price = rate_per_km * distance
        
        offers.append({
            'exchange': exchange,
            'rate_per_km': round(rate_per_km, 2),
            'total_price': round(total_price, 2),
            'currency': 'EUR',
            'date': (datetime.now() - timedelta(days=random.randint(0, days))).strftime('%Y-%m-%d')
        })
    
    avg_rate = sum(o['rate_per_km'] for o in offers) / len(offers)
    avg_total = sum(o['total_price'] for o in offers) / len(offers)
    
    # Oblicz liczbę ofert per dzień dla każdej giełdy
    for offer in offers:
        offer['offers_per_day'] = round(random.uniform(0.5, 3.0), 1)
    
    # Oblicz średnią liczbę ofert per dzień
    avg_offers_per_day = sum(o['offers_per_day'] for o in offers) / len(offers)
    
    return {
        'offers': offers,
        'average_rate_per_km': round(avg_rate, 2),
        'average_total_price': round(avg_total, 2),
        'average_offers_per_day': round(avg_offers_per_day, 1),
        'days': days
    }

# Funkcja do generowania historycznych danych firmowych
def generate_historical_data(distance, start_location, end_location, days=7):
    """Generuje przykładowe dane historyczne firmy dla określonej liczby dni"""
    # Losowa decyzja czy mamy dane historyczne dla tej trasy
    has_history = random.choice([True, True, False])
    
    if not has_history:
        return {
            'has_data': False,
            'orders': [],
            'average_rate_per_km': None,
            'average_total_price': None,
            'days': days
        }
    
    base_rate = random.uniform(0.45, 0.62)  # Stawki firmowe zwykle trochę wyższe (EUR za km)
    orders = []
    
    # Liczba zleceń zależy od okresu
    num_orders = min(random.randint(2, 8), days // 3)
    
    for i in range(max(2, num_orders)):
        rate_per_km = base_rate + random.uniform(-0.4, 0.4)
        total_price = rate_per_km * distance
        
        orders.append({
            'order_id': f'ORD-{random.randint(1000, 9999)}',
            'date': (datetime.now() - timedelta(days=random.randint(0, days))).strftime('%Y-%m-%d'),
            'carrier': f'Przewoźnik {random.choice(["A", "B", "C", "D", "E"])} Sp. z o.o.',
            'rate_per_km': round(rate_per_km, 2),
            'total_price': round(total_price, 2),
            'currency': 'EUR'
        })
    
    avg_rate = sum(o['rate_per_km'] for o in orders) / len(orders)
    avg_total = sum(o['total_price'] for o in orders) / len(orders)
    
    # Oblicz liczbę zleceń per dzień
    orders_per_day = round(len(orders) / days, 1)
    
    return {
        'has_data': True,
        'orders': orders,
        'average_rate_per_km': round(avg_rate, 2),
        'average_total_price': round(avg_total, 2),
        'orders_per_day': orders_per_day,
        'days': days
    }

# Funkcja do generowania danych o opłatach drogowych
def generate_toll_data(start_location, end_location, distance):
    """Generuje przykładowe dane o opłatach drogowych"""
    # Symulacja opłat w zależności od trasy
    tolls = []
    
    # Dodaj opłaty dla tras międzynarodowych
    countries = []
    if any(city in start_location.lower() or city in end_location.lower() 
           for city in ['berlin', 'praga', 'wiedeń', 'budapeszt']):
        countries = ['Polska', 'Niemcy'] if 'berlin' in (start_location + end_location).lower() else ['Polska']
    else:
        countries = ['Polska']
    
    total_toll = 0
    for country in countries:
        if country == 'Polska':
            toll_amount = distance * 0.067  # ~0.067 EUR/km dla pojazdów ciężarowych
            tolls.append({
                'country': country,
                'system': 'e-TOLL',
                'amount': round(toll_amount, 2),
                'currency': 'EUR'
            })
            total_toll += toll_amount
        elif country == 'Niemcy':
            toll_amount = distance * 0.19  # ~0.19 EUR/km
            tolls.append({
                'country': country,
                'system': 'Toll Collect',
                'amount': round(toll_amount, 2),
                'currency': 'EUR'
            })
            total_toll += toll_amount
    
    return {
        'tolls': tolls,
        'total_toll': round(total_toll, 2),
        'currency': 'EUR'
    }

# Funkcja do generowania sugerowanych przewoźników
def generate_carrier_suggestions(start_location, end_location):
    """Generuje listę sugerowanych przewoźników"""
    carrier_names = [
        'Trans-Logistics', 'Euro-Transport', 'Fast Cargo', 'Reliable Freight',
        'Express Delivery', 'Safe Transport', 'Quick Route', 'Prime Logistics',
        'Best Carriers', 'Global Transport'
    ]
    
    # Przewoźnicy historyczni (z którymi firma już współpracowała)
    historical_carriers = []
    num_historical = random.randint(2, 4)
    
    for i in range(num_historical):
        historical_carriers.append({
            'name': f'{random.choice(carrier_names)} Sp. z o.o.',
            'rating': round(random.uniform(4.0, 5.0), 1),
            'completed_orders': random.randint(5, 50),
            'avg_rate_per_km': round(random.uniform(0.49, 0.62), 2),
            'reliability': random.choice(['Wysoka', 'Bardzo wysoka']),
            'contact': f'+48 {random.randint(500, 799)} {random.randint(100, 999)} {random.randint(100, 999)}'
        })
    
    # Przewoźnicy z giełdy
    exchange_carriers = []
    num_exchange = random.randint(3, 6)
    
    for i in range(num_exchange):
        exchange_carriers.append({
            'name': f'{random.choice(carrier_names)} S.A.',
            'rating': round(random.uniform(3.5, 4.8), 1),
            'available_trucks': random.randint(1, 5),
            'avg_rate_per_km': round(random.uniform(0.40, 0.55), 2),
            'exchange': random.choice(['Trans.eu', 'TimoCom', 'Teleroute']),
            'response_time': f'{random.randint(1, 24)}h'
        })
    
    return {
        'historical': historical_carriers,
        'exchange': exchange_carriers
    }

@app.route('/')
def index():
    """Strona główna aplikacji"""
    return render_template('index.html')

@app.route('/api/calculate', methods=['POST'])
def calculate_route():
    """Endpoint do wyceny trasy"""
    data = request.json
    start_location = data.get('start_location', '')
    end_location = data.get('end_location', '')
    start_location_raw = data.get('start_location_raw', start_location)  # Faktyczny kod wpisany przez użytkownika
    end_location_raw = data.get('end_location_raw', end_location)  # Faktyczny kod wpisany przez użytkownika
    vehicle_type = data.get('vehicle_type', 'naczepa')
    body_type = data.get('body_type', 'standard')
    start_coords = data.get('start_coords')
    end_coords = data.get('end_coords')
    calculated_distance = data.get('calculated_distance')
    
    if not start_location or not end_location:
        return jsonify({'error': 'Brak wymaganych lokalizacji'}), 400
    
    # Użyj obliczonej odległości z frontendu lub wygeneruj dane trasy
    if start_coords and end_coords and calculated_distance:
        # Użyj rzeczywistych współrzędnych
        route_data = {
            'start': start_coords,
            'end': end_coords,
            'route': [start_coords, end_coords]  # Prosta linia między punktami
        }
        distance = calculated_distance
    else:
        # Fallback do starej metody
        route_data = generate_route_coordinates(start_location, end_location)
        distance = random.randint(200, 800)
    
    # Pobierz liczbę dni z zapytania (domyślnie 7)
    days = data.get('days', 7)
    
    # Generowanie danych dla wybranego okresu
    exchange_data = generate_exchange_data(distance, days)
    historical_data = generate_historical_data(distance, start_location, end_location, days)
    toll_data = generate_toll_data(start_location, end_location, distance)
    carriers = generate_carrier_suggestions(start_location, end_location)
    
    # Generowanie danych dla wszystkich okresów (do przełączania po stronie frontendu)
    exchange_data_7 = generate_exchange_data(distance, 7)
    exchange_data_30 = generate_exchange_data(distance, 30)
    exchange_data_90 = generate_exchange_data(distance, 90)
    
    historical_data_7 = generate_historical_data(distance, start_location, end_location, 7)
    historical_data_30 = generate_historical_data(distance, start_location, end_location, 30)
    historical_data_90 = generate_historical_data(distance, start_location, end_location, 90)
    
    result = {
        'route': route_data,
        'distance': distance,
        'start_location': start_location,
        'end_location': end_location,
        'start_location_raw': start_location_raw,
        'end_location_raw': end_location_raw,
        'vehicle_type': vehicle_type,
        'body_type': body_type,
        'exchange_rates': exchange_data,
        'historical_rates': historical_data,
        'tolls': toll_data,
        'suggested_carriers': carriers,
        # Dane dla wszystkich okresów
        'exchange_rates_by_days': {
            '7': exchange_data_7,
            '30': exchange_data_30,
            '90': exchange_data_90
        },
        'historical_rates_by_days': {
            '7': historical_data_7,
            '30': historical_data_30,
            '90': historical_data_90
        }
    }
    
    return jsonify(result)

if __name__ == '__main__':
    # Pobierz port z zmiennej środowiskowej (dla Render) lub użyj 5000 lokalnie
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
