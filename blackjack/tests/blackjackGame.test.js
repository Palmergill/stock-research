const game = require('../blackjackGame');

const C = game.createCard;

function stateWithDraws(draws, options = {}) {
    const filler = Array.from({ length: 60 }, () => C('2', 'clubs'));
    return game.createState({
        bankroll: 1000,
        startingBet: 100,
        shoe: [...filler, ...[...draws].reverse()],
        ...options
    });
}

describe('blackjack rules', () => {
    test('scores soft hands and ace adjustments correctly', () => {
        expect(game.handValue([C('A', 'spades'), C('6', 'clubs')])).toMatchObject({
            total: 17,
            soft: true,
            bust: false
        });

        expect(game.handValue([C('A', 'spades'), C('6', 'clubs'), C('K', 'hearts')])).toMatchObject({
            total: 17,
            soft: false,
            bust: false
        });
    });

    test('player blackjack pays 3:2', () => {
        const state = stateWithDraws([
            C('A', 'spades'),
            C('5', 'clubs'),
            C('K', 'diamonds'),
            C('9', 'clubs')
        ]);

        game.startRound(state, 100);

        expect(state.status).toBe('roundOver');
        expect(state.playerHands[0].result).toBe('blackjack');
        expect(state.balance).toBe(1150);
        expect(state.message).toContain('Blackjack pays 3:2');
    });

    test('dealer hits soft 17', () => {
        const state = stateWithDraws([
            C('10', 'spades'),
            C('A', 'clubs'),
            C('Q', 'diamonds'),
            C('6', 'hearts'),
            C('4', 'clubs')
        ]);

        game.startRound(state, 100);
        game.declineInsurance(state);
        game.stand(state);

        expect(game.handValue(state.dealerHand)).toMatchObject({
            total: 21,
            soft: true
        });
        expect(state.dealerHand).toHaveLength(3);
        expect(state.playerHands[0].result).toBe('lose');
        expect(state.balance).toBe(900);
    });

    test('split aces receive one card each and then resolve', () => {
        const state = stateWithDraws([
            C('A', 'spades'),
            C('9', 'clubs'),
            C('A', 'diamonds'),
            C('7', 'hearts'),
            C('10', 'clubs'),
            C('K', 'diamonds'),
            C('5', 'clubs')
        ], { startingBet: 50 });

        game.startRound(state, 50);
        game.split(state);

        expect(state.playerHands).toHaveLength(2);
        state.playerHands.forEach((hand) => {
            expect(hand.cards).toHaveLength(2);
            expect(hand.stood).toBe(true);
            expect(hand.isSplitAces).toBe(true);
            expect(hand.result).toBe('push');
        });
        expect(game.handValue(state.dealerHand).total).toBe(21);
        expect(state.status).toBe('roundOver');
        expect(state.balance).toBe(1000);
    });

    test('insurance pays 2:1 when dealer has blackjack', () => {
        const state = stateWithDraws([
            C('10', 'spades'),
            C('A', 'clubs'),
            C('Q', 'diamonds'),
            C('K', 'hearts')
        ]);

        game.startRound(state, 100);
        expect(state.status).toBe('insurance');

        game.takeInsurance(state);

        expect(state.status).toBe('roundOver');
        expect(state.insuranceBet).toBe(50);
        expect(state.playerHands[0].result).toBe('lose');
        expect(state.balance).toBe(1000);
        expect(state.message).toContain('Insurance wins $100');
    });

    test('double after split is allowed on non-ace pairs', () => {
        const state = stateWithDraws([
            C('8', 'spades'),
            C('6', 'clubs'),
            C('8', 'diamonds'),
            C('9', 'hearts'),
            C('3', 'clubs'),
            C('2', 'diamonds'),
            C('K', 'clubs')
        ], { startingBet: 50 });

        game.startRound(state, 50);
        game.split(state);

        expect(game.canDoubleHand(state, state.playerHands[0])).toBe(true);
        game.doubleDown(state);

        expect(state.playerHands[0].doubled).toBe(true);
        expect(state.playerHands[0].bet).toBe(100);
    });
});
