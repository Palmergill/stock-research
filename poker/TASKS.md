# Poker App - Task List

## 🐛 Bugs to Fix

### High Priority
- [x] **Side pot calculation** - Fixed: Now properly calculates and awards side pots when players go all-in for different amounts
- [x] **Hand strength evaluation bug** - Fixed: `_is_straight` now correctly identifies wheel straights (A-5)
- [x] **AI infinite loop protection** - Fixed: Added `MAX_AI_TURNS` config with proper enforcement in action and next-hand endpoints (enforced in `/api/poker/games/{game_id}/action` with error logging if limit reached)
- [ ] **Game state persistence** - Games stored in memory are lost on backend restart (consider Redis or DB)

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
- [ ] **Chat feature** - Simple chat between players
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
- [ ] **Unit tests** - Jest/Vitest for game logic
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
- [ ] **More sophisticated AI** - Positional awareness, stack size consideration
- [ ] **AI tells** - Make AI more human-like (timing tells, bet sizing patterns)
- [ ] **Adaptive AI** - AI adjusts to player tendencies
- [ ] **AI difficulty** - Configurable skill levels
- [ ] **GTO approximation** - Game theory optimal play option

## 🎨 Design Tasks

- [x] **Dark mode toggle** - Fixed: Added light/dark mode toggle with CSS custom properties, persists preference in localStorage, smooth transitions between modes, all UI elements adapt including felt colors
- [ ] **Card deck themes** - Different card designs
- [ ] **Avatar system** - Player profile pictures
- [ ] **Animated backgrounds** - Subtle felt texture animation
- [ ] **Mobile gestures** - Swipe to fold, tap to call
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
- [ ] **CSRF protection** - If adding auth
- [ ] **Game integrity** - Prevent cheating/exploits
- [x] **HTTPS enforcement** - Fixed: Added HTTPS enforcement middleware that redirects HTTP to HTTPS in production (non-DEBUG mode), with health check exemption to avoid breaking monitoring

## 📊 Analytics

- [ ] **Game metrics** - Track hands per hour, average pot size
- [ ] **Player behavior** - Track fold/call/raise percentages
- [ ] **Error tracking** - Sentry integration
- [ ] **Performance monitoring** - Track API response times
- [ ] **Usage analytics** - Track active users, session length

## 🚀 Deployment

- [ ] **CI/CD pipeline** - GitHub Actions for testing and deployment
- [ ] **Staging environment** - Separate staging for testing
- [ ] **Health checks** - Better health/monitoring endpoints
- [ ] **Auto-scaling** - Handle traffic spikes
- [ ] **Backup strategy** - Backup game data if persisted
- [ ] **CDN** - Serve static assets from CDN

## 📝 Documentation

- [ ] **API documentation** - Document all endpoints
- [ ] **Architecture diagram** - Show system design
- [ ] **Contributing guide** - For open source
- [x] **Changelog** - Added: CHANGELOG.md following Keep a Changelog format
- [ ] **User guide** - How to play, rules reference

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
