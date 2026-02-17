const API_BASE = 'https://stock-research-production-b3ac.up.railway.app/api';

let currentTicker = '';

// Helper functions (defined globally for use in displayResults)
function formatMarketCap(value) {
    if (!value) return 'N/A';
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toLocaleString()}`;
}

function formatPercent(value) {
    if (value === null || value === undefined) return 'N/A';
    return `${value.toFixed(2)}%`;
}

function formatNumber(value, decimals = 2) {
    if (value === null || value === undefined) return 'N/A';
    return value.toFixed(decimals);
}

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', () => {
    // DOM elements
    const searchForm = document.getElementById('searchForm');
    const tickerInput = document.getElementById('tickerInput');
    const searchBtn = document.getElementById('searchBtn');
    const searchSuggestions = document.getElementById('searchSuggestions');
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const errorMessage = document.getElementById('errorMessage');
    const retryBtn = document.getElementById('retryBtn');
    const empty = document.getElementById('empty');
    const results = document.getElementById('results');

    if (!searchForm) {
        console.error('Search form not found');
        return;
    }

    // Autocomplete functionality
    let searchTimeout = null;
    let selectedSuggestionIndex = -1;
    let currentSuggestions = [];

    async function fetchSuggestions(query) {
        if (!query || query.length < 1) {
            searchSuggestions.classList.add('hidden');
            return;
        }

        try {
            const response = await fetch(`${API_BASE}/stocks/search?q=${encodeURIComponent(query)}&limit=10`);
            if (response.ok) {
                const data = await response.json();
                currentSuggestions = data.results || [];
                renderSuggestions(currentSuggestions);
            }
        } catch (err) {
            console.error('Error fetching suggestions:', err);
        }
    }

    function renderSuggestions(suggestions) {
        if (suggestions.length === 0) {
            searchSuggestions.classList.add('hidden');
            return;
        }

        searchSuggestions.innerHTML = suggestions.map((item, index) => `
            <div class="suggestion-item" data-ticker="${item.ticker}" data-index="${index}">
                <div class="suggestion-main">
                    <span class="suggestion-ticker">${item.ticker}</span>
                    <span class="suggestion-name">${item.name}</span>
                </div>
                <span class="suggestion-sector">${item.sector}</span>
            </div>
        `).join('');

        searchSuggestions.classList.remove('hidden');
        selectedSuggestionIndex = -1;

        // Add click handlers
        searchSuggestions.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                const ticker = item.dataset.ticker;
                tickerInput.value = ticker;
                searchSuggestions.classList.add('hidden');
                loadStock(ticker);
            });
        });
    }

    // Input handling with debounce
    tickerInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            fetchSuggestions(query);
        }, 150);
    });

    // Keyboard navigation
    tickerInput.addEventListener('keydown', (e) => {
        if (currentSuggestions.length === 0) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            selectedSuggestionIndex = Math.min(selectedSuggestionIndex + 1, currentSuggestions.length - 1);
            updateSelection();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            selectedSuggestionIndex = Math.max(selectedSuggestionIndex - 1, -1);
            updateSelection();
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (selectedSuggestionIndex >= 0 && selectedSuggestionIndex < currentSuggestions.length) {
                const ticker = currentSuggestions[selectedSuggestionIndex].ticker;
                tickerInput.value = ticker;
                searchSuggestions.classList.add('hidden');
                loadStock(ticker);
            } else {
                const query = tickerInput.value.trim().toUpperCase();
                if (query) {
                    searchSuggestions.classList.add('hidden');
                    loadStock(query);
                }
            }
        } else if (e.key === 'Escape') {
            searchSuggestions.classList.add('hidden');
        }
    });

    function updateSelection() {
        const items = searchSuggestions.querySelectorAll('.suggestion-item');
        items.forEach((item, index) => {
            item.classList.toggle('active', index === selectedSuggestionIndex);
        });
    }

    // Hide suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchForm.contains(e.target)) {
            searchSuggestions.classList.add('hidden');
        }
    });

    // Refresh button handler - MOVED: auto-load at end of file
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            if (currentTicker) {
                refreshBtn.disabled = true;
                refreshBtn.textContent = 'Refreshing...';
                try {
                    await loadStock(currentTicker, true); // force refresh
                } finally {
                    refreshBtn.disabled = false;
                    refreshBtn.textContent = '↻ Refresh';
                }
            }
        });
    }

    // Tab switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            
            // Update active states
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(tabId).classList.add('active');
            
            // Redraw charts in the active tab (they might not render properly when hidden)
            if (window.lastChartData) {
                setTimeout(() => {
                    const chartData = [...window.lastChartData].reverse();
                    if (tabId === 'overview') {
                        drawPriceChart(window.lastPriceHistory || chartData);
                        drawEPSChart(chartData);
                    } else if (tabId === 'earnings') {
                        drawPriceChart(window.lastPriceHistory || chartData);
                        drawEPSChart(chartData);
                    } else if (tabId === 'financials') {
                        drawRevenueChart(chartData);
                        drawFCFChart(chartData);
                    } else if (tabId === 'valuation') {
                        drawPEChart(chartData, window.lastPriceHistory);
                    }
                }, 10);
            }
        });
    });

    // Search handler
    searchForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const ticker = tickerInput.value.trim().toUpperCase();
        if (!ticker) return;
        
        await loadStock(ticker);
    });

    // Retry handler
    retryBtn.addEventListener('click', () => {
        if (currentTicker) {
            loadStock(currentTicker);
        }
    });

    async function loadStock(ticker, forceRefresh = false) {
        currentTicker = ticker;
        
        // Show loading
        loading.classList.remove('hidden');
        error.classList.add('hidden');
        empty.classList.add('hidden');
        results.classList.add('hidden');
        searchBtn.disabled = true;
        
        const url = `${API_BASE}/stocks/${ticker}?refresh=${forceRefresh}`;
        
        try {
            const response = await fetch(url);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                let errorDetail = errorData.detail || `Server error: ${response.status}`;
                
                // Clean up error message for display
                if (errorDetail.includes('Finnhub') && errorDetail.includes('Yahoo') && errorDetail.includes('Alpha')) {
                    errorDetail = `Unable to fetch data for "${ticker}". All data sources failed. Please check the ticker symbol and try again.`;
                }
                
                throw new Error(errorDetail);
            }
            
            const data = await response.json();
            console.log('Received data:', data);
            
            // Validate data
            if (!data || !data.summary) {
                throw new Error('Invalid data structure received from server');
            }
            
            displayResults(data);
            
        } catch (err) {
            loading.classList.add('hidden');
            error.classList.remove('hidden');
            
            // Show user-friendly error
            let displayError = err.message;
            if (displayError.includes('Failed to fetch')) {
                displayError = 'Network error. Please check your connection and try again.';
            } else if (displayError.includes('404')) {
                displayError = `Stock "${ticker}" not found. Please check the ticker symbol.`;
            }
            
            errorMessage.innerHTML = `<strong>Error:</strong> ${displayError}<br><br><button onclick="document.getElementById('retryBtn').click()" class="retry-btn">Try Again</button>`;
            console.error('Load error:', err);
        } finally {
            searchBtn.disabled = false;
        }
    }

    function displayResults(data) {
        console.log('displayResults called with:', data);
        
        // Validate data structure
        if (!data || !data.summary) {
            console.error('Invalid data structure:', data);
            loading.classList.add('hidden');
            error.classList.remove('hidden');
            errorMessage.textContent = 'Invalid data received from server. Please try again.';
            return;
        }
        
        loading.classList.add('hidden');
        results.classList.remove('hidden');
        
        // Safely get summary values
        const summary = data.summary || {};
        
        // Update basic metrics
        document.getElementById('companyName').textContent = data.name || data.ticker || 'Unknown';
        document.getElementById('companyTicker').textContent = data.ticker || '';
        document.getElementById('currentPrice').textContent = summary.current_price 
            ? `$${summary.current_price.toFixed(2)}` 
            : 'N/A';
        document.getElementById('marketCap').textContent = formatMarketCap(summary.market_cap);
        document.getElementById('peRatio').textContent = formatNumber(summary.pe_ratio);
        
        // Update key financial metrics
        document.getElementById('revenueGrowth').textContent = formatPercent(summary.revenue_growth);
        document.getElementById('freeCashFlow').textContent = formatMarketCap(summary.free_cash_flow);
        document.getElementById('debtToEquity').textContent = formatNumber(summary.debt_to_equity);
        document.getElementById('roe').textContent = formatPercent(summary.roe);
        document.getElementById('profitMargin').textContent = formatPercent(summary.profit_margin);
        document.getElementById('operatingMargin').textContent = formatPercent(summary.operating_margin);
        
        // Valuation Metrics
        document.getElementById('psRatio').textContent = formatNumber(summary.ps_ratio);
        document.getElementById('pbRatio').textContent = formatNumber(summary.pb_ratio);
        document.getElementById('evebitda').textContent = formatNumber(summary.ev_ebitda);
        document.getElementById('marketCap2').textContent = formatMarketCap(summary.market_cap);
        document.getElementById('enterpriseValue').textContent = formatMarketCap(summary.enterprise_value);
        document.getElementById('sharesOutstanding').textContent = summary.shares_outstanding 
            ? formatNumber(summary.shares_outstanding / 1e9) + 'B' 
            : '-';
        
        // Profitability Metrics
        document.getElementById('grossMargin').textContent = formatPercent(summary.gross_margin);
        document.getElementById('ebitdaMargin').textContent = formatPercent(summary.ebitda_margin);
        document.getElementById('roa').textContent = formatPercent(summary.roa);
        document.getElementById('roic').textContent = formatPercent(summary.roic);
        
        // Financial Health
        document.getElementById('currentRatio').textContent = formatNumber(summary.current_ratio);
        document.getElementById('quickRatio').textContent = formatNumber(summary.quick_ratio);
        document.getElementById('interestCoverage').textContent = formatNumber(summary.interest_coverage);
        document.getElementById('cash').textContent = formatMarketCap(summary.cash);
        document.getElementById('workingCapital').textContent = formatMarketCap(summary.working_capital);
        
        // Market Data
        document.getElementById('price52wHigh').textContent = summary.price_52w_high 
            ? `$${summary.price_52w_high.toFixed(2)}` 
            : '-';
        document.getElementById('price52wLow').textContent = summary.price_52w_low 
            ? `$${summary.price_52w_low.toFixed(2)}` 
            : '-';
        
        // Calculate 52-week position
        if (summary.current_price && summary.price_52w_high && summary.price_52w_low) {
            const range = summary.price_52w_high - summary.price_52w_low;
            const position = ((summary.current_price - summary.price_52w_low) / range) * 100;
            document.getElementById('price52wPosition').textContent = `${position.toFixed(1)}%`;
        } else {
            document.getElementById('price52wPosition').textContent = '-';
        }
        
        document.getElementById('beta').textContent = formatNumber(summary.beta);
        document.getElementById('avgVolume').textContent = summary.avg_volume 
            ? formatNumber(summary.avg_volume / 1e6) + 'M' 
            : '-';
        
        // Draw charts (reverse data for chronological order)
        const chartData = [...data.earnings].reverse();
        window.lastChartData = chartData;  // Store for tab switching
        
        // Get active tab safely
        const activeTabEl = document.querySelector('.tab-content.active');
        const activeTab = activeTabEl ? activeTabEl.id : 'overview';
        
        console.log(`Drawing charts for active tab: ${activeTab}`);
        
        // Always draw charts for Overview on load
        // For now, use earnings data for price chart (will be updated when price history loads)
        drawPriceChart(chartData);
        drawEPSChart(chartData);
        
        // Fetch price history separately to avoid rate limits
        fetchPriceHistory(data.ticker);
        
        // Draw other charts if their tabs are active
        if (activeTab === 'financials') {
            drawRevenueChart(chartData);
            drawFCFChart(chartData);
        }
        if (activeTab === 'valuation') {
            drawPEChart(chartData, window.lastPriceHistory);
        }
    }

    // ============================================
    // AUTO-LOAD TSLA ON HOMEPAGE
    // ============================================
    console.log('Initializing auto-load for TSLA...');
    tickerInput.value = 'TSLA';
    empty.classList.add('hidden');
    loading.classList.remove('hidden');
    
    // Small delay to ensure everything is ready
    setTimeout(async () => {
        try {
            console.log('Auto-loading TSLA...');
            await loadStock('TSLA');
            console.log('TSLA loaded successfully');
        } catch (err) {
            console.error('Failed to load TSLA:', err);
            loading.classList.add('hidden');
            error.classList.remove('hidden');
            if (errorMessage) {
                errorMessage.textContent = err.message || 'Failed to load data';
            }
            // Show empty state again on error
            empty.classList.remove('hidden');
        }
    }, 100);

    // Store price history for P/E calculation
    window.lastPriceHistory = null;
    
    // Fetch price history separately to avoid rate limits
    async function fetchPriceHistory(ticker) {
        try {
            console.log(`Fetching price history for ${ticker}...`);
            const response = await fetch(`${API_BASE}/stocks/${ticker}/prices?days=365`);
            
            if (!response.ok) {
                console.log('Price history not available (rate limit or error)');
                return;
            }
            
            const data = await response.json();
            if (data.prices && data.prices.length > 0) {
                console.log(`Received ${data.prices.length} price points`);
                window.lastPriceHistory = data.prices;
                // Redraw price chart with real historical data
                drawPriceChart(data.prices);
                // Also redraw P/E chart if we have earnings data
                if (window.lastChartData) {
                    const chartData = [...window.lastChartData].reverse();
                    drawPEChart(chartData, data.prices);
                }
            }
        } catch (err) {
            console.log('Could not fetch price history:', err.message);
        }
    }

    // Chart drawing functions
function drawEPSChart(data) {
    const canvas = document.getElementById('epsChart');
    if (!canvas) return;
    
    // Show only last 4 quarters for cleaner chart
    const chartData = data.slice(-4);
    
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    
    // Set canvas size for retina displays
    canvas.width = 800 * dpr;
    canvas.height = 300 * dpr;
    ctx.scale(dpr, dpr);
    canvas.style.width = '100%';
    canvas.style.height = 'auto';
    
    const padding = { top: 40, right: 40, bottom: 60, left: 60 };
    const chartWidth = 800 - padding.left - padding.right;
    const chartHeight = 300 - padding.top - padding.bottom;
    
    // Clear
    ctx.clearRect(0, 0, 800, 300);
    
    // Check if we have data
    const allValues = [...chartData.map(d => d.reported_eps), ...chartData.map(d => d.estimated_eps)].filter(v => v != null);
    if (allValues.length === 0) {
        ctx.fillStyle = '#94a3b8';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No EPS data available', 400, 150);
        return;
    }
    
    const maxVal = Math.max(...allValues) * 1.1;
    const minVal = Math.min(...allValues) * 0.9;
    
    // Draw grid
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 5]);
    
    for (let i = 0; i <= 5; i++) {
        const y = padding.top + (chartHeight * i / 5);
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(padding.left + chartWidth, y);
        ctx.stroke();
        
        // Y-axis labels
        const val = maxVal - (maxVal - minVal) * i / 5;
        ctx.fillStyle = '#94a3b8';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(`$${val.toFixed(2)}`, padding.left - 10, y + 4);
    }
    
    ctx.setLineDash([]);
    
    // Draw bars (actual EPS)
    const barWidth = chartWidth / chartData.length * 0.6;
    const spacing = chartWidth / chartData.length;
    
    chartData.forEach((d, i) => {
        const x = padding.left + spacing * i + (spacing - barWidth) / 2;
        const barHeight = ((d.reported_eps - minVal) / (maxVal - minVal)) * chartHeight;
        const y = padding.top + chartHeight - barHeight;
        
        // Bar
        ctx.fillStyle = '#3b82f6';
        ctx.fillRect(x, y, barWidth, barHeight);
        
        // X label
        ctx.fillStyle = '#94a3b8';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(d.fiscal_date.slice(0, 7), x + barWidth / 2, padding.top + chartHeight + 20);
    });
    
    // Draw line (estimated EPS)
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 3;
    ctx.beginPath();
    
    chartData.forEach((d, i) => {
        const x = padding.left + spacing * i + spacing / 2;
        const y = padding.top + chartHeight - ((d.estimated_eps - minVal) / (maxVal - minVal)) * chartHeight;
        
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();
    
    // Draw dots for estimates
    chartData.forEach((d, i) => {
        const x = padding.left + spacing * i + spacing / 2;
        const y = padding.top + chartHeight - ((d.estimated_eps - minVal) / (maxVal - minVal)) * chartHeight;
        
        ctx.fillStyle = '#f59e0b';
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fill();
    });
    
    // Legend
    ctx.fillStyle = '#3b82f6';
    ctx.fillRect(padding.left, 15, 15, 15);
    ctx.fillStyle = '#e2e8f0';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Actual EPS', padding.left + 20, 27);
    
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(padding.left + 100, 22);
    ctx.lineTo(padding.left + 115, 22);
    ctx.stroke();
    ctx.fillStyle = '#f59e0b';
    ctx.beginPath();
    ctx.arc(padding.left + 107, 22, 4, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#e2e8f0';
    ctx.fillText('Estimated EPS', padding.left + 125, 27);
}

function drawRevenueChart(data) {
    const canvas = document.getElementById('revenueChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    
    canvas.width = 800 * dpr;
    canvas.height = 250 * dpr;
    ctx.scale(dpr, dpr);
    canvas.style.width = '100%';
    canvas.style.height = 'auto';
    
    const padding = { top: 30, right: 40, bottom: 50, left: 60 };
    const chartWidth = 800 - padding.left - padding.right;
    const chartHeight = 250 - padding.top - padding.bottom;
    
    ctx.clearRect(0, 0, 800, 250);
    
    const revenues = data.map(d => d.revenue / 1e9).filter(v => v > 0);
    if (revenues.length === 0) {
        ctx.fillStyle = '#94a3b8';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No revenue data available', 400, 125);
        return;
    }
    
    const maxRev = Math.max(...revenues) * 1.1;
    
    // Grid
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 5]);
    
    for (let i = 0; i <= 5; i++) {
        const y = padding.top + (chartHeight * i / 5);
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(padding.left + chartWidth, y);
        ctx.stroke();
        
        const val = maxRev - maxRev * i / 5;
        ctx.fillStyle = '#94a3b8';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(`$${val.toFixed(0)}B`, padding.left - 10, y + 4);
    }
    
    ctx.setLineDash([]);
    
    // Bars
    const barWidth = chartWidth / data.length * 0.6;
    const spacing = chartWidth / data.length;
    
    data.forEach((d, i) => {
        const x = padding.left + spacing * i + (spacing - barWidth) / 2;
        const barHeight = (d.revenue / 1e9 / maxRev) * chartHeight;
        const y = padding.top + chartHeight - barHeight;
        
        ctx.fillStyle = '#10b981';
        ctx.fillRect(x, y, barWidth, barHeight);
        
        ctx.fillStyle = '#94a3b8';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(d.fiscal_date.slice(0, 7), x + barWidth / 2, padding.top + chartHeight + 20);
    });
}

function drawFCFChart(data) {
    const canvas = document.getElementById('fcfChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    
    canvas.width = 800 * dpr;
    canvas.height = 250 * dpr;
    ctx.scale(dpr, dpr);
    canvas.style.width = '100%';
    canvas.style.height = 'auto';
    
    const padding = { top: 30, right: 60, bottom: 50, left: 60 };
    const chartWidth = 800 - padding.left - padding.right;
    const chartHeight = 250 - padding.top - padding.bottom;
    
    ctx.clearRect(0, 0, 800, 250);
    
    const fcfs = data.map(d => d.free_cash_flow / 1e9).filter(v => v > 0);
    if (fcfs.length === 0) {
        ctx.fillStyle = '#94a3b8';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No free cash flow data available', 400, 125);
        return;
    }
    
    const maxFCF = Math.max(...fcfs) * 1.1;
    
    // Grid
    ctx.strokeStyle = '#334155';
    ctx.setLineDash([5, 5]);
    
    for (let i = 0; i <= 5; i++) {
        const y = padding.top + (chartHeight * i / 5);
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(padding.left + chartWidth, y);
        ctx.stroke();
        
        const val = maxFCF - maxFCF * i / 5;
        ctx.fillStyle = '#94a3b8';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(`$${val.toFixed(0)}B`, padding.left - 10, y + 4);
    }
    
    ctx.setLineDash([]);
    
    // Bars (FCF)
    const barWidth = chartWidth / data.length * 0.5;
    const spacing = chartWidth / data.length;
    
    data.forEach((d, i) => {
        const x = padding.left + spacing * i + (spacing - barWidth) / 2;
        const barHeight = (d.free_cash_flow / 1e9 / maxFCF) * chartHeight;
        const y = padding.top + chartHeight - barHeight;
        
        ctx.fillStyle = '#06b6d4';
        ctx.fillRect(x, y, barWidth, barHeight);
        
        ctx.fillStyle = '#94a3b8';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(d.fiscal_date.slice(0, 7), x + barWidth / 2, padding.top + chartHeight + 20);
    });
    
    // Legend
    ctx.fillStyle = '#06b6d4';
    ctx.fillRect(padding.left, 10, 15, 15);
    ctx.fillStyle = '#e2e8f0';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Free Cash Flow', padding.left + 20, 22);
}

function drawPEChart(data, priceHistory = null) {
    const canvas = document.getElementById('peChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    
    canvas.width = 800 * dpr;
    canvas.height = 250 * dpr;
    ctx.scale(dpr, dpr);
    canvas.style.width = '100%';
    canvas.style.height = 'auto';
    
    const padding = { top: 30, right: 40, bottom: 50, left: 60 };
    const chartWidth = 800 - padding.left - padding.right;
    const chartHeight = 250 - padding.top - padding.bottom;
    
    ctx.clearRect(0, 0, 800, 250);
    
    // Calculate P/E from price history if available
    let peData = data.map(d => ({ ...d }));
    
    if (priceHistory && priceHistory.length > 0) {
        // Create price lookup by date
        const priceByDate = {};
        priceHistory.forEach(p => {
            priceByDate[p.date] = p.close;
        });
        
        // Calculate P/E for each quarter
        peData = peData.map((d, i) => {
            const entry = { ...d };
            
            // Calculate TTM EPS (sum of this + 3 previous quarters)
            let ttmEps = 0;
            let quarters = 0;
            for (let j = i; j < Math.min(i + 4, peData.length); j++) {
                if (peData[j].reported_eps > 0) {
                    ttmEps += peData[j].reported_eps;
                    quarters++;
                }
            }
            
            // Find price on or near earnings date
            if (quarters >= 3 && ttmEps > 0) {
                const fiscalDate = d.fiscal_date;
                let price = priceByDate[fiscalDate];
                
                // Try nearby dates if exact match not found
                if (!price) {
                    const date = new Date(fiscalDate);
                    for (let offset = 1; offset <= 5 && !price; offset++) {
                        const fwd = new Date(date);
                        fwd.setDate(fwd.getDate() + offset);
                        price = priceByDate[fwd.toISOString().split('T')[0]];
                        
                        if (!price) {
                            const back = new Date(date);
                            back.setDate(back.getDate() - offset);
                            price = priceByDate[back.toISOString().split('T')[0]];
                        }
                    }
                }
                
                if (price) {
                    entry.pe_ratio = price / ttmEps;
                    entry.price = price;
                }
            }
            
            return entry;
        });
    }
    
    const pes = peData.map(d => d.pe_ratio).filter(v => v != null && !isNaN(v));
    
    if (pes.length === 0) {
        ctx.fillStyle = '#94a3b8';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No P/E data available', 400, 125);
        return;
    }
    
    const maxPE = Math.max(...pes) * 1.1;
    const minPE = Math.min(...pes) * 0.9;
    
    // Grid
    ctx.strokeStyle = '#334155';
    ctx.setLineDash([5, 5]);
    
    for (let i = 0; i <= 5; i++) {
        const y = padding.top + (chartHeight * i / 5);
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(padding.left + chartWidth, y);
        ctx.stroke();
        
        const val = maxPE - (maxPE - minPE) * i / 5;
        ctx.fillStyle = '#94a3b8';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(`${val.toFixed(0)}x`, padding.left - 10, y + 4);
    }
    
    ctx.setLineDash([]);
    
    // Area chart (simplified as line with fill)
    const spacing = chartWidth / (peData.length - 1);
    
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top + chartHeight);
    
    peData.forEach((d, i) => {
        if (d.pe_ratio != null && !isNaN(d.pe_ratio)) {
            const x = padding.left + spacing * i;
            const y = padding.top + chartHeight - ((d.pe_ratio - minPE) / (maxPE - minPE)) * chartHeight;
            ctx.lineTo(x, y);
        }
    });
    
    ctx.lineTo(padding.left + chartWidth, padding.top + chartHeight);
    ctx.closePath();
    
    ctx.fillStyle = 'rgba(139, 92, 246, 0.2)';
    ctx.fill();
    
    // Line
    ctx.strokeStyle = '#8b5cf6';
    ctx.lineWidth = 3;
    ctx.beginPath();
    
    let started = false;
    peData.forEach((d, i) => {
        if (d.pe_ratio != null && !isNaN(d.pe_ratio)) {
            const x = padding.left + spacing * i;
            const y = padding.top + chartHeight - ((d.pe_ratio - minPE) / (maxPE - minPE)) * chartHeight;
            
            if (!started) {
                ctx.moveTo(x, y);
                started = true;
            } else {
                ctx.lineTo(x, y);
            }
        }
    });
    ctx.stroke();
    
    // X labels
    peData.forEach((d, i) => {
        const x = padding.left + spacing * i;
        ctx.fillStyle = '#94a3b8';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(d.fiscal_date.slice(0, 7), x, padding.top + chartHeight + 20);
    });
}

function drawPriceChart(data) {
    const canvas = document.getElementById('priceChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    
    canvas.width = 800 * dpr;
    canvas.height = 300 * dpr;
    ctx.scale(dpr, dpr);
    canvas.style.width = '100%';
    canvas.style.height = 'auto';
    
    const padding = { top: 40, right: 40, bottom: 60, left: 70 };
    const chartWidth = 800 - padding.left - padding.right;
    const chartHeight = 300 - padding.top - padding.bottom;
    
    ctx.clearRect(0, 0, 800, 300);
    
    // Handle both formats: price_history (close) and earnings (price)
    const prices = data.map(d => d.close || d.price).filter(v => v != null);
    if (prices.length === 0) {
        ctx.fillStyle = '#94a3b8';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No price data available', 400, 150);
        return;
    }
    
    const maxPrice = Math.max(...prices) * 1.05;
    const minPrice = Math.min(...prices) * 0.95;
    const priceRange = maxPrice - minPrice;
    
    // Grid
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 5]);
    
    for (let i = 0; i <= 5; i++) {
        const y = padding.top + (chartHeight * i / 5);
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(padding.left + chartWidth, y);
        ctx.stroke();
        
        const val = maxPrice - priceRange * i / 5;
        ctx.fillStyle = '#94a3b8';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(`$${val.toFixed(0)}`, padding.left - 10, y + 4);
    }
    
    ctx.setLineDash([]);
    
    // Area under line
    const spacing = chartWidth / (data.length - 1);
    
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top + chartHeight);
    
    data.forEach((d, i) => {
        const price = d.close || d.price;
        const x = padding.left + spacing * i;
        const y = padding.top + chartHeight - ((price - minPrice) / priceRange) * chartHeight;
        ctx.lineTo(x, y);
    });
    
    ctx.lineTo(padding.left + chartWidth, padding.top + chartHeight);
    ctx.closePath();
    
    ctx.fillStyle = 'rgba(16, 185, 129, 0.15)';  // Green with opacity
    ctx.fill();
    
    // Price line
    ctx.strokeStyle = '#10b981';  // Green
    ctx.lineWidth = 3;
    ctx.beginPath();
    
    data.forEach((d, i) => {
        const price = d.close || d.price;
        const x = padding.left + spacing * i;
        const y = padding.top + chartHeight - ((price - minPrice) / priceRange) * chartHeight;
        
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();
    
    // Data points (only show every ~20th point to avoid clutter)
    data.forEach((d, i) => {
        if (i % 20 !== 0) return;  // Show every 20th point
        const price = d.close || d.price;
        const x = padding.left + spacing * i;
        const y = padding.top + chartHeight - ((price - minPrice) / priceRange) * chartHeight;
        
        ctx.fillStyle = '#10b981';
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
        
        // White border on dots
        ctx.strokeStyle = '#1e293b';
        ctx.lineWidth = 2;
        ctx.stroke();
    });
    
    // X labels (show monthly labels)
    let lastMonth = '';
    data.forEach((d, i) => {
        const dateStr = d.date || d.fiscal_date;
        const month = dateStr.slice(0, 7);  // YYYY-MM
        if (month === lastMonth) return;  // Skip if same month
        lastMonth = month;
        
        const x = padding.left + spacing * i;
        ctx.fillStyle = '#94a3b8';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(month, x, padding.top + chartHeight + 20);
    });
    
    // Legend
    ctx.fillStyle = '#10b981';
    ctx.fillRect(padding.left, 15, 15, 15);
    ctx.fillStyle = '#e2e8f0';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Stock Price', padding.left + 20, 27);
    
    // Calculate and show change
    const firstPrice = data[0]?.close || data[0]?.price;
    const lastPrice = data[data.length - 1]?.close || data[data.length - 1]?.price;
    if (firstPrice && lastPrice) {
        const change = ((lastPrice - firstPrice) / firstPrice) * 100;
        const changeColor = change >= 0 ? '#22c55e' : '#ef4444';
        const changeSymbol = change >= 0 ? '+' : '';
        const periodLabel = data.length > 100 ? '1Y' : '8Q';  // Show 1Y for daily data
        
        ctx.fillStyle = changeColor;
        ctx.font = 'bold 12px sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText(`${changeSymbol}${change.toFixed(1)}% (${periodLabel})`, padding.left + 110, 27);
    }
}
});
