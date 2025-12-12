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
        
        if (!startLocation || !endLocation) {
            alert('Podaj kody pocztowe start i end');
            return;
        }
        
        console.log(`📝 Kody: ${startLocation} -> ${endLocation}`);
        
        // Wywołaj API - dystans jest obliczany przez backend
        await calculateRoute(startLocation, endLocation);
    });
});


async function calculateRoute(startCode, endCode) {
    try {
        console.log(`🌐 Wywołuję API: ${startCode} -> ${endCode}`);
        
        // Pokaż spinner
        showLoadingSpinner();
        
        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                start_location: startCode,
                end_location: endCode
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            console.error('❌ Błąd:', data);
            alert(`Błąd: ${data.error || 'Nieznany błąd'}\n${data.message || ''}`);
            return;
        }
        
        console.log('✅ Dane z API:', data);
        
        // Ukryj spinner
        hideLoadingSpinner();
        
        // Pokaż wyniki
        displayResults(data);
        
    } catch (error) {
        console.error('❌ Błąd:', error);
        hideLoadingSpinner();
        alert(`Błąd połączenia: ${error.message}`);
    }
}


function showLoadingSpinner() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) spinner.style.display = 'block';
    
    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) resultsSection.style.display = 'none';
}


function hideLoadingSpinner() {
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) spinner.style.display = 'none';
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
        // Wyświetl tabelę ofert
        displayExchangeDetails(exchangeRates.offers || []);
    } else {
        displayExchangeDetails([]);
    }
    
    // Dane historyczne - FTL i LTL osobno
    const historicalRates = data.historical_rates || {};
    
    // FTL
    if (historicalRates.ftl && historicalRates.ftl.has_data) {
        const ftlRate = historicalRates.ftl.avg_rate_per_km;
        const ftlAmount = historicalRates.ftl.avg_amount;
        
        document.getElementById('avgHistoricalRateFTL').textContent = ftlRate ? `${ftlRate.toFixed(2)} EUR/km` : 'Brak danych';
        document.getElementById('avgHistoricalFTL').textContent = ftlAmount ? `${ftlAmount.toFixed(2)} EUR` : '';
    } else {
        document.getElementById('avgHistoricalRateFTL').textContent = 'Brak danych';
        document.getElementById('avgHistoricalFTL').textContent = '';
    }
    
    // LTL
    if (historicalRates.ltl && historicalRates.ltl.has_data) {
        const ltlRate = historicalRates.ltl.avg_rate_per_km;
        const ltlAmount = historicalRates.ltl.avg_amount;
        
        document.getElementById('avgHistoricalRateLTL').textContent = ltlRate ? `${ltlRate.toFixed(2)} EUR/km` : 'Brak danych';
        document.getElementById('avgHistoricalLTL').textContent = ltlAmount ? `${ltlAmount.toFixed(2)} EUR` : '';
    } else {
        document.getElementById('avgHistoricalRateLTL').textContent = 'Brak danych';
        document.getElementById('avgHistoricalLTL').textContent = '';
    }
    
    // Wyświetl przewoźników historycznych
    displayHistoricalCarriers(data.historical_rates || {});
    
    // Wyświetl zlecenia historyczne
    displayHistoricalOrders(data.historical_orders || []);
    
    // Scroll do wyników
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}


function displayExchangeDetails(offers) {
    const container = document.getElementById('exchangeDetails');
    if (!container) return;
    
    if (!offers || offers.length === 0) {
        container.innerHTML = '<p class="text-muted">Brak danych giełdowych</p>';
        return;
    }
    
    let html = '<div class="table-responsive"><table class="table table-sm"><thead><tr><th>Giełda</th><th>Typ</th><th>EUR/km</th><th>Całość</th><th>Oferty</th></tr></thead><tbody>';
    
    offers.forEach(offer => {
        if (offer.has_data) {
            html += `<tr>
                <td>${offer.exchange}</td>
                <td>${offer.vehicle_type || '-'}</td>
                <td>${offer.rate_per_km ? offer.rate_per_km.toFixed(2) : '-'}</td>
                <td>${offer.total_price ? offer.total_price.toFixed(2) : '-'}</td>
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


function displayHistoricalCarriers(historicalData) {
    const container = document.getElementById('historicalCarriersTable');
    if (!container) return;
    
    const ftlCarriers = (historicalData.ftl && historicalData.ftl.carriers) || [];
    const ltlCarriers = (historicalData.ltl && historicalData.ltl.carriers) || [];
    const allCarriers = [...ftlCarriers, ...ltlCarriers];
    
    if (allCarriers.length === 0) {
        container.innerHTML = '<p class="text-muted">Brak danych o przewoźnikach historycznych dla tej trasy.</p>';
        return;
    }
    
    let html = '<div class="table-responsive"><table class="table table-hover table-sm" style="font-size: 0.85rem;"><thead><tr>';
    html += '<th><i class="fas fa-truck"></i> Przewoźnik</th>';
    html += '<th style="min-width: 90px;"><i class="fas fa-box"></i> Typ</th>';
    html += '<th style="min-width: 95px;"><i class="fas fa-euro-sign"></i> Stawka</th>';
    html += '<th style="min-width: 75px;"><i class="fas fa-money-bill-wave"></i> Kwota</th>';
    html += '<th style="min-width: 85px;"><i class="fas fa-clipboard-list"></i> Zlecenia</th>';
    html += '</tr></thead><tbody>';
    
    // FTL carriers
    ftlCarriers.forEach(carrier => {
        const currency = carrier.currency || 'EUR';
        const currencyDisplay = currency === 'EUR' ? '€' : currency;
        html += `<tr>
            <td><strong>${carrier.carrier || 'Nieznany'}</strong></td>
            <td><span class="badge bg-primary">FTL</span></td>
            <td>${carrier.rate_per_km ? carrier.rate_per_km.toFixed(2) : '-'} ${currencyDisplay}/km</td>
            <td><strong>${carrier.total_price ? carrier.total_price.toFixed(2) : '-'}</strong> ${currencyDisplay}</td>
            <td><span class="badge bg-secondary">${carrier.order_count || 0}</span></td>
        </tr>`;
    });
    
    // LTL carriers
    ltlCarriers.forEach(carrier => {
        const currency = carrier.currency || 'EUR';
        const currencyDisplay = currency === 'EUR' ? '€' : currency;
        html += `<tr>
            <td><strong>${carrier.carrier || 'Nieznany'}</strong></td>
            <td><span class="badge bg-info">LTL</span></td>
            <td>${carrier.rate_per_km ? carrier.rate_per_km.toFixed(2) : '-'} ${currencyDisplay}/km</td>
            <td><strong>${carrier.total_price ? carrier.total_price.toFixed(2) : '-'}</strong> ${currencyDisplay}</td>
            <td><span class="badge bg-secondary">${carrier.order_count || 0}</span></td>
        </tr>`;
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}


function displayHistoricalOrders(orders) {
    const container = document.getElementById('historicalOrdersTable');
    if (!container) return;
    
    if (!orders || orders.length === 0) {
        container.innerHTML = '<p class="text-muted">Brak zleceń historycznych dla tej trasy.</p>';
        return;
    }
    
    let html = '<div class="table-responsive"><table class="table table-hover table-sm" style="font-size: 0.85rem;"><thead><tr>';
    html += '<th style="min-width: 110px;"><i class="fas fa-calendar"></i> Data</th>';
    html += '<th><i class="fas fa-truck"></i> Przewoźnik</th>';
    html += '<th style="min-width: 60px;"><i class="fas fa-address-book"></i></th>';
    html += '<th style="min-width: 90px;"><i class="fas fa-cubes"></i> Ładunek</th>';
    html += '<th style="min-width: 95px;"><i class="fas fa-euro-sign"></i> Stawka</th>';
    html += '<th style="min-width: 75px;"><i class="fas fa-money-bill-wave"></i> Kwota</th>';
    html += '<th style="min-width: 85px;"><i class="fas fa-road"></i> Dystans</th>';
    html += '</tr></thead><tbody>';
    
    orders.forEach((order, index) => {
        const currency = order.currency || 'EUR';
        const currencyDisplay = currency === 'EUR' ? '€' : currency;
        const email = order.carrier_email || '';
        const contact = order.carrier_contact || '';
        
        html += `<tr>
            <td style="white-space: nowrap;">${order.date || '-'}</td>
            <td><strong>${order.carrier || 'Nieznany'}</strong></td>
            <td style="white-space: nowrap;">
                ${email ? `<i class="fas fa-envelope text-primary me-2" style="cursor: pointer;" 
                    onclick="copyToClipboard('${email.replace(/'/g, "\\'")}', 'email-${index}')" 
                    title="${email}"></i>
                    <span id="email-${index}" class="copy-notification" style="display:none; font-size:0.7rem; color:green;">Skopiowano!</span>` : ''}
                ${contact ? `<i class="fas fa-info-circle text-info" style="cursor: pointer;" 
                    onclick="copyToClipboard('${contact.replace(/'/g, "\\'")}', 'contact-${index}')" 
                    title="${contact}"></i>
                    <span id="contact-${index}" class="copy-notification" style="display:none; font-size:0.7rem; color:green;">Skopiowano!</span>` : ''}
            </td>
            <td>${order.cargo_type || '-'}</td>
            <td>${order.rate_per_km ? order.rate_per_km.toFixed(2) : '-'} ${currencyDisplay}/km</td>
            <td><strong>${order.amount ? order.amount.toFixed(2) : '-'}</strong> ${currencyDisplay}</td>
            <td>${order.distance ? order.distance.toFixed(0) : '-'} km</td>
        </tr>`;
    });
    
    html += '</tbody></table></div>';
    container.innerHTML = html;
}


// Funkcja kopiowania do schowka
function copyToClipboard(text, notificationId) {
    navigator.clipboard.writeText(text).then(() => {
        // Pokaż komunikat "Skopiowano!"
        const notification = document.getElementById(notificationId);
        if (notification) {
            notification.style.display = 'inline';
            setTimeout(() => {
                notification.style.display = 'none';
            }, 2000);
        }
    }).catch(err => {
        console.error('Błąd kopiowania:', err);
        alert('Nie udało się skopiować do schowka');
    });
}


// Toggle szczegółów historycznych
document.addEventListener('click', function(e) {
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
