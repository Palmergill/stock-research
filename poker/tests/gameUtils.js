/**
 * Poker Game Utilities - Testable functions extracted from app.js
 */

/**
 * Calculate pot odds
 * @param {number} potSize - Current pot size
 * @param {number} betToCall - Amount needed to call
 * @returns {Object} Pot odds info { ratio, equity }
 */
function calculatePotOdds(potSize, betToCall) {
  if (!betToCall || betToCall <= 0) {
    return null;
  }
  const ratio = potSize / betToCall;
  const equity = (betToCall / (potSize + betToCall)) * 100;
  return {
    ratio: ratio.toFixed(1),
    equity: Math.round(equity)
  };
}

/**
 * Format chips for display
 * @param {number} chips - Number of chips
 * @returns {string} Formatted chip string
 */
function formatChips(chips) {
  if (chips >= 1000000) {
    return (chips / 1000000).toFixed(1) + 'M';
  }
  if (chips >= 1000) {
    return (chips / 1000).toFixed(1) + 'K';
  }
  return chips.toString();
}

/**
 * Get card rank value (for comparison)
 * @param {string} rank - Card rank (2-10, J, Q, K, A)
 * @returns {number} Numeric value
 */
function getCardValue(rank) {
  const values = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
    '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14
  };
  return values[rank] || 0;
}

/**
 * Format hand strength description
 * @param {string} handRank - Hand rank name
 * @returns {string} Formatted description
 */
function formatHandStrength(handRank) {
  if (!handRank) return '';
  
  const descriptions = {
    'high_card': 'High Card',
    'one_pair': 'Pair',
    'two_pair': 'Two Pair',
    'three_of_a_kind': 'Three of a Kind',
    'straight': 'Straight',
    'flush': 'Flush',
    'full_house': 'Full House',
    'four_of_a_kind': 'Four of a Kind',
    'straight_flush': 'Straight Flush',
    'royal_flush': 'Royal Flush'
  };
  
  return descriptions[handRank] || handRank.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Validate raise amount
 * @param {number} amount - Raise amount
 * @param {number} minRaise - Minimum raise
 * @param {number} maxRaise - Maximum raise (player's stack)
 * @param {number} currentBet - Current bet to call
 * @returns {Object} Validation result
 */
function validateRaiseAmount(amount, minRaise, maxRaise, currentBet) {
  const totalBet = currentBet + amount;
  
  if (amount <= 0) {
    return { valid: false, error: 'Raise amount must be positive' };
  }
  
  if (totalBet < minRaise) {
    return { valid: false, error: `Minimum raise is ${minRaise}` };
  }
  
  if (totalBet > maxRaise) {
    return { valid: false, error: `Maximum raise is ${maxRaise}` };
  }
  
  return { valid: true };
}

/**
 * Check if player can perform action
 * @param {string} action - Action type
 * @param {Object} gameState - Current game state
 * @param {string} playerId - Player ID
 * @returns {boolean} Whether action is allowed
 */
function canPerformAction(action, gameState, playerId) {
  if (!gameState || gameState.status !== 'active') {
    return false;
  }
  
  if (gameState.current_player_id !== playerId) {
    return false;
  }
  
  const player = gameState.players?.find(p => p.id === playerId);
  if (!player || player.folded || player.all_in) {
    return false;
  }
  
  if (action === 'check') {
    // Can only check if no bet to call or already matched
    const currentBet = player.current_bet || 0;
    const highestBet = Math.max(...(gameState.players?.map(p => p.current_bet || 0) || [0]));
    return currentBet >= highestBet;
  }
  
  if (action === 'call') {
    // Can call if there's a bet to match
    const currentBet = player.current_bet || 0;
    const highestBet = Math.max(...(gameState.players?.map(p => p.current_bet || 0) || [0]));
    return highestBet > currentBet;
  }
  
  if (action === 'raise') {
    // Can raise if player has chips
    return player.chips > 0;
  }
  
  if (action === 'fold') {
    // Can always fold
    return true;
  }
  
  return false;
}

/**
 * Generate avatar from player name
 * @param {string} name - Player name
 * @returns {Object} Avatar info { emoji, bgColor }
 */
function generateAvatar(name) {
  const emojis = ['🤖', '👾', '🎰', '🎯', '🎲', '🃏', '🦁', '🐯', '🦊', '🐺'];
  const colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e91e63', '#ff5722'];
  
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  
  const emojiIndex = Math.abs(hash) % emojis.length;
  const colorIndex = Math.abs(hash >> 4) % colors.length;
  
  return {
    emoji: emojis[emojiIndex],
    bgColor: colors[colorIndex],
    initials: name.substring(0, 2).toUpperCase()
  };
}

// Export for testing (Node.js environment)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    calculatePotOdds,
    formatChips,
    getCardValue,
    formatHandStrength,
    validateRaiseAmount,
    canPerformAction,
    generateAvatar
  };
}
