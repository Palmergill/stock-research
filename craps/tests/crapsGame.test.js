const fs = require('fs');
const path = require('path');
const { TextDecoder, TextEncoder } = require('util');

global.TextDecoder = TextDecoder;
global.TextEncoder = TextEncoder;

const { JSDOM } = require('jsdom');

function loadGame() {
  const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
  return new JSDOM(html, {
    runScripts: 'dangerously',
    url: 'http://localhost/craps/',
  }).window;
}

function readState(window) {
  return JSON.parse(window.eval(`JSON.stringify({
    balance,
    point,
    isComeOutRoll,
    passLine: bets.passLine,
    passLineOdds: oddsBets.passLine,
    place6: bets.place6,
    field: bets.field,
    comeBets,
    dontComeBets,
    currentPopupBetId,
    status: document.getElementById('gameStatus').textContent,
    rollDisabled: document.getElementById('rollButton').disabled,
  })`));
}

describe('craps game regressions', () => {
  test("established Come and Don't Come bets survive pass-line come-out naturals", () => {
    const window = loadGame();
    window.eval(`
      balance = 970;
      point = null;
      isComeOutRoll = true;
      bets.passLine = 10;
      comeBets = [{ id: 1, point: 6, amount: 10, odds: 5 }];
      dontComeBets = [{ id: 2, point: 8, amount: 10, odds: 5 }];
      nextComeBetId = 3;
    `);

    window.resolveRoll(3, 4);
    const state = readState(window);

    expect(state.balance).toBe(990);
    expect(state.point).toBeNull();
    expect(state.isComeOutRoll).toBe(true);
    expect(state.passLine).toBe(0);
    expect(state.comeBets).toEqual([{ id: 1, point: 6, amount: 10, odds: 5 }]);
    expect(state.dontComeBets).toEqual([{ id: 2, point: 8, amount: 10, odds: 5 }]);
  });

  test('point popup odds are capped at the remaining max odds', () => {
    const window = loadGame();
    window.eval(`
      balance = 1000;
      point = 6;
      isComeOutRoll = false;
      bets.passLine = 10;
      oddsBets.passLine = 40;
      currentPopupBetType = 'passLine';
      currentPopupBetId = null;
    `);

    window.takeOddsFromPopup(3);
    const state = readState(window);

    expect(state.balance).toBe(990);
    expect(state.passLineOdds).toBe(50);
  });

  test('Come odds popup targets the same bet after earlier resolved bets are removed', () => {
    const window = loadGame();
    window.setTimeout = (fn) => {
      fn();
      return 1;
    };
    window.eval(`
      balance = 990;
      point = 8;
      isComeOutRoll = false;
      comeBets = [
        { id: 1, point: 6, amount: 5, odds: 0 },
        { id: 2, point: null, amount: 5, odds: 0 },
      ];
      nextComeBetId = 3;
    `);

    window.resolveRoll(3, 3);
    expect(readState(window).currentPopupBetId).toBe(2);

    window.takeOddsFromPopup(1);
    const state = readState(window);

    expect(state.balance).toBe(995);
    expect(state.comeBets).toEqual([{ id: 2, point: 6, amount: 5, odds: 5 }]);
  });

  test('line odds popup uses the popup point even if the global point changes', () => {
    const window = loadGame();
    window.eval(`
      balance = 1000;
      point = 4;
      isComeOutRoll = false;
      bets.passLine = 10;
    `);

    window.showPointPopup(4, 'passLine');
    window.eval('point = 6');
    window.takeOddsFromPopup('max');
    const state = readState(window);

    expect(state.balance).toBe(970);
    expect(state.passLineOdds).toBe(30);
  });

  test('roll button stays disabled while point popup is pending or open', () => {
    const window = loadGame();
    const callbacks = [];
    window.setTimeout = (fn) => {
      callbacks.push(fn);
      return callbacks.length;
    };

    window.schedulePointPopup(6, 'passLine', null, 500);
    expect(readState(window).rollDisabled).toBe(true);

    callbacks.shift()();
    expect(readState(window).rollDisabled).toBe(true);

    window.closePointPopup();
    expect(readState(window).rollDisabled).toBe(false);
  });

  test('contract Pass Line and established Come bets cannot be cleared', () => {
    const window = loadGame();
    window.eval(`
      balance = 975;
      point = 6;
      isComeOutRoll = false;
      bets.passLine = 10;
      bets.field = 5;
      comeBets = [{ id: 1, point: 8, amount: 10, odds: 0 }];
    `);

    window.clearAllBets();
    const state = readState(window);

    expect(state.balance).toBe(980);
    expect(state.passLine).toBe(10);
    expect(state.field).toBe(0);
    expect(state.comeBets).toEqual([{ id: 1, point: 8, amount: 10, odds: 0 }]);
  });

  test('place 6 bets require exact payout increments', () => {
    const window = loadGame();

    window.openBetModal('place6');
    window.document.getElementById('betInput').value = '5';
    window.confirmBet();
    expect(readState(window)).toMatchObject({
      balance: 1000,
      place6: 0,
      status: 'Minimum bet is $6',
    });

    window.document.getElementById('betInput').value = '6';
    window.confirmBet();
    expect(readState(window)).toMatchObject({
      balance: 994,
      place6: 6,
    });
  });

  test('primary table controls are native buttons', () => {
    const window = loadGame();

    expect(window.document.getElementById('passLineBtn').tagName).toBe('BUTTON');
    expect(window.document.getElementById('place6Btn').tagName).toBe('BUTTON');
    expect(window.document.getElementById('hard6TileBtn').tagName).toBe('BUTTON');
    expect(window.document.getElementById('comeBtn').disabled).toBe(true);
  });
});

describe('shared nav dependencies', () => {
  test('lucide script is pinned to an exact version', () => {
    const navSource = fs.readFileSync(path.join(__dirname, '..', '..', 'shared', 'site-nav.js'), 'utf8');

    expect(navSource).toContain('lucide@0.468.0');
    expect(navSource).not.toContain('lucide@latest');
  });
});
