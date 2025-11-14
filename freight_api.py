"""
Moduł do komunikacji z API giełd (TimoCom, Trans.eu)
Używane dla trybu "teraz" - pobiera aktualne oferty na podstawie realnych adresów
"""

import os
import requests
import base64
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()

class TimocomAPI:
    """Klient API TimoCom"""
    
    def __init__(self):
        self.username = os.getenv('TIMOCOM_USERNAME')
        self.password = os.getenv('TIMOCOM_PASSWORD')
        self.base_url = os.getenv('TIMOCOM_API_URL', 'https://api.timocom.com')
        self.api_url = f"{self.base_url}/freight-exchange/3"
        
    def _get_headers(self) -> Dict[str, str]:
        """Generuje nagłówki z Basic Auth"""
        if not self.username or not self.password:
            raise ValueError("Brak credentials dla TimoCom")
        
        credentials = f"{self.username}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        return {
            'Authorization': f'Basic {encoded}',
            'Content-Type': 'application/json'
        }
    
    def search_freight_offers(
        self,
        start_location: str,
        end_location: str,
        limit: int = 30,
        start_coords: list = None,
        end_coords: list = None
    ) -> Dict[str, Any]:
        """
        Wyszukuje oferty frachtu na podstawie lokalizacji
        
        Args:
            start_location: Adres startowy (np. "Warsaw, Poland" lub kod pocztowy)
            end_location: Adres docelowy
            limit: Maksymalna liczba wyników
            start_coords: Współrzędne startu [lat, lng]
            end_coords: Współrzędne celu [lat, lng]
            
        Returns:
            Słownik z ofertami
        """
        # Walidacja lokalizacji
        if not start_location or not start_location.strip():
            print(f"❌ TimoCom: Brak lokalizacji startowej")
            return {
                'success': False,
                'error': 'Empty start_location',
                'offers': []
            }
        
        if not end_location or not end_location.strip():
            print(f"❌ TimoCom: Brak lokalizacji docelowej")
            return {
                'success': False,
                'error': 'Empty end_location',
                'offers': []
            }
        
        try:
            url = f"{self.api_url}/freight-offers/search"
            
            # Parametry wyszukiwania - TimoCom wymaga konkretnej struktury
            # Parsuj adres na części
            def parse_address(location_str):
                """Parsuje 'kod_pocztowy miasto, kraj' na komponenty"""
                parts = location_str.split(',')
                if len(parts) >= 2:
                    city_postal = parts[0].strip()
                    country = parts[1].strip()
                    
                    # Spróbuj wyciągnąć kod pocztowy
                    import re
                    match = re.match(r'^([\d\-]+)\s+(.+)$', city_postal)
                    if match:
                        postal = match.group(1)
                        city = match.group(2)
                    else:
                        postal = ''
                        city = city_postal
                    
                    return {'postal_code': postal, 'city': city, 'country': country}
                
                return {'postal_code': '', 'city': location_str, 'country': ''}
            
            origin_parsed = parse_address(start_location)
            dest_parsed = parse_address(end_location)
            
            # Konwersja nazw krajów na kody ISO (TimoCom wymaga tego)
            country_to_iso = {
                'Poland': 'PL', 'Germany': 'DE', 'France': 'FR', 'Spain': 'ES', 'Italy': 'IT',
                'United Kingdom': 'GB', 'Netherlands': 'NL', 'Belgium': 'BE', 'Austria': 'AT',
                'Czech Republic': 'CZ', 'Slovakia': 'SK', 'Hungary': 'HU', 'Romania': 'RO',
                'Bulgaria': 'BG', 'Croatia': 'HR', 'Slovenia': 'SI', 'Lithuania': 'LT',
                'Latvia': 'LV', 'Estonia': 'EE', 'Denmark': 'DK', 'Sweden': 'SE',
                'Norway': 'NO', 'Finland': 'FI', 'Portugal': 'PT', 'Ireland': 'IE',
                'Switzerland': 'CH', 'Luxembourg': 'LU', 'Greece': 'GR'
            }
            
            origin_country = country_to_iso.get(origin_parsed['country'], origin_parsed['country'])
            dest_country = country_to_iso.get(dest_parsed['country'], dest_parsed['country'])
            
            # Użyj współrzędnych z parametrów lub domyślnych przybliżonych
            if start_coords and len(start_coords) == 2:
                origin_lat = start_coords[0]
                origin_lng = start_coords[1]
            else:
                # Przybliżone współrzędne jako fallback
                origin_lat = 52.0 if origin_country == 'PL' else 51.0
                origin_lng = 19.0 if origin_country == 'PL' else 10.0
                print(f"⚠️  Używam przybliżonych współrzędnych dla startu: {origin_lat}, {origin_lng}")
            
            if end_coords and len(end_coords) == 2:
                dest_lat = end_coords[0]
                dest_lng = end_coords[1]
            else:
                # Przybliżone współrzędne jako fallback
                dest_lat = 52.0 if dest_country == 'PL' else 51.0
                dest_lng = 19.0 if dest_country == 'PL' else 10.0
                print(f"⚠️  Używam przybliżonych współrzędnych dla celu: {dest_lat}, {dest_lng}")
            
            # TimoCom API format (zgodny z dokumentacją)
            from datetime import datetime, timedelta
            today = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            
            # Parametr inclusiveRightUpperBoundDateTime - 4 godziny wstecz od teraz
            # Format: ISO 8601 z UTC timezone
            upper_bound_time = (datetime.utcnow() - timedelta(hours=4)).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            payload = {
                "sortings": [
                    {
                        "ascending": True,
                        "field": "creationDateTime"
                    }
                ],
                "inclusiveRightUpperBoundDateTime": upper_bound_time,
                "startLocation": {
                    "objectType": "areaSearch",
                    "area": {
                        "address": {
                            "objectType": "address",
                            "city": origin_parsed['city'],
                            "country": origin_country,
                            "geoCoordinate": {
                                "latitude": origin_lat,
                                "longitude": origin_lng
                            },
                            "postalCode": origin_parsed['postal_code']
                        },
                        "size_km": 50  # Promień wyszukiwania 50 km
                    }
                },
                "destinationLocation": {
                    "objectType": "areaSearch",
                    "area": {
                        "address": {
                            "objectType": "address",
                            "city": dest_parsed['city'],
                            "country": dest_country,
                            "geoCoordinate": {
                                "latitude": dest_lat,
                                "longitude": dest_lng
                            },
                            "postalCode": dest_parsed['postal_code']
                        },
                        "size_km": 50  # Promień wyszukiwania 50 km
                    }
                },
                "loadingDate": {
                    "objectType": "dateInterval",
                    "start": today,
                    "end": end_date
                },
                "firstResult": 0,
                "maxResults": 30  # Pobieramy 30 na stronę
            }
            
            print(f"🔄 TimoCom API: Zapytanie {start_location} -> {end_location}")
            print(f"   📅 Przedział czasowy: oferty utworzone przed {upper_bound_time} (4h wstecz)")
            print(f"   📅 Data załadunku: {today} do {end_date}")
            print(f"   📍 Start: {origin_parsed['city']}, {origin_country} ({origin_lat}, {origin_lng})")
            print(f"   📍 Cel: {dest_parsed['city']}, {dest_country} ({dest_lat}, {dest_lng})")
            
            # PAGINACJA - pobierz kolejne strony aż mamy wystarczająco ofert z cenami
            all_offers = []
            offers_with_price = 0
            max_pages = 5  # Maksymalnie 5 stron (150 ofert)
            page = 0
            
            while page < max_pages and offers_with_price < 20:  # Zbieramy do 20 ofert z ceną
                payload['firstResult'] = page * 30
                
                print(f"   📄 Strona {page + 1} (firstResult={payload['firstResult']})")
                
                response = requests.post(
                    url,
                    json=payload,
                    headers=self._get_headers(),
                    timeout=15
                )
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                page_offers = data.get('payload', [])
                
                if not page_offers:  # Brak więcej ofert
                    break
                
                # Policz ile ofert ma cenę na tej stronie
                offers_with_price_on_page = sum(1 for o in page_offers 
                    if isinstance(o.get('price', {}), dict) and o.get('price', {}).get('amount', 0) > 0)
                
                print(f"   ✓ Znaleziono {len(page_offers)} ofert ({offers_with_price_on_page} z ceną)")
                
                all_offers.extend(page_offers)
                offers_with_price += offers_with_price_on_page
                page += 1
            
            print(f"✓ TimoCom: Łącznie {len(all_offers)} ofert z {page} stron ({offers_with_price} z ceną)")
            
            # Logowanie struktury pierwszej oferty dla debugowania
            if all_offers and len(all_offers) > 0:
                print(f"   📦 Przykładowa oferta (klucze): {list(all_offers[0].keys())}")
                if 'price' in all_offers[0]:
                    print(f"   💰 Cena: {all_offers[0]['price']}")
            
            return {
                'success': True,
                'offers': all_offers,
                'count': len(all_offers)
            }
                
        except Exception as e:
            print(f"❌ TimoCom API exception: {e}")
            return {
                'success': False,
                'error': str(e),
                'offers': []
            }


class TranseuAPI:
    """Klient API Trans.eu - używa stałego tokenu z env zamiast OAuth"""
    
    def __init__(self):
        # Użyj TRANSEU_TOKEN jako Bearer token i TRANSEU_API_KEY jako Api-key
        self.token = os.getenv('TRANSEU_TOKEN', '')  # JWT Bearer token
        self.api_key = os.getenv('TRANSEU_API_KEY', '')  # Api-key header
        self.base_url = 'https://api.platform.trans.eu'  # Nowa platforma
    
    def search_freight_offers(
        self,
        start_location: str,
        end_location: str,
        limit: int = 30,
        start_coords: list = None,
        end_coords: list = None
    ) -> Dict[str, Any]:
        """
        Wyszukuje oferty frachtu na podstawie lokalizacji
        
        Args:
            start_location: Adres startowy
            end_location: Adres docelowy
            limit: Maksymalna liczba wyników
            start_coords: Współrzędne startu [lat, lng]
            end_coords: Współrzędne celu [lat, lng]
            
        Returns:
            Słownik z ofertami
        """
        print(f"🔄 Trans.eu API: Zapytanie {start_location} -> {end_location}")
        
        # Sprawdź czy mamy token i API key
        if not self.token:
            print(f"⚠️  Brak TRANSEU_TOKEN w zmiennych środowiskowych")
            return {
                'success': False,
                'error': 'Missing TRANSEU_TOKEN',
                'offers': []
            }
        
        if not self.api_key:
            print(f"⚠️  Brak TRANSEU_API_KEY w zmiennych środowiskowych")
            return {
                'success': False,
                'error': 'Missing TRANSEU_API_KEY',
                'offers': []
            }
        
        try:
            # Endpoint wyszukiwania ofert (v2 API)
            endpoint = '/ext/offers-api/v2/offers'
            
            # Format Trans.eu v2 API - WYMAGANE współrzędne (zgodnie z przykładem)
            if not start_coords or not end_coords:
                print(f"⚠️  Brak współrzędnych dla Trans.eu API")
                return {
                    'success': False,
                    'error': 'Missing coordinates for Trans.eu API',
                    'offers': []
                }
            
            filter_params = {
                "loading_place": {
                    "coordinates": {
                        "latitude": start_coords[0],
                        "longitude": start_coords[1],
                        "range": 125
                    }
                },
                "unloading_place": {
                    "coordinates": {
                        "latitude": end_coords[0],
                        "longitude": end_coords[1],
                        "range": 125
                    }
                },
                "required_truck_body": [
                    "curtainsider",
                    "standard-tent",
                    "box",
                    "open-box",
                    "mega",
                    "low-loader",
                    "truck"
                ],
                "required_vehicle_size": ["lorry"],
                "transport_type": ["ftl"]  # Tylko FTL
            }
            
            # Serializuj filter jako JSON w query string
            import json
            import urllib.parse
            import requests
            
            # Logowanie parametrów zapytania
            print(f"   📍 Loading: {start_coords[0]}, {start_coords[1]} (radius: 125km)")
            print(f"   📍 Unloading: {end_coords[0]}, {end_coords[1]} (radius: 125km)")
            
            # Serializuj JSON BEZ SPACJI i z ensure_ascii=False
            filter_json = json.dumps(filter_params, separators=(',', ':'), ensure_ascii=False)
            print(f"   🔍 Filter JSON: {filter_json}")
            
            # Użyj quote_plus dla prawidłowego enkodowania
            from urllib.parse import quote
            full_url = f"{self.base_url}{endpoint}?filter={quote(filter_json)}"
            print(f"   🌐 Full URL: {full_url}")
            
            # Headers zgodnie z przykładem - Bearer token + Api-key
            headers = {
                'Authorization': f'Bearer {self.token}',  # TRANSEU_TOKEN jako Bearer (JWT)
                'Api-key': self.api_key,  # TRANSEU_API_KEY jako Api-key header
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                full_url,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                offers = data.get('items', data.get('loads', []))
                print(f"✓ Trans.eu: Znaleziono {len(offers)} ofert")
                return {
                    'success': True,
                    'offers': offers,
                    'count': len(offers)
                }
            else:
                error_detail = response.text if response.text else 'No details'
                print(f"⚠ Trans.eu API error: {response.status_code}")
                print(f"   URL: {full_url[:200]}...")
                print(f"   Response: {error_detail}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'details': error_detail,
                    'offers': []
                }
                
        except Exception as e:
            print(f"❌ Trans.eu API exception: {e}")
            return {
                'success': False,
                'error': str(e),
                'offers': []
            }


def get_current_offers(
    start_location: str,
    end_location: str,
    distance: float,
    start_coords: list = None,
    end_coords: list = None
) -> Dict[str, Any]:
    """
    Pobiera aktualne oferty z obu giełd dla trybu "teraz"
    
    Args:
        start_location: Adres startowy (np. "50-340, Wrocław, Poland")
        end_location: Adres docelowy
        distance: Dystans w km
        start_coords: Współrzędne startu [lat, lng]
        end_coords: Współrzędne celu [lat, lng]
        
    Returns:
        Słownik z ofertami z obu giełd
    """
    print(f"\n🌐 Pobieranie aktualnych ofert z API giełd")
    print(f"   Start: '{start_location}' (coords: {start_coords})")
    print(f"   Cel: '{end_location}' (coords: {end_coords})")
    print(f"   Dystans: {distance} km")
    
    # Walidacja
    if not start_location or not end_location:
        print(f"❌ BŁĄD: Puste lokalizacje!")
        return {
            'has_data': False,
            'offers': [],
            'message': 'Puste lokalizacje start lub end',
            'data_source': 'live_api'
        }
    
    # Inicjalizuj klientów API
    timocom = TimocomAPI()
    transeu = TranseuAPI()
    
    # Pobierz oferty z obu giełd - przekaż współrzędne
    # TimoCom używa wewnętrznej paginacji (zbiera do 20 ofert z ceną)
    timocom_result = timocom.search_freight_offers(
        start_location, end_location, 
        limit=30,  # Parametr nie używany - paginacja wewnętrzna
        start_coords=start_coords,
        end_coords=end_coords
    )
    transeu_result = transeu.search_freight_offers(
        start_location, end_location, 
        limit=30,
        start_coords=start_coords,
        end_coords=end_coords
    )
    
    # Agreguj wyniki
    all_offers = []
    
    # Przetworz oferty TimoCom
    skipped_offers = 0
    if timocom_result['success'] and timocom_result['offers']:
        print(f"   🔄 Przetwarzanie {len(timocom_result['offers'])} ofert TimoCom...")
        for idx, offer in enumerate(timocom_result['offers']):
            # TimoCom API może zwracać różne struktury - sprawdźmy co mamy
            # Możliwe struktury:
            # 1. offer['price']['amount'] i offer['distance_km']
            # 2. offer['pricePerKm'] bezpośrednio
            
            price_obj = offer.get('price', {})
            if isinstance(price_obj, dict):
                total_price = price_obj.get('amount', 0)
                currency = price_obj.get('currency', 'EUR')
            else:
                total_price = offer.get('total_price', 0)
                currency = offer.get('currency', 'EUR')
            
            distance_km = offer.get('distance_km', distance)
            rate_per_km = (total_price / distance_km) if distance_km > 0 else 0
            
            # Loguj pierwszą ofertę dla debugowania
            if idx == 0:
                print(f"   📦 TimoCom oferta #1: price={total_price} {currency}, distance={distance_km}km, rate={rate_per_km:.2f} EUR/km")
            
            # POMIŃ oferty bez ceny (cena = 0 lub brak)
            if total_price <= 0 or rate_per_km <= 0:
                skipped_offers += 1
                continue
            
            # Konwertuj format API na format aplikacji
            all_offers.append({
                'exchange': 'TimoCom',
                'rate_per_km': round(rate_per_km, 2),
                'total_price': round(total_price, 2),
                'currency': currency,
                'vehicle_type': offer.get('vehicleType', 'N/A'),
                'loading_date': offer.get('loadingDate', 'N/A'),
                'has_data': True,
                'raw_data': offer  # Zachowaj surowe dane
            })
        
        if skipped_offers > 0:
            print(f"   ⚠️  Pominięto {skipped_offers} ofert bez ceny z TimoCom")
    
    # Przetworz oferty Trans.eu
    if transeu_result['success'] and transeu_result['offers']:
        for offer in transeu_result['offers']:
            rate_per_km = offer.get('pricePerKm', 0) if distance > 0 else 0
            total_price = offer.get('price', 0)
            
            # POMIŃ oferty bez ceny (cena = 0 lub brak)
            if total_price <= 0 or rate_per_km <= 0:
                continue
            
            all_offers.append({
                'exchange': 'Trans.eu',
                'rate_per_km': round(rate_per_km, 2),
                'total_price': round(total_price, 2),
                'currency': offer.get('currency', 'EUR'),
                'vehicle_type': offer.get('vehicleType', 'N/A'),
                'loading_date': offer.get('loadingDate', 'N/A'),
                'has_data': True,
                'raw_data': offer
            })
    
    # Oblicz statystyki
    if all_offers:
        rates = [o['rate_per_km'] for o in all_offers if o['rate_per_km'] > 0]
        totals = [o['total_price'] for o in all_offers if o['total_price'] > 0]
        
        avg_rate = sum(rates) / len(rates) if rates else 0
        avg_total = sum(totals) / len(totals) if totals else 0
        
        print(f"\n✓ Pobrano łącznie {len(all_offers)} aktualnych ofert")
        print(f"   TimoCom: {len([o for o in all_offers if o['exchange'] == 'TimoCom'])} ofert")
        print(f"   Trans.eu: {len([o for o in all_offers if o['exchange'] == 'Trans.eu'])} ofert")
        print(f"   Średnia stawka: {avg_rate:.2f} EUR/km")
        
        return {
            'has_data': True,
            'offers': all_offers,
            'average_rate_per_km': round(avg_rate, 2),
            'average_total_price': round(avg_total, 2),
            'total_count': len(all_offers),
            'timocom_count': len([o for o in all_offers if o['exchange'] == 'TimoCom']),
            'transeu_count': len([o for o in all_offers if o['exchange'] == 'Trans.eu']),
            'data_source': 'live_api'
        }
    else:
        print(f"\n⚠ Brak aktualnych ofert dla tej trasy")
        
        return {
            'has_data': False,
            'offers': [],
            'average_rate_per_km': None,
            'average_total_price': None,
            'total_count': 0,
            'message': 'Brak aktualnych ofert dla tej trasy',
            'data_source': 'live_api'
        }


if __name__ == '__main__':
    # Test
    result = get_current_offers(
        "50-340, Wrocław, Poland",
        "08034, Barcelona, Spain",
        1500
    )
    print(f"\nWynik: {result}")
