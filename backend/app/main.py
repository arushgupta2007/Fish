from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import logging
import uvicorn
from typing import Dict, List

from app.api.routes import router as api_router
from app.api.websocket import WebSocketManager
from app.services.game_service import GameService
from app.utils.game_state_manager import GameStateManager
from app.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
game_service = GameService()
game_state_manager = GameStateManager()
websocket_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    logger.info("Starting Half Suit Game Server...")
    
    # Startup
    try:
        # Initialize services
        await game_service.initialize()
        await game_state_manager.initialize()
        logger.info("Game services initialized successfully")
        
        # You could add database connections, Redis connections, etc. here
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Half Suit Game Server...")
    try:
        await game_service.cleanup()
        await game_state_manager.cleanup()
        await websocket_manager.cleanup()
        logger.info("Cleanup completed successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Half Suit Card Game",
    description="A strategic team-based card game for six players",
    version="1.0.0",
    lifespan=lifespan
)

# Get settings
settings = get_settings()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Make services available to routes
app.state.game_service = game_service
app.state.game_state_manager = game_state_manager
app.state.websocket_manager = websocket_manager

@app.get("/")
async def root():
    """
    Root endpoint - basic health check and info.
    """
    return {
        "message": "Half Suit Card Game Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "api": "/api/v1",
            "websocket": "/ws/{game_id}/{player_id}",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    """
    try:
        # Check if services are healthy
        game_service_healthy = await game_service.health_check()
        websocket_healthy = websocket_manager.is_healthy()
        
        status = "healthy" if game_service_healthy and websocket_healthy else "unhealthy"
        
        return {
            "status": status,
            "services": {
                "game_service": "healthy" if game_service_healthy else "unhealthy",
                "websocket_manager": "healthy" if websocket_healthy else "unhealthy"
            },
            "active_games": len(game_service.get_active_games()),
            "connected_players": websocket_manager.get_connection_count()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.websocket("/ws/{game_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, player_id: str):
    """
    WebSocket endpoint for real-time game communication.
    
    Args:
        websocket: WebSocket connection
        game_id: The game ID to connect to
        player_id: The player ID connecting
    """
    try:
        # Validate game and player exist
        if not game_service.game_exists(game_id):
            await websocket.close(code=4004, reason="Game not found")
            return
        
        if not game_service.player_exists(game_id, player_id):
            await websocket.close(code=4004, reason="Player not found")
            return
        
        # Accept the connection
        await websocket_manager.connect(websocket, game_id, player_id)
        
        logger.info(f"Player {player_id} connected to game {game_id}")
        
        # Send initial game state
        game_state = await game_service.get_game_state(game_id, player_id)
        await websocket_manager.send_to_player(game_id, player_id, {
            "type": "state_update",
            "data": game_state.dict()
        })
        
        # Notify other players
        await websocket_manager.broadcast_to_game(game_id, {
            "type": "player_connected",
            "data": {
                "player_id": player_id,
                "message": f"Player {player_id} connected"
            }
        }, exclude_player=player_id)
        
        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                await handle_websocket_message(websocket, game_id, player_id, data)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                await websocket_manager.send_to_player(game_id, player_id, {
                    "type": "error",
                    "data": {"message": f"Error processing message: {str(e)}"}
                })
                
    except WebSocketDisconnect:
        logger.info(f"Player {player_id} disconnected from game {game_id}")
    except Exception as e:
        logger.error(f"WebSocket error for player {player_id} in game {game_id}: {e}")
    finally:
        # Clean up connection
        await websocket_manager.disconnect(game_id, player_id)
        
        # Notify other players
        await websocket_manager.broadcast_to_game(game_id, {
            "type": "player_disconnected",
            "data": {
                "player_id": player_id,
                "message": f"Player {player_id} disconnected"
            }
        })

async def handle_websocket_message(websocket: WebSocket, game_id: str, player_id: str, data: dict):
    """
    Handle incoming WebSocket messages.
    
    Args:
        websocket: The WebSocket connection
        game_id: The game ID
        player_id: The player ID
        data: The message data
    """
    try:
        message_type = data.get("type")
        message_data = data.get("data", {})
        
        logger.info(f"Received message: {message_type} from {player_id} in game {game_id}")
        
        if message_type == "ask":
            await handle_ask_action(game_id, player_id, message_data)
        elif message_type == "claim":
            await handle_claim_action(game_id, player_id, message_data)
        elif message_type == "counter_claim":
            await handle_counter_claim_action(game_id, player_id, message_data)
        elif message_type == "select_player":
            await handle_select_player_action(game_id, player_id, message_data)
        elif message_type == "ping":
            # Respond to ping with pong
            await websocket_manager.send_to_player(game_id, player_id, {
                "type": "pong",
                "data": {"timestamp": message_data.get("timestamp")}
            })
        else:
            logger.warning(f"Unknown message type: {message_type}")
            await websocket_manager.send_to_player(game_id, player_id, {
                "type": "error",
                "data": {"message": f"Unknown message type: {message_type}"}
            })
            
    except Exception as e:
        logger.error(f"Error handling WebSocket message: {e}")
        await websocket_manager.send_to_player(game_id, player_id, {
            "type": "error",
            "data": {"message": str(e)}
        })

async def handle_ask_action(game_id: str, player_id: str, data: dict):
    """
    Handle ask action from WebSocket.
    """
    try:
        result = await game_service.handle_ask_action(
            game_id=game_id,
            asking_player_id=player_id,
            target_player_id=data.get("target_player_id"),
            card_unique_id=data.get("card_unique_id")
        )
        
        # Broadcast the result to all players
        await websocket_manager.broadcast_to_game(game_id, {
            "type": "ask_result",
            "data": result
        })
        
        # Send updated game state to all players
        await broadcast_game_state_update(game_id)
        
    except Exception as e:
        logger.error(f"Error handling ask action: {e}")
        await websocket_manager.send_to_player(game_id, player_id, {
            "type": "error",
            "data": {"message": str(e)}
        })

async def handle_claim_action(game_id: str, player_id: str, data: dict):
    """
    Handle claim action from WebSocket.
    """
    try:
        result = await game_service.handle_claim_action(
            game_id=game_id,
            claiming_player_id=player_id,
            half_suit_id=data.get("half_suit_id"),
            assignments=data.get("assignments"),
            claim_for_other_team=data.get("claim_for_other_team", False)
        )
        
        # Broadcast the result to all players
        await websocket_manager.broadcast_to_game(game_id, {
            "type": "claim_result",
            "data": result
        })
        
        # Send updated game state to all players
        await broadcast_game_state_update(game_id)
        
    except Exception as e:
        logger.error(f"Error handling claim action: {e}")
        await websocket_manager.send_to_player(game_id, player_id, {
            "type": "error",
            "data": {"message": str(e)}
        })

async def handle_counter_claim_action(game_id: str, player_id: str, data: dict):
    """
    Handle counter-claim action from WebSocket.
    """
    try:
        result = await game_service.handle_counter_claim_action(
            game_id=game_id,
            counter_claiming_player_id=player_id,
            half_suit_id=data.get("half_suit_id"),
            assignments=data.get("assignments")
        )
        
        # Broadcast the result to all players
        await websocket_manager.broadcast_to_game(game_id, {
            "type": "counter_claim_result",
            "data": result
        })
        
        # Send updated game state to all players
        await broadcast_game_state_update(game_id)
        
    except Exception as e:
        logger.error(f"Error handling counter-claim action: {e}")
        await websocket_manager.send_to_player(game_id, player_id, {
            "type": "error",
            "data": {"message": str(e)}
        })

async def handle_select_player_action(game_id: str, player_id: str, data: dict):
    """
    Handle player selection for turns.
    """
    try:
        result = await game_service.select_current_player(
            game_id=game_id,
            selecting_player_id=player_id,
            selected_player_id=data.get("selected_player_id")
        )
        
        # Broadcast the result to all players
        await websocket_manager.broadcast_to_game(game_id, {
            "type": "player_selected",
            "data": result
        })
        
        # Send updated game state to all players
        await broadcast_game_state_update(game_id)
        
    except Exception as e:
        logger.error(f"Error handling select player action: {e}")
        await websocket_manager.send_to_player(game_id, player_id, {
            "type": "error",
            "data": {"message": str(e)}
        })

async def broadcast_game_state_update(game_id: str):
    """
    Broadcast game state update to all players in a game.
    """
    try:
        # Get all players in the game
        players = game_service.get_game_players(game_id)
        
        # Send personalized game state to each player
        for player in players:
            game_state = await game_service.get_game_state(game_id, player.id)
            await websocket_manager.send_to_player(game_id, player.id, {
                "type": "state_update",
                "data": game_state.dict()
            })
            
    except Exception as e:
        logger.error(f"Error broadcasting game state update: {e}")

@app.get("/stats")
async def get_server_stats():
    """
    Get server statistics for monitoring.
    """
    try:
        return {
            "active_games": len(game_service.get_active_games()),
            "total_players": game_service.get_total_player_count(),
            "websocket_connections": websocket_manager.get_connection_count(),
            "games_completed": game_service.get_completed_games_count(),
            "uptime": game_service.get_uptime()
        }
    except Exception as e:
        logger.error(f"Error getting server stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get server statistics")

@app.get("/games/{game_id}/status")
async def get_game_status(game_id: str):
    """
    Get public status of a specific game.
    """
    try:
        if not game_service.game_exists(game_id):
            raise HTTPException(status_code=404, detail="Game not found")
        
        return await game_service.get_game_public_status(game_id)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get game status")

# Development/testing endpoint
@app.get("/test")
async def test_endpoint():
    """
    Test endpoint for development and debugging.
    """
    return {
        "message": "Test endpoint working",
        "services": {
            "game_service": "available",
            "websocket_manager": "available",
            "game_state_manager": "available"
        }
    }

if __name__ == "__main__":
    # This allows running the app directly with: python main.py
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )