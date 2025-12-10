/**
 * Cargo Scout Wycena - Prosty Frontend
 * Bez geokodowania - tylko wysyłanie kodów pocztowych do API
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Cargo Scout UI - Simple Mode');
    
    const form = document.getElementById('routeForm');
    
    // Obsługa formularza
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const startLocation = document.getElementById('startLocation').value.trim();
        const endLocation = document.getElementById('endLocation').value.trim();
        const vehicleType = document.getElementById('vehicleType').value;
        const bodyType = document.getElementById('bodyType').value;
        
        if (!startLocation || !endLocation) {
            alert('Podaj kody pocztowe start i end');
            return;
        }
        
        console.log(`📝 Kody: ${startLocation} -> ${endLocation}`);
        console.log(`🚛 Typ: ${vehicleType}, Nadwozie: ${bodyType}`);
        
        // Wywołaj API z prostymi kodami pocztowymi
        // Dystans: 500km jako placeholder (można dodać kalkulację AWS później)
        await calculateRoute(startLocation, endLocation, 500, vehicleType, bodyType);
    });
});


async function calculateRoute(startCode, endCode, distance, vehicleType, bodyType) {
    try {
        console.log(`🌐 Wywołuję API: ${startCode} -> ${endCode}, ${distance}km, ${vehicleType}/${bodyType}`);
        
        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                start_location: startCode,
                end_location: endCode,
                calculated_distance: distance,
                vehicle_type: vehicleType,
                body_type: bodyType,
                start_coords: [52.0, 19.0],  // Placeholder
                end_coords: [50.0, 20.0]      // Placeholder
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            console.error('❌ Błąd:', data);
            alert(`Błąd: ${data.error || 'Nieznany błąd'}\n${data.message || ''}`);
            return;
        }
        
        console.log('✅ Dane z API:', data);
        
        // Pokaż wyniki
        displayResults(data);
        
    } catch (error) {
        console.error('❌ Błąd:', error);
        alert(`Błąd połączenia: ${error.message}`);
    }
}


function displayResults(data) {
    // Pokaż sekcję wyników
    const resultsSection = document.getElementById('resultsSection');
    resultsSection.style.display = 'block';
    
    // Podstawowe informacje
    document.getElementById('infoStart').textContent = data.start_location || '';
    document.getElementById('infoEnd').textContent = data.end_location || '';
    document.getElementById('infoDistance').textContent = data.distance || '';
    
    // Dane giełdowe
    const exchangeRates = data.exchange_rates || {};
    if (exchangeRates.has_data) {
        const avgRate = exchangeRates.average_rate_per_km;
        const avgTotal = exchangeRates.average_rate_per_km * data.distance;
        
        document.getElementById('avgExchangeRate').textContent = avgRate ? `${avgRate.toFixed(2)} EUR/km` : 'Brak danych';
        document.getElementById('avgExchange').textContent = avgTotal ? `${avgTotal.toFixed(2)} EUR` : '';
        
        // Szczegóły ofert
        displayExchangeDetails(exchangeRates.offers || []);
    } else {
        document.getElementById('avgExchangeRate').textContent = 'Brak danych';
        document.getElementById('avgExchange').textContent = '';
    }
    
    // Dane historyczne
    const historicalRates = data.historical_rates || {};
    if (historicalRates.has_data) {
        const avgRate = historicalRates.average_rate_per_km;
        const avgTotal = avgRate * data.distance;
        
        document.getElementById('avgHistoricalRate').textContent = avgRate ? `${avgRate.toFixed(2)} EUR/km` : 'Brak danych';
        document.getElementById('avgHistorical').textContent = avgTotal ? `${avgTotal.toFixed(2)} EUR` : '';
        
        // Szczegóły zleceń
        displayHistoricalDetails(historicalRates.orders || []);
    } else {
        document.getElementById('avgHistoricalRate').textContent = 'Brak danych';
        document.getElementById('avgHistorical').textContent = '';
    }
    
    // Scroll do wyników
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}


function displayExchangeDetails(offers) {
    const container = document.getElementById('exchangeDetails');
    if (!container) return;
    
    let html = '<div class="table-responsive"><table class="table table-sm"><thead><tr><th>Giełda</th><th>Typ</th><th>EUR/km</th><th>Całość</th><th>Oferty</th></tr></thead><tbody>';
    
    offers.forEach(offer => {
        if (offer.has_data) {
            html += `<tr>
                <td>${offer.exchange}</td>
                <td>${offer.vehicle_type || '-'}</td>
                <td>${offer.rate_per_km ? offer.rate_per_km.toFixed(2) : '-'}</td>
                <td>${offer.total_price ? offer.total_price.toFixed(2) : '-'} EUR</td>
                <td>${offer.total_offers_sum || 0}</td>
            </tr>`;
        } else {
            html += `<tr><td>${offer.exchange}</td><td colspan="4" class="text-muted">Brak danych</td></tr>`;
        }
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}


function displayHistoricalDetails(orders) {
    const container = document.getElementById('historicalDetails');
    if (!container) return;
    
    let html = '<div class="table-responsive"><table class="table table-sm"><thead><tr><th>Przewoźnik</th><th>Typ</th><th>EUR/km</th><th>Kwota</th><th>Zleceń</th></tr></thead><tbody>';
    
    orders.forEach(order => {
        html += `<tr>
            <td>${order.carrier || '-'}</td>
            <td><span class="badge bg-${order.type === 'FTL' ? 'primary' : 'info'}">${order.type}</span></td>
            <td>${order.rate_per_km ? order.rate_per_km.toFixed(2) : '-'}</td>
            <td>${order.total_price ? order.total_price.toFixed(2) : '-'} EUR</td>
            <td>${order.order_count || 0}</td>
        </tr>`;
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}


// Toggle szczegółów
document.addEventListener('click', function(e) {
    if (e.target.id === 'toggleExchangeDetails' || e.target.parentElement.id === 'toggleExchangeDetails') {
        e.preventDefault();
        const details = document.getElementById('exchangeDetails');
        const icon = document.querySelector('#toggleExchangeDetails i');
        
        if (details.style.display === 'none') {
            details.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
        } else {
            details.style.display = 'none';
            icon.className = 'fas fa-chevron-down';
        }
    }
    
    if (e.target.id === 'toggleHistoricalDetails' || e.target.parentElement.id === 'toggleHistoricalDetails') {
        e.preventDefault();
        const details = document.getElementById('historicalDetails');
        const icon = document.querySelector('#toggleHistoricalDetails i');
        
        if (details.style.display === 'none') {
            details.style.display = 'block';
            icon.className = 'fas fa-chevron-up';
        } else {
            details.style.display = 'none';
            icon.className = 'fas fa-chevron-down';
        }
    }
});
