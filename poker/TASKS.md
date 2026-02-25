# Poker App - Task List

## 🐛 Bugs to Fix

### High Priority
- [x] **Side pot calculation** - Fixed: Now properly calculates and awards side pots when players go all-in for different amounts
- [x] **Hand strength evaluation bug** - Fixed: `_is_straight` now correctly identifies wheel straights (A-5)
- [ ] **AI infinite loop protection** - The `max_turns` limit exists but may not catch all edge cases where AI keeps raising each other
- [ ] **Game state persistence** - Games stored in memory are lost on backend restart (consider Redis or DB)

### Medium Priority
- [ ] **Raise amount validation** - Frontend allows raises even when player doesn't have enough chips
- [ ] **Card rendering on showdown** - Winner's cards may not show correctly in results overlay
- [ ] **Polling continues after game ends** - Need to properly stop polling when player leaves/disconnects
- [ ] **CORS errors** - May occur in some browser environments

### Low Priority
- [ ] **Duplicate logging setup** - Multiple loggers created in different files
- [x] **Memory leak** - Fixed: Games older than 1 hour are now automatically cleaned up
- [ ] **Race condition in polling** - Multiple rapid actions could cause state conflicts

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
- [ ] **Hand strength indicator** - Show "Pair", "Two Pair", etc. for your hand
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
- [ ] **Add tests** - pytest for game logic and API
- [ ] **Type hints** - Complete type coverage
- [ ] **API documentation** - OpenAPI/Swagger docs
- [ ] **Rate limiting** - Prevent abuse
- [ ] **Better logging** - Structured logging with correlation IDs
- [ ] **Configuration** - Environment-based config
- [ ] **Docker** - Containerize for easier deployment

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

- [ ] **Input validation** - Validate all inputs server-side
- [ ] **Rate limiting** - Prevent spam/abuse
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
