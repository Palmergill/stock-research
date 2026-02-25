// Poker Game Frontend
const API_BASE = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'https://stock-research-production-b3ac.up.railway.app';

let gameState = null;
let playerId = null;
let gameId = null;
let isMyTurn = false;
let raiseSliderValue = 0;

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
    toCall: document.getElementById('to-call'),
    humanName: document.getElementById('human-name'),
    humanChips: document.getElementById('human-chips'),
    humanCards: document.getElementById('human-cards'),
    humanBet: document.getElementById('human-bet'),
    gameLog: document.getElementById('game-log'),
    actionBar: document.getElementById('action-bar'),
    btnFold: document.getElementById('btn-fold'),
    btnCheck: document.getElementById('btn-check'),
    btnCall: document.getElementById('btn-call'),
    btnRaise: document.getElementById('btn-raise'),
    raiseSliderContainer: document.getElementById('raise-slider-container'),
    raiseSlider: document.getElementById('raise-slider'),
    raiseAmount: document.getElementById('raise-amount'),
    btnMinRaise: document.getElementById('btn-min-raise'),
    btnPot: document.getElementById('btn-pot'),
    btnAllIn: document.getElementById('btn-all-in'),
    btnConfirmRaise: document.getElementById('btn-confirm-raise'),
    btnCancelRaise: document.getElementById('btn-cancel-raise'),
    handResult: document.getElementById('hand-result'),
    resultTitle: document.getElementById('result-title'),
    resultDetails: document.getElementById('result-details'),
    btnNextHand: document.getElementById('btn-next-hand')
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    elements.startBtn.addEventListener('click', startGame);
    elements.btnFold.addEventListener('click', () => playerAction('fold'));
    elements.btnCheck.addEventListener('click', () => playerAction('check'));
    elements.btnCall.addEventListener('click', () => playerAction('call'));
    elements.btnRaise.addEventListener('click', showRaiseSlider);
    elements.btnConfirmRaise.addEventListener('click', confirmRaise);
    elements.btnCancelRaise.addEventListener('click', hideRaiseSlider);
    elements.btnNextHand.addEventListener('click', nextHand);
    
    elements.raiseSlider.addEventListener('input', (e) => {
        raiseSliderValue = parseInt(e.target.value);
        elements.raiseAmount.textContent = raiseSliderValue;
    });
    
    elements.btnMinRaise.addEventListener('click', () => {
        const min = gameState?.min_raise || 20;
        setRaiseAmount(min);
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

async function startGame() {
    const name = elements.playerName.value.trim() || 'Player';
    
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
        
        elements.humanName.textContent = name;
        
        switchScreen('game');
        updateGameDisplay();
        addLogEntry('Game started! Good luck!');
        
        // Check if we need to process AI turns
        checkAndProcessAITurns();
        
    } catch (error) {
        console.error('Error starting game:', error);
        alert('Failed to start game. Please try again.');
        elements.startBtn.disabled = false;
        elements.startBtn.textContent = 'Play Now';
    }
}

async function playerAction(action, amount = null) {
    if (!isMyTurn) return;
    
    try {
        const body = { player_id: playerId, action };
        if (amount) body.amount = amount;
        
        const response = await fetch(`${API_BASE}/api/poker/games/${gameId}/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        if (!response.ok) throw new Error('Action failed');
        
        gameState = await response.json();
        
        // Log action
        const myPlayer = gameState.players.find(p => p.id === playerId);
        if (action === 'raise') {
            addLogEntry(`You raise to ${amount}`);
        } else {
            addLogEntry(`You ${action}`);
        }
        
        updateGameDisplay();
        
        // Check for hand complete
        if (gameState.phase === 'showdown') {
            showHandResult();
        } else {
            checkAndProcessAITurns();
        }
        
    } catch (error) {
        console.error('Error:', error);
    }
}

async function checkAndProcessAITurns() {
    // Poll until it's human's turn or hand is over
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/api/poker/games/${gameId}?player_id=${playerId}`);
            if (!response.ok) return;
            
            gameState = await response.json();
            
            // Log AI actions
            if (gameState.last_action && gameState.last_action.player !== elements.humanName.textContent) {
                const action = gameState.last_action;
                let logText = `${action.player} ${action.action}`;
                if (action.amount) {
                    logText += ` ${action.amount}`;
                }
                addLogEntry(logText);
            }
            
            updateGameDisplay();
            
            if (gameState.phase === 'showdown') {
                clearInterval(pollInterval);
                showHandResult();
            } else if (gameState.current_player === playerId) {
                clearInterval(pollInterval);
            }
            
        } catch (error) {
            console.error('Polling error:', error);
        }
    }, 1000);
}

async function nextHand() {
    try {
        elements.btnNextHand.disabled = true;
        elements.btnNextHand.textContent = 'Dealing...';
        
        const response = await fetch(`${API_BASE}/api/poker/games/${gameId}/next-hand`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ player_id: playerId })
        });
        
        if (!response.ok) throw new Error('Failed to start next hand');
        
        gameState = await response.json();
        
        hideHandResult();
        addLogEntry(`--- Hand #${gameState.hand_number} ---`);
        updateGameDisplay();
        
        checkAndProcessAITurns();
        
    } catch (error) {
        console.error('Error:', error);
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
    
    // Update human info
    const myPlayer = gameState.players.find(p => p.id === playerId);
    if (myPlayer) {
        elements.humanChips.textContent = myPlayer.chips;
        elements.humanBet.textContent = myPlayer.bet > 0 ? myPlayer.bet : '';
        
        // Display human cards
        elements.humanCards.innerHTML = myPlayer.hand.map(card => renderCard(card)).join('');
    }
    
    // Update all seats
    gameState.players.forEach((player, index) => {
        const seatEl = document.getElementById(`seat-${index}`);
        if (!seatEl) return;
        
        // Update name and chips
        const nameEl = seatEl.querySelector('.player-name');
        const chipsEl = seatEl.querySelector('.player-chips');
        const betEl = seatEl.querySelector('.player-bet');
        const cardsEl = seatEl.querySelector('.player-cards');
        const dealerBtn = seatEl.querySelector('.dealer-btn');
        
        if (nameEl) nameEl.textContent = player.name;
        if (chipsEl) chipsEl.textContent = player.chips;
        if (betEl) betEl.textContent = player.bet > 0 ? player.bet : '';
        
        // Dealer button
        if (dealerBtn) {
            dealerBtn.classList.toggle('hidden', index !== gameState.dealer_index);
        }
        
        // Cards
        if (cardsEl && !player.is_human) {
            if (gameState.phase === 'showdown' && !player.folded) {
                // Show bot cards at showdown
                cardsEl.innerHTML = player.hand.map(card => renderCard(card)).join('');
            } else {
                // Hidden cards
                cardsEl.innerHTML = `<div class="card hidden"></div><div class="card hidden"></div>`;
            }
        }
        
        // Folded state
        seatEl.classList.toggle('folded', player.folded);
        
        // Active turn
        const isCurrentPlayer = gameState.current_player === player.id;
        seatEl.classList.toggle('active-turn', isCurrentPlayer);
    });
    
    // Update community cards
    const communityCards = gameState.community_cards;
    const flop1 = document.getElementById('flop-1');
    const flop2 = document.getElementById('flop-2');
    const flop3 = document.getElementById('flop-3');
    const turn = document.getElementById('turn');
    const river = document.getElementById('river');
    
    if (flop1) flop1.innerHTML = communityCards[0] ? renderCard(communityCards[0]) : '';
    if (flop2) flop2.innerHTML = communityCards[1] ? renderCard(communityCards[1]) : '';
    if (flop3) flop3.innerHTML = communityCards[2] ? renderCard(communityCards[2]) : '';
    if (turn) turn.innerHTML = communityCards[3] ? renderCard(communityCards[3]) : '';
    if (river) river.innerHTML = communityCards[4] ? renderCard(communityCards[4]) : '';
    
    // Update action buttons
    updateActionButtons();
}

function updateActionButtons() {
    if (!gameState || gameState.phase === 'showdown') {
        elements.actionBar.classList.add('hidden');
        return;
    }
    
    const myPlayer = gameState.players.find(p => p.id === playerId);
    isMyTurn = gameState.current_player === playerId;
    
    if (!isMyTurn || !myPlayer) {
        elements.actionBar.classList.add('hidden');
        return;
    }
    
    elements.actionBar.classList.remove('hidden');
    
    const toCall = gameState.current_bet - myPlayer.bet;
    elements.toCall.textContent = toCall;
    
    // Show/hide buttons based on what's allowed
    elements.btnFold.classList.remove('hidden');
    elements.btnRaise.classList.remove('hidden');
    
    if (toCall === 0) {
        // Can check
        elements.btnCheck.classList.remove('hidden');
        elements.btnCall.classList.add('hidden');
    } else {
        // Must call or fold
        elements.btnCheck.classList.add('hidden');
        elements.btnCall.classList.remove('hidden');
        elements.btnCall.textContent = `Call ${toCall}`;
    }
    
    // Disable if can't afford
    if (toCall > myPlayer.chips) {
        elements.btnCall.textContent = 'All In';
    }
}

function renderCard(card) {
    if (!card) return '';
    const suitClass = card.suit.toLowerCase();
    const display = card.display || '';
    const rank = display.slice(0, -1);
    const suit = display.slice(-1);
    
    return `<div class="card ${suitClass}">
        <span class="rank">${rank}</span>
        <span class="suit">${suit}</span>
    </div>`;
}

function showRaiseSlider() {
    const myPlayer = gameState.players.find(p => p.id === playerId);
    if (!myPlayer) return;
    
    const toCall = gameState.current_bet - myPlayer.bet;
    const minRaise = gameState.min_raise || 20;
    const minTotal = toCall + minRaise;
    
    elements.raiseSlider.min = minTotal;
    elements.raiseSlider.max = myPlayer.chips;
    elements.raiseSlider.value = minTotal;
    raiseSliderValue = minTotal;
    elements.raiseAmount.textContent = minTotal;
    
    elements.raiseSliderContainer.classList.remove('hidden');
    elements.btnFold.classList.add('hidden');
    elements.btnCheck.classList.add('hidden');
    elements.btnCall.classList.add('hidden');
    elements.btnRaise.classList.add('hidden');
}

function hideRaiseSlider() {
    elements.raiseSliderContainer.classList.add('hidden');
    updateActionButtons();
}

function setRaiseAmount(amount) {
    const myPlayer = gameState.players.find(p => p.id === playerId);
    if (!myPlayer) return;
    
    amount = Math.min(amount, myPlayer.chips);
    elements.raiseSlider.value = amount;
    raiseSliderValue = amount;
    elements.raiseAmount.textContent = amount;
}

function confirmRaise() {
    const myPlayer = gameState.players.find(p => p.id === playerId);
    if (!myPlayer) return;
    
    const toCall = gameState.current_bet - myPlayer.bet;
    const raiseAmount = raiseSliderValue - toCall;
    
    hideRaiseSlider();
    playerAction('raise', Math.max(raiseAmount, 0));
}

function showHandResult() {
    if (!gameState.winners || gameState.winners.length === 0) return;
    
    const winner = gameState.winners[0];
    const isMe = winner.id === playerId;
    
    elements.resultTitle.textContent = isMe ? '🎉 You Win!' : `${winner.name} Wins`;
    
    let detailsHTML = `<p class="winner-name">${winner.name}</p>`;
    detailsHTML += `<p class="win-amount">+${winner.amount} chips</p>`;
    
    if (winner.hand && winner.hand.length > 0) {
        detailsHTML += `<p>Winning hand:</p>`;
        detailsHTML += `<div class="winning-hand">`;
        detailsHTML += winner.hand.map(card => renderCard(card)).join('');
        detailsHTML += `</div>`;
    }
    
    elements.resultDetails.innerHTML = detailsHTML;
    elements.handResult.classList.remove('hidden');
}

function hideHandResult() {
    elements.handResult.classList.add('hidden');
}

function addLogEntry(message) {
    const entry = document.createElement('div');
    entry.className = 'log-entry';
    entry.textContent = message;
    elements.gameLog.appendChild(entry);
    elements.gameLog.scrollTop = elements.gameLog.scrollHeight;
}

function switchScreen(screenName) {
    Object.values(screens).forEach(screen => screen.classList.remove('active'));
    screens[screenName].classList.add('active');
}
