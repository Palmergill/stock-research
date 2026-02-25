"""
Tests for FastAPI endpoints
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app, games, ai_managers


@pytest.fixture
def client():
    """Create a test client"""
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture(autouse=True)
def clear_games():
    """Clear games dict before each test"""
    games.clear()
    ai_managers.clear()
    yield
    games.clear()
    ai_managers.clear()


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/api/poker/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "active_games" in data
        assert "config" in data


class TestCreateGame:
    """Test game creation endpoint"""
    
    @pytest.mark.asyncio
    async def test_create_game_default_name(self, client):
        response = await client.post("/api/poker/games", json={})
        assert response.status_code == 200
        data = response.json()
        assert "game_id" in data
        assert "player_id" in data
        assert "state" in data
        assert len(data["game_id"]) == 8
    
    @pytest.mark.asyncio
    async def test_create_game_custom_name(self, client):
        response = await client.post("/api/poker/games", json={"player_name": "Palmer"})
        assert response.status_code == 200
        data = response.json()
        state = data["state"]
        player_names = [p["name"] for p in state["players"]]
        assert "Palmer" in player_names
    
    @pytest.mark.asyncio
    async def test_create_game_sanitizes_name(self, client):
        response = await client.post("/api/poker/games", json={"player_name": "  Test <script>  "})
        assert response.status_code == 200
        # Name should be sanitized


class TestGameState:
    """Test getting game state"""
    
    @pytest.mark.asyncio
    async def test_get_game_state_404(self, client):
        response = await client.get("/api/poker/games/nonexistent?player_id=test123")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_game_state_success(self, client):
        # First create a game
        create_resp = await client.post("/api/poker/games", json={})
        data = create_resp.json()
        game_id = data["game_id"]
        player_id = data["player_id"]
        
        # Get state
        state_resp = await client.get(f"/api/poker/games/{game_id}?player_id={player_id}")
        assert state_resp.status_code == 200
        state = state_resp.json()
        assert state["game_id"] == game_id
    
    @pytest.mark.asyncio
    async def test_get_game_invalid_game_id(self, client):
        response = await client.get("/api/poker/games/invalid<>id?player_id=test123")
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_get_game_invalid_player_id(self, client):
        response = await client.get("/api/poker/games/test123?player_id=invalid<>id")
        assert response.status_code == 400


class TestPlayerAction:
    """Test player action endpoint"""
    
    @pytest.mark.asyncio
    async def test_action_game_not_found(self, client):
        response = await client.post("/api/poker/games/nonexistent/action", json={
            "player_id": "test123",
            "action": "fold"
        })
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_action_invalid_action(self, client):
        # Create game first
        create_resp = await client.post("/api/poker/games", json={})
        game_id = create_resp.json()["game_id"]
        
        response = await client.post(f"/api/poker/games/{game_id}/action", json={
            "player_id": "test123",
            "action": "invalid_action"
        })
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_action_invalid_player_id_chars(self, client):
        create_resp = await client.post("/api/poker/games", json={})
        game_id = create_resp.json()["game_id"]
        
        response = await client.post(f"/api/poker/games/{game_id}/action", json={
            "player_id": "test<script>",
            "action": "fold"
        })
        assert response.status_code == 422  # Validation error


class TestNextHand:
    """Test next hand endpoint"""
    
    @pytest.mark.asyncio
    async def test_next_hand_game_not_found(self, client):
        response = await client.post("/api/poker/games/nonexistent/next-hand?player_id=test123")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_next_hand_hand_in_progress(self, client):
        # Create game
        create_resp = await client.post("/api/poker/games", json={})
        data = create_resp.json()
        game_id = data["game_id"]
        player_id = data["player_id"]
        
        # Try to start next hand while in progress
        response = await client.post(f"/api/poker/games/{game_id}/next-hand?player_id={player_id}")
        assert response.status_code == 400
        assert "Hand still in progress" in response.json()["detail"]


class TestRateLimiting:
    """Test rate limiting headers"""
    
    @pytest.mark.asyncio
    async def test_rate_limit_headers_present(self, client):
        response = await client.get("/api/poker/games/test123?player_id=test456")
        # Even on 404, rate limit headers should be present
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Limit" in response.headers
    
    @pytest.mark.asyncio
    async def test_health_exempt_from_rate_limit(self, client):
        # Health check should not have rate limit headers
        response = await client.get("/api/poker/health")
        assert response.status_code == 200
        # Rate limiting is skipped for health checks


class TestCorrelationId:
    """Test correlation ID middleware"""
    
    @pytest.mark.asyncio
    async def test_correlation_id_generated(self, client):
        response = await client.get("/api/poker/health")
        assert "X-Correlation-ID" in response.headers
        assert len(response.headers["X-Correlation-ID"]) > 0
    
    @pytest.mark.asyncio
    async def test_correlation_id_preserved(self, client):
        custom_id = "test-12345"
        response = await client.get(
            "/api/poker/health",
            headers={"X-Correlation-ID": custom_id}
        )
        assert response.headers["X-Correlation-ID"] == custom_id
