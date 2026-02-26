# Poker App - Task List

## 🐛 Bugs to Fix

### High Priority
- [x] **Side pot calculation** - Fixed: Now properly calculates and awards side pots when players go all-in for different amounts
- [x] **Hand strength evaluation bug** - Fixed: `_is_straight` now correctly identifies wheel straights (A-5)
- [x] **AI infinite loop protection** - Fixed: Added `MAX_AI_TURNS` config with proper enforcement in action and next-hand endpoints (enforced in `/api/poker/games/{game_id}/action` with error logging if limit reached)
- [x] **Game state persistence** - Fixed: Added file-based persistence system (`persistence.py`) that saves games every 5 minutes and on shutdown. Games are automatically restored on startup if less than 24 hours old. Configurable via environment variables.

### Medium Priority
- [x] **Raise amount validation** - Fixed: Raise button now hidden when player can't afford minimum raise
- [x] **Card rendering on showdown** - Fixed: Added robust null/undefined checks in `renderCard()` function to prevent display issues with malformed card data
- [x] **Polling continues after game ends** - Fixed: Proper cleanup on page unload, tab visibility change, and 404 errors
- [x] **CORS configuration** - Fixed: CORS properly configured in main.py with `Config.CORS_ORIGINS` environment variable support, allowing credentials and all methods/headers

### Low Priority
- [x] **Duplicate logging setup** - Fixed: Created centralized logging in `config.py` with `setup_logging()` and `get_logger()` functions
- [x] **Memory leak** - Fixed: Games older than 1 hour are now automatically cleaned up
- [x] **Race condition in polling** - Fixed: Added `isRequestPending` lock in app.js to prevent multiple simultaneous requests in `playerAction()` and `nextHand()` functions

## ✨ Features to Add

### Game Features
- [ ] **Tournament mode** - Sit & go tournaments with increasing blinds
- [x] **Hand history** - Fixed: Each hand is now logged with timestamp, players, hole cards, community cards, pot size, winners, and action sequence. History accessible via `/api/poker/games/{game_id}/history` endpoint
- [x] **Player statistics** - Fixed: Added StatsManager that tracks hands played, hands won, win rate, biggest pot won, net profit/loss, and best hand achieved. Data persists across sessions using localStorage. Stats view accessible via button on start screen with option to reset.
- [x] **Chat feature** - Fixed: Added simple chat system between players with chat panel UI, message persistence in game state, and real-time updates via polling. Players can send messages up to 200 characters, chat history is limited to 100 messages per game, and the UI shows new message indicators when chat is closed.
- [x] **Sound effects** - Fixed: Added Web Audio API sound manager with card deal, chip, win, and loss sounds. Sounds are generated programmatically (no external files needed) and respect browser autoplay policies.
- [x] **Vibration on turn** - Fixed: Added haptic feedback via `navigator.vibrate([50, 100, 50])` when it's the player's turn, with mobile device detection and graceful fallback
- [x] **All-in showdown** - Fixed: When all active players are all-in, the board runs out immediately (deals all remaining community cards at once) and goes straight to showdown. Implemented `_all_active_players_all_in()` and `_run_out_board()` methods in game.py.

### UI Improvements
- [x] **Better card animations** - Fixed: Cards now deal one by one with staggered animation. Player hole cards animate first (positions 1-2), then community cards with offset timing. Cards flip and slide in with 3D rotation effect. Each new hand triggers fresh animations.
- [x] **Chip stack visualization** - Fixed: Added visual chip stacks with color-coded denominations (blue=1, red=5, green=25, gold=100, black=500, purple=1000), realistic chip appearance with edge stripes and gradients, used in pot display, player chips, opponent chips, and bets
- [x] **Hand strength indicator** - Added: Shows "Pair of Aces", "Flush", "Straight", etc. in gold badge below cards
- [x] **Pot odds calculator** - Fixed: Added real-time pot odds display in the header showing ratio (e.g., "3.5:1") and required equity percentage. Shows only when there's a bet to call, hidden otherwise.
- [x] **Timer for decisions** - Added: 30-second countdown timer with visual progress bar, auto-folds when time expires
- [x] **Bet slider improvements** - Fixed: Added min/max labels below the slider that update dynamically based on current game state. Shows "Min: X" (minimum raise amount) and "Max: X" (player's chip stack) to help users make informed betting decisions.
- [x] **Table themes** - Fixed: Added 5 table theme options (Green, Blue, Red, Black, Purple) with CSS custom properties. Theme toggle button in top-right corner with localStorage persistence.
- [x] **Portrait/landscape support** - Fixed: Added improved layout handling for landscape orientation. Side-by-side layout when device is in landscape mode with felt area taking 70% width and controls panel taking 30%. Opponents stack vertically on the left. Optimized for phones in landscape with short height (< 500px).

### Backend Improvements
- [x] **Health checks** - Fixed: Added `/api/poker/health/detailed` endpoint with uptime, memory usage estimates, games by phase, average game age, and total player counts. Also added `/api/poker/games/{game_id}/ai-stats` endpoint to view AI bot statistics and behavioral patterns.
- [ ] **WebSocket support** - Real-time updates instead of polling
- [ ] **Database persistence** - Store game history, player stats
- [ ] **Authentication** - Optional user accounts
- [ ] **Multi-table support** - Play at multiple tables
- [ ] **Spectator mode** - Watch games without playing
- [x] **AI difficulty levels** - Fixed: Added AIDifficulty preset system with easy/medium/hard/expert levels. Each level controls aggression, bluff frequency, hand strength thresholds, raise sizing, and call thresholds. Set via `AI_DIFFICULTY` env var or defaults to mixed (varied opponents)

## 🔧 Code Improvements

### Frontend (JavaScript)
- [ ] **Add TypeScript** - Type safety for game state
- [ ] **State management** - Use Redux/Zustand instead of global variables
- [ ] **Component structure** - Break into React/Vue components
- [x] **Error boundaries** - Fixed: Added comprehensive error boundary system with `ErrorBoundary` object in app.js featuring global error handlers, user-friendly toast notifications, and async function wrapping
- [x] **Unit tests** - Fixed: Set up Jest testing framework with jsdom environment. Created test utilities module (poker/tests/gameUtils.js) with testable functions extracted from app.js including pot odds calculation, chip formatting, card value mapping, hand strength formatting, raise validation, action permissions, and avatar generation. Added comprehensive test suite (poker/tests/gameUtils.test.js) with 32 tests covering all utility functions.
- [x] **PWA support** - Fixed: Added manifest.json with app metadata and icons, created sw.js service worker with cache-first strategy for static assets, updated index.html with manifest link and service worker registration
- [x] **Service worker** - Fixed: Service worker already implemented with cache-first strategy for static assets, proper cache versioning, offline API error handling, and message handling for skipWaiting

### Backend (Python)
- [x] **Add tests** - Fixed: Added pytest test suite with 63 tests covering game logic (hand evaluation, player actions, betting), API endpoints (health, create game, actions, rate limiting), and AI behavior (decision making, aggression levels)
- [x] **Type hints** - Fixed: Completed type coverage in ai.py - added proper types for `make_decision()`, `_preflop_strength()`, `AIManager.bots`, and `process_bot_turn()` return types
- [x] **API documentation** - Fixed: Added comprehensive OpenAPI/Swagger documentation with detailed request/response models (GameState, CreateGameRequest/Response, ActionRequest/Response, etc.), endpoint summaries, descriptions, response codes, and automatic redirect from root to /docs
- [x] **Rate limiting** - Fixed: Already implemented in-memory rate limiter (20 req/min burst per IP)
- [x] **Better logging** - Fixed: Already implemented structured logging with correlation IDs in `config.py`
- [x] **Configuration** - Fixed: Added `Config` class in `config.py` with environment variable support for HOST, PORT, CORS_ORIGINS, STARTING_CHIPS, SMALL_BLIND, BIG_BLIND, and AI delays
- [x] **Docker** - Fixed: Added Dockerfile and docker-compose.yml for containerized deployment

### AI Improvements
- [x] **More sophisticated AI** - Fixed: Added stack size consideration (calculates stack in BB and adjusts thresholds 0.7x-1.3x based on depth) and positional awareness (early/late position multipliers 0.85x-1.25x). AI now plays tighter with short stacks and looser in late position.
- [x] **AI tells** - Fixed: Added human-like behavioral patterns including timing tells (fast/normal/deliberate/tanker patterns), betting styles (precise/rounded/psychological), decision delay calculation based on hand strength, and bet sizing patterns. Each bot gets unique tell patterns on initialization. Added `get_decision_delay()`, `get_bet_size()`, and `get_stats()` methods to PokerAI class.
- [x] **Adaptive AI** - Fixed: AI now tracks player tendencies (VPIP, PFR, aggression factor) and dynamically adjusts its strategy. Added player type classification (TAG, LAG, Rock, Calling Station, Nit) with specific counter-strategies. New endpoints: `/api/poker/analytics/player/{player_id}` and `/api/poker/analytics/players`
- [x] **AI difficulty** - Fixed: Added configurable difficulty levels (easy/medium/hard/expert) with varying aggression, bluff frequency, and hand strength thresholds
- [ ] **GTO approximation** - Game theory optimal play option

## 🎨 Design Tasks

- [x] **Dark mode toggle** - Fixed: Added light/dark mode toggle with CSS custom properties, persists preference in localStorage, smooth transitions between modes, all UI elements adapt including felt colors
- [x] **Card deck themes** - Fixed: Added 5 card deck theme options (Classic, Modern, Minimal, Vintage, Neon). Each theme changes card appearance with unique styling - gradients, borders, shadows, and color schemes. Classic has subtle gradient with corner suit symbols; Modern has sleek rounded design; Minimal is flat and clean; Vintage has aged paper look; Neon has cyberpunk glow effect for dark mode. Toggle button in top-right with localStorage persistence.
- [x] **Avatar system** - Fixed: Added visual avatar system with emoji-based AI opponent avatars (10 avatar sets across different themes) and initials-based player avatars. Avatars are deterministically generated based on player names, have colorful backgrounds, and are displayed for both opponents (small size) and player (medium size with gold border).
- [x] **Animated backgrounds** - Fixed: Added subtle animated felt texture effects using CSS animations. Green theme has diagonal shimmer pattern; Blue theme has pulsing radial gradients; Red theme has rotating conic gradient; Purple theme has breathing opacity pulse. All animations are smooth (6-25s cycles) and non-distracting. Implemented with ::before and ::after pseudo-elements for performance.
- [x] **Mobile gestures** - Fixed: Implemented touch gesture system with swipe left to fold, double-tap to call/check, and swipe right for check (when available). Includes visual feedback overlays, gesture hints on mobile devices, and supports both touch and mouse events for testing on desktop.
- [x] **Loading states** - Fixed: Added full-screen loading overlay with animated spinner and descriptive text ("Starting game...", "Dealing next hand..."). Shows during game initialization and between hands for better user feedback.
- [x] **Empty states** - Fixed: Improved opponent folded state visualization with "FOLDED" text badge in red, dimmed chips color, grayed-out card backs, and reduced opacity for clearer game state indication.

## 📱 Mobile Optimization

- [x] **Viewport fixes** - Fixed: Added `viewport-fit=cover` to viewport meta tag and `min-height: 100dvh` for dynamic viewport support
- [x] **Touch targets** - Fixed: All action buttons have minimum 44px touch targets (primary buttons: 18px 32px padding, action buttons: 16px 12px padding)
- [x] **Font scaling** - Fixed: Added `text-size-adjust: 100%` and `html { font-size: 100% }` to respect user font size preferences
- [x] **Orientation lock** - Fixed: Added `screen.orientation.lock('portrait')` call when entering game screen, with graceful fallback for unsupported devices
- [x] **Safe area** - Fixed: Added CSS `@supports (padding-top: env(safe-area-inset-top))` rules to handle iPhone notch and safe areas
- [x] **Keyboard handling** - Fixed: Added CSS to prevent layout shift when virtual keyboard opens on mobile. Body uses fixed positioning with 100dvh, and media query adjusts layout for small viewports (<500px height) to ensure game remains playable.

## 🔒 Security

- [x] **Input validation** - Fixed: Added comprehensive server-side validation using Pydantic validators for player names (1-20 chars, sanitized), player IDs (alphanumeric), action types (fold/check/call/raise only), raise amounts (0-1M bounds), and game IDs (format validation with regex)
- [x] **Rate limiting** - Fixed: Implemented in-memory rate limiter with 20 req/min burst per IP, 1-minute block on violation, with proper headers (X-RateLimit-Remaining, X-RateLimit-Limit) and health check exemption
- [x] **CSRF protection** - Fixed: Added CSRF protection middleware using double-submit cookie pattern. CSRF tokens are generated per-session and validated on state-changing requests (POST/PUT/PATCH/DELETE). Frontend includes CSRFManager utility that automatically adds X-CSRF-Token header to requests. Exempt paths include health checks and documentation endpoints.
- [x] **Game integrity** - Fixed: Added comprehensive game integrity system with action tokens (prevents replay attacks), player session validation, per-player rate limiting (30 actions/min), state fingerprinting for tamper detection, and suspicious activity monitoring. New `/api/poker/health/integrity/{game_id}` endpoint for security monitoring.
- [x] **HTTPS enforcement** - Fixed: Added HTTPS enforcement middleware that redirects HTTP to HTTPS in production (non-DEBUG mode), with health check exemption to avoid breaking monitoring

## 📊 Analytics

- [x] **Game metrics** - Fixed: Added comprehensive metrics tracking including hands per hour (calculated from recent hand timing), average pot size, total pot accumulated, and phase distribution. New `/api/poker/games/{game_id}/metrics` endpoint returns session duration, hands played, and performance stats.
- [x] **Player behavior** - Fixed: Added PlayerBehavior class that tracks fold/call/raise percentages, all-in frequency, and total actions per player. Integrated with game action logging to automatically record every player decision.
- [x] **Error tracking** - Fixed: Added Sentry integration with automatic error reporting, environment-based configuration, FastAPI/Starlette integration, and performance profiling. Configurable via SENTRY_DSN, SENTRY_ENVIRONMENT, and SENTRY_TRACES_SAMPLE_RATE environment variables.
- [x] **Performance monitoring** - Fixed: Added performance monitoring middleware that tracks API response times, per-endpoint statistics (count, avg/min/max/p95), overall metrics (p95, p99, average, median), slow request detection (500ms threshold), and X-Response-Time-Ms headers. New `/api/poker/health/performance` endpoint returns aggregated stats. Configurable via ENABLE_PERFORMANCE_MONITORING and SLOW_REQUEST_THRESHOLD_MS env vars.
- [x] **Usage analytics** - Fixed: Added comprehensive usage analytics tracking including active sessions, unique players, session duration, request rates, hourly activity, and daily statistics. Tracks games created, hands played, and player actions. New endpoint: `/api/poker/analytics/usage`

## 🚀 Deployment

- [x] **CI/CD pipeline** - Fixed: Created GitHub Actions workflow (.github/workflows/ci-cd.yml) with jobs for backend testing (pytest), frontend testing (Jest), and automatic Vercel deployment on main branch merges
- [ ] **Staging environment** - Separate staging for testing
- [x] **Health checks** - Fixed: Added Kubernetes-style readiness probe (`/api/poker/health/ready`) and liveness probe (`/api/poker/health/live`) endpoints. Also added persistence status endpoint and manual save trigger.
- [ ] **Auto-scaling** - Handle traffic spikes
- [ ] **Backup strategy** - Backup game data if persisted
- [x] **CDN** - Fixed: Added cache-control headers in vercel.json for optimal CDN performance. Static assets (images, fonts, etc.) cached for 1 year with immutable flag. JavaScript and CSS files cached for 1 hour with must-revalidate. HTML files set to no-cache to ensure fresh content. Vercel CDN automatically serves cached content from edge locations.

## 📝 Documentation

- [x] **API documentation** - Fixed: Created comprehensive API.md with all endpoints documented, including request/response schemas, error handling, rate limiting details, and code examples in JavaScript and Python
- [x] **Architecture diagram** - Fixed: Created ARCHITECTURE.md with system design documentation including Mermaid diagrams for system overview, component architecture, data flow, deployment architecture, and security layers
- [x] **Contributing guide** - Fixed: Added CONTRIBUTING.md with setup instructions, development workflow, code style guidelines, branch naming conventions, and contribution process
- [x] **Changelog** - Added: CHANGELOG.md following Keep a Changelog format
- [x] **User guide** - Fixed: Added comprehensive USER_GUIDE.md with quick start instructions, Texas Hold'em rules, hand rankings, interface guide, feature explanations, customization options, strategy tips, troubleshooting, and keyboard shortcuts

## Priority Order

### Week 1 (Critical)
1. Fix side pot calculation
2. Add proper game cleanup
3. Fix mobile viewport issues
4. Add error boundaries

### Week 2 (High Value)
1. Add hand history
2. Better card animations
3. Add sound effects
4. Improve AI tells

### Week 3 (Polish)
1. Dark mode
2. Better mobile gestures
3. Player statistics
4. Tournament mode MVP

### Week 4 (Advanced)
1. WebSocket migration
2. Database persistence
3. Authentication
4. Multi-table support
