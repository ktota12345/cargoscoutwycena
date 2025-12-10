/**
 * POSTAL CODE SEARCH - Standalone JavaScript Module
 * 
 * System wyszukiwania regionów po kodach pocztowych
 * Format: KOD_KRAJU (2 litery) + pierwsze 2 cyfry kodu pocztowego
 * Przykłady: PL50, DE12, FR75, ES28
 * 
 * WYMAGANIA:
 * - Turf.js dla operacji geo (https://turfjs.org/)
 * - Pliki JSON: postal_code_to_region.json, voronoi_regions.geojson
 */

class PostalCodeSearch {
    constructor() {
        this.allRegionsData = [];
        this.postalCodeMapping = {};
        this.initialized = false;
    }

    /**
     * Inicjalizuje system - ładuje regiony i mapowanie
     * @param {string} regionsFile - Ścieżka do pliku GeoJSON z regionami
     * @param {string} mappingFile - Ścieżka do pliku JSON z mapowaniem
     */
    async initialize(regionsFile, mappingFile) {
        try {
            // Załaduj regiony
            console.log(`Ładowanie regionów z ${regionsFile}...`);
            const regionsResponse = await fetch(`${regionsFile}?v=${Date.now()}`);
            if (!regionsResponse.ok) throw new Error(`Błąd HTTP: ${regionsResponse.status}`);
            const regionsData = await regionsResponse.json();

            // Przetwórz regiony
            this.allRegionsData = regionsData.features.map(feature => {
                const centroid = turf.centroid(feature.geometry);
                return {
                    id: feature.properties.id,
                    identifier: this.getRegionIdentifier(feature.properties),
                    feature: feature,
                    centroid: centroid,
                    properties: feature.properties
                };
            });

            console.log(`✓ Załadowano ${this.allRegionsData.length} regionów`);

            // Załaduj mapowanie kodów pocztowych
            console.log(`Ładowanie mapowania z ${mappingFile}...`);
            const mappingResponse = await fetch(`${mappingFile}?v=${Date.now()}`);
            if (!mappingResponse.ok) throw new Error(`Błąd HTTP: ${mappingResponse.status}`);
            this.postalCodeMapping = await mappingResponse.json();

            console.log(`✓ Załadowano mapowanie ${Object.keys(this.postalCodeMapping).length} kodów pocztowych`);

            this.initialized = true;
            return true;
        } catch (error) {
            console.error('Błąd inicjalizacji PostalCodeSearch:', error);
            return false;
        }
    }

    /**
     * Sprawdza czy zapytanie może być kodem pocztowym
     * @param {string} query - Zapytanie użytkownika
     * @returns {boolean}
     */
    isPotentialPostalCode(query) {
        const normalized = query.replace(/\s|-/g, '');
        return /^[a-zA-Z]{2}\d+/.test(normalized) && normalized.length < 10;
    }

    /**
     * Normalizuje kod pocztowy do formatu standardowego
     * @param {string} query - Kod pocztowy
     * @returns {string} Znormalizowany kod
     */
    normalizePostalCode(query) {
        return query.replace(/\s|-/g, '').toUpperCase();
    }

    /**
     * Tworzy identyfikator regionu z properties
     * @param {object} props - Properties regionu z GeoJSON
     * @returns {string}
     */
    getRegionIdentifier(props) {
        if (props && props.country && props.postal_code) {
            return `${props.country}-${String(props.postal_code).substring(0, 2)}`;
        }
        return `Region ${props.id}`;
    }

    /**
     * Znajduje region po ID
     * @param {number} regionId - ID regionu
     * @returns {object|null}
     */
    getRegionById(regionId) {
        return this.allRegionsData.find(r => r.id === regionId) || null;
    }

    /**
     * Znajduje najbliższy region na podstawie kodu pocztowego
     * @param {string} query - Kod pocztowy (np. "PL50", "DE12")
     * @returns {object|null} Region lub null
     */
    findRegionByPostalCode(query) {
        if (!this.initialized) {
            console.warn('PostalCodeSearch nie został zainicjalizowany!');
            return null;
        }

        const normalized = this.normalizePostalCode(query);
        
        // Spróbuj znaleźć w mapowaniu kodów pocztowych
        if (this.postalCodeMapping[normalized]) {
            const regionId = this.postalCodeMapping[normalized].region_id;
            return this.getRegionById(regionId);
        }
        
        // Fallback: logika oparta na numerach (jeśli dokładne mapowanie nie działa)
        return this.findRegionByNumberFallback(normalized);
    }

    /**
     * Fallback: Znajduje najbliższy region numerycznie w tym samym kraju
     * @param {string} normalized - Znormalizowany kod pocztowy
     * @returns {object|null}
     */
    findRegionByNumberFallback(normalized) {
        const countryMatch = normalized.match(/^[A-Z]{2}/);
        const numberMatch = normalized.match(/\d+/);

        if (!countryMatch || !numberMatch) return null;

        const countryCode = countryMatch[0];
        const targetNumber = parseInt(numberMatch[0], 10);

        const regionsInCountry = this.allRegionsData.filter(r => 
            r.identifier.toUpperCase().startsWith(countryCode)
        );

        let closestRegion = null;
        let smallestDifference = Infinity;

        for (const region of regionsInCountry) {
            const regionNumberMatch = region.identifier.match(/(\d+)/);
            if (regionNumberMatch) {
                const regionNumber = parseInt(regionNumberMatch[0], 10);
                const difference = Math.abs(targetNumber - regionNumber);

                if (difference < smallestDifference) {
                    smallestDifference = difference;
                    closestRegion = region;
                }
            }
        }
        
        return closestRegion;
    }

    /**
     * Wyszukuje regiony na podstawie zapytania
     * @param {string} query - Zapytanie użytkownika
     * @param {number} limit - Maksymalna liczba wyników (domyślnie 50)
     * @returns {Array} Lista regionów
     */
    search(query, limit = 50) {
        if (!this.initialized) {
            console.warn('PostalCodeSearch nie został zainicjalizowany!');
            return [];
        }

        if (!query) {
            return this.allRegionsData.slice(0, limit);
        }

        const normalizedQuery = query.toLowerCase().replace(/\s|-/g, '');
        
        // Wyszukaj w identyfikatorach regionów
        let results = this.allRegionsData.filter(r => 
            r.identifier.toLowerCase().replace(/\s|-/g, '').includes(normalizedQuery)
        );

        // Jeśli brak wyników i to potencjalny kod pocztowy
        if (results.length === 0 && this.isPotentialPostalCode(query)) {
            const closestRegion = this.findRegionByPostalCode(query);
            if (closestRegion) {
                results = [closestRegion];
            }
        }

        return results.slice(0, limit);
    }

    /**
     * Pobiera sugestie kodów pocztowych (autouzupełnianie)
     * @param {string} query - Częściowy kod pocztowy
     * @param {number} limit - Maksymalna liczba sugestii
     * @returns {Array} Lista sugestii
     */
    getSuggestions(query, limit = 5) {
        if (!this.initialized) return [];

        const normalized = this.normalizePostalCode(query);
        return Object.keys(this.postalCodeMapping)
            .filter(key => key.startsWith(normalized))
            .slice(0, limit)
            .map(key => ({
                code: key,
                region: this.getRegionById(this.postalCodeMapping[key].region_id),
                distance: this.postalCodeMapping[key].distance_km
            }));
    }

    /**
     * Pobiera wszystkie regiony dla danego kraju
     * @param {string} countryCode - Kod kraju (2 litery)
     * @returns {Array} Lista regionów
     */
    getRegionsByCountry(countryCode) {
        if (!this.initialized) return [];

        const code = countryCode.toUpperCase();
        return this.allRegionsData.filter(r => 
            r.identifier.toUpperCase().startsWith(code)
        );
    }

    /**
     * Pobiera statystyki systemu
     * @returns {object}
     */
    getStats() {
        return {
            totalRegions: this.allRegionsData.length,
            totalPostalCodes: Object.keys(this.postalCodeMapping).length,
            countries: this.getCountryList(),
            initialized: this.initialized
        };
    }

    /**
     * Pobiera listę dostępnych krajów
     * @returns {Array}
     */
    getCountryList() {
        const countries = new Set();
        this.allRegionsData.forEach(r => {
            const match = r.identifier.match(/^[A-Z]{2}/);
            if (match) countries.add(match[0]);
        });
        return Array.from(countries).sort();
    }
}

// Export dla różnych środowisk
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PostalCodeSearch;
}
if (typeof window !== 'undefined') {
    window.PostalCodeSearch = PostalCodeSearch;
}

/**
 * PRZYKŁAD UŻYCIA:
 * 
 * // 1. Inicjalizacja
 * const postalSearch = new PostalCodeSearch();
 * await postalSearch.initialize(
 *     'voronoi_regions.geojson',
 *     'postal_code_to_region.json'
 * );
 * 
 * // 2. Wyszukiwanie regionu po kodzie pocztowym
 * const region = postalSearch.findRegionByPostalCode('PL50');
 * console.log(region); // {id: 134, identifier: "PL-50", ...}
 * 
 * // 3. Wyszukiwanie ogólne
 * const results = postalSearch.search('PL5');
 * console.log(results); // [region1, region2, ...]
 * 
 * // 4. Autouzupełnianie
 * const suggestions = postalSearch.getSuggestions('PL');
 * console.log(suggestions); // [{code: "PL50", region: {...}}, ...]
 * 
 * // 5. Regiony w kraju
 * const plRegions = postalSearch.getRegionsByCountry('PL');
 * console.log(plRegions); // [wszystkie regiony PL]
 * 
 * // 6. Statystyki
 * const stats = postalSearch.getStats();
 * console.log(stats); // {totalRegions: 250, totalPostalCodes: 9000, ...}
 */
