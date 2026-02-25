# Poker API Documentation

Complete documentation for the Texas Hold'em Poker REST API.

**Base URL:** `https://palmergill.com/api/poker`

**Current Version:** 1.0.7

---

## Table of Contents

- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Game Flow](#game-flow)
- [Endpoints](#endpoints)
- [Error Handling](#error-handling)
- [WebSocket (Future)](#websocket-future)

---

## Authentication

Currently, the API uses simple player IDs for identification. No authentication tokens are required.

- Player IDs are returned when creating a game
- Player IDs must be included in requests that access game state

---

## Rate Limiting

API requests are rate-limited to prevent abuse:

- **Burst Limit:** 20 requests per minute per IP
- **Block Duration:** 60 seconds if limit exceeded
- **Health Check Exemption:** `/api/poker/health` is exempt from rate limiting

**Headers:**
- `X-RateLimit-Remaining` - Remaining requests in current window
- `X-RateLimit-Limit` - Maximum burst size (20)
- `X-Response-Time-Ms` - Response time in milliseconds

---

## Game Flow

### 1. Create a Game
```
POST /api/poker/games
```
Returns a `game_id` and your `player_id`.

### 2. Poll for State
```
GET /api/poker/games/{game_id}?player_id={player_id}
```
Poll every 1-2 seconds to get current game state.

### 3. Take Actions
```
POST /api/poker/games/{game_id}/action
```
When it's your turn, send fold/check/call/raise actions.

### 4. Next Hand
```
POST /api/poker/games/{game_id}/next-hand?player_id={player_id}
```
After showdown, start the next hand.

---

## Endpoints

### Game Management

#### Create Game
```
POST /api/poker/games
```

Create a new poker game with AI opponents.

**Request Body:**
```json
{
  "player_name": "Alice"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| player_name | string | No | Display name (1-20 chars, defaults to "Player") |

**Response (201):**
```json
{
  "game_id": "abc123",
  "player_id": "p1a2b3c4d",
  "state": { /* GameState object */ }
}
```

---

### Game State

#### Get Game State
```
GET /api/poker/games/{game_id}?player_id={player_id}
```

Retrieve the current state of a game.

**Path Parameters:**
| Field | Type | Description |
|-------|------|-------------|
| game_id | string | 8-character game identifier |

**Query Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| player_id | string | Yes | Your player identifier |

**Response (200):**
```json
{
  "game_id": "abc123",
  "phase": "preflop",
  "hand_number": 1,
  "community_cards": [],
  "pot": 150,
  "current_bet": 100,
  "min_raise": 100,
  "players": [...],
  "current_player": "p1a2b3c4d",
  "dealer_index": 0,
  "last_action": "Bob raised to 100",
  "winners": null
}
```

#### Get Game History
```
GET /api/poker/games/{game_id}/history
```

Retrieve hand history for completed hands.

**Response (200):**
```json
{
  "game_id": "abc123",
  "hands": [
    {
      "hand_number": 1,
      "timestamp": "2026-02-25T17:55:00Z",
      "players": ["Alice", "Bob", "Charlie"],
      "community_cards": ["Ah", "Kh", "Qh", "Jh", "Th"],
      "pot": 500,
      "winners": [{"name": "Alice", "amount": 500, "hand": "Royal Flush"}]
    }
  ]
}
```

#### Get Game Metrics
```
GET /api/poker/games/{game_id}/metrics
```

Retrieve detailed analytics for a game.

**Response (200):**
```json
{
  "game_id": "abc123",
  "session_start": "2026-02-25T17:00:00Z",
  "session_duration_minutes": 55.5,
  "hands_played": 12,
  "average_pot_size": 325.5,
  "hands_per_hour": 13.1,
  "total_pot_accumulated": 3906,
  "phase_distribution": {
    "showdown": 8,
    "preflop": 4
  },
  "player_behaviors": [
    {
      "player_id": "p1a2b3c4d",
      "player_name": "Alice",
      "total_actions": 45,
      "fold_percentage": 25.0,
      "call_percentage": 45.0,
      "raise_percentage": 30.0,
      "all_ins": 2,
      "checks": 8
    }
  ]
}
```

#### Get AI Stats
```
GET /api/poker/games/{game_id}/ai-stats
```

Get behavioral statistics for AI bots.

**Response (200):**
```json
{
  "game_id": "abc123",
  "bots": {
    "Bob": {
      "aggression": 0.7,
      "hands_played": 45,
      "hands_won": 12,
      "biggest_pot": 850,
      "fold_percentage": 35,
      "timing_tell": "deliberate"
    }
  }
}
```

---

### Gameplay

#### Player Action
```
POST /api/poker/games/{game_id}/action
```

Execute a player action. Automatically processes AI turns until it's the human player's turn again.

**Request Body:**
```json
{
  "player_id": "p1a2b3c4d",
  "action": "raise",
  "amount": 200
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| player_id | string | Yes | Your player identifier |
| action | string | Yes | One of: fold, check, call, raise |
| amount | integer | Conditional | Required for raise action (0-1,000,000) |

**Actions:**
- **fold** - Give up your hand
- **check** - Pass when no bet to call (only when current_bet equals your bet)
- **call** - Match the current bet
- **raise** - Increase the bet (requires amount parameter)

**Response (200):** Updated GameState object

---

#### Next Hand
```
POST /api/poker/games/{game_id}/next-hand?player_id={player_id}
```

Start a new hand after the current hand completes.

**Query Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| player_id | string | Yes | Your player identifier |

**Response (200):** Updated GameState object

---

### System

#### Health Check
```
GET /api/poker/health
```

Basic health check for monitoring.

**Response (200):**
```json
{
  "status": "ok",
  "active_games": 42,
  "config": {
    "starting_chips": 1000,
    "small_blind": 10,
    "big_blind": 20,
    "ai_difficulty": "mixed"
  }
}
```

#### Detailed Health Check
```
GET /api/poker/health/detailed
```

Detailed system metrics.

**Response (200):**
```json
{
  "status": "ok",
  "uptime_seconds": 3600,
  "active_games": 42,
  "total_players": 252,
  "memory_usage_mb": 2.1,
  "games_by_phase": {
    "preflop": 15,
    "flop": 12,
    "turn": 8,
    "river": 5,
    "showdown": 2
  },
  "avg_game_age_minutes": 23.5,
  "config": { ... },
  "version": "1.0.7"
}
```

#### Performance Metrics
```
GET /api/poker/health/performance
```

API performance statistics.

**Response (200):**
```json
{
  "endpoints": {
    "GET /api/poker/games/{game_id}": {
      "count": 1500,
      "avg_ms": 12.5,
      "min_ms": 5,
      "max_ms": 150,
      "p95_ms": 25
    }
  },
  "overall": {
    "total_requests": 5000,
    "p95_ms": 45,
    "p99_ms": 120,
    "avg_ms": 20
  },
  "slow_requests": 3
}
```

---

## Data Models

### GameState

| Field | Type | Description |
|-------|------|-------------|
| game_id | string | Unique game identifier |
| phase | string | Current phase: preflop, flop, turn, river, showdown, waiting |
| hand_number | integer | Current hand number |
| community_cards | array | Community cards on the table |
| pot | integer | Main pot amount |
| current_bet | integer | Current bet to call |
| min_raise | integer | Minimum raise amount |
| players | array | All players (cards hidden for opponents) |
| current_player | string | ID of player whose turn it is |
| dealer_index | integer | Index of dealer button |
| last_action | string | Description of last action |
| winners | array | Winners from showdown (null if not showdown) |

### Player

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique player identifier |
| name | string | Display name |
| chips | integer | Current chip stack |
| bet | integer | Current bet in the pot |
| folded | boolean | Whether player has folded |
| is_human | boolean | True if human player |
| is_dealer | boolean | True if dealer button |
| is_small_blind | boolean | True if posted small blind |
| is_big_blind | boolean | True if posted big blind |
| is_all_in | boolean | True if all-in |
| cards | array | Hole cards (only visible to requesting player) |
| avatar | string | Avatar emoji |

### Card

| Field | Type | Description |
|-------|------|-------------|
| rank | string | Card rank: 2-10, J, Q, K, A |
| suit | string | Suit: hearts, diamonds, clubs, spades |

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

| Code | Description | Common Causes |
|------|-------------|---------------|
| 200 | OK | Request successful |
| 201 | Created | Game created successfully |
| 400 | Bad Request | Invalid parameters, not your turn, action failed |
| 404 | Not Found | Game not found, player not found |
| 422 | Validation Error | Invalid request body format |
| 429 | Rate Limited | Too many requests |
| 500 | Server Error | Unexpected server error |

### Common Errors

**Not Your Turn (400):**
```json
{
  "detail": "Not your turn"
}
```

**Invalid Action (400):**
```json
{
  "detail": "Action failed"
}
```

**Game Not Found (404):**
```json
{
  "detail": "Game not found"
}
```

**Rate Limit Exceeded (429):**
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

---

## WebSocket (Future)

WebSocket support is planned for real-time updates instead of polling.

**Proposed Endpoint:**
```
ws://palmergill.com/api/poker/ws/{game_id}?player_id={player_id}
```

**Message Types:**
- `state_update` - Game state changed
- `your_turn` - It's your turn to act
- `player_action` - Another player acted
- `hand_complete` - Hand ended, show winners
- `error` - Error occurred

---

## SDK Examples

### JavaScript/Fetch

```javascript
// Create game
const createGame = async (playerName) => {
  const res = await fetch('/api/poker/games', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ player_name: playerName })
  });
  return res.json();
};

// Get game state
const getState = async (gameId, playerId) => {
  const res = await fetch(`/api/poker/games/${gameId}?player_id=${playerId}`);
  return res.json();
};

// Take action
const takeAction = async (gameId, playerId, action, amount) => {
  const body = { player_id: playerId, action };
  if (amount) body.amount = amount;
  
  const res = await fetch(`/api/poker/games/${gameId}/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  return res.json();
};

// Poll for updates
const pollGame = (gameId, playerId, onUpdate) => {
  const interval = setInterval(async () => {
    const state = await getState(gameId, playerId);
    onUpdate(state);
  }, 1000);
  return () => clearInterval(interval);
};
```

### Python/requests

```python
import requests

BASE_URL = "https://palmergill.com/api/poker"

# Create game
response = requests.post(f"{BASE_URL}/games", json={"player_name": "Alice"})
data = response.json()
game_id = data["game_id"]
player_id = data["player_id"]

# Get state
state = requests.get(f"{BASE_URL}/games/{game_id}?player_id={player_id}").json()

# Take action
action_response = requests.post(
    f"{BASE_URL}/games/{game_id}/action",
    json={"player_id": player_id, "action": "call"}
).json()
```

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/Palmergill/stock-research/issues
- Website: https://palmergill.com/poker
