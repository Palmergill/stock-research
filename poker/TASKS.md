# Poker App - Task List

## 🐛 Bugs to Fix

### High Priority
- [x] **Side pot calculation** - Fixed: Now properly calculates and awards side pots when players go all-in for different amounts
- [x] **Hand strength evaluation bug** - Fixed: `_is_straight` now correctly identifies wheel straights (A-5)
- [ ] **AI infinite loop protection** - Improved: Added `MAX_AI_TURNS` config with proper enforcement in action and next-hand endpoints
- [ ] **Game state persistence** - Games stored in memory are lost on backend restart (consider Redis or DB)

### Medium Priority
- [x] **Raise amount validation** - Fixed: Raise button now hidden when player can't afford minimum raise
- [x] **Card rendering on showdown** - Fixed: Added robust null/undefined checks in `renderCard()` function to prevent display issues with malformed card data
- [x] **Polling continues after game ends** - Fixed: Proper cleanup on page unload, tab visibility change, and 404 errors
- [ ] **CORS errors** - May occur in some browser environments

### Low Priority
- [x] **Duplicate logging setup** - Fixed: Created centralized logging in `config.py` with `setup_logging()` and `get_logger()` functions
- [x] **Memory leak** - Fixed: Games older than 1 hour are now automatically cleaned up
- [x] **Race condition in polling** - Fixed: Added `isRequestPending` lock in app.js to prevent multiple simultaneous requests in `playerAction()` and `nextHand()` functions

## ✨ Features to Add

### Game Features
- [ ] **Tournament mode** - Sit & go tournaments with increasing blinds
- [ ] **Hand history** - Log all hands played with replay capability
- [ ] **Player statistics** - Track win rate, biggest pot, hands played
- [ ] **Chat feature** - Simple chat between players
- [ ] **Sound effects** - Card deals, chips, win sounds
- [ ] **Vibration on turn** - Mobile haptic feedback when it's your turn
- [ ] **All-in showdown** - Show all cards immediately when all-in

### UI Improvements
- [ ] **Better card animations** - Deal cards one by one with animation
- [ ] **Chip stack visualization** - Show actual chip stacks, not just numbers
- [x] **Hand strength indicator** - Added: Shows "Pair of Aces", "Flush", "Straight", etc. in gold badge below cards
- [ ] **Pot odds calculator** - Show pot odds in real-time
- [ ] **Timer for decisions** - Countdown timer for player actions
- [ ] **Bet slider improvements** - Show min/max/pot on slider
- [ ] **Table themes** - Different felt colors/designs
- [ ] **Portrait/landscape support** - Better layout handling

### Backend Improvements
- [ ] **WebSocket support** - Real-time updates instead of polling
- [ ] **Database persistence** - Store game history, player stats
- [ ] **Authentication** - Optional user accounts
- [ ] **Multi-table support** - Play at multiple tables
- [ ] **Spectator mode** - Watch games without playing
- [ ] **AI difficulty levels** - Easy, medium, hard, expert

## 🔧 Code Improvements

### Frontend (JavaScript)
- [ ] **Add TypeScript** - Type safety for game state
- [ ] **State management** - Use Redux/Zustand instead of global variables
- [ ] **Component structure** - Break into React/Vue components
- [ ] **Error boundaries** - Better error handling
- [ ] **Unit tests** - Jest/Vitest for game logic
- [ ] **PWA support** - Offline capability, app install
- [ ] **Service worker** - Cache assets for faster loads

### Backend (Python)
- [x] **Add tests** - Fixed: Added pytest test suite with 63 tests covering game logic (hand evaluation, player actions, betting), API endpoints (health, create game, actions, rate limiting), and AI behavior (decision making, aggression levels)
- [ ] **Type hints** - Complete type coverage
- [ ] **API documentation** - OpenAPI/Swagger docs
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

- [ ] **Dark mode toggle** - Alternative color scheme
- [ ] **Card deck themes** - Different card designs
- [ ] **Avatar system** - Player profile pictures
- [ ] **Animated backgrounds** - Subtle felt texture animation
- [ ] **Mobile gestures** - Swipe to fold, tap to call
- [ ] **Loading states** - Better loading indicators
- [ ] **Empty states** - Better empty/opponent-folded states

## 📱 Mobile Optimization

- [ ] **Viewport fixes** - Handle mobile browser chrome properly
- [ ] **Touch targets** - Ensure buttons are large enough (44px min)
- [ ] **Font scaling** - Respect user font size preferences
- [ ] **Orientation lock** - Lock to portrait on mobile
- [ ] **Safe area** - Handle iPhone notch/safe areas
- [ ] **Keyboard handling** - Prevent layout shift when keyboard opens

## 🔒 Security

- [x] **Input validation** - Fixed: Added comprehensive server-side validation using Pydantic validators for player names (1-20 chars, sanitized), player IDs (alphanumeric), action types (fold/check/call/raise only), raise amounts (0-1M bounds), and game IDs (format validation with regex)
- [x] **Rate limiting** - Fixed: Implemented in-memory rate limiter with 20 req/min burst per IP, 1-minute block on violation, with proper headers (X-RateLimit-Remaining, X-RateLimit-Limit) and health check exemption
- [ ] **CSRF protection** - If adding auth
- [ ] **Game integrity** - Prevent cheating/exploits
- [ ] **HTTPS enforcement** - Ensure all traffic is encrypted

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
- [ ] **Changelog** - Track version changes
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
