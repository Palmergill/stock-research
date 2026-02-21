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

// Store previous values for flash animation
window.previousValues = {};

// Helper to update value with flash animation
function updateValueWithFlash(elementId, newValue, formatter = (v) => v) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const oldValue = window.previousValues[elementId];
    const formattedNew = formatter(newValue);
    
    // Skip if first load or no change
    if (oldValue === undefined || oldValue === formattedNew) {
        element.textContent = formattedNew;
        window.previousValues[elementId] = formattedNew;
        return;
    }
    
    // Determine direction for color flash
    const oldNum = parseFloat(oldValue.toString().replace(/[^0-9.-]/g, ''));
    const newNum = parseFloat(formattedNew.toString().replace(/[^0-9.-]/g, ''));
    
    element.classList.remove('flash-up', 'flash-down');
    void element.offsetWidth; // Trigger reflow
    
    if (!isNaN(oldNum) && !isNaN(newNum)) {
        if (newNum > oldNum) {
            element.classList.add('flash-up');
        } else if (newNum < oldNum) {
            element.classList.add('flash-down');
        }
    }
    
    element.textContent = formattedNew;
    window.previousValues[elementId] = formattedNew;
    
    // Remove animation class after animation completes
    setTimeout(() => {
        element.classList.remove('flash-up', 'flash-down');
    }, 800);
}

// Calculate trends from earnings data and update metric indicators
function calculateAndDisplayTrends(earnings) {
    if (!earnings || earnings.length < 2) return;
    
    // Sort by date (oldest first)
    const sorted = [...earnings].sort((a, b) => new Date(a.fiscal_date) - new Date(b.fiscal_date));
    const recent = sorted.slice(-4); // Last 4 quarters
    const older = sorted.slice(-8, -4); // 4 quarters before that
    
    if (recent.length < 2) return;
    
    // Calculate revenue trend
    const recentRevenue = recent.reduce((sum, e) => sum + (e.revenue || 0), 0) / recent.length;
    const olderRevenue = older.length > 0 ? older.reduce((sum, e) => sum + (e.revenue || 0), 0) / older.length : recentRevenue;
    const revenueTrend = recentRevenue > olderRevenue * 1.05 ? 'up' : recentRevenue < olderRevenue * 0.95 ? 'down' : 'neutral';
    updateMetricTrend('revenueGrowth', revenueTrend);
    
    // Calculate EPS trend
    const recentEPS = recent.reduce((sum, e) => sum + (e.basic_eps || 0), 0) / recent.length;
    const olderEPS = older.length > 0 ? older.reduce((sum, e) => sum + (e.basic_eps || 0), 0) / older.length : recentEPS;
    const epsTrend = recentEPS > olderEPS * 1.1 ? 'up' : recentEPS < olderEPS * 0.9 ? 'down' : 'neutral';
    updateMetricTrend('peRatio', epsTrend); // P/E trend based on EPS direction
    
    // Calculate FCF trend (if available)
    const recentFCF = recent.reduce((sum, e) => sum + (e.free_cash_flow || 0), 0) / recent.length;
    const olderFCF = older.length > 0 ? older.reduce((sum, e) => sum + (e.free_cash_flow || 0), 0) / older.length : recentFCF;
    const fcfTrend = recentFCF > olderFCF * 1.1 ? 'up' : recentFCF < olderFCF * 0.9 ? 'down' : 'neutral';
    updateMetricTrend('freeCashFlow', fcfTrend);
}

function updateMetricTrend(elementId, trend) {
    const element = document.getElementById(elementId);
    if (!element) return;
    const metricCard = element.closest('.metric');
    if (metricCard) {
        metricCard.dataset.trend = trend;
    }
}

// Count-up animation helper
function animateCountUp(element, start, end, duration = 500, prefix = '', suffix = '', decimals = 2) {
    if (!element) return;
    
    if (start === end || isNaN(start) || isNaN(end)) {
        element.textContent = `${prefix}${end.toFixed(decimals)}${suffix}`;
        return;
    }
    
    const range = end - start;
    const minTimer = 50;
    let stepTime = Math.abs(Math.floor(duration / range));
    stepTime = Math.max(stepTime, minTimer);
    
    let startTime = new Date().getTime();
    let endTime = startTime + duration;
    let timer;
    
    function run() {
        let now = new Date().getTime();
        let remaining = Math.max((endTime - now) / duration, 0);
        let value = Math.round(end - (remaining * range));
        let displayValue = decimals > 0 ? (start + (end - start) * (1 - remaining)).toFixed(decimals) : value;
        element.textContent = `${prefix}${displayValue}${suffix}`;
        
        if (value == end) {
            clearInterval(timer);
            element.textContent = `${prefix}${end.toFixed(decimals)}${suffix}`;
        }
    }
    
    timer = setInterval(run, stepTime);
    run();
}

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', () => {
    
    // Add ripple effect to all buttons
    function createRipple(event) {
        const button = event.currentTarget;
        const circle = document.createElement('span');
        const diameter = Math.max(button.clientWidth, button.clientHeight);
        const radius = diameter / 2;
        
        circle.style.width = circle.style.height = `${diameter}px`;
        circle.style.left = `${event.clientX - button.getBoundingClientRect().left - radius}px`;
        circle.style.top = `${event.clientY - button.getBoundingClientRect().top - radius}px`;
        circle.classList.add('ripple');
        
        const existingRipple = button.getElementsByClassName('ripple')[0];
        if (existingRipple) {
            existingRipple.remove();
        }
        
        button.appendChild(circle);
        
        setTimeout(() => circle.remove(), 600);
    }
    
    document.querySelectorAll('button').forEach(button => {
        button.addEventListener('click', createRipple);
    });
    
    // Magnetic button effect for primary buttons
    function initMagneticButtons() {
        const magneticButtons = document.querySelectorAll('button:not(.tab-btn):not(.refresh-btn)');
        
        magneticButtons.forEach(button => {
            button.classList.add('magnetic');
            
            button.addEventListener('mousemove', (e) => {
                const rect = button.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;
                
                // Magnetic pull strength (max 8px movement)
                const strength = 0.3;
                const maxMove = 8;
                
                const moveX = Math.max(-maxMove, Math.min(maxMove, x * strength));
                const moveY = Math.max(-maxMove, Math.min(maxMove, y * strength));
                
                button.style.transform = `translate(${moveX}px, ${moveY}px)`;
            });
            
            button.addEventListener('mouseleave', () => {
                button.style.transform = '';
            });
        });
    }
    
    initMagneticButtons();
    
    // Initialize custom metric tooltips
    function initMetricTooltips() {
        const tooltip = document.getElementById('metricTooltip');
        if (!tooltip) return;
        
        const titleEl = tooltip.querySelector('.tooltip-title');
        const descEl = tooltip.querySelector('.tooltip-description');
        
        // Find all metric cards with title attributes
        document.querySelectorAll('.metric[title]').forEach(metric => {
            const titleText = metric.getAttribute('title');
            if (!titleText) return;
            
            // Extract label as title and rest as description
            const labelEl = metric.querySelector('.metric-label');
            const label = labelEl ? labelEl.textContent : 'Metric';
            
            // Remove default title to prevent browser tooltip
            metric.removeAttribute('title');
            metric.dataset.tooltipTitle = label;
            metric.dataset.tooltipDesc = titleText;
            
            metric.addEventListener('mouseenter', (e) => {
                titleEl.textContent = label;
                descEl.textContent = titleText;
                tooltip.classList.remove('hidden');
                
                // Position tooltip
                positionTooltip(e, tooltip, metric);
            });
            
            metric.addEventListener('mousemove', (e) => {
                positionTooltip(e, tooltip, metric);
            });
            
            metric.addEventListener('mouseleave', () => {
                tooltip.classList.add('hidden');
            });
        });
        
        function positionTooltip(e, tooltip, metric) {
            const rect = metric.getBoundingClientRect();
            const tooltipRect = tooltip.getBoundingClientRect();
            
            // Position above the metric by default
            let top = rect.top - tooltipRect.height - 12;
            let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);
            
            // Adjust if going off screen
            if (top < 10) {
                top = rect.bottom + 12; // Show below if not enough space above
            }
            if (left < 10) {
                left = 10;
            } else if (left + tooltipRect.width > window.innerWidth - 10) {
                left = window.innerWidth - tooltipRect.width - 10;
            }
            
            tooltip.style.top = `${top}px`;
            tooltip.style.left = `${left}px`;
        }
    }
    
    // Run after a short delay to ensure DOM is ready
    setTimeout(initMetricTooltips, 100);
    
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
    
    // Verify critical elements exist
    if (!searchForm || !tickerInput || !searchBtn) {
        console.error('Missing elements:', { searchForm, tickerInput, searchBtn });
        return;
    }
    
    // Initialize trending stock buttons
    function initTrendingStocks() {
        document.querySelectorAll('.trending-stock').forEach(btn => {
            btn.addEventListener('click', () => {
                const ticker = btn.dataset.ticker;
                if (ticker) {
                    tickerInput.value = ticker;
                    loadStock(ticker);
                }
            });
        });
    }
    
    initTrendingStocks();

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
            searchSuggestions.classList.remove('visible');
            setTimeout(() => searchSuggestions.classList.add('hidden'), 200);
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
            searchSuggestions.classList.remove('visible');
            setTimeout(() => searchSuggestions.classList.add('hidden'), 200);
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
        // Trigger animation in next frame
        requestAnimationFrame(() => {
            searchSuggestions.classList.add('visible');
        });
        selectedSuggestionIndex = -1;

        // Add click handlers
        searchSuggestions.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                const ticker = item.dataset.ticker;
                tickerInput.value = ticker;
                searchSuggestions.classList.remove('visible');
                setTimeout(() => searchSuggestions.classList.add('hidden'), 200);
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
                searchSuggestions.classList.remove('visible');
                setTimeout(() => searchSuggestions.classList.add('hidden'), 200);
                loadStock(ticker);
            } else {
                const query = tickerInput.value.trim().toUpperCase();
                if (query) {
                    searchSuggestions.classList.remove('visible');
                    setTimeout(() => searchSuggestions.classList.add('hidden'), 200);
                    loadStock(query);
                }
            }
        } else if (e.key === 'Escape') {
            searchSuggestions.classList.remove('visible');
            setTimeout(() => searchSuggestions.classList.add('hidden'), 200);
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
            searchSuggestions.classList.remove('visible');
            setTimeout(() => searchSuggestions.classList.add('hidden'), 200);
        }
    });

    // Refresh button handler - MOVED: auto-load at end of file
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            if (currentTicker) {
                const spinner = refreshBtn.querySelector('.refresh-spinner');
                refreshBtn.disabled = true;
                refreshBtn.classList.add('loading');
                if (spinner) spinner.classList.remove('hidden');
                
                try {
                    await loadStock(currentTicker, true); // force refresh
                } finally {
                    refreshBtn.disabled = false;
                    refreshBtn.classList.remove('loading');
                    if (spinner) spinner.classList.add('hidden');
                }
            }
        });
    }

    // Tab switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const tabIndicator = document.querySelector('.tab-indicator');
    const tabsContainer = document.querySelector('.tabs');
    
    // Function to update sliding indicator position
    function updateTabIndicator(activeBtn) {
        if (!tabIndicator || !activeBtn) return;
        
        const tabsRect = tabsContainer.getBoundingClientRect();
        const btnRect = activeBtn.getBoundingClientRect();
        
        const left = btnRect.left - tabsRect.left;
        const width = btnRect.width;
        
        tabIndicator.style.transform = `translateX(${left}px)`;
        tabIndicator.style.width = `${width}px`;
    }
    
    // Initialize indicator on page load
    const initialActiveTab = document.querySelector('.tab-btn.active');
    if (initialActiveTab) {
        setTimeout(() => updateTabIndicator(initialActiveTab), 0);
    }
    
    // Update indicator on window resize
    window.addEventListener('resize', () => {
        const activeTab = document.querySelector('.tab-btn.active');
        updateTabIndicator(activeTab);
    });
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.dataset.tab;
            
            // Update active states
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(tabId).classList.add('active');
            
            // Update sliding indicator
            updateTabIndicator(btn);
            
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
    async function handleSearch(e) {
        if (e) e.preventDefault();
        const ticker = tickerInput.value.trim().toUpperCase();
        if (!ticker) return;
        
        // Shelby Easter Egg
        if (ticker === 'SHELBY') {
            showShelbyEasterEgg();
            return;
        }
        
        // Visual feedback
        const btnText = searchBtn.querySelector('.btn-text');
        const btnSpinner = searchBtn.querySelector('.btn-spinner');
        if (btnText) btnText.classList.add('hidden');
        if (btnSpinner) btnSpinner.classList.remove('hidden');
        searchBtn.disabled = true;
        
        try {
            await loadStock(ticker);
        } catch (err) {
            console.error('Error loading stock:', err);
        } finally {
            if (btnText) btnText.classList.remove('hidden');
            if (btnSpinner) btnSpinner.classList.add('hidden');
            searchBtn.disabled = false;
        }
    }
    
    searchForm.addEventListener('submit', handleSearch);
    
    // ============================================
    // SHELBY EASTER EGG
    // ============================================
    function showShelbyEasterEgg() {
        const overlay = document.getElementById('shelbyOverlay');
        const canvas = document.getElementById('shelbyCanvas');
        const message = document.getElementById('shelbyMessage');
        const heartsContainer = document.getElementById('shelbyHearts');
        const hint = document.querySelector('.shelby-hint');
        
        if (!overlay || !canvas) return;
        
        // Show overlay
        overlay.classList.remove('hidden');
        setTimeout(() => overlay.classList.add('visible'), 10);
        
        // Setup canvas
        const ctx = canvas.getContext('2d');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        
        // Heart drawing animation - positioned below the text
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2 + 80; // Moved down to make room for text
        const size = Math.min(canvas.width, canvas.height) * 0.22; // Slightly smaller
        
        let progress = 0;
        const duration = 3000; // 3 seconds to draw
        const startTime = performance.now();
        let heartsStarted = false;
        
        function drawHeart(p) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // Draw heart path with sparkle
            ctx.beginPath();
            ctx.strokeStyle = '#ff1744';
            ctx.lineWidth = 4;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            ctx.shadowBlur = 20;
            ctx.shadowColor = '#ff1744';
            
            // Heart shape using parametric equations
            const points = [];
            const totalPoints = 200;
            const drawPoints = Math.floor(totalPoints * p);
            
            for (let i = 0; i <= drawPoints; i++) {
                const t = (i / totalPoints) * Math.PI * 2;
                const x = centerX + size * (16 * Math.pow(Math.sin(t), 3)) / 16;
                const y = centerY - size * (13 * Math.cos(t) - 5 * Math.cos(2*t) - 2 * Math.cos(3*t) - Math.cos(4*t)) / 16;
                points.push({x, y});
            }
            
            if (points.length > 1) {
                ctx.moveTo(points[0].x, points[0].y);
                for (let i = 1; i < points.length; i++) {
                    ctx.lineTo(points[i].x, points[i].y);
                }
                ctx.stroke();
                
                // Add sparkle at the end
                if (points.length > 5) {
                    const last = points[points.length - 1];
                    ctx.shadowBlur = 30;
                    ctx.fillStyle = '#fff';
                    ctx.beginPath();
                    ctx.arc(last.x, last.y, 6, 0, Math.PI * 2);
                    ctx.fill();
                }
            }
            
            // Add glow effect
            if (p > 0.8) {
                ctx.globalAlpha = (p - 0.8) * 5;
                ctx.fillStyle = '#ff1744';
                ctx.beginPath();
                for (let i = 0; i < points.length; i++) {
                    const t = (i / totalPoints) * Math.PI * 2;
                    const x = centerX + size * 0.9 * (16 * Math.pow(Math.sin(t), 3)) / 16;
                    const y = centerY - size * 0.9 * (13 * Math.cos(t) - 5 * Math.cos(2*t) - 2 * Math.cos(3*t) - Math.cos(4*t)) / 16;
                    if (i === 0) ctx.moveTo(x, y);
                    else ctx.lineTo(x, y);
                }
                ctx.fill();
                ctx.globalAlpha = 1;
            }
        }
        
        function animate(currentTime) {
            const elapsed = currentTime - startTime;
            progress = Math.min(elapsed / duration, 1);
            
            drawHeart(progress);
            
            // Start hearts early (at 30% progress)
            if (progress > 0.3 && !heartsStarted) {
                heartsStarted = true;
                startFloatingHearts();
            }
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                // Show message when heart is complete
                message.classList.add('visible');
                // Show hint
                setTimeout(() => hint.classList.add('visible'), 2000);
            }
        }
        
        requestAnimationFrame(animate);
        
        // Floating hearts
        function startFloatingHearts() {
            const heartEmojis = ['❤️', '💕', '💗', '💖', '💝'];
            
            function createHeart() {
                const heart = document.createElement('div');
                heart.className = 'shelby-heart';
                heart.textContent = heartEmojis[Math.floor(Math.random() * heartEmojis.length)];
                heart.style.left = Math.random() * 100 + '%';
                heart.style.fontSize = (16 + Math.random() * 24) + 'px';
                heart.style.animationDuration = (3 + Math.random() * 3) + 's';
                heart.style.animationDelay = Math.random() * 2 + 's';
                heartsContainer.appendChild(heart);
                
                // Remove after animation
                setTimeout(() => heart.remove(), 7000);
            }
            
            // Create hearts continuously
            const heartInterval = setInterval(createHeart, 300);
            
            // Store interval for cleanup
            overlay.dataset.heartInterval = heartInterval;
        }
        
        // Click to close
        function closeOverlay() {
            overlay.classList.remove('visible');
            setTimeout(() => {
                overlay.classList.add('hidden');
                message.classList.remove('visible');
                hint.classList.remove('visible');
                heartsContainer.innerHTML = '';
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                if (overlay.dataset.heartInterval) {
                    clearInterval(parseInt(overlay.dataset.heartInterval));
                }
            }, 1000);
            overlay.removeEventListener('click', closeOverlay);
            overlay.removeEventListener('touchstart', closeOverlay);
        }
        
        setTimeout(() => {
            overlay.addEventListener('click', closeOverlay);
            overlay.addEventListener('touchstart', closeOverlay);
        }, 4000); // Allow close after animation
    }

    // Retry handler
    retryBtn.addEventListener('click', () => {
        // Clear any running countdown
        if (window.currentRetryInterval) {
            clearInterval(window.currentRetryInterval);
            window.currentRetryInterval = null;
        }
        const retryCountdown = document.getElementById('retryCountdown');
        if (retryCountdown) retryCountdown.classList.add('hidden');
        retryBtn.classList.remove('hidden');
        
        if (currentTicker) {
            loadStock(currentTicker);
        }
    });
    
    // Update loading progress bar
    function updateLoadingProgress(step) {
        const progressFill = document.querySelector('#loadingProgress .progress-fill');
        const steps = document.querySelectorAll('.progress-step');
        
        if (progressFill) {
            const progress = (step / 3) * 100;
            progressFill.style.width = `${progress}%`;
        }
        
        steps.forEach((s, index) => {
            s.classList.remove('active', 'completed');
            if (index + 1 === step) {
                s.classList.add('active');
            } else if (index + 1 < step) {
                s.classList.add('completed');
            }
        });
    }
    
    // Stock tips for loading state
    const stockTips = [
        { icon: '💡', text: 'The P/E ratio helps compare valuations across companies.' },
        { icon: '📈', text: 'Revenue growth shows if a business is expanding over time.' },
        { icon: '💰', text: 'Free Cash Flow is more reliable than net income for analysis.' },
        { icon: '⚖️', text: 'Debt-to-Equity ratio shows financial risk and flexibility.' },
        { icon: '🎯', text: 'ROE above 15% often signals a competitive advantage.' },
        { icon: '📊', text: 'EPS surprises drive stock price movements on earnings day.' },
        { icon: '🔍', text: 'Compare P/E ratios to industry averages for context.' },
        { icon: '📉', text: '52-week range shows where current price sits historically.' }
    ];
    
    let tipInterval = null;
    let currentTipIndex = 0;
    
    function startStockTips() {
        const tipContainer = document.getElementById('stockTip');
        if (!tipContainer) return;
        
        // Clear any existing interval
        if (tipInterval) clearInterval(tipInterval);
        
        currentTipIndex = 0;
        updateTip(tipContainer, 0);
        
        tipInterval = setInterval(() => {
            currentTipIndex = (currentTipIndex + 1) % stockTips.length;
            
            // Fade out
            tipContainer.classList.add('fade-out');
            
            setTimeout(() => {
                updateTip(tipContainer, currentTipIndex);
                tipContainer.classList.remove('fade-out');
            }, 500);
        }, 4000);
    }
    
    function stopStockTips() {
        if (tipInterval) {
            clearInterval(tipInterval);
            tipInterval = null;
        }
    }
    
    function updateTip(container, index) {
        const tip = stockTips[index];
        const iconSpan = container.querySelector('.tip-icon');
        const textSpan = container.querySelector('.tip-text');
        if (iconSpan) iconSpan.textContent = tip.icon;
        if (textSpan) textSpan.textContent = tip.text;
    }

    async function loadStock(ticker, forceRefresh = false, attempt = 1) {
        currentTicker = ticker;
        
        // Show loading
        loading.classList.remove('hidden');
        error.classList.add('hidden');
        empty.classList.add('hidden');
        results.classList.remove('visible');
        results.classList.add('hidden');
        searchBtn.disabled = true;
        
        // Show loading spinners
        const inputSpinner = document.getElementById('inputSpinner');
        const btnSpinner = document.querySelector('#searchBtn .btn-spinner');
        if (inputSpinner) inputSpinner.classList.remove('hidden');
        if (btnSpinner) btnSpinner.classList.remove('hidden');
        searchBtn.classList.add('loading');
        
        // Start rotating stock tips
        startStockTips();
        
        // Update progress bar
        updateLoadingProgress(1);
        
        const url = `${API_BASE}/stocks/${ticker}?refresh=${forceRefresh}`;
        console.log('Fetching URL:', url);
        
        try {
            const response = await fetch(url);
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                let errorDetail = errorData.detail || `Server error: ${response.status}`;
                
                // Clean up error message for display
                if (errorDetail.includes('Finnhub') && errorDetail.includes('Yahoo') && errorDetail.includes('Alpha')) {
                    errorDetail = `Unable to fetch data for "${ticker}". All data sources failed. Please check the ticker symbol and try again.`;
                }
                
                throw new Error(errorDetail);
            }
            
            // Update progress - step 1 complete
            updateLoadingProgress(2);
            
            const data = await response.json();
            console.log('Received data:', data);
            
            // Validate data
            if (!data || !data.summary) {
                throw new Error('Invalid data structure received from server');
            }
            
            // Fetch price history
            await fetchPriceHistory(ticker);
            
            // Update progress - step 2 complete
            updateLoadingProgress(3);
            
            displayResults(data);
            
        } catch (err) {
            console.error('Error in loadStock fetch:', err);
            loading.classList.add('hidden');
            error.classList.remove('hidden');
            
            // Auto-retry logic (max 3 attempts)
            if (attempt < 3) {
                const retryCountdown = document.getElementById('retryCountdown');
                const countdownSpan = retryCountdown?.querySelector('.countdown-seconds');
                const retryBtn = document.getElementById('retryBtn');
                
                if (retryCountdown && countdownSpan) {
                    retryCountdown.classList.remove('hidden');
                    if (retryBtn) retryBtn.classList.add('hidden');
                    
                    // Show attempt number
                    const attemptText = document.createElement('div');
                    attemptText.className = 'retry-attempt';
                    attemptText.textContent = `Attempt ${attempt} of 3`;
                    attemptText.style.cssText = 'font-size: 12px; color: var(--text-muted); margin-top: 8px;';
                    retryCountdown.appendChild(attemptText);
                    
                    let seconds = 3;
                    countdownSpan.textContent = seconds;
                    
                    const countdownInterval = setInterval(() => {
                        seconds--;
                        countdownSpan.textContent = seconds;
                        
                        if (seconds <= 0) {
                            clearInterval(countdownInterval);
                            retryCountdown.classList.add('hidden');
                            if (retryBtn) retryBtn.classList.remove('hidden');
                            // Remove attempt text
                            const attemptEl = retryCountdown.querySelector('.retry-attempt');
                            if (attemptEl) attemptEl.remove();
                            loadStock(ticker, forceRefresh, attempt + 1);
                        }
                    }, 1000);
                    
                    // Store interval ID so it can be cleared if user clicks retry manually
                    window.currentRetryInterval = countdownInterval;
                }
            } else {
                // Show final attempt message
                const retryCountdown = document.getElementById('retryCountdown');
                if (retryCountdown) {
                    retryCountdown.innerHTML = '<span style="color: var(--accent-red);">All retry attempts failed</span>';
                    retryCountdown.classList.remove('hidden');
                }
            }
            
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
            
            // Hide loading spinners
            const inputSpinner = document.getElementById('inputSpinner');
            const btnSpinner = document.querySelector('#searchBtn .btn-spinner');
            if (inputSpinner) inputSpinner.classList.add('hidden');
            if (btnSpinner) btnSpinner.classList.add('hidden');
            searchBtn.classList.remove('loading');
            
            // Stop stock tips
            stopStockTips();
        }
    }

    function displayResults(data) {
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
        
        // Trigger slide-up animation
        requestAnimationFrame(() => {
            results.classList.add('visible');
        });
        
        // Safely get summary values
        const summary = data.summary || {};
        
        // Update basic metrics (with count-up animation)
        document.getElementById('companyName').textContent = data.name || data.ticker || 'Unknown';
        document.getElementById('companyTicker').textContent = data.ticker || '';
        
        // Update header price and change
        const headerPriceEl = document.getElementById('headerPrice');
        const headerChangeEl = document.getElementById('headerChange');
        if (headerPriceEl && summary.current_price) {
            headerPriceEl.textContent = '$' + summary.current_price.toFixed(2);
        }
        if (headerChangeEl && window.lastPriceHistory && window.lastPriceHistory.length >= 2) {
            const prices = window.lastPriceHistory.map(d => d.close || d.price).filter(v => v != null);
            if (prices.length >= 2) {
                const currentPrice = prices[prices.length - 1];
                const priorClose = prices[prices.length - 2];
                const change = currentPrice - priorClose;
                const changePercent = (change / priorClose) * 100;
                const isPositive = change >= 0;
                const changeSymbol = isPositive ? '+' : '';
                headerChangeEl.textContent = `${changeSymbol}$${change.toFixed(2)} (${changeSymbol}${changePercent.toFixed(2)}%)`;
                headerChangeEl.className = 'header-change ' + (isPositive ? 'positive' : 'negative');
            }
        }
        
        // Animate key metrics with count-up effect
        if (summary.current_price) {
            const currentPriceEl = document.getElementById('currentPrice');
            if (currentPriceEl) {
                animateCountUp(currentPriceEl, 0, summary.current_price, 600, '$', '', 2);
            }
        } else {
            const currentPriceEl = document.getElementById('currentPrice');
            if (currentPriceEl) {
                currentPriceEl.textContent = 'N/A';
            }
        }
        
        const marketCapEl = document.getElementById('marketCap');
        if (marketCapEl) {
            marketCapEl.textContent = formatMarketCap(summary.market_cap);
        }
        
        if (summary.pe_ratio != null) {
            animateCountUp(document.getElementById('peRatio'), 0, summary.pe_ratio, 500, '', '', 2);
        } else {
            document.getElementById('peRatio').textContent = 'N/A';
        }
        
        // Update key financial metrics with animations
        if (summary.revenue_growth != null) {
            animateCountUp(document.getElementById('revenueGrowth'), 0, summary.revenue_growth, 500, '', '%', 2);
        } else {
            document.getElementById('revenueGrowth').textContent = 'N/A';
        }
        
        // Calculate TTM Earnings and Revenue from last 4 quarters
        const earnings = data.earnings || [];
        const last4Quarters = earnings.slice(0, 4);
        const ttmEarnings = last4Quarters.reduce((sum, e) => sum + (e.reported_eps || 0), 0);
        const ttmRevenue = last4Quarters.reduce((sum, e) => sum + (e.revenue || 0), 0);
        
        const ttmEarningsEl = document.getElementById('ttmEarnings');
        if (ttmEarningsEl) {
            ttmEarningsEl.textContent = '$' + ttmEarnings.toFixed(2) + '/share';
        }
        
        const ttmRevenueEl = document.getElementById('ttmRevenue');
        if (ttmRevenueEl) {
            ttmRevenueEl.textContent = formatMarketCap(ttmRevenue);
        }
        
        // Calculate and display trends based on earnings data
        calculateAndDisplayTrends(data.earnings || []);
        
        // Draw sparklines for key metrics
        drawSparklines(data.earnings || []);
        
        // Valuation Metrics (with flash animation on change)
        updateValueWithFlash('psRatio', summary.ps_ratio, formatNumber);
        updateValueWithFlash('pbRatio', summary.pb_ratio, formatNumber);
        updateValueWithFlash('evebitda', summary.ev_ebitda, formatNumber);
        updateValueWithFlash('marketCap2', summary.market_cap, formatMarketCap);
        updateValueWithFlash('enterpriseValue', summary.enterprise_value, formatMarketCap);
        updateValueWithFlash('sharesOutstanding', summary.shares_outstanding, 
            (v) => v ? formatNumber(v / 1e9) + 'B' : '-');
        
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
        
        // Draw charts (reverse data for chronological order)
        const chartData = [...data.earnings].reverse();
        window.lastChartData = chartData;  // Store for tab switching
        window.sharesOutstanding = summary.shares_outstanding; // Store for total earnings calc
        
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
        
        // Trigger card entrance animations
        const cards = document.querySelectorAll('#results .card');
        cards.forEach(card => card.classList.remove('animate-in'));
        
        // Force reflow to ensure animation restarts
        void document.body.offsetHeight;
        
        // Add animate-in class with slight delay for stagger effect
        setTimeout(() => {
            cards.forEach((card, index) => {
                setTimeout(() => {
                    card.classList.add('animate-in');
                }, index * 50); // 50ms stagger between cards
            });
        }, 50);
    }

    // ============================================
    // AUTO-LOAD TSLA ON HOMEPAGE
    // ============================================
    tickerInput.value = 'TSLA';
    empty.classList.add('hidden');
    loading.classList.remove('hidden');
    
    // Small delay to ensure everything is ready
    setTimeout(async () => {
        try {
            await loadStock('TSLA');
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

    // ============================================
    // FULL SCREEN CHART MODAL
    // ============================================
    const chartModal = document.getElementById('chartModal');
    const closeChartModalBtn = document.getElementById('closeChartModal');
    const chartModalBackdrop = document.querySelector('.chart-modal-backdrop');
    const chartModalTitle = document.getElementById('chartModalTitle');

    // Close modal handlers
    closeChartModalBtn?.addEventListener('click', closeChartModal);
    chartModalBackdrop?.addEventListener('click', closeChartModal);
    
    // ESC key to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !chartModal.classList.contains('hidden')) {
            closeChartModal();
        }
    });

    // Store original orientation to restore later
    let originalOrientation = null;

    function openChartModal() {
        if (!window.lastPriceHistory && !window.lastChartData) return;
        
        // Use bottom sheet on mobile
        const isMobile = window.innerWidth <= 768;
        if (isMobile) {
            chartModal.classList.add('bottom-sheet');
        } else {
            chartModal.classList.remove('bottom-sheet');
        }
        
        chartModal.classList.remove('hidden');
        document.body.classList.add('chart-modal-open');
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
        
        // Try to lock to landscape on mobile (only for non-bottom-sheet)
        if (!isMobile && screen.orientation && screen.orientation.lock) {
            originalOrientation = screen.orientation.type;
            screen.orientation.lock('landscape').catch(() => {
                // Lock not supported or failed, CSS rotation will handle it
                console.log('Orientation lock not available, using CSS rotation');
            });
        }
        
        // Update title with current ticker
        if (currentTicker) {
            chartModalTitle.textContent = `${currentTicker} - Stock Price History`;
        }
        
        // Draw full screen chart with more detail
        setTimeout(() => {
            drawFullScreenPriceChart(window.lastPriceHistory || window.lastChartData);
        }, 10);
    }

    function closeChartModal() {
        // Add closing class for exit animation
        chartModal.classList.add('closing');
        
        // Wait for animation to complete before hiding
        setTimeout(() => {
            chartModal.classList.add('hidden');
            chartModal.classList.remove('closing');
            document.body.classList.remove('chart-modal-open');
            document.body.style.overflow = ''; // Restore scrolling
            
            // Unlock orientation if we locked it
            if (screen.orientation && screen.orientation.unlock && originalOrientation) {
                screen.orientation.unlock();
                originalOrientation = null;
            }
        }, 200);
    }

    // Chart drawing functions
function drawEPSChart(data) {
    const canvas = document.getElementById('epsChart');
    if (!canvas) return;
    
    // Show only last 4 quarters for cleaner chart
    const chartData = data.slice(-4);
    
    // Get shares outstanding for total earnings calculation
    const sharesOutstanding = window.sharesOutstanding || 1;
    
    // Convert EPS to total earnings (in billions) and FCF to billions
    const convertedData = chartData.map(d => ({
        ...d,
        reported_eps: d.reported_eps ? (d.reported_eps * sharesOutstanding) / 1e9 : null,
        estimated_eps: d.estimated_eps ? (d.estimated_eps * sharesOutstanding) / 1e9 : null,
        fcf: d.free_cash_flow ? d.free_cash_flow / 1e9 : null
    }));
    
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
    const allValues = [
        ...convertedData.map(d => d.reported_eps), 
        ...convertedData.map(d => d.estimated_eps),
        ...convertedData.map(d => d.fcf)
    ].filter(v => v != null);
    if (allValues.length === 0) {
        ctx.fillStyle = '#94a3b8';
        ctx.font = '14px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No earnings data available', 400, 150);
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
        
        // Y-axis labels (in billions)
        const val = maxVal - (maxVal - minVal) * i / 5;
        ctx.fillStyle = '#94a3b8';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(`$${val.toFixed(1)}B`, padding.left - 10, y + 4);
    }
    
    ctx.setLineDash([]);
    
    // Draw bars (actual earnings and FCF)
    const groupWidth = chartWidth / convertedData.length * 0.7;
    const spacing = chartWidth / convertedData.length;
    const barWidth = groupWidth / 2;
    
    convertedData.forEach((d, i) => {
        const groupX = padding.left + spacing * i + (spacing - groupWidth) / 2;
        
        // Earnings bar (left)
        const earningsHeight = ((d.reported_eps - minVal) / (maxVal - minVal)) * chartHeight;
        const earningsY = padding.top + chartHeight - earningsHeight;
        
        // Determine if beat or miss
        const surprise = d.reported_eps && d.estimated_eps ? 
            ((d.reported_eps - d.estimated_eps) / Math.abs(d.estimated_eps)) * 100 : null;
        const isBeat = surprise && surprise > 0;
        const isMiss = surprise && surprise < 0;
        
        // Earnings bar color based on beat/miss
        let earningsColor;
        if (isBeat) {
            earningsColor = '#10b981'; // Green for beat
        } else if (isMiss) {
            earningsColor = '#ef4444'; // Red for miss
        } else {
            earningsColor = '#3b82f6'; // Blue for neutral
        }
        ctx.fillStyle = earningsColor;
        ctx.fillRect(groupX, earningsY, barWidth, earningsHeight);
        
        // FCF bar (right) - purple color
        if (d.fcf !== null) {
            const fcfHeight = ((d.fcf - minVal) / (maxVal - minVal)) * chartHeight;
            const fcfY = padding.top + chartHeight - fcfHeight;
            ctx.fillStyle = '#8b5cf6'; // Purple for FCF
            ctx.fillRect(groupX + barWidth + 2, fcfY, barWidth, fcfHeight);
        }
        
        // Add pattern overlay for accessibility (color blindness)
        if (isBeat) {
            // Diagonal stripes for beat
            ctx.save();
            ctx.beginPath();
            ctx.rect(x, y, barWidth, barHeight);
            ctx.clip();
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
            ctx.lineWidth = 2;
            for (let i = -barHeight; i < barWidth; i += 6) {
                ctx.beginPath();
                ctx.moveTo(x + i, y + barHeight);
                ctx.lineTo(x + i + barHeight, y);
                ctx.stroke();
            }
            ctx.restore();
        } else if (isMiss) {
            // Dots for miss
            ctx.save();
            ctx.beginPath();
            ctx.rect(x, y, barWidth, barHeight);
            ctx.clip();
            ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
            for (let dx = 4; dx < barWidth; dx += 8) {
                for (let dy = 4; dy < barHeight; dy += 8) {
                    ctx.beginPath();
                    ctx.arc(x + dx, y + dy, 1.5, 0, Math.PI * 2);
                    ctx.fill();
                }
            }
            ctx.restore();
        }
        
        // Add surprise indicator above bar
        if (surprise !== null) {
            const surpriseY = y - 25;
            const surpriseText = isBeat ? `+${surprise.toFixed(1)}%` : `${surprise.toFixed(1)}%`;
            
            // Background pill
            ctx.fillStyle = isBeat ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)';
            ctx.beginPath();
            ctx.roundRect(x + barWidth/2 - 25, surpriseY - 8, 50, 16, 8);
            ctx.fill();
            
            // Text
            ctx.fillStyle = isBeat ? '#10b981' : '#ef4444';
            ctx.font = 'bold 10px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(surpriseText, x + barWidth / 2, surpriseY + 3);
            
            // Beat/Miss icon
            ctx.font = '12px sans-serif';
            const iconY = surpriseY - 12;
            if (isBeat) {
                ctx.fillText('▲', x + barWidth / 2, iconY);
            } else if (isMiss) {
                ctx.fillText('▼', x + barWidth / 2, iconY);
            }
        }
        
        // X label (centered under the group)
        ctx.fillStyle = '#94a3b8';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(d.fiscal_date.slice(0, 7), groupX + groupWidth / 2, padding.top + chartHeight + 20);
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
    convertedData.forEach((d, i) => {
        const x = padding.left + spacing * i + spacing / 2;
        const y = padding.top + chartHeight - ((d.estimated_eps - minVal) / (maxVal - minVal)) * chartHeight;
        
        ctx.fillStyle = '#f59e0b';
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, Math.PI * 2);
        ctx.fill();
    });
    
    // Interactive Legend with click to toggle
    const legendItems = [
        { label: 'Actual Earnings', color: '#3b82f6', type: 'bar', key: 'actual', visible: true },
        { label: 'FCF', color: '#8b5cf6', type: 'bar', key: 'fcf', visible: true },
        { label: 'Estimated Earnings', color: '#f59e0b', type: 'line', key: 'estimated', visible: true }
    ];
    
    // Store legend state on canvas
    canvas.dataset.legendState = JSON.stringify(legendItems);
    
    function drawLegend() {
        const state = JSON.parse(canvas.dataset.legendState || '[]');
        let xOffset = padding.left;
        
        state.forEach((item, index) => {
            const alpha = item.visible ? 1 : 0.3;
            
            if (item.type === 'bar') {
                ctx.fillStyle = item.color;
                ctx.globalAlpha = alpha;
                ctx.fillRect(xOffset, 15, 15, 15);
                ctx.globalAlpha = 1;
            } else {
                ctx.strokeStyle = item.color;
                ctx.lineWidth = 3;
                ctx.globalAlpha = alpha;
                ctx.beginPath();
                ctx.moveTo(xOffset, 22);
                ctx.lineTo(xOffset + 15, 22);
                ctx.stroke();
                ctx.beginPath();
                ctx.arc(xOffset + 7, 22, 4, 0, Math.PI * 2);
                ctx.fillStyle = item.color;
                ctx.fill();
                ctx.globalAlpha = 1;
            }
            
            ctx.fillStyle = '#e2e8f0';
            ctx.font = '12px sans-serif';
            ctx.textAlign = 'left';
            ctx.globalAlpha = alpha;
            ctx.fillText(item.label, xOffset + 20, 27);
            ctx.globalAlpha = 1;
            
            // Store click area for this legend item
            item.clickArea = { x: xOffset, y: 10, width: 90, height: 25 };
            
            xOffset += 110;
        });
        
        canvas.dataset.legendState = JSON.stringify(state);
    }
    
    drawLegend();
    
    // Add click handler for legend
    if (!canvas.dataset.legendClickSetup) {
        canvas.addEventListener('click', (e) => {
            const rect = canvas.getBoundingClientRect();
            const x = (e.clientX - rect.left) * (canvas.width / rect.width);
            const y = (e.clientY - rect.top) * (canvas.height / rect.height);
            
            // Check if click is in legend area
            if (y < 40) {
                const state = JSON.parse(canvas.dataset.legendState || '[]');
                let changed = false;
                
                state.forEach(item => {
                    if (item.clickArea && 
                        x >= item.clickArea.x && 
                        x <= item.clickArea.x + item.clickArea.width &&
                        y >= item.clickArea.y && 
                        y <= item.clickArea.y + item.clickArea.height) {
                        item.visible = !item.visible;
                        changed = true;
                    }
                });
                
                if (changed) {
                    canvas.dataset.legendState = JSON.stringify(state);
                    // Redraw chart with new visibility
                    drawEPSChart(data);
                }
            }
        });
        canvas.dataset.legendClickSetup = 'true';
    }
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
    
    // Industry average P/E reference line (S&P 500 ~20-25)
    const industryAvgPE = 22;
    if (industryAvgPE >= minPE && industryAvgPE <= maxPE) {
        const avgY = padding.top + chartHeight - ((industryAvgPE - minPE) / (maxPE - minPE)) * chartHeight;
        ctx.save();
        ctx.strokeStyle = '#f59e0b'; // Orange for benchmark
        ctx.lineWidth = 2;
        ctx.setLineDash([8, 4]);
        ctx.beginPath();
        ctx.moveTo(padding.left, avgY);
        ctx.lineTo(padding.left + chartWidth, avgY);
        ctx.stroke();
        
        // Label
        ctx.fillStyle = '#f59e0b';
        ctx.font = '11px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText('S&P 500 Avg (~22)', padding.left + chartWidth, avgY - 5);
        ctx.restore();
    }
    
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

function drawSparklines(earnings) {
    if (!earnings || earnings.length < 2) return;
    
    // Sort by date (oldest first)
    const sorted = [...earnings].sort((a, b) => new Date(a.fiscal_date) - new Date(b.fiscal_date));
    
    // Draw P/E sparkline
    const peCanvas = document.getElementById('peSparkline');
    if (peCanvas) {
        const peData = sorted.map(e => e.pe_ratio).filter(v => v != null);
        if (peData.length >= 2) {
            drawSparkline(peCanvas, peData, '#3b82f6');
        }
    }
    
    // Draw Revenue Growth sparkline
    const revCanvas = document.getElementById('revenueSparkline');
    if (revCanvas) {
        const revData = sorted.map(e => e.revenue_growth).filter(v => v != null);
        if (revData.length >= 2) {
            drawSparkline(revCanvas, revData, '#10b981');
        }
    }
    
    // Draw FCF sparkline
    const fcfCanvas = document.getElementById('fcfSparkline');
    if (fcfCanvas) {
        const fcfData = sorted.map(e => e.free_cash_flow).filter(v => v != null);
        if (fcfData.length >= 2) {
            // Normalize FCF data for better visualization
            const maxFCF = Math.max(...fcfData.map(Math.abs));
            const normalizedFCF = fcfData.map(v => v / maxFCF);
            drawSparkline(fcfCanvas, normalizedFCF, '#8b5cf6');
        }
    }
}

// Pattern fill helpers for accessibility
function createStripePattern(ctx, color) {
    const patternCanvas = document.createElement('canvas');
    patternCanvas.width = 8;
    patternCanvas.height = 8;
    const pctx = patternCanvas.getContext('2d');
    
    pctx.strokeStyle = color;
    pctx.lineWidth = 1;
    pctx.beginPath();
    pctx.moveTo(0, 8);
    pctx.lineTo(8, 0);
    pctx.stroke();
    
    return ctx.createPattern(patternCanvas, 'repeat');
}

function createDotPattern(ctx, color) {
    const patternCanvas = document.createElement('canvas');
    patternCanvas.width = 8;
    patternCanvas.height = 8;
    const pctx = patternCanvas.getContext('2d');
    
    pctx.fillStyle = color;
    pctx.beginPath();
    pctx.arc(4, 4, 1.5, 0, Math.PI * 2);
    pctx.fill();
    
    return ctx.createPattern(patternCanvas, 'repeat');
}

// Draw reference line on chart
function drawReferenceLine(ctx, y, label, color = '#94a3b8') {
    ctx.save();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(padding.left, y);
    ctx.lineTo(padding.left + chartWidth, y);
    ctx.stroke();
    
    ctx.fillStyle = color;
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(label, padding.left + chartWidth, y - 5);
    ctx.restore();
}

function drawSparkline(canvas, data, color) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    ctx.clearRect(0, 0, width, height);
    
    const minVal = Math.min(...data);
    const maxVal = Math.max(...data);
    const range = maxVal - minVal || 1;
    
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    
    ctx.beginPath();
    data.forEach((val, i) => {
        const x = (i / (data.length - 1)) * width;
        const y = height - ((val - minVal) / range) * height * 0.8 - height * 0.1;
        
        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.stroke();
    
    // Draw end dot
    const lastX = width;
    const lastY = height - ((data[data.length - 1] - minVal) / range) * height * 0.8 - height * 0.1;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(lastX - 3, lastY, 3, 0, Math.PI * 2);
    ctx.fill();
}

// Global Chart.js instances
let priceChartInstance = null;

function drawPriceChart(data) {
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not loaded, skipping chart render');
        return;
    }
    
    const canvas = document.getElementById('priceChart');
    if (!canvas) return;
    
    // Destroy existing chart if any
    if (priceChartInstance) {
        priceChartInstance.destroy();
    }
    
    const ctx = canvas.getContext('2d');
    
    // Prepare data
    const prices = data.map(d => d.close || d.price).filter(v => v != null);
    if (prices.length === 0) return;
    
    // Calculate percent change for the period
    const startPrice = prices[0];
    const endPrice = prices[prices.length - 1];
    const percentChange = ((endPrice - startPrice) / startPrice) * 100;
    const isPositive = percentChange >= 0;
    const changeColor = isPositive ? '#10b981' : '#ef4444';
    const changeSymbol = isPositive ? '+' : '';
    
    // Format labels (show every ~15th date)
    const labels = data.map((d, i) => {
        if (i % 15 === 0 || i === data.length - 1) {
            const date = d.date || d.fiscal_date;
            return date ? date.slice(0, 7) : '';
        }
        return '';
    });
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, isPositive ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)');
    gradient.addColorStop(1, isPositive ? 'rgba(16, 185, 129, 0.02)' : 'rgba(239, 68, 68, 0.02)');
    
    // Create Chart.js chart
    priceChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Price',
                data: prices,
                borderColor: changeColor,
                backgroundColor: gradient,
                borderWidth: 2.5,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: changeColor,
                pointHoverBorderColor: '#fff',
                pointHoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: `${changeSymbol}${percentChange.toFixed(2)}%`,
                    color: changeColor,
                    font: {
                        size: 18,
                        weight: 'bold'
                    },
                    padding: {
                        top: 10,
                        bottom: 10
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    titleColor: '#94a3b8',
                    bodyColor: '#f8fafc',
                    borderColor: 'rgba(59, 130, 246, 0.3)',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        title: function(context) {
                            const idx = context[0].dataIndex;
                            const d = data[idx];
                            return d.date || d.fiscal_date || '';
                        },
                        label: function(context) {
                            return '$' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        color: '#64748b',
                        maxTicksLimit: 6,
                        font: {
                            size: 10
                        }
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(51, 65, 85, 0.5)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#64748b',
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        },
                        font: {
                            size: 11
                        }
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeOutQuart'
            }
        }
    });
}

function drawFullScreenPriceChart(data) {
    const canvas = document.getElementById('fullScreenPriceChart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    
    // Detect mobile and orientation
    const isMobile = window.innerWidth <= 768;
    const isPortrait = window.innerHeight > window.innerWidth;
    
    // Size canvas appropriately for the container
    // Portrait: smaller landscape-oriented chart that fits in the modal
    // Landscape: use more of the available space
    let canvasWidth, canvasHeight;
    if (isMobile && isPortrait) {
        // Portrait: landscape chart that fits within ~400px wide modal
        canvasWidth = 500;
        canvasHeight = 280;
    } else if (isMobile) {
        // Device is already in landscape
        canvasWidth = Math.min(window.innerWidth * 0.85, 700);
        canvasHeight = Math.min(window.innerHeight * 0.6, 350);
    } else {
        // Desktop
        canvasWidth = 800;
        canvasHeight = 400;
    }

    canvas.width = canvasWidth * dpr;
    canvas.height = canvasHeight * dpr;
    ctx.scale(dpr, dpr);
    canvas.style.width = '100%';
    canvas.style.height = 'auto';
    canvas.style.maxWidth = '100%';
    canvas.style.maxHeight = '100%';

    const padding = isMobile 
        ? { top: 40, right: 50, bottom: 50, left: 60 }
        : { top: 50, right: 70, bottom: 70, left: 70 };
    const chartWidth = canvasWidth - padding.left - padding.right;
    const chartHeight = canvasHeight - padding.top - padding.bottom;

    ctx.clearRect(0, 0, canvasWidth, canvasHeight);

    // Handle both formats: price_history (close) and earnings (price)
    const prices = data.map(d => d.close || d.price).filter(v => v != null);
    if (prices.length === 0) {
        ctx.fillStyle = '#94a3b8';
        ctx.font = isMobile ? '14px sans-serif' : '16px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('No price data available', canvasWidth / 2, canvasHeight / 2);
        return;
    }

    const maxPrice = Math.max(...prices);
    const minPrice = Math.min(...prices);
    const priceRange = maxPrice - minPrice;

    // Add padding to min/max for visual breathing room
    const chartMax = maxPrice + priceRange * 0.1;
    const chartMin = Math.max(0, minPrice - priceRange * 0.1);
    const chartRange = chartMax - chartMin;

    const spacing = chartWidth / (data.length - 1);

    // Helper to get Y coordinate for a price
    const getY = (price) => padding.top + chartHeight - ((price - chartMin) / chartRange) * chartHeight;
    const getX = (i) => padding.left + spacing * i;

    // Draw grid lines - more detailed for full screen
    ctx.strokeStyle = '#334155';
    ctx.lineWidth = 1;
    ctx.setLineDash([5, 5]);

    // 5 horizontal grid lines
    for (let i = 0; i <= 4; i++) {
        const val = chartMax - chartRange * i / 4;
        const y = getY(val);
        
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(padding.left + chartWidth, y);
        ctx.stroke();

        ctx.fillStyle = '#64748b';
        ctx.font = isMobile ? '11px sans-serif' : '13px sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(`$${val.toFixed(2)}`, padding.left - 12, y + 4);
    }

    ctx.setLineDash([]);

    // Area under line with smooth gradient
    const gradient = ctx.createLinearGradient(0, padding.top, 0, padding.top + chartHeight);
    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.3)');
    gradient.addColorStop(1, 'rgba(16, 185, 129, 0.02)');

    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top + chartHeight);

    // Build smooth curve using bezier
    const points = data.map((d, i) => ({
        x: getX(i),
        y: getY(d.close || d.price)
    }));

    ctx.lineTo(points[0].x, points[0].y);

    for (let i = 0; i < points.length - 1; i++) {
        const curr = points[i];
        const next = points[i + 1];
        const cp1x = curr.x + (next.x - curr.x) * 0.3;
        const cp1y = curr.y;
        const cp2x = next.x - (next.x - curr.x) * 0.3;
        const cp2y = next.y;
        ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, next.x, next.y);
    }

    ctx.lineTo(padding.left + chartWidth, padding.top + chartHeight);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Smooth price line - thicker for full screen
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);

    for (let i = 0; i < points.length - 1; i++) {
        const curr = points[i];
        const next = points[i + 1];
        const cp1x = curr.x + (next.x - curr.x) * 0.3;
        const cp1y = curr.y;
        const cp2x = next.x - (next.x - curr.x) * 0.3;
        const cp2y = next.y;
        ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, next.x, next.y);
    }
    ctx.stroke();

    // Find high and low points
    let highIdx = 0, lowIdx = 0;
    prices.forEach((p, i) => {
        if (p > prices[highIdx]) highIdx = i;
        if (p < prices[lowIdx]) lowIdx = i;
    });

    // Draw high point marker - larger for full screen
    const highX = getX(highIdx);
    const highY = getY(prices[highIdx]);
    const markerSize = isMobile ? 6 : 7;
    const labelOffset = isMobile ? 10 : 15;

    ctx.fillStyle = '#22c55e';
    ctx.beginPath();
    ctx.arc(highX, highY, markerSize, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = isMobile ? 2 : 3;
    ctx.stroke();

    // High label with background
    ctx.fillStyle = '#22c55e';
    ctx.font = isMobile ? 'bold 12px sans-serif' : 'bold 14px sans-serif';
    ctx.textAlign = highIdx < data.length / 2 ? 'left' : 'right';
    ctx.fillText(`High: $${prices[highIdx].toFixed(2)}`, highX + (highIdx < data.length / 2 ? labelOffset : -labelOffset), highY - labelOffset);

    // Draw low point marker
    const lowX = getX(lowIdx);
    const lowY = getY(prices[lowIdx]);

    ctx.fillStyle = '#ef4444';
    ctx.beginPath();
    ctx.arc(lowX, lowY, markerSize, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = isMobile ? 2 : 3;
    ctx.stroke();

    // Low label
    ctx.fillStyle = '#ef4444';
    ctx.font = isMobile ? 'bold 12px sans-serif' : 'bold 14px sans-serif';
    ctx.textAlign = lowIdx < data.length / 2 ? 'left' : 'right';
    const lowLabelOffset = isMobile ? 10 : 15;
    ctx.fillText(`Low: $${prices[lowIdx].toFixed(2)}`, lowX + (lowIdx < data.length / 2 ? lowLabelOffset : -lowLabelOffset), lowY + (isMobile ? 20 : 25));

    // X-axis labels - monthly for more detail (skip some on mobile if too crowded)
    let lastMonth = '';
    let labelCount = 0;
    const skipInterval = isMobile && data.length > 100 ? 2 : 1; // Skip every other label on mobile
    data.forEach((d, i) => {
        const dateStr = d.date || d.fiscal_date;
        const month = dateStr.slice(0, 7);  // YYYY-MM
        if (month === lastMonth) return;
        lastMonth = month;
        labelCount++;
        
        // Skip labels to prevent crowding on mobile
        if (skipInterval > 1 && labelCount % skipInterval !== 0) return;

        const x = getX(i);
        ctx.fillStyle = '#64748b';
        ctx.font = isMobile ? '10px sans-serif' : '12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(month, x, padding.top + chartHeight + (isMobile ? 20 : 30));
    });

    // Current price label at end
    const lastPrice = prices[prices.length - 1];
    const lastX = points[points.length - 1].x;
    const lastY = points[points.length - 1].y;

    ctx.fillStyle = '#10b981';
    ctx.font = isMobile ? 'bold 12px sans-serif' : 'bold 14px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`$${lastPrice.toFixed(2)}`, lastX + 10, lastY + 4);

    // Legend
    const legendSize = isMobile ? 12 : 16;
    ctx.fillStyle = '#10b981';
    ctx.fillRect(padding.left, 16, legendSize, legendSize);
    ctx.fillStyle = '#e2e8f0';
    ctx.font = isMobile ? '12px sans-serif' : '14px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('Price', padding.left + legendSize + 8, isMobile ? 26 : 30);

    // Stats box
    const firstPrice = data[0]?.close || data[0]?.price;
    if (firstPrice && lastPrice) {
        const change = ((lastPrice - firstPrice) / firstPrice) * 100;
        const changeColor = change >= 0 ? '#22c55e' : '#ef4444';
        const changeSymbol = change >= 0 ? '+' : '';
        
        ctx.fillStyle = changeColor;
        ctx.font = isMobile ? 'bold 12px sans-serif' : 'bold 14px sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText(`${changeSymbol}${change.toFixed(2)}%`, padding.left + (isMobile ? 70 : 100), isMobile ? 26 : 30);
    }
}

    // Pull-to-refresh for mobile
    function initPullToRefresh() {
        const pullThreshold = 100;
        let startY = 0;
        let currentY = 0;
        let isPulling = false;
        let refreshIndicator = null;
        
        // Only enable on mobile
        if (window.innerWidth > 768) return;
        
        // Create refresh indicator
        refreshIndicator = document.createElement('div');
        refreshIndicator.className = 'pull-refresh-indicator';
        refreshIndicator.innerHTML = '<div class="pull-refresh-spinner"></div><span>Pull to refresh</span>';
        refreshIndicator.style.cssText = `
            position: fixed;
            top: -60px;
            left: 0;
            right: 0;
            height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--bg-tertiary);
            transition: transform 0.2s ease;
            z-index: 100;
            font-size: 13px;
            color: var(--text-muted);
        `;
        document.body.appendChild(refreshIndicator);
        
        const main = document.getElementById('main');
        
        main.addEventListener('touchstart', (e) => {
            // Only trigger if at top of page
            if (window.scrollY > 0) return;
            
            startY = e.touches[0].clientY;
            isPulling = true;
        }, { passive: true });
        
        main.addEventListener('touchmove', (e) => {
            if (!isPulling) return;
            
            currentY = e.touches[0].clientY;
            const diff = currentY - startY;
            
            if (diff > 0 && window.scrollY === 0) {
                // Prevent default scroll when pulling down at top
                if (diff < pullThreshold) {
                    e.preventDefault();
                }
                
                // Move indicator
                const translateY = Math.min(diff * 0.5, pullThreshold);
                refreshIndicator.style.transform = `translateY(${translateY}px)`;
                
                // Update text based on pull distance
                const span = refreshIndicator.querySelector('span');
                if (translateY >= pullThreshold * 0.7) {
                    span.textContent = 'Release to refresh';
                    refreshIndicator.querySelector('.pull-refresh-spinner').style.animation = 'spin 0.5s linear infinite';
                } else {
                    span.textContent = 'Pull to refresh';
                    refreshIndicator.querySelector('.pull-refresh-spinner').style.animation = 'none';
                }
            }
        }, { passive: false });
        
        main.addEventListener('touchend', () => {
            if (!isPulling) return;
            
            const diff = currentY - startY;
            
            if (diff > pullThreshold * 0.7 && currentTicker) {
                // Trigger refresh
                refreshIndicator.querySelector('span').textContent = 'Refreshing...';
                refreshIndicator.style.transform = 'translateY(0)';
                
                loadStock(currentTicker, true).then(() => {
                    // Reset after refresh
                    setTimeout(() => {
                        refreshIndicator.style.transform = 'translateY(-60px)';
                    }, 500);
                });
            } else {
                // Reset without refreshing
                refreshIndicator.style.transform = 'translateY(-60px)';
            }
            
            isPulling = false;
            startY = 0;
            currentY = 0;
        });
    }
    
    // Initialize pull-to-refresh on mobile
    initPullToRefresh();
});
