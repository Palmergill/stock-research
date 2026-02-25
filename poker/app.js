// Poker Game Frontend - Option A: Bottom Focus Design
const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://stock-research-production-b3ac.up.railway.app';

// Sound Manager - Web Audio API for game sounds
const SoundManager = {
    audioContext: null,
    enabled: true,

    init() {
        // Initialize on first user interaction to comply with browser autoplay policies
        const initAudio = () => {
            if (!this.audioContext) {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            if (this.audioContext.state === 'suspended') {
                this.audioContext.resume();
            }
        };
        document.addEventListener('click', initAudio, { once: true });
        document.addEventListener('touchstart', initAudio, { once: true });
    },

    // Play card deal sound - quick noise burst with filter
    playCardDeal() {
        if (!this.enabled || !this.audioContext) return;
        try {
            const osc = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();
            const filter = this.audioContext.createBiquadFilter();

            osc.type = 'sine';
            osc.frequency.setValueAtTime(800, this.audioContext.currentTime);
            osc.frequency.exponentialRampToValueAtTime(400, this.audioContext.currentTime + 0.05);

            filter.type = 'lowpass';
            filter.frequency.setValueAtTime(2000, this.audioContext.currentTime);

            gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.05);

            osc.connect(filter);
            filter.connect(gainNode);
            gainNode.connect(this.audioContext.destination);

            osc.start(this.audioContext.currentTime);
            osc.stop(this.audioContext.currentTime + 0.05);
        } catch (e) {
            console.log('[Sound] Card deal sound failed:', e.message);
        }
    },

    // Play chip sound - short high tick
    playChip() {
        if (!this.enabled || !this.audioContext) return;
        try {
            const osc = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();

            osc.type = 'triangle';
            osc.frequency.setValueAtTime(1200, this.audioContext.currentTime);
            osc.frequency.exponentialRampToValueAtTime(600, this.audioContext.currentTime + 0.08);

            gainNode.gain.setValueAtTime(0.08, this.audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.08);

            osc.connect(gainNode);
            gainNode.connect(this.audioContext.destination);

            osc.start(this.audioContext.currentTime);
            osc.stop(this.audioContext.currentTime + 0.08);
        } catch (e) {
            console.log('[Sound] Chip sound failed:', e.message);
        }
    },

    // Play win sound - ascending arpeggio
    playWin() {
        if (!this.enabled || !this.audioContext) return;
        try {
            const notes = [523.25, 659.25, 783.99, 1046.50]; // C major arpeggio
            notes.forEach((freq, i) => {
                const osc = this.audioContext.createOscillator();
                const gainNode = this.audioContext.createGain();

                osc.type = 'sine';
                osc.frequency.setValueAtTime(freq, this.audioContext.currentTime + i * 0.08);

                gainNode.gain.setValueAtTime(0, this.audioContext.currentTime + i * 0.08);
                gainNode.gain.linearRampToValueAtTime(0.15, this.audioContext.currentTime + i * 0.08 + 0.02);
                gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + i * 0.08 + 0.25);

                osc.connect(gainNode);
                gainNode.connect(this.audioContext.destination);

                osc.start(this.audioContext.currentTime + i * 0.08);
                osc.stop(this.audioContext.currentTime + i * 0.08 + 0.25);
            });
        } catch (e) {
            console.log('[Sound] Win sound failed:', e.message);
        }
    },

    // Play loss sound - descending tone
    playLoss() {
        if (!this.enabled || !this.audioContext) return;
        try {
            const osc = this.audioContext.createOscillator();
            const gainNode = this.audioContext.createGain();

            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(300, this.audioContext.currentTime);
            osc.frequency.exponentialRampToValueAtTime(150, this.audioContext.currentTime + 0.3);

            gainNode.gain.setValueAtTime(0.1, this.audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.3);

            osc.connect(gainNode);
            gainNode.connect(this.audioContext.destination);

            osc.start(this.audioContext.currentTime);
            osc.stop(this.audioContext.currentTime + 0.3);
        } catch (e) {
            console.log('[Sound] Loss sound failed:', e.message);
        }
    },

    toggle() {
        this.enabled = !this.enabled;
        return this.enabled;
    }
};

// Error Boundary - Global error handling
const ErrorBoundary = {
    container: null,

    init() {
        // Create error container
        this.container = document.createElement('div');
        this.container.id = 'error-boundary';
        this.container.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            max-width: 90%;
            z-index: 10000;
            display: flex;
            flex-direction: column;
            gap: 8px;
            pointer-events: none;
        `;
        document.body.appendChild(this.container);

        // Global error handler
        window.addEventListener('error', (e) => {
            console.error('Global error:', e.error);
            this.show('An unexpected error occurred. Please refresh the page if the game is not working.', 'error');
        });

        // Unhandled promise rejection handler
        window.addEventListener('unhandledrejection', (e) => {
            console.error('Unhandled promise rejection:', e.reason);
            this.show('Network or server error. Please check your connection and try again.', 'error');
        });
    },

    show(message, type = 'error') {
        const toast = document.createElement('div');
        const colors = {
            error: '#ef4444',
            warning: '#f59e0b',
            info: '#3b82f6'
        };

        toast.style.cssText = `
            background: ${colors[type] || colors.error};
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            animation: slideInDown 0.3s ease-out;
            pointer-events: auto;
            max-width: 400px;
            text-align: center;
        `;
        toast.textContent = message;

        // Add close button
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '×';
        closeBtn.style.cssText = `
            background: none;
            border: none;
            color: white;
            font-size: 20px;
            cursor: pointer;
            margin-left: 12px;
            padding: 0 4px;
            float: right;
        `;
        closeBtn.onclick = () => toast.remove();
        toast.appendChild(closeBtn);

        this.container.appendChild(toast);

        // Auto-remove after 8 seconds
        setTimeout(() => {
            toast.style.animation = 'fadeOutUp 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        }, 8000);
    },

    // Wrap async functions with error handling
    async wrap(asyncFn, errorMessage = 'Something went wrong') {
        try {
            return await asyncFn();
        } catch (error) {
            console.error(errorMessage, error);
            this.show(`${errorMessage}: ${error.message || 'Unknown error'}`, 'error');
            throw error;
        }
    }
};

// Add animation styles for error boundary
const errorStyles = document.createElement('style');
errorStyles.textContent = `
    @keyframes slideInDown {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeOutUp {
        from { opacity: 1; transform: translateY(0); }
        to { opacity: 0; transform: translateY(-20px); }
    }
`;
document.head.appendChild(errorStyles);

let gameState = null;
let playerId = null;
let gameId = null;
let isMyTurn = false;
let raiseAmount = 0;
let pollIntervalId = null;
let isRequestPending = false; // Lock to prevent race conditions
let turnStartTime = null;
let turnTimerId = null;
const TURN_TIME_LIMIT = 30000; // 30 seconds per turn
let hasVibratedThisTurn = false; // Track if we've vibrated for current turn

// DOM Elements
const screens = {
    start: document.getElementById('start-screen'),
    game: document.getElementById('game-screen')
};

const elements = {
    playerName: document.getElementById('player-name'),
    startBtn: document.getElementById('start-btn'),
    handNumber: document.getElementById('hand-number'),
    phase: document.getElementById('phase'),
    potAmount: document.getElementById('pot-amount'),
    potOdds: document.getElementById('pot-odds'),
    potOddsText: document.getElementById('pot-odds-text'),
    opponentsRow: document.getElementById('opponents-row'),
    communityCards: document.getElementById('community-cards'),
    yourCards: document.getElementById('your-cards'),
    handStrength: document.getElementById('hand-strength'),
    yourName: document.getElementById('your-name'),
    yourChips: document.getElementById('your-chips'),
    actionButtons: document.getElementById('action-buttons'),
    btnFold: document.getElementById('btn-fold'),
    btnCall: document.getElementById('btn-call'),
    btnRaise: document.getElementById('btn-raise'),
    raiseContainer: document.getElementById('raise-container'),
    raiseSlider: document.getElementById('raise-slider'),
    raiseDisplay: document.getElementById('raise-display'),
    btnMin: document.getElementById('btn-min'),
    btnPot: document.getElementById('btn-pot'),
    btnAllIn: document.getElementById('btn-allin'),
    btnCancel: document.getElementById('btn-cancel'),
    btnConfirmRaise: document.getElementById('btn-confirm-raise'),
    handResult: document.getElementById('hand-result'),
    resultTitle: document.getElementById('result-title'),
    resultDetails: document.getElementById('result-details'),
    btnNextHand: document.getElementById('btn-next-hand'),
    decisionTimer: document.getElementById('decision-timer'),
    timerText: document.getElementById('timer-text'),
    timerFill: document.getElementById('timer-fill')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Initialize error boundary and sound manager
    ErrorBoundary.init();
    SoundManager.init();

    // Cleanup on page unload
    window.addEventListener('beforeunload', stopPolling);
    window.addEventListener('pagehide', stopPolling);
    
    // Pause polling when tab is hidden
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            stopPolling();
        } else if (gameState && gameState.phase !== 'showdown') {
            startPolling();
        }
    });
    
    elements.startBtn.addEventListener('click', startGame);
    elements.btnFold.addEventListener('click', () => playerAction('fold'));
    elements.btnCall.addEventListener('click', () => playerAction('call'));
    elements.btnRaise.addEventListener('click', showRaiseControls);
    elements.btnCancel.addEventListener('click', hideRaiseControls);
    elements.btnConfirmRaise.addEventListener('click', confirmRaise);
    elements.btnNextHand.addEventListener('click', nextHand);
    
    elements.raiseSlider.addEventListener('input', (e) => {
        raiseAmount = parseInt(e.target.value);
        elements.raiseDisplay.textContent = raiseAmount;
    });
    
    elements.btnMin.addEventListener('click', () => {
        const min = gameState?.min_raise || 20;
        const toCall = gameState?.current_bet || 0;
        const myPlayer = gameState?.players?.find(p => p.id === playerId);
        const myBet = myPlayer?.bet || 0;
        setRaiseAmount(toCall - myBet + min);
    });
    
    elements.btnPot.addEventListener('click', () => {
        const pot = gameState?.pot || 0;
        setRaiseAmount(pot);
    });
    
    elements.btnAllIn.addEventListener('click', () => {
        const myPlayer = gameState?.players?.find(p => p.id === playerId);
        if (myPlayer) {
            setRaiseAmount(myPlayer.chips);
        }
    });
});

function setRaiseAmount(amount) {
    const myPlayer = gameState?.players?.find(p => p.id === playerId);
    if (!myPlayer) return;
    
    amount = Math.min(amount, myPlayer.chips);
    amount = Math.max(amount, 0);
    
    elements.raiseSlider.value = amount;
    raiseAmount = amount;
    elements.raiseDisplay.textContent = amount;
}

async function startGame() {
    const name = elements.playerName.value.trim() || 'Palmer';

    try {
        elements.startBtn.disabled = true;
        elements.startBtn.textContent = 'Loading...';

        const response = await fetch(`${API_BASE}/api/poker/games`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ player_name: name })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Failed to start game');
        }

        const data = await response.json();
        gameId = data.game_id;
        playerId = data.player_id;
        gameState = data.state;

        elements.yourName.textContent = name;

        switchScreen('game');
        updateGameDisplay();

        // Poll for updates
        startPolling();
        
    } catch (error) {
        console.error('Error starting game:', error);
        ErrorBoundary.show('Failed to start game. Please try again.', 'error');
        elements.startBtn.disabled = false;
        elements.startBtn.textContent = 'Play Now';
    }
}

function startPolling() {
    // Clear any existing polling
    stopPolling();
    
    pollIntervalId = setInterval(async () => {
        if (!gameId || !playerId) {
            stopPolling();
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/api/poker/games/${gameId}?player_id=${playerId}&process_ai=true`);
            if (!response.ok) {
                if (response.status === 404) {
                    // Game no longer exists, stop polling
                    stopPolling();
                }
                return;
            }
            
            const newState = await response.json();
            gameState = newState;
            updateGameDisplay();
            
            if (gameState.phase === 'showdown') {
                stopPolling();
                showHandResult();
            }
            
        } catch (error) {
            console.error('Polling error:', error);
            // Don't show error toast for polling - it's too frequent
        }
    }, 1000);
}

function stopPolling() {
    if (pollIntervalId) {
        clearInterval(pollIntervalId);
        pollIntervalId = null;
    }
}

async function playerAction(action) {
    if (!isMyTurn && action !== 'fold') return;
    
    // Stop timer when action is taken
    stopTurnTimer();
    
    // Prevent race condition - ignore if request already pending
    if (isRequestPending) {
        console.log('Action ignored - request already in progress');
        return;
    }
    
    let amount = null;
    if (action === 'raise') {
        amount = raiseAmount;
    }
    
    isRequestPending = true;
    
    try {
        const body = { player_id: playerId, action };
        if (amount !== null) body.amount = amount;
        
        const response = await fetch(`${API_BASE}/api/poker/games/${gameId}/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        if (!response.ok) throw new Error('Action failed');
        
        gameState = await response.json();
        hideRaiseControls();
        
        // Play chip sound for betting actions
        if (action === 'raise' || action === 'call') {
            SoundManager.playChip();
        }
        
        updateGameDisplay();
        
        if (gameState.phase === 'showdown') {
            showHandResult();
        }
        
    } catch (error) {
        console.error('Error performing action:', error);
        ErrorBoundary.show('Action failed. Please try again.', 'error');
    } finally {
        isRequestPending = false;
    }
}

function showRaiseControls() {
    const myPlayer = gameState?.players?.find(p => p.id === playerId);
    if (!myPlayer) return;
    
    const toCall = (gameState?.current_bet || 0) - (myPlayer?.bet || 0);
    const minRaise = gameState?.min_raise || 20;
    const minTotal = toCall + minRaise;
    
    // Check if player can afford minimum raise
    if (myPlayer.chips < minTotal) {
        // Can't raise, auto-call or all-in
        if (myPlayer.chips <= toCall) {
            playerAction('call'); // Will become all-in
        }
        return;
    }
    
    elements.raiseSlider.min = minTotal;
    elements.raiseSlider.max = myPlayer.chips;
    elements.raiseSlider.value = minTotal;
    raiseAmount = minTotal;
    elements.raiseDisplay.textContent = minTotal;
    
    elements.raiseContainer.classList.remove('hidden');
    elements.actionButtons.classList.add('hidden');
}

function hideRaiseControls() {
    elements.raiseContainer.classList.add('hidden');
    elements.actionButtons.classList.remove('hidden');
}

function confirmRaise() {
    playerAction('raise');
}

async function nextHand() {
    // Prevent race condition
    if (isRequestPending) {
        console.log('Next hand ignored - request already in progress');
        return;
    }
    
    isRequestPending = true;
    
    try {
        elements.btnNextHand.disabled = true;
        elements.btnNextHand.textContent = 'Dealing...';
        
        const response = await fetch(`${API_BASE}/api/poker/games/${gameId}/next-hand?player_id=${playerId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || err.message || 'Failed to start next hand');
        }
        
        gameState = await response.json();
        hideHandResult();
        updateGameDisplay();
        
        // Restart polling for the new hand
        startPolling();
        
    } catch (error) {
        console.error('Error starting next hand:', error);
        const message = typeof error === 'string' ? error : (error.message || 'Failed to start next hand');
        ErrorBoundary.show(message, 'error');
    } finally {
        isRequestPending = false;
        elements.btnNextHand.disabled = false;
        elements.btnNextHand.textContent = 'Next Hand';
    }
}

function updateGameDisplay() {
    if (!gameState) return;
    
    // Update header
    elements.handNumber.textContent = gameState.hand_number;
    elements.phase.textContent = gameState.phase.replace('_', ' ').toUpperCase();
    elements.potAmount.textContent = gameState.pot;
    
    // Update pot odds
    updatePotOdds();
    
    // Check if it's your turn
    const isYourTurn = gameState.current_player === playerId && gameState.phase !== 'showdown';
    
    // Update your info
    const myPlayer = gameState.players.find(p => p.id === playerId);
    if (myPlayer) {
        elements.yourChips.textContent = myPlayer.chips;
        
        // Your cards with animation
        const cardsHTML = myPlayer.hand.map(card => renderCard(card, true)).join('');
        elements.yourCards.innerHTML = cardsHTML;
        
        // Show hand strength
        const handStrength = evaluateHandStrength(myPlayer.hand, gameState.community_cards);
        if (handStrength) {
            elements.handStrength.innerHTML = `<span class="hand-strength-text">${handStrength}</span>`;
        } else {
            elements.handStrength.innerHTML = '';
        }
        
        // Add/remove active-turn class
        if (isYourTurn) {
            elements.yourCards.classList.add('active-turn');
        } else {
            elements.yourCards.classList.remove('active-turn');
        }
    }
    
    // Update opponents
    const opponents = gameState.players.filter(p => !p.is_human);
    elements.opponentsRow.innerHTML = opponents.map(p => renderOpponent(p)).join('');
    
    // Update community cards with animation
    const community = gameState.community_cards;
    elements.communityCards.innerHTML = `
        <div class="card-slot" id="flop-1">${community[0] ? renderCard(community[0]) : ''}</div>
        <div class="card-slot" id="flop-2">${community[1] ? renderCard(community[1]) : ''}</div>
        <div class="card-slot" id="flop-3">${community[2] ? renderCard(community[2]) : ''}</div>
        <div class="card-slot" id="turn">${community[3] ? renderCard(community[3]) : ''}</div>
        <div class="card-slot" id="river">${community[4] ? renderCard(community[4]) : ''}</div>
    `;
    
    // Update action buttons
    updateActionButtons();
    
    // Handle turn timer
    if (isYourTurn && gameState.phase !== 'showdown') {
        if (!turnTimerId) {
            startTurnTimer();
        }
        // Trigger haptic feedback when it's player's turn (once per turn)
        if (!hasVibratedThisTurn) {
            triggerHapticFeedback();
            hasVibratedThisTurn = true;
        }
    } else {
        stopTurnTimer();
        hasVibratedThisTurn = false; // Reset when turn ends
    }
}

function renderOpponent(player) {
    const isCurrent = gameState.current_player === player.id;
    const showCards = gameState.phase === 'showdown' && !player.folded;
    
    return `
        <div class="opponent ${player.folded ? 'folded' : ''} ${isCurrent ? 'active-turn' : ''}">
            <div class="opponent-cards">
                ${showCards 
                    ? player.hand.map(c => renderCard(c)).join('')
                    : `<div class="card-back ${player.folded ? 'folded' : ''}">🂠</div><div class="card-back ${player.folded ? 'folded' : ''}">🂠</div>`
                }
            </div>
            <span class="opponent-name">${player.name}</span>
            <span class="opponent-chips">${player.chips}</span>
            ${player.bet > 0 ? `<span class="opponent-bet">${player.bet}</span>` : ''}
        </div>
    `;
}

function renderCard(card, isPlayerCard = false) {
    // Handle null/undefined cards
    if (!card || typeof card !== 'object') return '';
    
    // Handle missing suit or rank
    if (!card.suit || card.rank === undefined || card.rank === null) return '';
    
    const isRed = card.suit === 'HEARTS' || card.suit === 'DIAMONDS';
    const suitSymbol = { 'HEARTS': '♥', 'DIAMONDS': '♦', 'CLUBS': '♣', 'SPADES': '♠' }[card.suit] || '';
    const rank = { 14: 'A', 13: 'K', 12: 'Q', 11: 'J' }[card.rank] || card.rank;
    
    return `<div class="card ${isRed ? '' : 'black'}">${rank}${suitSymbol}</div>`;
}

function evaluateHandStrength(playerCards, communityCards) {
    if (!playerCards || playerCards.length < 2) return null;
    
    const allCards = [...playerCards, ...communityCards];
    if (allCards.length < 5) return null; // Need at least 5 cards to evaluate
    
    const ranks = allCards.map(c => c.rank);
    const suits = allCards.map(c => c.suit);
    
    // Count ranks
    const rankCounts = {};
    ranks.forEach(r => rankCounts[r] = (rankCounts[r] || 0) + 1);
    const counts = Object.values(rankCounts).sort((a, b) => b - a);
    
    // Count suits
    const suitCounts = {};
    suits.forEach(s => suitCounts[s] = (suitCounts[s] || 0) + 1);
    const maxSuitCount = Math.max(...Object.values(suitCounts));
    
    // Check for flush
    const isFlush = maxSuitCount >= 5;
    
    // Check for straight
    const uniqueRanks = [...new Set(ranks)].sort((a, b) => b - a);
    let isStraight = false;
    let straightHigh = 0;
    
    for (let i = 0; i <= uniqueRanks.length - 5; i++) {
        if (uniqueRanks[i] - uniqueRanks[i + 4] === 4) {
            isStraight = true;
            straightHigh = uniqueRanks[i];
            break;
        }
    }
    // Check wheel (A-5)
    if (!isStraight && uniqueRanks.includes(14) && uniqueRanks.includes(5) && 
        uniqueRanks.includes(4) && uniqueRanks.includes(3) && uniqueRanks.includes(2)) {
        isStraight = true;
        straightHigh = 5;
    }
    
    // Get rank names for display
    const rankNames = { 14: 'Ace', 13: 'King', 12: 'Queen', 11: 'Jack' };
    const pluralize = (rank) => {
        const name = rankNames[rank] || rank;
        return name + (rank !== 6 && rank !== 9 && rank !== 10 ? 's' : 'es');
    };
    
    const getRankName = (rank) => rankNames[rank] || rank;
    
    // Find the ranks with specific counts
    const getRanksWithCount = (n) => {
        return Object.entries(rankCounts)
            .filter(([r, c]) => c === n)
            .map(([r, c]) => parseInt(r))
            .sort((a, b) => b - a);
    };
    
    // Determine hand rank
    if (isFlush && isStraight) {
        if (straightHigh === 14) return 'Royal Flush! 👑';
        return `Straight Flush - ${getRankName(straightHigh)} high`;
    }
    
    if (counts[0] === 4) {
        const quadRank = getRanksWithCount(4)[0];
        return `Four of a Kind - ${pluralize(quadRank)}`;
    }
    
    if (counts[0] === 3 && counts[1] >= 2) {
        const tripRank = getRanksWithCount(3)[0];
        const pairRank = getRanksWithCount(2)[0];
        return `Full House - ${pluralize(tripRank)} full of ${pluralize(pairRank)}`;
    }
    
    if (isFlush) return 'Flush';
    
    if (isStraight) {
        return `Straight - ${getRankName(straightHigh)} high`;
    }
    
    if (counts[0] === 3) {
        const tripRank = getRanksWithCount(3)[0];
        return `Three of a Kind - ${pluralize(tripRank)}`;
    }
    
    if (counts[0] === 2 && counts[1] === 2) {
        const pairs = getRanksWithCount(2);
        return `Two Pair - ${pluralize(pairs[0])} and ${pluralize(pairs[1])}`;
    }
    
    if (counts[0] === 2) {
        const pairRank = getRanksWithCount(2)[0];
        return `Pair of ${pluralize(pairRank)}`;
    }
    
    // High card - show the best card
    const highCard = Math.max(...ranks);
    return `${getRankName(highCard)} High`;
}

function updateActionButtons() {
    if (!gameState || gameState.phase === 'showdown') {
        elements.actionButtons.classList.add('hidden');
        return;
    }
    
    const myPlayer = gameState.players.find(p => p.id === playerId);
    isMyTurn = gameState.current_player === playerId;
    
    if (!isMyTurn || !myPlayer) {
        elements.actionButtons.classList.add('hidden');
        return;
    }
    
    elements.actionButtons.classList.remove('hidden');
    
    const toCall = gameState.current_bet - myPlayer.bet;
    
    if (toCall === 0) {
        elements.btnCall.textContent = 'Check';
    } else {
        const callAmount = Math.min(toCall, myPlayer.chips);
        elements.btnCall.textContent = myPlayer.chips <= toCall ? 'All In' : `Call ${callAmount}`;
    }
    
    // Hide raise button if can't afford min raise
    const minRaise = gameState.min_raise || 20;
    const canRaise = myPlayer.chips > toCall + minRaise;
    if (canRaise) {
        elements.btnRaise.classList.remove('hidden');
        elements.btnRaise.disabled = false;
        elements.btnRaise.style.opacity = '1';
    } else {
        elements.btnRaise.classList.add('hidden');
    }
}

function updatePotOdds() {
    if (!gameState || !elements.potOdds || !elements.potOddsText) return;
    
    const myPlayer = gameState.players.find(p => p.id === playerId);
    if (!myPlayer || gameState.phase === 'showdown') {
        elements.potOdds.classList.add('hidden');
        return;
    }
    
    const toCall = gameState.current_bet - myPlayer.bet;
    const pot = gameState.pot;
    
    // Only show pot odds when there's a bet to call
    if (toCall <= 0) {
        elements.potOdds.classList.add('hidden');
        return;
    }
    
    // Calculate pot odds: (pot + toCall) : toCall
    // This gives the ratio of potential win to amount to call
    const totalPot = pot + toCall;  // Including your call
    const ratio = totalPot / toCall;
    const percentage = (toCall / totalPot) * 100;
    
    // Format: "Pot odds: 3.5:1 (22%)"
    elements.potOddsText.textContent = `Pot odds: ${ratio.toFixed(1)}:1 (${percentage.toFixed(0)}% equity needed)`;
    elements.potOdds.classList.remove('hidden');
}

function showHandResult() {
    if (!gameState.winners || gameState.winners.length === 0) return;
    
    // Update display one more time to show all cards
    updateGameDisplay();
    
    const winner = gameState.winners[0];
    const isMe = winner.id === playerId;
    
    // Play win/loss sound
    if (isMe) {
        SoundManager.playWin();
    } else {
        SoundManager.playLoss();
    }
    
    elements.resultTitle.textContent = isMe ? '🎉 You Win!' : `${winner.name} Wins`;
    
    let detailsHTML = `<p style="font-size: 1.2rem; margin-bottom: 8px;">${winner.name}</p>`;
    detailsHTML += `<p style="font-size: 1.5rem; color: #10b981; font-weight: 700; margin-bottom: 15px;">+${winner.amount} chips</p>`;
    
    // Show winner's hand
    if (winner.hand && winner.hand.length > 0) {
        detailsHTML += `<p style="font-size: 0.9rem; color: #94a3b8; margin-bottom: 8px;">Winning Hand</p>`;
        detailsHTML += `<div style="display: flex; justify-content: center; gap: 8px; margin-bottom: 15px;">`;
        detailsHTML += winner.hand.map(c => renderCard(c)).join('');
        detailsHTML += `</div>`;
    }
    
    elements.resultDetails.innerHTML = detailsHTML;
    elements.handResult.classList.remove('hidden');
}

function hideHandResult() {
    elements.handResult.classList.add('hidden');
}

function switchScreen(screenName) {
    Object.values(screens).forEach(screen => screen.classList.remove('active'));
    screens[screenName].classList.add('active');
    
    // Lock orientation to portrait when entering game screen on mobile
    if (screenName === 'game') {
        lockOrientationPortrait();
    }
}

// Orientation Lock Function
function lockOrientationPortrait() {
    if (typeof screen !== 'undefined' && screen.orientation && screen.orientation.lock) {
        screen.orientation.lock('portrait').catch((err) => {
            console.log('[Orientation] Could not lock orientation:', err.message);
        });
    }
}

// Decision Timer Functions
function startTurnTimer() {
    stopTurnTimer(); // Clear any existing timer
    
    turnStartTime = Date.now();
    elements.decisionTimer.classList.remove('hidden');
    
    updateTimerDisplay();
    
    // Update every 100ms for smooth countdown
    turnTimerId = setInterval(() => {
        updateTimerDisplay();
        
        const elapsed = Date.now() - turnStartTime;
        if (elapsed >= TURN_TIME_LIMIT) {
            stopTurnTimer();
            // Auto-fold on timeout
            elements.timerText.textContent = 'Time up! Folding...';
            elements.timerText.classList.add('urgent');
            setTimeout(() => {
                playerAction('fold');
            }, 500);
        }
    }, 100);
}

function stopTurnTimer() {
    if (turnTimerId) {
        clearInterval(turnTimerId);
        turnTimerId = null;
    }
    turnStartTime = null;
    if (elements.decisionTimer) {
        elements.decisionTimer.classList.add('hidden');
    }
    if (elements.timerText) {
        elements.timerText.classList.remove('urgent');
    }
}

function updateTimerDisplay() {
    if (!turnStartTime || !elements.timerText || !elements.timerFill) return;
    
    const elapsed = Date.now() - turnStartTime;
    const remaining = Math.max(0, TURN_TIME_LIMIT - elapsed);
    const seconds = Math.ceil(remaining / 1000);
    const percentage = (remaining / TURN_TIME_LIMIT) * 100;
    
    elements.timerText.textContent = `Your turn - ${seconds}s`;
    elements.timerFill.style.width = `${percentage}%`;
    
    // Add urgency styling when time is low
    if (seconds <= 5) {
        elements.timerText.classList.add('urgent');
    } else {
        elements.timerText.classList.remove('urgent');
    }
}

// Haptic Feedback Function
function triggerHapticFeedback() {
    // Check if vibration API is supported and device is mobile
    if (typeof navigator !== 'undefined' && navigator.vibrate && /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent)) {
        try {
            // Pattern: 50ms vibration, 100ms pause, 50ms vibration (double tap feel)
            navigator.vibrate([50, 100, 50]);
            console.log('[Haptic] Turn notification vibrated');
        } catch (e) {
            // Silently fail if vibration is blocked or fails
            console.log('[Haptic] Vibration failed:', e.message);
        }
    }
}
