# Poker App Architecture

System architecture and design documentation for the Texas Hold'em Poker application.

**Version:** 1.0.7  
**Last Updated:** February 25, 2026

---

## System Overview

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
        PWA[Progressive Web App]
    end
    
    subgraph "Frontend (Vercel)"
        Static[Static Assets<br/>HTML/CSS/JS]
        SW[Service Worker]
    end
    
    subgraph "Backend (Railway)"
        FastAPI[FastAPI Server]
        GameLogic[Game Logic<br/>PokerGame, Player, Hand Eval]
        AI[AI Manager<br/>PokerAI, AIManager]
        Metrics[Metrics & Analytics]
        Security[Security Layer<br/>Rate Limiting, CORS, Validation]
    end
    
    subgraph "External Services"
        Sentry[Sentry Error Tracking]
    end
    
    Browser --> |HTTPS| Static
    PWA --> |HTTPS| Static
    Static --> |API Calls| FastAPI
    SW --> |Cache/Offline| Static
    FastAPI --> GameLogic
    FastAPI --> AI
    FastAPI --> Metrics
    FastAPI --> Security
    FastAPI --> |Error Reports| Sentry
```

---

## Architecture Decisions

### 1. Polling over WebSockets

**Decision:** Use HTTP polling instead of WebSockets for real-time updates.

**Rationale:**
- Simpler deployment (no WebSocket server management)
- Better compatibility with serverless environments
- Easier caching and CDN integration
- Lower infrastructure costs

**Trade-offs:**
- Higher latency (~500ms-2s vs instant)
- More server load from frequent requests
- Mitigated by efficient game state serialization

**Future:** WebSocket support is planned for v2.0.

---

### 2. Monolithic Game State

**Decision:** Store entire game state in memory on a single server.

**Rationale:**
- Poker games are short-lived (1-2 hours max)
- Single game fits easily in memory (~50KB)
- No need for database complexity for MVP
- Fast read/write operations

**Trade-offs:**
- Games lost on server restart
- No horizontal scaling (single server)
- Limited to ~10,000 concurrent games

**Future:** Redis persistence and multi-server support planned.

---

### 3. AI as Server-Side Logic

**Decision:** Run all AI decision-making on the server.

**Rationale:**
- Prevents cheating (can't inspect AI logic)
- Consistent behavior across clients
- Easier to update AI without client updates
- Server has full game state context

**Trade-offs:**
- Higher server CPU usage
- Must optimize AI algorithms

---

### 4. Vanilla JavaScript Frontend

**Decision:** Use vanilla HTML/CSS/JS instead of React/Vue.

**Rationale:**
- Smaller bundle size (~50KB vs ~200KB+)
- Faster initial load
- No build step complexity
- Easier to optimize for performance

**Trade-offs:**
- Manual DOM manipulation
- No component reusability
- Harder to maintain at scale

---

## Component Architecture

### Backend Components

```mermaid
graph LR
    subgraph "API Layer"
        Routes[FastAPI Routes]
        Middleware[CORS, Rate Limit, Performance]
        Validation[Pydantic Validators]
    end
    
    subgraph "Game Engine"
        PokerGame[PokerGame]
        Player[Player]
        HandEval[Hand Evaluator]
        Betting[Betting Manager]
    end
    
    subgraph "AI System"
        AIManager[AI Manager]
        PokerAI[PokerAI Bot]
        Strategy[Strategy Engine]
    end
    
    subgraph "Infrastructure"
        Config[Configuration]
        Logging[Logging]
        Metrics[Metrics]
        Monitoring[Performance Monitoring]
    end
    
    Routes --> Middleware
    Middleware --> Validation
    Validation --> PokerGame
    PokerGame --> Player
    PokerGame --> HandEval
    PokerGame --> Betting
    AIManager --> PokerAI
    PokerAI --> Strategy
    Routes --> AIManager
    Routes --> Config
    Routes --> Logging
    Routes --> Metrics
    Middleware --> Monitoring
```

### Frontend Components

```mermaid
graph TB
    subgraph "App Core"
        App[app.js]
        State[Game State Manager]
        API[API Client]
    end
    
    subgraph "UI Modules"
        Render[Render Engine]
        Animations[Animation System]
        Audio[Audio Manager]
        Gestures[Gesture Handler]
    end
    
    subgraph "Features"
        Timer[Decision Timer]
        Stats[Player Stats]
        Themes[Theme Manager]
        PWA[PWA Support]
    end
    
    App --> State
    App --> API
    App --> Render
    App --> Animations
    App --> Audio
    App --> Gestures
    App --> Timer
    App --> Stats
    App --> Themes
    App --> PWA
```

---

## Data Flow

### Game Creation Flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant GameLogic
    participant AI
    
    Client->>FastAPI: POST /games {player_name}
    FastAPI->>GameLogic: Create PokerGame
    GameLogic->>GameLogic: Generate game_id
    GameLogic->>GameLogic: Add human player
    GameLogic-->>FastAPI: Return game instance
    FastAPI->>AI: Create AIManager
    AI->>AI: Add 5 bots with varied difficulty
    AI-->>FastAPI: AI ready
    FastAPI->>GameLogic: start_hand()
    GameLogic->>GameLogic: Deal cards, post blinds
    GameLogic-->>FastAPI: Game state
    FastAPI-->>Client: {game_id, player_id, state}
```

### Player Action Flow

```mermaid
sequenceDiagram
    participant Client
    participant FastAPI
    participant GameLogic
    participant AI
    
    Client->>FastAPI: POST /action {fold/check/call/raise}
    FastAPI->>GameLogic: Validate turn
    GameLogic->>GameLogic: Execute action
    GameLogic->>GameLogic: Check phase transition
    GameLogic-->>FastAPI: Updated state
    
    loop AI Turns
        FastAPI->>GameLogic: get_current_player()
        GameLogic-->>FastAPI: AI player
        FastAPI->>AI: process_bot_turn_async()
        AI->>AI: Calculate decision
        AI->>GameLogic: Execute action
        GameLogic-->>AI: Updated state
        AI-->>FastAPI: Complete
    end
    
    FastAPI-->>Client: Final game state
```

---

## Database Schema (Future)

When database persistence is implemented:

```mermaid
erDiagram
    GAME {
        string id PK
        timestamp created_at
        timestamp updated_at
        string status
        json config
    }
    
    PLAYER {
        string id PK
        string game_id FK
        string name
        boolean is_human
        int chips
        json stats
    }
    
    HAND {
        string id PK
        string game_id FK
        int hand_number
        timestamp started_at
        timestamp ended_at
        json community_cards
        int total_pot
        json winners
    }
    
    ACTION {
        string id PK
        string hand_id FK
        string player_id FK
        string action_type
        int amount
        timestamp created_at
    }
    
    USER {
        string id PK
        string email
        string password_hash
        timestamp created_at
    }
    
    GAME ||--o{ PLAYER : has
    GAME ||--o{ HAND : contains
    HAND ||--o{ ACTION : has
    PLAYER ||--o{ ACTION : performs
    USER ||--o{ PLAYER : plays_as
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph "User"
        Browser[Browser/PWA]
    end
    
    subgraph "Vercel Edge Network"
        CDN[Vercel CDN]
        Functions[Vercel Functions<br/>API Routes]
    end
    
    subgraph "Railway"
        LB[Load Balancer]
        API1[API Instance 1]
        API2[API Instance 2]
    end
    
    subgraph "External"
        DNS[DNS/CDN]
        Sentry[Sentry.io]
    end
    
    Browser --> DNS
    DNS --> CDN
    CDN --> |Static Assets| Browser
    CDN --> |/api/poker/*| Functions
    Functions --> |Proxy| LB
    LB --> API1
    LB --> API2
    API1 --> |Errors| Sentry
    API2 --> |Errors| Sentry
```

### Infrastructure Details

| Component | Provider | Purpose |
|-----------|----------|---------|
| Frontend Hosting | Vercel | Static assets, CDN, edge functions |
| Backend Hosting | Railway | FastAPI server, auto-scaling |
| DNS | Cloudflare | DNS, DDoS protection |
| Error Tracking | Sentry | Error monitoring, performance |
| Domain | Porkbun/Cloudflare | palmergill.com |

---

## Security Architecture

```mermaid
graph TB
    subgraph "Security Layers"
        HTTPS[HTTPS/TLS 1.3]
        CORS[CORS Policy]
        RateLimit[Rate Limiting]
        Validation[Input Validation]
        Middleware[Security Middleware]
    end
    
    subgraph "Threat Mitigation"
        Injection[SQL/NoSQL Injection Prevention]
        XSS[XSS Prevention]
        CSRF[CSRF Protection]
        Enumeration[ID Enumeration Prevention]
    end
    
    HTTPS --> CORS
    CORS --> RateLimit
    RateLimit --> Middleware
    Middleware --> Validation
    Validation --> Injection
    Middleware --> XSS
    Middleware --> Enumeration
```

### Security Measures

1. **HTTPS Enforcement** - All traffic redirected to HTTPS in production
2. **CORS** - Configured to only allow palmergill.com origins
3. **Rate Limiting** - 20 req/min burst per IP
4. **Input Validation** - Pydantic validators on all inputs
5. **No Database** - In-memory only prevents injection attacks
6. **No Auth** - No session tokens to steal (stateless player IDs)

---

## Performance Optimizations

### Backend

- **Response Time:** <50ms average (p95 <150ms)
- **Game State Serialization:** Optimized dict conversion
- **AI Decisions:** <10ms per bot
- **Memory:** ~50KB per game
- **Cleanup:** Games auto-expire after 1 hour

### Frontend

- **Bundle Size:** ~50KB gzipped
- **First Paint:** <1s
- **Time to Interactive:** <2s
- **Polling:** 1s interval with backoff
- **Caching:** Service worker caches static assets

---

## Scaling Considerations

### Current Limits

- **Concurrent Games:** ~10,000 (memory constrained)
- **Requests/Second:** ~1,000 (CPU constrained)
- **Players per Game:** 6 (including human)

### Scaling Path

1. **Vertical Scaling** - Increase server RAM/CPU (current)
2. **Redis Persistence** - Store games in Redis for horizontal scaling
3. **WebSocket Server** - Separate WebSocket service for real-time
4. **CDN** - Cache static assets globally
5. **Multi-Region** - Deploy to multiple regions for lower latency

---

## Monitoring & Observability

```mermaid
graph LR
    subgraph "Metrics Collection"
        Perf[Performance Middleware]
        Logs[Structured Logging]
        GameMetrics[Game Metrics]
    end
    
    subgraph "Storage"
        Memory[In-Memory Stats]
        Sentry[Sentry.io]
    end
    
    subgraph "Access"
        Health[Health Endpoints]
        Dashboard[Metrics API]
    end
    
    Perf --> Memory
    Logs --> Sentry
    GameMetrics --> Memory
    Memory --> Health
    Memory --> Dashboard
```

### Endpoints

- `/api/poker/health` - Basic health check
- `/api/poker/health/detailed` - System metrics
- `/api/poker/health/performance` - API performance stats
- `/api/poker/games/{id}/metrics` - Per-game analytics
- `/api/poker/games/{id}/ai-stats` - AI behavior stats

---

## Future Architecture (v2.0)

```mermaid
graph TB
    subgraph "v2.0 Goals"
        WS[WebSocket Server]
        Redis[(Redis Cache)]
        DB[(PostgreSQL)]
        Auth[Authentication Service]
        Tournament[Tournament Engine]
    end
    
    subgraph "Current"
        API[FastAPI]
        Memory[In-Memory Games]
    end
    
    API -.-> WS
    Memory -.-> Redis
    Memory -.-> DB
    API -.-> Auth
    API -.-> Tournament
```

### Planned Features

1. **WebSocket Support** - Real-time updates
2. **Redis Persistence** - Game state survives restarts
3. **PostgreSQL** - Long-term storage for history/stats
4. **Authentication** - User accounts with JWT
5. **Tournament Mode** - Multi-table tournaments
6. **Spectator Mode** - Watch games without playing

---

## Development Workflow

```mermaid
graph LR
    subgraph "Development"
        Local[Local Development]
        Docker[Docker Compose]
    end
    
    subgraph "CI/CD"
        GitHub[GitHub Actions]
        Test[Run Tests]
        Deploy[Deploy to Railway/Vercel]
    end
    
    subgraph "Production"
        Prod[Production]
        Monitor[Monitoring]
    end
    
    Local --> GitHub
    Docker --> GitHub
    GitHub --> Test
    Test --> Deploy
    Deploy --> Prod
    Prod --> Monitor
```

### Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vanilla HTML/CSS/JS |
| Backend | Python 3.11 + FastAPI |
| Testing | pytest |
| Deployment | Docker + Railway + Vercel |
| Monitoring | Sentry + Custom metrics |

---

## API Documentation

See [API.md](API.md) for detailed endpoint documentation.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.
