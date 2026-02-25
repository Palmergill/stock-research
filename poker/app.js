// Poker Game Frontend - Option A: Bottom Focus Design
const API_BASE = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'https://stock-research-production-b3ac.up.railway.app';

let gameState = null;
let playerId = null;
let gameId = null;
let isMyTurn = false;
let raiseAmount = 0;
let pollIntervalId = null;

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
    opponentsRow: document.getElementById('opponents-row'),
    communityCards: document.getElementById('community-cards'),
    yourCards: document.getElementById('your-cards'),
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
    btnNextHand: document.getElementById('btn-next-hand')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
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
        
        if (!response.ok) throw new Error('Failed to start game');
        
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
        alert('Failed to start game. Please try again.');
        elements.startBtn.disabled = false;
        elements.startBtn.textContent = 'Play Now';
    }
}

function startPolling() {
    // Clear any existing polling
    if (pollIntervalId) {
        clearInterval(pollIntervalId);
        pollIntervalId = null;
    }
    
    pollIntervalId = setInterval(async () => {
        if (!gameId || !playerId) {
            clearInterval(pollIntervalId);
            pollIntervalId = null;
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/api/poker/games/${gameId}?player_id=${playerId}&process_ai=true`);
            if (!response.ok) return;
            
            const newState = await response.json();
            gameState = newState;
            updateGameDisplay();
            
            if (gameState.phase === 'showdown') {
                clearInterval(pollIntervalId);
                pollIntervalId = null;
                showHandResult();
            }
            
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 1000);
}

async function playerAction(action) {
    if (!isMyTurn && action !== 'fold') return;
    
    let amount = null;
    if (action === 'raise') {
        amount = raiseAmount;
    }
    
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
        updateGameDisplay();
        
        if (gameState.phase === 'showdown') {
            showHandResult();
        }
        
    } catch (error) {
        console.error('Error:', error);
    }
}

function showRaiseControls() {
    const myPlayer = gameState?.players?.find(p => p.id === playerId);
    if (!myPlayer) return;
    
    const toCall = (gameState?.current_bet || 0) - (myPlayer?.bet || 0);
    const minRaise = gameState?.min_raise || 20;
    const minTotal = toCall + minRaise;
    
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
        console.error('Error:', error);
        const message = typeof error === 'string' ? error : (error.message || 'Failed to start next hand');
        alert(message);
    } finally {
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
    
    // Check if it's your turn
    const isYourTurn = gameState.current_player === playerId && gameState.phase !== 'showdown';
    
    // Update your info
    const myPlayer = gameState.players.find(p => p.id === playerId);
    if (myPlayer) {
        elements.yourChips.textContent = myPlayer.chips;
        
        // Your cards with animation
        const cardsHTML = myPlayer.hand.map(card => renderCard(card, true)).join('');
        elements.yourCards.innerHTML = cardsHTML;
        
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
    if (!card) return '';
    
    const isRed = card.suit === 'HEARTS' || card.suit === 'DIAMONDS';
    const suitSymbol = { 'HEARTS': '♥', 'DIAMONDS': '♦', 'CLUBS': '♣', 'SPADES': '♠' }[card.suit] || '';
    const rank = { 14: 'A', 13: 'K', 12: 'Q', 11: 'J' }[card.rank] || card.rank;
    
    return `<div class="card ${isRed ? '' : 'black'}">${rank}${suitSymbol}</div>`;
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
    
    // Disable raise if can't afford min raise
    const minRaise = gameState.min_raise || 20;
    const canRaise = myPlayer.chips > toCall + minRaise;
    elements.btnRaise.disabled = !canRaise;
    elements.btnRaise.style.opacity = canRaise ? '1' : '0.4';
}

function showHandResult() {
    if (!gameState.winners || gameState.winners.length === 0) return;
    
    // Update display one more time to show all cards
    updateGameDisplay();
    
    const winner = gameState.winners[0];
    const isMe = winner.id === playerId;
    
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
}
