# Changelog

All notable changes to the Texas Hold'em Poker app will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
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
