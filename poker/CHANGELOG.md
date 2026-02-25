# Changelog

All notable changes to the Texas Hold'em Poker app will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Card deck themes - 5 different card styles to choose from
  - Classic: Traditional design with subtle gradient and corner suit symbols
  - Modern: Sleek rounded cards with smooth shadows
  - Minimal: Clean flat design for distraction-free play
  - Vintage: Aged paper look for retro casino feel
  - Neon: Cyberpunk glow effect optimized for dark mode
  - Toggle button with localStorage persistence
- Animated felt backgrounds - Subtle texture animations per table theme
  - Green: Diagonal shimmer pattern (20s cycle)
  - Blue: Pulsing radial gradients (15s cycle)
  - Red: Rotating conic gradient effect (25s cycle)
  - Purple: Breathing opacity pulse (6s cycle)
  - Non-distracting, smooth CSS animations
- Dark mode toggle - Switch between dark and light themes
  - Persists preference in localStorage
  - Smooth transition between modes
  - All UI elements adapt to current theme
- Chip stack visualization - Visual representation of chip amounts
  - Color-coded chips by denomination (blue, red, green, gold, black, purple)
  - Realistic chip appearance with edge stripes
  - Used in pot display, player chips, opponent chips, and bets
  - Compact view for opponents, detailed view for main player and pot
- Better card animations - cards now deal one by one with staggered animation
  - Player hole cards animate first (positions 1-2)
  - Community cards animate with offset timing
  - Cards flip and slide in with 3D rotation effect
  - Each new hand triggers fresh animations
- Portrait/landscape support - improved layout handling for landscape orientation
  - Side-by-side layout when device is in landscape mode
  - Felt area takes 70% width, controls panel takes 30%
  - Opponents stack vertically on the left in landscape
  - Optimized for phones in landscape with short height
- Player statistics tracking - persists across sessions using localStorage
  - Hands played, hands won, win rate percentage
  - Biggest pot won, net profit/loss tracking
  - Best hand achieved tracking
  - Stats modal accessible from start screen with reset option
- Decision timer - countdown display when it's your turn to act
- Changelog file to track version history

## [1.0.0] - 2025-02-20

### Added
- Initial Texas Hold'em Poker game with AI opponents
- Real-time game state with polling-based updates
- Hand strength indicator showing current hand rank
- Error boundary system for graceful error handling
- PWA support with service worker and manifest
- Comprehensive test suite (63 tests)
- API documentation with OpenAPI/Swagger
- Rate limiting (20 req/min per IP)
- Input validation for security
- HTTPS enforcement middleware
- Mobile optimization (safe areas, touch targets, viewport fixes)
- Memory cleanup for old games (1 hour expiry)
- Side pot calculation for all-in scenarios
- AI infinite loop protection

### Fixed
- Side pot calculation bugs
- Hand strength evaluation (wheel straights)
- Card rendering issues on showdown
- Polling continuing after game ends
- CORS configuration
- Duplicate logging setup
- Memory leaks
- Race conditions in polling
- Mobile viewport and touch target issues
