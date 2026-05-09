(function (root, factory) {
    if (typeof module === "object" && module.exports) {
        module.exports = factory();
    } else {
        root.BlackjackGame = factory();
    }
})(typeof self !== "undefined" ? self : this, function () {
    const SUITS = ["spades", "hearts", "diamonds", "clubs"];
    const RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"];
    const DEFAULTS = {
        decks: 6,
        minBet: 5,
        maxBet: 500,
        bankroll: 1000,
        startingBet: 25,
        maxHands: 4,
        dealerHitsSoft17: true,
        blackjackPayout: 1.5
    };

    function createCard(rank, suit) {
        return { rank, suit };
    }

    function cardPip(card) {
        if (!card) return "";
        const symbols = { spades: "♠", hearts: "♥", diamonds: "♦", clubs: "♣" };
        return `${card.rank}${symbols[card.suit] || ""}`;
    }

    function cardValue(card) {
        if (!card) return 0;
        if (card.rank === "A") return 11;
        if (["K", "Q", "J"].includes(card.rank)) return 10;
        return Number(card.rank);
    }

    function createShoe(decks = DEFAULTS.decks, rng = Math.random) {
        const cards = [];
        for (let deck = 0; deck < decks; deck += 1) {
            SUITS.forEach((suit) => {
                RANKS.forEach((rank) => cards.push(createCard(rank, suit)));
            });
        }

        for (let i = cards.length - 1; i > 0; i -= 1) {
            const j = Math.floor(rng() * (i + 1));
            [cards[i], cards[j]] = [cards[j], cards[i]];
        }
        return cards;
    }

    function handValue(cards) {
        let total = 0;
        let aces = 0;

        cards.forEach((card) => {
            total += cardValue(card);
            if (card.rank === "A") aces += 1;
        });

        while (total > 21 && aces > 0) {
            total -= 10;
            aces -= 1;
        }

        return {
            total,
            soft: aces > 0,
            bust: total > 21,
            blackjack: cards.length === 2 && total === 21
        };
    }

    function formatMoney(amount) {
        const rounded = Math.round(amount * 100) / 100;
        return rounded % 1 === 0 ? `$${rounded}` : `$${rounded.toFixed(2)}`;
    }

    function normalizeOptions(options = {}) {
        return { ...DEFAULTS, ...options };
    }

    function createState(options = {}) {
        const rules = normalizeOptions(options);
        return {
            rules,
            shoe: options.shoe ? [...options.shoe] : createShoe(rules.decks, options.rng || Math.random),
            balance: options.bankroll ?? rules.bankroll,
            currentBet: options.startingBet ?? rules.startingBet,
            status: "betting",
            message: "Place your bet.",
            dealerHand: [],
            playerHands: [],
            activeHandIndex: 0,
            insuranceAvailable: false,
            insuranceBet: 0,
            round: 0,
            lastOutcome: []
        };
    }

    function activeHand(state) {
        return state.playerHands[state.activeHandIndex] || null;
    }

    function canSplitHand(hand) {
        if (!hand || hand.cards.length !== 2) return false;
        return cardValue(hand.cards[0]) === cardValue(hand.cards[1]);
    }

    function canDoubleHand(state, hand = activeHand(state)) {
        return state.status === "playing" &&
            hand &&
            hand.cards.length === 2 &&
            !hand.stood &&
            !hand.isSplitAces &&
            state.balance >= hand.bet;
    }

    function canSplit(state, hand = activeHand(state)) {
        return state.status === "playing" &&
            canSplitHand(hand) &&
            state.playerHands.length < state.rules.maxHands &&
            state.balance >= hand.bet;
    }

    function ensureShoe(state) {
        if (state.shoe.length < 52) {
            state.shoe = createShoe(state.rules.decks);
            state.message = "Shuffling a fresh six-deck shoe.";
        }
    }

    function dealCard(state) {
        if (state.shoe.length === 0) {
            state.shoe = createShoe(state.rules.decks);
        }
        return state.shoe.pop();
    }

    function setBet(state, amount) {
        const cleanAmount = Math.max(state.rules.minBet, Math.min(state.rules.maxBet, Math.round(Number(amount) || state.rules.minBet)));
        state.currentBet = Math.min(cleanAmount, Math.floor(state.balance));
        state.message = `Bet set to ${formatMoney(state.currentBet)}.`;
        return state;
    }

    function startRound(state, amount = state.currentBet) {
        if (state.status === "playing" || state.status === "insurance") return state;

        ensureShoe(state);
        const bet = Math.max(state.rules.minBet, Math.min(state.rules.maxBet, Math.round(Number(amount) || state.currentBet)));
        if (bet > state.balance) {
            state.message = "You do not have enough chips for that bet.";
            return state;
        }

        state.balance -= bet;
        state.currentBet = bet;
        state.round += 1;
        state.dealerHand = [];
        state.playerHands = [{ cards: [], bet, doubled: false, stood: false, isSplitAces: false, result: null, payout: 0 }];
        state.activeHandIndex = 0;
        state.insuranceAvailable = false;
        state.insuranceBet = 0;
        state.lastOutcome = [];

        state.playerHands[0].cards.push(dealCard(state));
        state.dealerHand.push(dealCard(state));
        state.playerHands[0].cards.push(dealCard(state));
        state.dealerHand.push(dealCard(state));

        const dealerUpCard = state.dealerHand[0];
        const playerValue = handValue(state.playerHands[0].cards);

        if (dealerUpCard.rank === "A" && !playerValue.blackjack) {
            state.status = "insurance";
            state.insuranceAvailable = true;
            state.message = "Dealer shows an ace. Take insurance?";
            return state;
        }

        return settleInitialBlackjack(state);
    }

    function takeInsurance(state) {
        if (state.status !== "insurance" || !state.insuranceAvailable) return state;
        const wager = state.playerHands[0].bet / 2;
        if (state.balance < wager) {
            state.message = "Not enough chips for insurance.";
            return state;
        }
        state.balance -= wager;
        state.insuranceBet = wager;
        state.insuranceAvailable = false;
        state.message = `Insurance booked for ${formatMoney(wager)}.`;
        return settleInitialBlackjack(state);
    }

    function declineInsurance(state) {
        if (state.status !== "insurance") return state;
        state.insuranceAvailable = false;
        state.message = "Insurance declined.";
        return settleInitialBlackjack(state);
    }

    function settleInitialBlackjack(state) {
        const hand = state.playerHands[0];
        const playerValue = handValue(hand.cards);
        const dealerValue = handValue(state.dealerHand);
        const dealerBlackjack = dealerValue.blackjack;
        const playerBlackjack = playerValue.blackjack;

        if (state.insuranceBet > 0) {
            if (dealerBlackjack) {
                const insuranceReturn = state.insuranceBet * 3;
                state.balance += insuranceReturn;
                state.lastOutcome.push(`Insurance wins ${formatMoney(insuranceReturn - state.insuranceBet)}.`);
            } else {
                state.lastOutcome.push("Insurance loses.");
            }
        }

        if (playerBlackjack || dealerBlackjack) {
            state.status = "roundOver";
            hand.stood = true;

            if (playerBlackjack && dealerBlackjack) {
                hand.result = "push";
                hand.payout = hand.bet;
                state.balance += hand.bet;
                state.lastOutcome.push("Both have blackjack. Push.");
            } else if (playerBlackjack) {
                const payout = hand.bet * (1 + state.rules.blackjackPayout);
                hand.result = "blackjack";
                hand.payout = payout;
                state.balance += payout;
                state.lastOutcome.push(`Blackjack pays 3:2. You win ${formatMoney(payout - hand.bet)}.`);
            } else {
                hand.result = "lose";
                state.lastOutcome.push("Dealer has blackjack.");
            }

            state.message = state.lastOutcome.join(" ");
            return state;
        }

        state.status = "playing";
        state.message = "Your move.";
        return state;
    }

    function hit(state) {
        if (state.status !== "playing") return state;
        const hand = activeHand(state);
        if (!hand || hand.stood || hand.isSplitAces) return state;

        hand.cards.push(dealCard(state));
        const value = handValue(hand.cards);
        if (value.bust) {
            hand.result = "lose";
            hand.stood = true;
            state.message = `Hand ${state.activeHandIndex + 1} busts with ${value.total}.`;
            return advanceHand(state);
        }

        state.message = `Hand ${state.activeHandIndex + 1}: ${value.total}${value.soft ? " soft" : ""}.`;
        return state;
    }

    function stand(state) {
        if (state.status !== "playing") return state;
        const hand = activeHand(state);
        if (!hand) return state;
        hand.stood = true;
        state.message = `Standing on hand ${state.activeHandIndex + 1}.`;
        return advanceHand(state);
    }

    function doubleDown(state) {
        const hand = activeHand(state);
        if (!canDoubleHand(state, hand)) return state;

        state.balance -= hand.bet;
        hand.bet *= 2;
        hand.doubled = true;
        hand.cards.push(dealCard(state));
        hand.stood = true;

        const value = handValue(hand.cards);
        state.message = value.bust
            ? `Double down busts with ${value.total}.`
            : `Double down to ${value.total}.`;

        if (value.bust) hand.result = "lose";
        return advanceHand(state);
    }

    function split(state) {
        const hand = activeHand(state);
        if (!canSplit(state, hand)) return state;

        state.balance -= hand.bet;
        const splitAces = hand.cards[0].rank === "A" && hand.cards[1].rank === "A";
        const left = {
            cards: [hand.cards[0], dealCard(state)],
            bet: hand.bet,
            doubled: false,
            stood: splitAces,
            isSplitAces: splitAces,
            result: null,
            payout: 0
        };
        const right = {
            cards: [hand.cards[1], dealCard(state)],
            bet: hand.bet,
            doubled: false,
            stood: splitAces,
            isSplitAces: splitAces,
            result: null,
            payout: 0
        };

        state.playerHands.splice(state.activeHandIndex, 1, left, right);
        state.message = splitAces ? "Split aces receive one card each." : "Hand split.";

        if (splitAces) {
            return advanceHand(state);
        }

        return state;
    }

    function advanceHand(state) {
        for (let i = state.activeHandIndex + 1; i < state.playerHands.length; i += 1) {
            const hand = state.playerHands[i];
            if (!hand.stood && !hand.result) {
                state.activeHandIndex = i;
                return state;
            }
        }

        const firstPlayable = state.playerHands.findIndex((hand) => !hand.stood && !hand.result);
        if (firstPlayable !== -1) {
            state.activeHandIndex = firstPlayable;
            return state;
        }

        return playDealerAndResolve(state);
    }

    function playDealerAndResolve(state) {
        const liveHands = state.playerHands.filter((hand) => hand.result !== "lose" && !handValue(hand.cards).bust);
        if (liveHands.length === 0) {
            state.status = "roundOver";
            state.message = state.message || "All hands busted.";
            return state;
        }

        let dealerValue = handValue(state.dealerHand);
        while (dealerValue.total < 17 || (state.rules.dealerHitsSoft17 && dealerValue.total === 17 && dealerValue.soft)) {
            state.dealerHand.push(dealCard(state));
            dealerValue = handValue(state.dealerHand);
        }

        const outcomes = [];
        state.playerHands.forEach((hand, index) => {
            if (hand.result === "lose" || handValue(hand.cards).bust) {
                hand.result = "lose";
                outcomes.push(`Hand ${index + 1} loses.`);
                return;
            }

            const playerValue = handValue(hand.cards);
            if (dealerValue.bust || playerValue.total > dealerValue.total) {
                hand.result = "win";
                hand.payout = hand.bet * 2;
                state.balance += hand.payout;
                outcomes.push(`Hand ${index + 1} wins ${formatMoney(hand.bet)}.`);
            } else if (playerValue.total === dealerValue.total) {
                hand.result = "push";
                hand.payout = hand.bet;
                state.balance += hand.bet;
                outcomes.push(`Hand ${index + 1} pushes.`);
            } else {
                hand.result = "lose";
                outcomes.push(`Hand ${index + 1} loses.`);
            }
        });

        state.status = "roundOver";
        state.lastOutcome = outcomes;
        state.message = outcomes.join(" ");
        return state;
    }

    function newShoe(state) {
        state.shoe = createShoe(state.rules.decks);
        state.status = "betting";
        state.dealerHand = [];
        state.playerHands = [];
        state.activeHandIndex = 0;
        state.insuranceAvailable = false;
        state.insuranceBet = 0;
        state.lastOutcome = [];
        state.message = "Fresh six-deck shoe.";
        return state;
    }

    function resetBankroll(state) {
        state.balance = state.rules.bankroll;
        state.currentBet = state.rules.startingBet;
        return newShoe(state);
    }

    return {
        DEFAULTS,
        RANKS,
        SUITS,
        activeHand,
        canDoubleHand,
        canSplit,
        canSplitHand,
        cardPip,
        cardValue,
        createCard,
        createShoe,
        createState,
        declineInsurance,
        doubleDown,
        formatMoney,
        handValue,
        hit,
        newShoe,
        resetBankroll,
        setBet,
        split,
        stand,
        startRound,
        takeInsurance
    };
});
