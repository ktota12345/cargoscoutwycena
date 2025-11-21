// Inicjalizacja mapy
let map;
let routeLayer;

// Inicjalizacja systemu wyszukiwania kodów pocztowych
let postalSearch;
let selectedStartRegion = null;
let selectedEndRegion = null;

// Przechowywanie danych dla różnych okresów
let currentRouteData = null;
let selectedDays = 7;
let isNowMode = false; // Tryb "teraz"
let nowDataLoaded = false; // Czy dane "teraz" zostały już załadowane dla tego wyszukiwania
let cachedNowData = null; // Przechowuj dane live z trybu "teraz"

// Lokalne dane kodów pocztowych
let postalCodesData = null;

// Inicjalizacja przy załadowaniu strony
document.addEventListener('DOMContentLoaded', async function() {
    // Inicjalizacja PostalCodeSearch (ładuje wszystkie dane regionów)
    await initializePostalSearch();
    
    // Inicjalizacja przycisków rozwijanych (raz na start)
    initializeToggleButtons();
    
    // Obsługa formularza
    document.getElementById('routeForm').addEventListener('submit', handleFormSubmit);
    
    // Obsługa zmiany typu samochodu
    const vehicleTypeSelect = document.getElementById('vehicleType');
    const bodyTypeContainer = document.getElementById('bodyTypeContainer');
    
    // Funkcja do pokazywania/ukrywania pola nadwozia
    function toggleBodyTypeVisibility() {
        if (vehicleTypeSelect.value === 'naczepa') {
            bodyTypeContainer.style.display = 'block';
        } else {
            bodyTypeContainer.style.display = 'none';
        }
    }
    
    // Ustawienie początkowej widoczności (domyślnie naczepa jest wybrana)
    toggleBodyTypeVisibility();
    
    // Dodanie nasłuchiwania na zmianę typu samochodu
    vehicleTypeSelect.addEventListener('change', toggleBodyTypeVisibility);
    
    // Inicjalizacja autocomplete dla lokalizacji
    setupAutocomplete('startLocation', 'startLocationSuggestions', (region) => {
        selectedStartRegion = region;
    });
    
    setupAutocomplete('endLocation', 'endLocationSuggestions', (region) => {
        selectedEndRegion = region;
    });
    
    // Ukryj sugestie po kliknięciu poza nimi
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.position-relative')) {
            document.querySelectorAll('.autocomplete-suggestions').forEach(el => {
                el.classList.remove('show');
            });
        }
    });
});

// Inicjalizacja systemu wyszukiwania kodów pocztowych
async function initializePostalSearch() {
    try {
        console.log('Inicjalizacja PostalCodeSearch...');
        postalSearch = new PostalCodeSearch();
        const success = await postalSearch.initialize(
            '/static/data/voronoi_regions.geojson',
            '/static/data/postal_code_to_region_transeu.json'
        );
        
        if (success) {
            console.log('✓ PostalCodeSearch zainicjalizowany pomyślnie');
            const stats = postalSearch.getStats();
            console.log(`✓ Załadowano ${stats.totalRegions} regionów w ${stats.countries.length} krajach`);
        } else {
            console.error('✗ Błąd inicjalizacji PostalCodeSearch');
        }
        
        // Załaduj lokalne dane kodów pocztowych
        console.log('Ładowanie lokalnych kodów pocztowych...');
        const postalCodesResponse = await fetch('/static/data/filtered_postal_codes.geojson');
        if (postalCodesResponse.ok) {
            postalCodesData = await postalCodesResponse.json();
            console.log(`✓ Załadowano ${postalCodesData.features.length} kodów pocztowych`);
        } else {
            console.error('✗ Nie udało się załadować kodów pocztowych');
        }
    } catch (error) {
        console.error('✗ Błąd podczas inicjalizacji PostalCodeSearch:', error);
    }
}

// Konfiguracja autocomplete dla pola wejściowego
function setupAutocomplete(inputId, suggestionsId, onSelect) {
    const input = document.getElementById(inputId);
    const suggestionsContainer = document.getElementById(suggestionsId);
    let debounceTimer;
    
    input.addEventListener('input', function(e) {
        clearTimeout(debounceTimer);
        const query = e.target.value.trim();
        
        if (query.length < 2) {
            // Nie pokazuj sugestii (wyłączone)
            // suggestionsContainer.classList.remove('show');
            return;
        }
        
        debounceTimer = setTimeout(() => {
            // Mechanizm działa w tle, ale bez wyświetlania sugestii
            // showSuggestions(query, suggestionsContainer, input, onSelect);
        }, 300);
    });
    
    input.addEventListener('focus', function(e) {
        const query = e.target.value.trim();
        if (query.length >= 2) {
            // Nie pokazuj sugestii (wyłączone)
            // showSuggestions(query, suggestionsContainer, input, onSelect);
        }
    });
    
    // Obsługa klawiatury (strzałki i Enter) - wyłączone
    input.addEventListener('keydown', function(e) {
        // Obsługa klawiszy wyłączona - sugestie nie są wyświetlane
        if (e.key === 'Escape') {
            suggestionsContainer.classList.remove('show');
        }
    });
}

// Wyświetlanie sugestii
function showSuggestions(query, container, input, onSelect) {
    if (!postalSearch || !postalSearch.initialized) {
        container.innerHTML = '<div class="autocomplete-loading">Ładowanie danych...</div>';
        container.classList.add('show');
        return;
    }
    
    const results = postalSearch.search(query, 10);
    
    if (results.length === 0) {
        container.innerHTML = '<div class="autocomplete-no-results">Nie znaleziono regionów</div>';
        container.classList.add('show');
        return;
    }
    
    let html = '';
    results.forEach(region => {
        const cityName = region.properties.city_name || '';
        const countryName = getCountryName(region.properties.country);
        
        html += `
            <div class="autocomplete-item" data-region-id="${region.id}">
                <div class="autocomplete-code">${region.identifier}</div>
                <div class="autocomplete-details">
                    <span class="autocomplete-country">${countryName}</span>
                    ${cityName}
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
    container.classList.add('show');
    
    // Dodanie event listenerów do itemów
    container.querySelectorAll('.autocomplete-item').forEach(item => {
        item.addEventListener('click', function() {
            const regionId = parseInt(this.dataset.regionId);
            const region = postalSearch.getRegionById(regionId);
            
            if (region) {
                input.value = region.identifier;
                onSelect(region);
                container.classList.remove('show');
            }
        });
    });
}

// Mapowanie kodów krajów na nazwy
function getCountryName(code) {
    const countries = {
        'PL': 'Polska', 'DE': 'Niemcy', 'FR': 'Francja', 'ES': 'Hiszpania',
        'IT': 'Włochy', 'GB': 'W. Brytania', 'NL': 'Holandia', 'BE': 'Belgia',
        'AT': 'Austria', 'CZ': 'Czechy', 'SK': 'Słowacja', 'HU': 'Węgry',
        'RO': 'Rumunia', 'BG': 'Bułgaria', 'PT': 'Portugalia', 'GR': 'Grecja',
        'DK': 'Dania', 'SE': 'Szwecja', 'NO': 'Norwegia', 'FI': 'Finlandia',
        'CH': 'Szwajcaria', 'HR': 'Chorwacja', 'SI': 'Słowenia', 'LT': 'Litwa',
        'LV': 'Łotwa', 'EE': 'Estonia', 'IE': 'Irlandia', 'LU': 'Luksemburg'
    };
    return countries[code] || code;
}

// Normalizacja kodu pocztowego do formatu używanego w systemie
// Przykłady: PL50123 -> PL50, PL50-340 -> PL50, DE10115 -> DE10
function normalizePostalCodeForSearch(postalCode) {
    if (!postalCode) return '';
    
    // Usuń spacje, myślniki i inne znaki specjalne
    const cleaned = postalCode.toUpperCase().replace(/[^A-Z0-9]/g, '');
    
    // Wyciągnij kod kraju (pierwsze 2 litery) i pierwsze 2 cyfry
    const match = cleaned.match(/^([A-Z]{2})(\d{2})/);
    
    if (match) {
        return match[1] + match[2]; // np. PL50, DE10
    }
    
    // Jeśli nie pasuje do wzorca, zwróć oryginał (dla kompatybilności wstecznej)
    return cleaned.substring(0, 4);
}

// Geokodowanie kodu pocztowego do precyzyjnych współrzędnych używając lokalnych danych
async function geocodePostalCode(postalCode) {
    if (!postalCode || !postalCodesData) return null;
    
    try {
        // Wyciągnij kod kraju i pierwsze 2 cyfry kodu pocztowego
        let country = '';
        let cleanPostalCode = postalCode.toUpperCase().trim();
        
        // Spróbuj wyodrębnić kod kraju (pierwsze 2 litery)
        const countryMatch = cleanPostalCode.match(/^([A-Z]{2})/);
        if (countryMatch) {
            country = countryMatch[1];
            // Usuń kod kraju z kodu pocztowego
            cleanPostalCode = cleanPostalCode.substring(2);
        }
        
        // Usuń wszystko oprócz cyfr i myślników
        cleanPostalCode = cleanPostalCode.replace(/[^0-9\-]/g, '').trim();
        
        // Weź pierwsze 2 cyfry (bo tak są w pliku)
        const postalPrefix = cleanPostalCode.substring(0, 2);
        
        // Jeśli nie ma kodu pocztowego, zwróć null
        if (!postalPrefix || postalPrefix.length < 2) {
            console.warn(`   ✗ Nie można wyodrębnić kodu pocztowego z: ${postalCode}`);
            return null;
        }
        
        console.log(`   🔍 Szukam lokalnie: ${country}${postalPrefix}`);
        
        // Szukaj w lokalnych danych
        const found = postalCodesData.features.find(feature => 
            feature.properties.country_code === country && 
            feature.properties.postal_code === postalPrefix
        );
        
        if (found) {
            const coords = found.geometry.coordinates; // [lng, lat]
            console.log(`   ✓ Znaleziono lokalnie: ${country}-${postalPrefix}`);
            console.log(`   📍 Współrzędne: [${coords[0].toFixed(4)}, ${coords[1].toFixed(4)}]`);
            return coords;
        }
        
        console.warn(`   ✗ Brak danych dla: ${country}-${postalPrefix}`);
        return null;
        
    } catch (error) {
        console.error('   ✗ Błąd geokodowania:', error);
        return null;
    }
}

// Obsługa wysłania formularza
async function handleFormSubmit(e) {
    e.preventDefault();
    
    const startLocationRaw = document.getElementById('startLocation').value.trim();
    const endLocationRaw = document.getElementById('endLocation').value.trim();
    const vehicleType = document.getElementById('vehicleType').value;
    const bodyType = vehicleType === 'naczepa' ? document.getElementById('bodyType').value : null;
    
    if (!startLocationRaw || !endLocationRaw) {
        alert('Proszę podać obie lokalizacje');
        return;
    }
    
    // Normalizuj kody pocztowe do formatu używanego w systemie (np. PL50123 -> PL50)
    const startLocationNormalized = normalizePostalCodeForSearch(startLocationRaw);
    const endLocationNormalized = normalizePostalCodeForSearch(endLocationRaw);
    
    // Jeśli regiony nie zostały wybrane z listy, spróbuj je znaleźć używając znormalizowanych kodów
    if (!selectedStartRegion && postalSearch) {
        selectedStartRegion = postalSearch.findRegionByPostalCode(startLocationNormalized);
    }
    if (!selectedEndRegion && postalSearch) {
        selectedEndRegion = postalSearch.findRegionByPostalCode(endLocationNormalized);
    }
    
    // Sprawdź czy udało się znaleźć regiony
    if (!selectedStartRegion || !selectedEndRegion) {
        alert('Nie można znaleźć regionów dla podanych kodów. Użyj formatu: kod kraju + cyfry (np. PL50, PL50-340, DE10)');
        return;
    }
    
    // Pokazanie spinnera
    document.getElementById('loadingSpinner').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    
    try {
        // Geokoduj faktyczne kody pocztowe do precyzyjnych współrzędnych
        console.log('🔍 Geokodowanie kodów pocztowych...');
        console.log(`   Start: ${startLocationRaw} (region: ${selectedStartRegion.identifier})`);
        console.log(`   Koniec: ${endLocationRaw} (region: ${selectedEndRegion.identifier})`);
        
        const startPreciseCoords = await geocodePostalCode(startLocationRaw);
        const endPreciseCoords = await geocodePostalCode(endLocationRaw);
        
        // Użyj precyzyjnych współrzędnych jeśli są dostępne, w przeciwnym razie centroidy regionów
        const startFinalCoords = startPreciseCoords || selectedStartRegion.centroid.geometry.coordinates;
        const endFinalCoords = endPreciseCoords || selectedEndRegion.centroid.geometry.coordinates;
        
        if (startPreciseCoords && endPreciseCoords) {
            console.log('✓ Geokodowanie zakończone pomyślnie dla obu lokalizacji');
        } else {
            if (!startPreciseCoords) {
                console.warn('⚠ Geokodowanie nie powiodło się dla startu - używam centroidu regionu');
            }
            if (!endPreciseCoords) {
                console.warn('⚠ Geokodowanie nie powiodło się dla końca - używam centroidu regionu');
            }
        }
        
        // Oblicz odległość Haversine (w linii prostej) jako fallback
        const haversineDistance = turf.distance(
            turf.point(startFinalCoords),
            turf.point(endFinalCoords),
            { units: 'kilometers' }
        );
        
        console.log(`📏 Odległość Haversine: ${Math.round(haversineDistance)} km`);
        
        // Wywołaj AWS Location Service API dla rzeczywistego dystansu drogowego
        let distance = haversineDistance;
        let distanceMethod = 'haversine';
        let awsRouteGeometry = null;
        let awsRouteDuration = null;
        
        try {
            console.log('🌐 Wywołuję AWS Location Service API...');
            const distanceResponse = await fetch('/api/calculate-distance', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    start_coords: [startFinalCoords[1], startFinalCoords[0]], // [lat, lng]
                    end_coords: [endFinalCoords[1], endFinalCoords[0]],       // [lat, lng]
                    fallback_distance: Math.round(haversineDistance),
                    include_geometry: true  // Poproś o geometrię trasy
                })
            });
            
            if (distanceResponse.ok) {
                const distanceData = await distanceResponse.json();
                if (distanceData.success) {
                    distance = distanceData.distance;
                    distanceMethod = distanceData.method;
                    
                    if (distanceMethod === 'aws') {
                        console.log(`✅ Dystans AWS (rzeczywisty drogowy): ${Math.round(distance)} km`);
                        
                        // Zapisz geometrię trasy jeśli jest dostępna
                        if (distanceData.geometry && distanceData.geometry.length > 0) {
                            awsRouteGeometry = distanceData.geometry;
                            awsRouteDuration = distanceData.duration;
                            console.log(`✅ Pobrano geometrię trasy AWS: ${awsRouteGeometry.length} punktów`);
                            console.log(`⏱️  Czas przejazdu: ${Math.round(awsRouteDuration / 60)} minut`);
                        }
                    } else {
                        console.log(`⚠️  AWS niedostępny - używam Haversine: ${Math.round(distance)} km`);
                    }
                }
            }
        } catch (error) {
            console.warn('⚠️  Błąd AWS API - używam Haversine:', error);
        }
        
        // Buduj pełne adresy z danych regionów (dla API giełd)
        // Struktura region: { city_name, country, postal_code, ... }
        const countryNames = {
            'PL': 'Poland', 'DE': 'Germany', 'FR': 'France', 'ES': 'Spain', 'IT': 'Italy',
            'GB': 'United Kingdom', 'NL': 'Netherlands', 'BE': 'Belgium', 'AT': 'Austria',
            'CZ': 'Czech Republic', 'SK': 'Slovakia', 'HU': 'Hungary', 'RO': 'Romania',
            'BG': 'Bulgaria', 'HR': 'Croatia', 'SI': 'Slovenia', 'LT': 'Lithuania',
            'LV': 'Latvia', 'EE': 'Estonia', 'DK': 'Denmark', 'SE': 'Sweden',
            'NO': 'Norway', 'FI': 'Finland', 'PT': 'Portugal', 'IE': 'Ireland',
            'CH': 'Switzerland', 'LU': 'Luxembourg', 'GR': 'Greece'
        };
        
        console.log('Debug selectedStartRegion:', selectedStartRegion);
        console.log('Debug selectedEndRegion:', selectedEndRegion);
        
        // Budowanie adresu - używaj properties z GeoJSON jeśli dostępne
        let startLocationFull = startLocationNormalized;
        let endLocationFull = endLocationNormalized;
        
        // Funkcja pomocnicza do budowania adresu
        const buildAddress = (props) => {
            if (!props) return '';
            
            const parts = [];
            const postalCode = props.postal_code?.trim();
            const cityName = (props.city_name || props.city)?.trim();
            const country = props.country?.trim();
            const countryFull = country ? (countryNames[country] || country) : '';
            
            // Dodaj kod pocztowy i miasto razem jeśli są
            if (postalCode && cityName) {
                parts.push(`${postalCode} ${cityName}`);
            } else if (cityName) {
                parts.push(cityName);
            } else if (postalCode) {
                parts.push(postalCode);
            }
            
            // Dodaj kraj jeśli jest
            if (countryFull) {
                parts.push(countryFull);
            }
            
            return parts.join(', ');
        };
        
        if (selectedStartRegion && selectedStartRegion.properties) {
            startLocationFull = buildAddress(selectedStartRegion.properties) || startLocationNormalized;
        }
        
        if (selectedEndRegion && selectedEndRegion.properties) {
            endLocationFull = buildAddress(selectedEndRegion.properties) || endLocationNormalized;
        }
        
        console.log(`📍 Adresy dla API: ${startLocationFull} -> ${endLocationFull}`);
        
        // Wysłanie zapytania do API
        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                start_location: startLocationFull,  // Pełny adres dla API giełd
                end_location: endLocationFull,       // Pełny adres dla API giełd
                start_location_raw: startLocationRaw,  // Kod pocztowy wpisany przez użytkownika
                end_location_raw: endLocationRaw,
                start_region_id: selectedStartRegion.id,  // ID regionu dla bazy danych
                end_region_id: selectedEndRegion.id,      // ID regionu dla bazy danych
                vehicle_type: vehicleType,
                body_type: bodyType,
                start_coords: [startFinalCoords[1], startFinalCoords[0]], // [lat, lng] - precyzyjne
                end_coords: [endFinalCoords[1], endFinalCoords[0]], // [lat, lng] - precyzyjne
                start_precise_coords: startPreciseCoords ? [startPreciseCoords[1], startPreciseCoords[0]] : null,
                end_precise_coords: endPreciseCoords ? [endPreciseCoords[1], endPreciseCoords[0]] : null,
                calculated_distance: Math.round(distance),
                distance_method: distanceMethod,  // 'aws' lub 'haversine' lub 'haversine_fallback'
                haversine_distance: Math.round(haversineDistance)  // Oryginalny dystans Haversine
            })
        });
        
        if (!response.ok) {
            throw new Error('Błąd podczas pobierania danych');
        }
        
        const data = await response.json();
        
        // Dodaj informacje o regionach i precyzyjnych współrzędnych do danych
        data.startRegion = selectedStartRegion;
        data.endRegion = selectedEndRegion;
        data.startPreciseCoords = startPreciseCoords;
        data.endPreciseCoords = endPreciseCoords;
        data.startLocationRaw = startLocationRaw;
        data.endLocationRaw = endLocationRaw;
        data.awsRouteGeometry = awsRouteGeometry;  // Geometria trasy z AWS (jeśli dostępna)
        data.awsRouteDuration = awsRouteDuration;  // Czas przejazdu (sekundy)
        
        // Reset flagi "teraz" dla nowego wyszukiwania
        nowDataLoaded = false;
        isNowMode = false;
        cachedNowData = null;
        
        // Wyświetlenie wyników
        displayResults(data);
        
        // Reset wybranych regionów dla następnego wyszukiwania
        selectedStartRegion = null;
        selectedEndRegion = null;
        
    } catch (error) {
        console.error('Error:', error);
        alert('Wystąpił błąd podczas wyceny trasy. Spróbuj ponownie.');
    } finally {
        document.getElementById('loadingSpinner').style.display = 'none';
    }
}

// Wyświetlenie wyników
function displayResults(data) {
    // Zapisz dane do późniejszego użycia
    currentRouteData = data;
    
    // Aktualizacja informacji o trasie dla funkcji wyceny
    updateCurrentRouteInfo(data);
    
    // Pokazanie sekcji wyników
    document.getElementById('resultsSection').style.display = 'block';
    document.getElementById('resultsSection').classList.add('fade-in');
    
    // Przewinięcie do wyników
    setTimeout(() => {
        document.getElementById('resultsSection').scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }, 100);
    
    // Inicjalizacja mapy (jeśli jeszcze nie istnieje)
    if (!map) {
        initMap();
    }
    
    // Wyświetlenie trasy na mapie z regionami i precyzyjnymi znacznikami
    displayRoute(data.route, data.startRegion, data.endRegion, data.startPreciseCoords, data.endPreciseCoords, data.startLocationRaw, data.endLocationRaw, data.awsRouteGeometry, data.awsRouteDuration);
    
    // Wyświetlenie informacji o trasie
    displayRouteInfo(data);
    
    // Wyświetlenie opłat drogowych
    displayTolls(data.tolls);
    
    // Wyświetlenie podsumowania kosztów (zawiera teraz szczegóły stawek)
    displayCostSummary(data);
    
    // Wyświetlenie sugerowanych przewoźników
    displayCarriers(data.suggested_carriers);
    
    // Inicjalizacja przycisków dni
    initializeDaysSelector();
}

// Inicjalizacja mapy Leaflet
function initMap() {
    map = L.map('map').setView([52.0, 19.0], 6);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);
}

// Wyświetlenie trasy na mapie
function displayRoute(routeData, startRegion, endRegion, startPreciseCoords, endPreciseCoords, startLocationRaw, endLocationRaw, awsRouteGeometry, awsRouteDuration) {
    // Usunięcie poprzedniej trasy
    if (routeLayer) {
        map.removeLayer(routeLayer);
    }
    
    // Dodanie nowej trasy
    routeLayer = L.layerGroup().addTo(map);
    
    // Jeśli mamy dane o regionach Voronoi, pokaż ich polygony
    if (startRegion && startRegion.feature) {
        L.geoJSON(startRegion.feature, {
            style: {
                color: '#024b11',
                weight: 2,
                opacity: 0.4,
                fillOpacity: 0.1
            }
        }).addTo(routeLayer).bindPopup(`<b>Region początkowy</b><br>${startRegion.identifier}`);
    }
    
    if (endRegion && endRegion.feature) {
        L.geoJSON(endRegion.feature, {
            style: {
                color: '#1d8b34',
                weight: 2,
                opacity: 0.4,
                fillOpacity: 0.1
            }
        }).addTo(routeLayer).bindPopup(`<b>Region końcowy</b><br>${endRegion.identifier}`);
    }
    
    // Linia trasy - PRIORYTET: geometria AWS > precyzyjne punkty > routeData
    let routePoints = routeData.route;
    let routeStyle = {
        color: '#1d8b34',
        weight: 4,
        opacity: 0.7,
        dashArray: '10, 10'
    };
    
    // Sprawdź czy mamy geometrię trasy z AWS
    const awsGeometry = awsRouteGeometry;
    if (awsGeometry && awsGeometry.length > 0) {
        // Konwertuj geometrię AWS [lng, lat] na format Leaflet [lat, lng]
        routePoints = awsGeometry.map(point => [point[1], point[0]]);
        routeStyle = {
            color: '#2196F3',  // Niebieski dla trasy AWS
            weight: 5,
            opacity: 0.8
        };
        console.log(`🗺️  Używam dokładnej trasy AWS: ${routePoints.length} punktów`);
    } else if (startPreciseCoords && endPreciseCoords) {
        // Użyj precyzyjnych punktów (prosta linia)
        routePoints = [
            [startPreciseCoords[1], startPreciseCoords[0]], // [lat, lng]
            [endPreciseCoords[1], endPreciseCoords[0]]      // [lat, lng]
        ];
        console.log('📍 Używam precyzyjnych punktów do prostej linii');
    } else {
        console.log('📍 Używam punktów z routeData do linii');
    }
    
    const routeLine = L.polyline(routePoints, routeStyle).addTo(routeLayer);
    
    // PRECYZYJNE ZNACZNIKI dla faktycznie wpisanych kodów pocztowych
    if (startPreciseCoords) {
        // Duży, wyraźny marker dla precyzyjnej lokalizacji startu
        L.marker([startPreciseCoords[1], startPreciseCoords[0]], {
            icon: L.divIcon({
                className: 'custom-marker-precise',
                html: `<div style="background-color: #024b11; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 3px solid #fff; box-shadow: 0 3px 8px rgba(0,0,0,0.4); font-size: 18px;">A</div>`,
                iconSize: [40, 40]
            }),
            zIndexOffset: 1000
        }).addTo(routeLayer).bindPopup(`<b>Start (precyzyjny)</b><br>${startLocationRaw}<br><small>Region: ${startRegion ? startRegion.identifier : 'N/A'}</small>`);
    } else {
        // Fallback do centroidu
        L.marker(routeData.start, {
            icon: L.divIcon({
                className: 'custom-marker',
                html: '<div style="background-color: #024b11; color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">A</div>',
                iconSize: [30, 30]
            })
        }).addTo(routeLayer).bindPopup(`<b>Start (centroid)</b><br>${startRegion ? startRegion.identifier : ''}`);
    }
    
    if (endPreciseCoords) {
        // Duży, wyraźny marker dla precyzyjnej lokalizacji końca
        L.marker([endPreciseCoords[1], endPreciseCoords[0]], {
            icon: L.divIcon({
                className: 'custom-marker-precise',
                html: `<div style="background-color: #d32f2f; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 3px solid #fff; box-shadow: 0 3px 8px rgba(0,0,0,0.4); font-size: 18px;">B</div>`,
                iconSize: [40, 40]
            }),
            zIndexOffset: 1000
        }).addTo(routeLayer).bindPopup(`<b>Koniec (precyzyjny)</b><br>${endLocationRaw}<br><small>Region: ${endRegion ? endRegion.identifier : 'N/A'}</small>`);
    } else {
        // Fallback do centroidu
        L.marker(routeData.end, {
            icon: L.divIcon({
                className: 'custom-marker',
                html: '<div style="background-color: #070707; color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">B</div>',
                iconSize: [30, 30]
            })
        }).addTo(routeLayer).bindPopup(`<b>Koniec (centroid)</b><br>${endRegion ? endRegion.identifier : ''}`);
    }
    
    // Dopasowanie widoku do trasy
    map.fitBounds(routeLine.getBounds(), { padding: [50, 50] });
}

// Wyświetlenie informacji o trasie
function displayRouteInfo(data) {
    // Wyświetl faktyczne kody wpisane przez użytkownika (jeśli dostępne)
    document.getElementById('infoStart').textContent = data.start_location_raw || data.start_location;
    document.getElementById('infoEnd').textContent = data.end_location_raw || data.end_location;
    
    // Dystans - dodaj czas przejazdu jeśli dostępny
    let distanceText = data.distance;
    if (data.awsRouteDuration) {
        const hours = Math.floor(data.awsRouteDuration / 3600);
        const minutes = Math.floor((data.awsRouteDuration % 3600) / 60);
        distanceText += ` (~${hours}h ${minutes}m)`;
    }
    document.getElementById('infoDistance').textContent = distanceText;
    
    // Wyświetl badge z metodą obliczania dystansu
    const badge = document.getElementById('distanceMethodBadge');
    const method = data.distance_method;
    
    if (method === 'aws') {
        badge.textContent = 'AWS API';
        badge.className = 'badge bg-success';
        const tooltipText = 'Rzeczywisty dystans drogowy obliczony przez AWS Location Service (uwzględnia autostrady, drogi i ograniczenia dla ciężarówek)';
        badge.title = data.awsRouteGeometry ? tooltipText + ' + Dokładna trasa na mapie' : tooltipText;
        badge.style.display = 'inline';
    } else if (method === 'haversine_fallback') {
        badge.textContent = 'Haversine (fallback)';
        badge.className = 'badge bg-warning text-dark';
        badge.title = 'AWS API niedostępny - używam dystansu w linii prostej';
        badge.style.display = 'inline';
    } else {
        badge.textContent = 'Haversine';
        badge.className = 'badge bg-secondary';
        badge.title = 'Dystans w linii prostej (może różnić się od rzeczywistego)';
        badge.style.display = 'inline';
    }
}

// Wyświetlenie szczegółów opłat drogowych
function displayTolls(tollData) {
    // Wypełnienie szczegółów opłat drogowych (rozwijana sekcja)
    let tollDetailsHtml = '';
    tollData.tolls.forEach(toll => {
        tollDetailsHtml += `
            <div class="detail-item">
                <strong>${toll.country}</strong> (${toll.system}): 
                ${toll.amount} ${toll.currency}
            </div>
        `;
    });
    document.getElementById('tollDetails').innerHTML = tollDetailsHtml;
}

// Wyświetlenie podsumowania kosztów
function displayCostSummary(data) {
    const distance = data.distance;
    const tolls = data.tolls.total_toll;
    
    // Użyj danych dla 7 dni jako domyślnych
    const exchangeData = data.exchange_rates_by_days['7'];
    const historicalData = data.historical_rates_by_days['7'];
    
    // Sprawdź czy są dane giełdowe
    const hasExchangeData = exchangeData.has_data !== false;
    const exchangeAvg = hasExchangeData ? exchangeData.average_total_price : null;
    const exchangeAvgRate = hasExchangeData ? exchangeData.average_rate_per_km : null;
    
    const historicalAvg = historicalData.has_data ? 
        historicalData.average_total_price : null;
    const historicalAvgRate = historicalData.has_data ? 
        historicalData.average_rate_per_km : null;
    
    // Stawka i kwota giełdowa
    if (hasExchangeData) {
        document.getElementById('avgExchangeRate').textContent = `${exchangeAvgRate} EUR/km`;
        document.getElementById('avgExchange').textContent = `${exchangeAvg} EUR`;
        
        // Pokaż ogólną liczbę ofert jako główną wartość
        const totalOffers = exchangeData.total_offers_sum || 0;
        const recordsCount = exchangeData.records_count || 0;
        
        if (totalOffers > 0) {
            document.getElementById('avgExchangeOffersPerDay').textContent = `${totalOffers} ofert`;
            
            if (recordsCount > 0) {
                document.getElementById('totalOffersCount').textContent = `(w ${recordsCount} dniach)`;
            } else {
                document.getElementById('totalOffersCount').textContent = '';
            }
        } else {
            document.getElementById('avgExchangeOffersPerDay').textContent = '0 ofert';
            document.getElementById('totalOffersCount').textContent = '';
        }
        
        // Szczegóły stawek giełdowych (tylko TimoCom i Trans.eu)
        let exchangeDetailsHtml = '';
        exchangeData.offers.forEach(offer => {
            // Filtruj tylko TimoCom i Trans.eu
            if (offer.exchange !== 'TimoCom' && offer.exchange !== 'Trans.eu') {
                return; // Pomiń Teleroute i Transporeon
            }
            
            if (offer.has_data === false) {
                // Oferta bez danych
                const message = offer.message || 'Brak danych';
                exchangeDetailsHtml += `
                    <div class="detail-item">
                        <strong>${offer.exchange}</strong>: 
                        <span class="text-muted" style="font-size: 0.9em;">${message}</span>
                    </div>
                `;
            } else {
                // Oferta z danymi - pokaż stawkę, cenę i liczbę ofert
                const totalOffers = offer.total_offers_sum || 0;
                const recordsCount = offer.records_count || 0;
                
                let offersInfo = '';
                if (totalOffers > 0) {
                    offersInfo = ` <span class="text-muted" style="font-size: 0.85em;">(${totalOffers} ofert w ${recordsCount} dniach)</span>`;
                } else if (recordsCount > 0) {
                    offersInfo = ` <span class="text-muted" style="font-size: 0.85em;">(${recordsCount} dni)</span>`;
                }
                
                exchangeDetailsHtml += `
                    <div class="detail-item">
                        <strong>${offer.exchange}</strong>: 
                        ${offer.rate_per_km} EUR/km | ${offer.total_price} EUR${offersInfo}
                    </div>
                `;
            }
        });
        document.getElementById('exchangeDetails').innerHTML = exchangeDetailsHtml;
    } else {
        // Brak danych giełdowych
        document.getElementById('avgExchangeRate').textContent = 'Brak danych';
        document.getElementById('avgExchange').textContent = '';
        document.getElementById('avgExchangeOffersPerDay').textContent = '-';
        
        const message = exchangeData.message || 'Brak danych dla tej trasy w wybranym okresie';
        document.getElementById('exchangeDetails').innerHTML = `
            <div class="alert alert-info mb-0" style="font-size: 0.9em;">
                <i class="fas fa-info-circle"></i> ${message}
            </div>
        `;
    }
    
    // Stawka i kwota historyczna
    if (historicalAvg) {
        document.getElementById('avgHistoricalRate').textContent = `${historicalAvgRate} EUR/km`;
        document.getElementById('avgHistorical').textContent = `${historicalAvg} EUR`;
        document.getElementById('avgHistoricalOffersPerDay').textContent = historicalData.orders_per_day;
        document.getElementById('historicalOffersPerDayContainer').style.display = 'block';
        
        // Szczegóły stawek historycznych (bez dat)
        let historicalDetailsHtml = '';
        historicalData.orders.forEach(order => {
            historicalDetailsHtml += `
                <div class="detail-item">
                    <strong>${order.order_id}</strong>: 
                    ${order.rate_per_km} EUR/km | ${order.total_price} EUR
                </div>
            `;
        });
        document.getElementById('historicalDetails').innerHTML = historicalDetailsHtml;
        
        // Pokaż link do szczegółów
        document.getElementById('historicalDetailsToggle').innerHTML = `
            <a href="#" id="toggleHistoricalDetails" class="text-decoration-none">
                <i class="fas fa-chevron-down"></i> szczegóły
            </a>
        `;
    } else {
        document.getElementById('avgHistoricalRate').textContent = 'Brak danych';
        document.getElementById('avgHistorical').textContent = '';
        document.getElementById('historicalOffersPerDayContainer').style.display = 'none';
        document.getElementById('historicalDetailsToggle').innerHTML = '';
    }
    
    document.getElementById('totalTolls').textContent = `${tolls} EUR`;
}

// Obsługa trybu "teraz" z paskiem postępu i pobieraniem danych
async function handleNowMode() {
    if (!currentRouteData) return;
    
    // Sprawdź czy dane już zostały załadowane dla tego wyszukiwania
    if (nowDataLoaded && cachedNowData) {
        console.log('📊 Dane "teraz" już załadowane - wyświetlam z cache');
        
        // Wyświetl dane z cache
        const offersData = cachedNowData;
        
        if (offersData.has_data && offersData.average_rate_per_km > 0) {
            document.getElementById('avgExchangeRate').textContent = `${offersData.average_rate_per_km} EUR/km`;
            document.getElementById('avgExchange').textContent = `${offersData.average_total_price} EUR`;
            
            const totalCount = offersData.total_count || 0;
            document.getElementById('avgExchangeOffersPerDay').textContent = `${totalCount} ofert na żywo`;
            document.getElementById('totalOffersCount').textContent = '';
        } else {
            document.getElementById('avgExchangeRate').textContent = 'Brak danych';
            document.getElementById('avgExchange').textContent = '';
            document.getElementById('avgExchangeOffersPerDay').textContent = '0';
            document.getElementById('totalOffersCount').textContent = '';
        }
        
        // Pokaż szczegóły dla każdej giełdy
        let detailsHtml = '<div style="margin: 10px 0;">';
        const timocomCount = offersData.timocom_count || 0;
        if (timocomCount > 0) {
            detailsHtml += `
                <div class="detail-item">
                    <strong>TimoCom</strong>: 
                    <span class="text-success"><i class="fas fa-check-circle"></i> ${timocomCount} ofert</span>
                </div>
            `;
        } else {
            detailsHtml += `
                <div class="detail-item">
                    <strong>TimoCom</strong>: 
                    <span class="text-muted">Brak ofert</span>
                </div>
            `;
        }
        
        const transeuCount = offersData.transeu_count || 0;
        if (transeuCount > 0) {
            detailsHtml += `
                <div class="detail-item">
                    <strong>Trans.eu</strong>: 
                    <span class="text-success"><i class="fas fa-check-circle"></i> ${transeuCount} ofert</span>
                </div>
            `;
        } else {
            detailsHtml += `
                <div class="detail-item">
                    <strong>Trans.eu</strong>: 
                    <span class="text-muted">Brak ofert</span>
                </div>
            `;
        }
        detailsHtml += '</div>';
        document.getElementById('exchangeDetails').innerHTML = detailsHtml;
        
        // Zmień wizualizację na okręgi
        displayRouteWithCircles(
            currentRouteData.route,
            currentRouteData.startPreciseCoords,
            currentRouteData.endPreciseCoords,
            currentRouteData.startLocationRaw,
            currentRouteData.endLocationRaw
        );
        return;
    }
    
    // UKRYJ dane podczas ładowania
    const costSummary = document.getElementById('costSummary');
    const originalDisplay = costSummary.style.display;
    costSummary.style.opacity = '0.3';
    costSummary.style.pointerEvents = 'none';
    
    // Pokaż pasek postępu
    const progressContainer = document.getElementById('nowLoadingProgress');
    const progressBar = document.getElementById('nowProgressBar');
    const progressText = document.getElementById('nowProgressText');
    
    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';
    progressText.textContent = 'Łączenie z API giełd...';
    
    // Pobierz aktualne oferty z API giełd - RÓWNOCZEŚNIE z paskiem postępu
    console.log('📊 Tryb "teraz" - pobieranie aktualnych ofert z API...');
    
    // Uruchom zapytanie do API i animację paska RÓWNOCZEŚNIE
    const apiPromise = fetch('/api/current-offers', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            start_location: currentRouteData.start_location,  // Znormalizowany adres (np. "Wrocław, Poland")
            end_location: currentRouteData.end_location,      // Znormalizowany adres
            start_location_raw: currentRouteData.startLocationRaw,  // Raw input użytkownika (np. "pl00")
            end_location_raw: currentRouteData.endLocationRaw,
            start_coords: currentRouteData.start_coords,  // [lat, lng]
            end_coords: currentRouteData.end_coords,      // [lat, lng]
            distance: currentRouteData.distance
        })
    }).then(response => response.json());
    
    // Animacja paska postępu RÓWNOCZEŚNIE z API
    const progressPromise = (async () => {
        const minDuration = 1000; // Minimum 1 sekunda
        const maxDuration = 8000; // Maksimum 8 sekund
        const steps = 100;
        const stepDuration = 50; // 50ms na krok
        
        let percent = 0;
        const startTime = Date.now();
        
        while (percent < 100) {
            await new Promise(resolve => setTimeout(resolve, stepDuration));
            percent = Math.min(100, percent + Math.random() * 3 + 1); // Losowy przyrost 1-4%
            progressBar.style.width = `${Math.floor(percent)}%`;
            
            // Zmień tekst na różnych etapach
            if (percent < 30) {
                progressText.textContent = 'Łączenie z giełdami...';
            } else if (percent < 60) {
                progressText.textContent = 'Pobieranie ofert...';
            } else if (percent < 90) {
                progressText.textContent = 'Analiza danych...';
            } else {
                progressText.textContent = 'Finalizacja...';
            }
        }
    })();
    
    // Czekaj aż zarówno API jak i minimalna animacja się skończą
    let result;
    try {
        result = await apiPromise;
        
        if (result.success && result.data) {
            console.log('✓ Pobrano aktualne oferty z API giełd:', result.data);
            
            const offersData = result.data;
            
            // Zapisz dane do cache
            cachedNowData = offersData;
            
            // Wyświetl średnią jeśli są dane
            if (offersData.has_data && offersData.average_rate_per_km > 0) {
                document.getElementById('avgExchangeRate').textContent = `${offersData.average_rate_per_km} EUR/km`;
                document.getElementById('avgExchange').textContent = `${offersData.average_total_price} EUR`;
                
                // W trybie "teraz" pokazujemy tylko liczbę ofert (nie "per dzień")
                const totalCount = offersData.total_count || 0;
                document.getElementById('avgExchangeOffersPerDay').textContent = `${totalCount} ofert na żywo`;
                document.getElementById('totalOffersCount').textContent = ''; // Nie pokazuj dodatkowej info w trybie teraz
            } else {
                document.getElementById('avgExchangeRate').textContent = 'Brak danych';
                document.getElementById('avgExchange').textContent = '';
                document.getElementById('avgExchangeOffersPerDay').textContent = '0';
                document.getElementById('totalOffersCount').textContent = '';
            }
            
            // Pokaż szczegóły dla każdej giełdy osobno
            let detailsHtml = '<div style="margin: 10px 0;">';
            
            // TimoCom
            const timocomCount = offersData.timocom_count || 0;
            if (timocomCount > 0) {
                detailsHtml += `
                    <div class="detail-item">
                        <strong>TimoCom</strong>: 
                        <span class="text-success"><i class="fas fa-check-circle"></i> ${timocomCount} ofert</span>
                    </div>
                `;
            } else {
                detailsHtml += `
                    <div class="detail-item">
                        <strong>TimoCom</strong>: 
                        <span class="text-muted"><i class="fas fa-info-circle"></i> Brak ofert z ceną</span>
                    </div>
                `;
            }
            
            // Trans.eu
            const transeuCount = offersData.transeu_count || 0;
            if (transeuCount > 0) {
                detailsHtml += `
                    <div class="detail-item">
                        <strong>Trans.eu</strong>: 
                        <span class="text-success"><i class="fas fa-check-circle"></i> ${transeuCount} ofert</span>
                    </div>
                `;
            } else {
                detailsHtml += `
                    <div class="detail-item">
                        <strong>Trans.eu</strong>: 
                        <span class="text-muted"><i class="fas fa-info-circle"></i> Brak ofert z ceną</span>
                    </div>
                `;
            }
            
            detailsHtml += `
                <small class="text-muted d-block mt-2">
                    <i class="fas fa-clock"></i> Dane na żywo z API giełd
                </small>
            </div>
            `;
            
            document.getElementById('exchangeDetails').innerHTML = detailsHtml;
            
        } else {
            console.warn('⚠ Brak aktualnych ofert lub błąd API');
            
            // Pokaż komunikat "Brak danych" zamiast fallback do bazy
            document.getElementById('avgExchangeRate').textContent = 'Brak danych';
            document.getElementById('avgExchange').textContent = '';
            document.getElementById('avgExchangeOffersPerDay').textContent = '';
            document.getElementById('totalOffersCount').textContent = '';
            document.getElementById('exchangeDetails').innerHTML = `
                <div class="alert alert-warning" style="margin: 10px 0; font-size: 0.9em;">
                    <i class="fas fa-exclamation-triangle"></i> Brak aktualnych ofert dla tej trasy
                </div>
            `;
        }
        
    } catch (error) {
        console.error('❌ Błąd pobierania aktualnych ofert:', error);
        result = null;
        
        // Pokaż błąd zamiast fallback do bazy
        document.getElementById('avgExchangeRate').textContent = 'Błąd';
        document.getElementById('avgExchange').textContent = '';
        document.getElementById('avgExchangeOffersPerDay').textContent = '';
        document.getElementById('totalOffersCount').textContent = '';
        document.getElementById('exchangeDetails').innerHTML = `
            <div class="alert alert-danger" style="margin: 10px 0; font-size: 0.9em;">
                <i class="fas fa-times-circle"></i> Błąd pobierania danych: ${error.message}
            </div>
        `;
    }
    
    // Poczekaj aż animacja paska się skończy (jeśli jeszcze trwa)
    await progressPromise;
    
    // Ustaw pasek na 100%
    progressBar.style.width = '100%';
    progressText.textContent = 'Gotowe!';
    
    // POKAŻ dane po zakończeniu
    costSummary.style.opacity = '1';
    costSummary.style.pointerEvents = 'auto';
    
    // Ukryj pasek postępu po chwili
    setTimeout(() => {
        progressContainer.style.display = 'none';
    }, 500);
    
    // Oznacz że dane zostały załadowane
    nowDataLoaded = true;
    
    // Zmień wizualizację na okręgi 100km
    displayRouteWithCircles(
        currentRouteData.route,
        currentRouteData.startPreciseCoords,
        currentRouteData.endPreciseCoords,
        currentRouteData.startLocationRaw,
        currentRouteData.endLocationRaw
    );
}

// Wyświetlenie trasy z okręgami 100km zamiast regionów Voronoi
function displayRouteWithCircles(routeData, startPreciseCoords, endPreciseCoords, startLocationRaw, endLocationRaw) {
    // Usunięcie poprzedniej trasy
    if (routeLayer) {
        map.removeLayer(routeLayer);
    }
    
    // Dodanie nowej trasy
    routeLayer = L.layerGroup().addTo(map);
    
    // Linia trasy
    let routePoints = routeData.route;
    if (startPreciseCoords && endPreciseCoords) {
        routePoints = [
            [startPreciseCoords[1], startPreciseCoords[0]],
            [endPreciseCoords[1], endPreciseCoords[0]]
        ];
    }
    
    const routeLine = L.polyline(routePoints, {
        color: '#1d8b34',
        weight: 4,
        opacity: 0.7,
        dashArray: '10, 10'
    }).addTo(routeLayer);
    
    // OKRĘGI 100km zamiast regionów Voronoi
    if (startPreciseCoords) {
        // Okrąg startu
        L.circle([startPreciseCoords[1], startPreciseCoords[0]], {
            color: '#024b11',
            fillColor: '#024b11',
            fillOpacity: 0.15,
            radius: 100000, // 100km w metrach
            weight: 2,
            opacity: 0.6
        }).addTo(routeLayer).bindPopup(`<b>Obszar startu</b><br>Promień: 100 km<br>${startLocationRaw}`);
        
        // Marker startu
        L.marker([startPreciseCoords[1], startPreciseCoords[0]], {
            icon: L.divIcon({
                className: 'custom-marker-precise',
                html: `<div style="background-color: #024b11; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 3px solid #fff; box-shadow: 0 3px 8px rgba(0,0,0,0.4); font-size: 18px;">A</div>`,
                iconSize: [40, 40]
            }),
            zIndexOffset: 1000
        }).addTo(routeLayer).bindPopup(`<b>Start</b><br>${startLocationRaw}`);
    }
    
    if (endPreciseCoords) {
        // Okrąg końca
        L.circle([endPreciseCoords[1], endPreciseCoords[0]], {
            color: '#d32f2f',
            fillColor: '#d32f2f',
            fillOpacity: 0.15,
            radius: 100000, // 100km w metrach
            weight: 2,
            opacity: 0.6
        }).addTo(routeLayer).bindPopup(`<b>Obszar końca</b><br>Promień: 100 km<br>${endLocationRaw}`);
        
        // Marker końca
        L.marker([endPreciseCoords[1], endPreciseCoords[0]], {
            icon: L.divIcon({
                className: 'custom-marker-precise',
                html: `<div style="background-color: #d32f2f; color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 3px solid #fff; box-shadow: 0 3px 8px rgba(0,0,0,0.4); font-size: 18px;">B</div>`,
                iconSize: [40, 40]
            }),
            zIndexOffset: 1000
        }).addTo(routeLayer).bindPopup(`<b>Koniec</b><br>${endLocationRaw}`);
    }
    
    // Dopasowanie widoku
    map.fitBounds(routeLine.getBounds(), { padding: [50, 50] });
}

// Inicjalizacja przycisków dni
function initializeDaysSelector() {
    const dayButtons = document.querySelectorAll('.days-selector .btn');
    
    dayButtons.forEach(button => {
        button.addEventListener('click', async function() {
            const daysValue = this.dataset.days;
            
            // Usuń klasę active ze wszystkich przycisków
            dayButtons.forEach(btn => btn.classList.remove('active'));
            
            // Dodaj klasę active do klikniętego przycisku
            this.classList.add('active');
            
            // Sprawdź czy to przycisk "teraz"
            if (daysValue === 'now') {
                isNowMode = true;
                await handleNowMode();
            } else {
                isNowMode = false;
                
                // Ukryj pasek postępu jeśli był widoczny
                document.getElementById('nowLoadingProgress').style.display = 'none';
                
                // Przywróć widoczność danych (na wypadek gdyby były ukryte)
                const costSummary = document.getElementById('costSummary');
                costSummary.style.opacity = '1';
                costSummary.style.pointerEvents = 'auto';
                
                // Pobierz wybraną liczbę dni
                const days = parseInt(daysValue);
                selectedDays = days;
                
                // Zaktualizuj wyświetlane dane
                updateRatesForSelectedDays(days);
                
                // Przywróć normalną wizualizację (regiony Voronoi)
                if (currentRouteData) {
                    displayRoute(
                        currentRouteData.route, 
                        currentRouteData.startRegion, 
                        currentRouteData.endRegion, 
                        currentRouteData.startPreciseCoords, 
                        currentRouteData.endPreciseCoords, 
                        currentRouteData.startLocationRaw, 
                        currentRouteData.endLocationRaw,
                        currentRouteData.awsRouteGeometry,
                        currentRouteData.awsRouteDuration
                    );
                }
            }
        });
    });
}

// Aktualizacja stawek dla wybranego okresu
function updateRatesForSelectedDays(days) {
    if (!currentRouteData || !currentRouteData.exchange_rates_by_days) {
        return;
    }
    
    const daysKey = days.toString();
    const exchangeData = currentRouteData.exchange_rates_by_days[daysKey];
    const historicalData = currentRouteData.historical_rates_by_days[daysKey];
    
    // DEBUG: Sprawdź dane dla tego okresu
    console.log(`🔄 Okres: ${days} dni - Oferty: ${exchangeData?.total_offers_sum || 0}, Dni z danymi: ${exchangeData?.records_count || 0}`);
    
    // Pobierz elementy box
    const exchangeBox = document.querySelector('.rate-group-box:nth-child(1)');
    const historicalBox = document.querySelector('.rate-group-box:nth-child(2)');
    
    // Dodaj klasę animacji
    if (exchangeBox) exchangeBox.classList.add('rate-updating');
    if (historicalBox) historicalBox.classList.add('rate-updating');
    
    // Opóźnij aktualizację danych dla efektu
    setTimeout(() => {
        // Aktualizuj stawki giełdowe
        if (exchangeData && exchangeData.has_data !== false) {
            document.getElementById('avgExchangeRate').textContent = `${exchangeData.average_rate_per_km} EUR/km`;
            document.getElementById('avgExchange').textContent = `${exchangeData.average_total_price} EUR`;
            
            // Pokaż ogólną liczbę ofert jako główną wartość
            const totalOffers = exchangeData.total_offers_sum || 0;
            const recordsCount = exchangeData.records_count || 0;
            
            if (totalOffers > 0) {
                document.getElementById('avgExchangeOffersPerDay').textContent = `${totalOffers} ofert`;
                
                if (recordsCount > 0) {
                    // Pokaż liczbę dni w nawiasie
                    document.getElementById('totalOffersCount').textContent = `(w ${recordsCount} dniach)`;
                } else {
                    document.getElementById('totalOffersCount').textContent = '';
                }
            } else {
                document.getElementById('avgExchangeOffersPerDay').textContent = '0 ofert';
                document.getElementById('totalOffersCount').textContent = '';
            }
            
            // Aktualizuj szczegóły (tylko TimoCom i Trans.eu)
            let exchangeDetailsHtml = '';
            exchangeData.offers.forEach(offer => {
                // Filtruj tylko TimoCom i Trans.eu
                if (offer.exchange !== 'TimoCom' && offer.exchange !== 'Trans.eu') {
                    return; // Pomiń Teleroute i Transporeon
                }
                
                if (offer.has_data === false) {
                    // Oferta bez danych
                    const message = offer.message || 'Brak danych';
                    exchangeDetailsHtml += `
                        <div class="detail-item">
                            <strong>${offer.exchange}</strong>: 
                            <span class="text-muted" style="font-size: 0.9em;">${message}</span>
                        </div>
                    `;
                } else {
                    // Oferta z danymi - pokaż stawkę, cenę i liczbę ofert
                    const totalOffers = offer.total_offers_sum || 0;
                    const recordsCount = offer.records_count || 0;
                    
                    let offersInfo = '';
                    if (totalOffers > 0) {
                        offersInfo = ` <span class="text-muted" style="font-size: 0.85em;">(${totalOffers} ofert w ${recordsCount} dniach)</span>`;
                    } else if (recordsCount > 0) {
                        offersInfo = ` <span class="text-muted" style="font-size: 0.85em;">(${recordsCount} dni)</span>`;
                    }
                    
                    exchangeDetailsHtml += `
                        <div class="detail-item">
                            <strong>${offer.exchange}</strong>: 
                            ${offer.rate_per_km} EUR/km | ${offer.total_price} EUR${offersInfo}
                        </div>
                    `;
                }
            });
            document.getElementById('exchangeDetails').innerHTML = exchangeDetailsHtml;
        } else {
            // Brak danych giełdowych
            document.getElementById('avgExchangeRate').textContent = 'Brak danych';
            document.getElementById('avgExchange').textContent = '';
            document.getElementById('avgExchangeOffersPerDay').textContent = '';
            document.getElementById('totalOffersCount').textContent = '';
            
            const message = exchangeData.message || 'Brak danych dla tej trasy w wybranym okresie';
            document.getElementById('exchangeDetails').innerHTML = `
                <div class="alert alert-info mb-0" style="font-size: 0.9em;">
                    <i class="fas fa-info-circle"></i> ${message}
                </div>
            `;
        }
        
        // Aktualizuj stawki historyczne - ZAWSZE "Brak danych"
        document.getElementById('avgHistoricalRate').textContent = 'Brak danych';
        document.getElementById('avgHistorical').textContent = '';
        document.getElementById('historicalOffersPerDayContainer').style.display = 'none';
        
        // Usuń klasę animacji i dodaj efekt pulse
        if (exchangeBox) {
            exchangeBox.classList.remove('rate-updating');
            exchangeBox.classList.add('updated');
            setTimeout(() => exchangeBox.classList.remove('updated'), 600);
        }
        if (historicalBox) {
            historicalBox.classList.remove('rate-updating');
            historicalBox.classList.add('updated');
            setTimeout(() => historicalBox.classList.remove('updated'), 600);
        }
    }, 200);
}

// Inicjalizacja przycisków rozwijanych (używając event delegation)
function initializeToggleButtons() {
    // Event delegation na całym dokumencie dla dynamicznie tworzonych elementów
    document.addEventListener('click', function(e) {
        // Sprawdź czy kliknięto link szczegółów giełdowych
        if (e.target.id === 'toggleExchangeDetails' || e.target.closest('#toggleExchangeDetails')) {
            e.preventDefault();
            const link = e.target.closest('#toggleExchangeDetails') || e.target;
            const details = document.getElementById('exchangeDetails');
            const icon = link.querySelector('i');
            
            if (details && icon) {
                if (details.style.display === 'none' || !details.style.display) {
                    details.style.display = 'block';
                    icon.classList.remove('fa-chevron-down');
                    icon.classList.add('fa-chevron-up');
                } else {
                    details.style.display = 'none';
                    icon.classList.remove('fa-chevron-up');
                    icon.classList.add('fa-chevron-down');
                }
            }
        }
        
        // Sprawdź czy kliknięto link szczegółów historycznych
        if (e.target.id === 'toggleHistoricalDetails' || e.target.closest('#toggleHistoricalDetails')) {
            e.preventDefault();
            const link = e.target.closest('#toggleHistoricalDetails') || e.target;
            const details = document.getElementById('historicalDetails');
            const icon = link.querySelector('i');
            
            if (details && icon) {
                if (details.style.display === 'none' || !details.style.display) {
                    details.style.display = 'block';
                    icon.classList.remove('fa-chevron-down');
                    icon.classList.add('fa-chevron-up');
                } else {
                    details.style.display = 'none';
                    icon.classList.remove('fa-chevron-up');
                    icon.classList.add('fa-chevron-down');
                }
            }
        }
        
        // Sprawdź czy kliknięto link szczegółów opłat
        if (e.target.id === 'toggleTollDetails' || e.target.closest('#toggleTollDetails')) {
            e.preventDefault();
            const link = e.target.closest('#toggleTollDetails') || e.target;
            const details = document.getElementById('tollDetails');
            const icon = link.querySelector('i');
            
            if (details && icon) {
                if (details.style.display === 'none' || !details.style.display) {
                    details.style.display = 'block';
                    icon.classList.remove('fa-chevron-down');
                    icon.classList.add('fa-chevron-up');
                } else {
                    details.style.display = 'none';
                    icon.classList.remove('fa-chevron-up');
                    icon.classList.add('fa-chevron-down');
                }
            }
        }
    });
}

// Wyświetlenie sugerowanych przewoźników
function displayCarriers(carriersData) {
    // Przewoźnicy historyczni
    const historicalContainer = document.getElementById('historicalCarriers');
    let historicalHtml = '';
    
    if (carriersData.historical.length === 0) {
        historicalHtml = `
            <div class="no-data-message">
                <i class="fas fa-user-times"></i>
                <p>Brak przewoźników historycznych</p>
            </div>
        `;
    } else {
        carriersData.historical.forEach((carrier, index) => {
            historicalHtml += `
                <div class="carrier-card">
                    <div class="carrier-name">
                        <i class="fas fa-truck"></i> ${carrier.name}
                    </div>
                    <div class="carrier-info">
                        <i class="fas fa-clipboard-check"></i> 
                        Zrealizowane zlecenia: ${carrier.completed_orders}
                    </div>
                    <div class="carrier-info">
                        <i class="fas fa-coins"></i> 
                        Średnia stawka: ${carrier.avg_rate_per_km} EUR/km
                    </div>
                    <div class="carrier-info">
                        <i class="fas fa-phone"></i> 
                        ${carrier.contact}
                    </div>
                    <div class="mt-2">
                        <div class="dropdown">
                            <button class="btn btn-primary btn-sm dropdown-toggle" type="button" id="dropdownCarrierH${index}" data-bs-toggle="dropdown" aria-expanded="false">
                                <i class="fas fa-calculator"></i> Wycena
                            </button>
                            <ul class="dropdown-menu" aria-labelledby="dropdownCarrierH${index}">
                                <li><a class="dropdown-item" href="#" onclick="sendQuoteMail('${carrier.name}'); return false;"><i class="fas fa-envelope"></i> Mail</a></li>
                                <li><a class="dropdown-item" href="#" onclick="showSmsModal('${carrier.name}', '${carrier.contact}'); return false;"><i class="fas fa-sms"></i> Telefon</a></li>
                                <li><a class="dropdown-item" href="https://www.trans.eu" target="_blank"><i class="fas fa-comments"></i> Komunikator</a></li>
                            </ul>
                        </div>
                    </div>
                </div>
            `;
        });
    }
    
    historicalContainer.innerHTML = historicalHtml;
    
    // Przewoźnicy z giełd
    const exchangeContainer = document.getElementById('exchangeCarriers');
    let exchangeHtml = '';
    
    carriersData.exchange.forEach((carrier, index) => {
        exchangeHtml += `
            <div class="carrier-card">
                <div class="carrier-name">
                    <i class="fas fa-truck"></i> ${carrier.name}
                </div>
                <div class="carrier-info">
                    <i class="fas fa-star"></i> 
                    <span class="rating-stars">${'★'.repeat(Math.floor(carrier.rating))}</span>
                    ${carrier.rating}
                </div>
                <div class="carrier-info">
                    <i class="fas fa-exchange-alt"></i> 
                    Giełda: <span class="badge bg-info">${carrier.exchange}</span>
                </div>
                <div class="carrier-info">
                    <i class="fas fa-truck-loading"></i> 
                    Dostępne pojazdy: ${carrier.available_trucks}
                </div>
                <div class="mt-2">
                    <div class="dropdown">
                        <button class="btn btn-primary btn-sm dropdown-toggle" type="button" id="dropdownCarrierE${index}" data-bs-toggle="dropdown" aria-expanded="false">
                            <i class="fas fa-calculator"></i> Wycena
                        </button>
                        <ul class="dropdown-menu" aria-labelledby="dropdownCarrierE${index}">
                            <li><a class="dropdown-item" href="#" onclick="sendQuoteMail('${carrier.name}'); return false;"><i class="fas fa-envelope"></i> Mail</a></li>
                            <li><a class="dropdown-item" href="#" onclick="showSmsModal('${carrier.name}', ''); return false;"><i class="fas fa-sms"></i> Telefon</a></li>
                            <li><a class="dropdown-item" href="https://www.trans.eu" target="_blank"><i class="fas fa-comments"></i> Komunikator</a></li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
    });
    
    exchangeContainer.innerHTML = exchangeHtml;
}

// Globalne zmienne dla aktualnej trasy
let currentRouteInfo = {
    startLocation: '',
    endLocation: '',
    vehicleType: '',
    bodyType: ''
};

// Aktualizacja informacji o trasie po obliczeniach
function updateCurrentRouteInfo(data) {
    currentRouteInfo.startLocation = data.start_location;
    currentRouteInfo.endLocation = data.end_location;
    currentRouteInfo.vehicleType = data.vehicle_type || 'naczepa';
    currentRouteInfo.bodyType = data.body_type || 'standard';
}

// Funkcja do generowania tekstu wiadomości
function generateQuoteMessage(carrierName) {
    const vehicleTypeNames = {
        'bus': 'Bus',
        'solo': 'Solo',
        'naczepa': 'Naczepa',
        'zestaw': 'Zestaw'
    };
    
    const bodyTypeNames = {
        'standard': 'Standard',
        'mega': 'Mega',
        'jumbo': 'Jumbo',
        'chlodnia': 'Chłodnia'
    };
    
    let vehicleDescription = vehicleTypeNames[currentRouteInfo.vehicleType] || 'Naczepa';
    if (currentRouteInfo.vehicleType === 'naczepa' && currentRouteInfo.bodyType) {
        vehicleDescription += ' ' + bodyTypeNames[currentRouteInfo.bodyType];
    }
    
    const relacja = `${currentRouteInfo.startLocation} - ${currentRouteInfo.endLocation}`;
    
    return `Dzień dobry,

Proszę o wycenę realizacji przewozu ${vehicleDescription} na trasie ${relacja} w dniu [DO UZUPEŁNIENIA], towar to [DO UZUPEŁNIENIA].

Pozdrawiam`;
}

// Funkcja do wysłania maila
function sendQuoteMail(carrierName) {
    const relacja = `${currentRouteInfo.startLocation} - ${currentRouteInfo.endLocation}`;
    const subject = `Wycena trasy ${relacja}`;
    const body = generateQuoteMessage(carrierName);
    
    const mailtoLink = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
    window.location.href = mailtoLink;
}

// Funkcja do pokazania modalu SMS
function showSmsModal(carrierName, phoneNumber) {
    const message = generateQuoteMessage(carrierName);
    document.getElementById('smsMessage').value = message;
    document.getElementById('smsPhone').value = phoneNumber || '';
    
    const modal = new bootstrap.Modal(document.getElementById('smsModal'));
    modal.show();
}

// Funkcja do wysłania SMS
function sendSms() {
    const phone = document.getElementById('smsPhone').value.trim();
    const message = document.getElementById('smsMessage').value;
    
    if (!phone) {
        alert('Proszę podać numer telefonu');
        return;
    }
    
    // W rzeczywistości tutaj powinno być połączenie z API do wysyłki SMS
    // Na razie pokazujemy tylko komunikat
    alert(`SMS został wysłany na numer: ${phone}\n\nTreść:\n${message}`);
    
    // Zamknij modal
    const modal = bootstrap.Modal.getInstance(document.getElementById('smsModal'));
    modal.hide();
}
