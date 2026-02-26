/**
 * @jest-environment jsdom
 */

const {
  calculatePotOdds,
  formatChips,
  getCardValue,
  formatHandStrength,
  validateRaiseAmount,
  canPerformAction,
  generateAvatar
} = require('./gameUtils');

describe('calculatePotOdds', () => {
  test('calculates correct pot odds for standard scenario', () => {
    const result = calculatePotOdds(100, 20);
    expect(result.ratio).toBe('5.0');
    expect(result.equity).toBe(17);
  });

  test('returns null when no bet to call', () => {
    expect(calculatePotOdds(100, 0)).toBeNull();
    expect(calculatePotOdds(100, null)).toBeNull();
    expect(calculatePotOdds(100, undefined)).toBeNull();
  });

  test('handles negative bet values', () => {
    expect(calculatePotOdds(100, -10)).toBeNull();
  });

  test('calculates correctly for all-in scenario', () => {
    const result = calculatePotOdds(500, 200);
    expect(result.ratio).toBe('2.5');
    expect(result.equity).toBe(29);
  });
});

describe('formatChips', () => {
  test('formats small numbers correctly', () => {
    expect(formatChips(100)).toBe('100');
    expect(formatChips(999)).toBe('999');
  });

  test('formats thousands with K suffix', () => {
    expect(formatChips(1000)).toBe('1.0K');
    expect(formatChips(2500)).toBe('2.5K');
    expect(formatChips(999999)).toBe('1000.0K');
  });

  test('formats millions with M suffix', () => {
    expect(formatChips(1000000)).toBe('1.0M');
    expect(formatChips(2500000)).toBe('2.5M');
  });
});

describe('getCardValue', () => {
  test('returns correct values for number cards', () => {
    expect(getCardValue('2')).toBe(2);
    expect(getCardValue('5')).toBe(5);
    expect(getCardValue('10')).toBe(10);
  });

  test('returns correct values for face cards', () => {
    expect(getCardValue('J')).toBe(11);
    expect(getCardValue('Q')).toBe(12);
    expect(getCardValue('K')).toBe(13);
    expect(getCardValue('A')).toBe(14);
  });

  test('returns 0 for invalid cards', () => {
    expect(getCardValue('')).toBe(0);
    expect(getCardValue('X')).toBe(0);
    expect(getCardValue(null)).toBe(0);
  });
});

describe('formatHandStrength', () => {
  test('formats standard hand ranks', () => {
    expect(formatHandStrength('high_card')).toBe('High Card');
    expect(formatHandStrength('one_pair')).toBe('Pair');
    expect(formatHandStrength('two_pair')).toBe('Two Pair');
    expect(formatHandStrength('straight')).toBe('Straight');
    expect(formatHandStrength('flush')).toBe('Flush');
    expect(formatHandStrength('royal_flush')).toBe('Royal Flush');
  });

  test('handles unknown hand ranks', () => {
    expect(formatHandStrength('unknown_hand')).toBe('Unknown Hand');
  });

  test('handles empty input', () => {
    expect(formatHandStrength('')).toBe('');
    expect(formatHandStrength(null)).toBe('');
  });
});

describe('validateRaiseAmount', () => {
  test('validates correct raise amount', () => {
    // currentBet=20, raising by 100 means total bet is 120, which exceeds minRaise of 100
    const result = validateRaiseAmount(100, 100, 500, 20);
    expect(result.valid).toBe(true);
    expect(result.error).toBeUndefined();
  });

  test('rejects negative raise', () => {
    const result = validateRaiseAmount(-10, 100, 500, 20);
    expect(result.valid).toBe(false);
    expect(result.error).toContain('positive');
  });

  test('rejects zero raise', () => {
    const result = validateRaiseAmount(0, 100, 500, 20);
    expect(result.valid).toBe(false);
  });

  test('rejects raise below minimum', () => {
    const result = validateRaiseAmount(10, 100, 500, 20);
    expect(result.valid).toBe(false);
    expect(result.error).toContain('Minimum raise');
  });

  test('rejects raise above maximum', () => {
    const result = validateRaiseAmount(500, 100, 400, 20);
    expect(result.valid).toBe(false);
    expect(result.error).toContain('Maximum raise');
  });
});

describe('canPerformAction', () => {
  const mockGameState = {
    status: 'active',
    current_player_id: 'player1',
    players: [
      { id: 'player1', folded: false, all_in: false, current_bet: 10, chips: 100 },
      { id: 'player2', folded: false, all_in: false, current_bet: 20, chips: 100 }
    ]
  };

  test('allows fold when it is player turn', () => {
    expect(canPerformAction('fold', mockGameState, 'player1')).toBe(true);
  });

  test('allows call when bet to match exists', () => {
    expect(canPerformAction('call', mockGameState, 'player1')).toBe(true);
  });

  test('rejects call when no bet to match', () => {
    const noBetState = {
      ...mockGameState,
      players: [
        { id: 'player1', folded: false, all_in: false, current_bet: 20, chips: 100 },
        { id: 'player2', folded: false, all_in: false, current_bet: 20, chips: 100 }
      ]
    };
    expect(canPerformAction('call', noBetState, 'player1')).toBe(false);
  });

  test('allows check when no bet to match', () => {
    const noBetState = {
      ...mockGameState,
      players: [
        { id: 'player1', folded: false, all_in: false, current_bet: 20, chips: 100 },
        { id: 'player2', folded: false, all_in: false, current_bet: 20, chips: 100 }
      ]
    };
    expect(canPerformAction('check', noBetState, 'player1')).toBe(true);
  });

  test('rejects check when bet to match exists', () => {
    expect(canPerformAction('check', mockGameState, 'player1')).toBe(false);
  });

  test('allows raise when player has chips', () => {
    expect(canPerformAction('raise', mockGameState, 'player1')).toBe(true);
  });

  test('rejects action when not player turn', () => {
    expect(canPerformAction('fold', mockGameState, 'player2')).toBe(false);
  });

  test('rejects action when game not active', () => {
    const inactiveState = { ...mockGameState, status: 'finished' };
    expect(canPerformAction('fold', inactiveState, 'player1')).toBe(false);
  });

  test('rejects action when player folded', () => {
    const foldedState = {
      ...mockGameState,
      players: [
        { id: 'player1', folded: true, all_in: false, current_bet: 10, chips: 100 },
        { id: 'player2', folded: false, all_in: false, current_bet: 20, chips: 100 }
      ]
    };
    expect(canPerformAction('fold', foldedState, 'player1')).toBe(false);
  });

  test('rejects action when player all-in', () => {
    const allInState = {
      ...mockGameState,
      players: [
        { id: 'player1', folded: false, all_in: true, current_bet: 100, chips: 0 },
        { id: 'player2', folded: false, all_in: false, current_bet: 20, chips: 100 }
      ]
    };
    expect(canPerformAction('fold', allInState, 'player1')).toBe(false);
  });
});

describe('generateAvatar', () => {
  test('generates consistent avatar for same name', () => {
    const avatar1 = generateAvatar('Alice');
    const avatar2 = generateAvatar('Alice');
    expect(avatar1.emoji).toBe(avatar2.emoji);
    expect(avatar1.bgColor).toBe(avatar2.bgColor);
  });

  test('generates different avatars for different names', () => {
    const avatar1 = generateAvatar('Alice');
    const avatar2 = generateAvatar('Bob');
    // They might be the same by chance, but unlikely with 10 emojis and 8 colors
    expect(avatar1.emoji !== avatar2.emoji || avatar1.bgColor !== avatar2.bgColor).toBe(true);
  });

  test('generates initials from name', () => {
    expect(generateAvatar('Alice').initials).toBe('AL');
    expect(generateAvatar('Bob').initials).toBe('BO');
    expect(generateAvatar('Charlie').initials).toBe('CH');
  });

  test('has required properties', () => {
    const avatar = generateAvatar('Test');
    expect(avatar).toHaveProperty('emoji');
    expect(avatar).toHaveProperty('bgColor');
    expect(avatar).toHaveProperty('initials');
    expect(typeof avatar.emoji).toBe('string');
    expect(typeof avatar.bgColor).toBe('string');
    expect(typeof avatar.initials).toBe('string');
  });
});
