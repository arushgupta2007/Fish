from fastapi import APIRouter, HTTPException, Depends, FastAPI
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid
import logging

# Import models and services (these would be implemented in their respective files)
from ..models.game_models import GameState, Player, Team, Card
from ..services.game_service import GameService
from ..services.player_service import PlayerService
from ..services.team_service import TeamService
from ..utils.game_state_manager import GameStateManager
from ..utils.validators import validate_game_id, validate_player_id

# Set up logging
logger = logging.getLogger(__name__)

# Create router instance
router = APIRouter(prefix="/api", tags=["game"])

# Request/Response models
class CreateGameRequest(BaseModel):
    creator_name: str = Field(..., min_length=1, max_length=50)

class CreateGameResponse(BaseModel):
    game_id: str

class JoinGameRequest(BaseModel):
    game_id: str = Field(..., min_length=1)
    player_name: str = Field(..., min_length=1, max_length=50)

class JoinGameResponse(BaseModel):
    player_id: str
    team_id: int

class StartGameRequest(BaseModel):
    game_id: str = Field(..., min_length=1)
    player_id: str = Field(..., min_length=1)

class StartGameResponse(BaseModel):
    ok: bool

class ErrorResponse(BaseModel):
    error: str
    message: str

# Global game state manager (in production, this would be a proper database or Redis)
game_state_manager = GameStateManager()
game_service = GameService(game_state_manager)
player_service = PlayerService()
team_service = TeamService()

@router.post("/create-game", response_model=CreateGameResponse)
async def create_game(request: CreateGameRequest) -> CreateGameResponse:
    """
    Create a new game lobby.
    
    Args:
        request: Contains the creator's name
        
    Returns:
        CreateGameResponse: Contains the unique game_id
        
    Raises:
        HTTPException: If game creation fails
    """
    try:
        # Generate unique game ID
        game_id = str(uuid.uuid4())[:8].upper()  # Short, readable game ID
        
        # Ensure game ID is unique
        while game_state_manager.game_exists(game_id):
            game_id = str(uuid.uuid4())[:8].upper()
        
        # Create the game
        game_state = game_service.create_game(game_id, request.creator_name)
        
        logger.info(f"Game created: {game_id} by {request.creator_name}")
        
        return CreateGameResponse(game_id=game_id)
        
    except Exception as e:
        logger.error(f"Failed to create game: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create game")

@router.post("/join-game", response_model=JoinGameResponse)
async def join_game(request: JoinGameRequest) -> JoinGameResponse:
    """
    Join an existing game lobby.
    
    Args:
        request: Contains game_id and player_name
        
    Returns:
        JoinGameResponse: Contains player_id and team_id
        
    Raises:
        HTTPException: If joining fails (game doesn't exist, full, etc.)
    """
    try:
        # Validate game exists
        if not game_state_manager.game_exists(request.game_id):
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Get current game state
        game_state = game_state_manager.get_game_state(request.game_id)
        
        # Check if game is in lobby state
        if game_state.status != "lobby":
            raise HTTPException(status_code=400, detail="Game has already started")
        
        # Check if game is full
        if len(game_state.players) >= 6:
            raise HTTPException(status_code=400, detail="Game is full")
        
        # Check if player name is already taken
        existing_names = [player.name for player in game_state.players]
        if request.player_name in existing_names:
            raise HTTPException(status_code=400, detail="Player name already taken")
        
        # Generate unique player ID
        player_id = str(uuid.uuid4())
        
        # Add player to game
        team_id = player_service.add_player_to_game(
            game_state, player_id, request.player_name
        )
        
        # Save updated game state
        game_state_manager.save_game_state(request.game_id, game_state)
        
        logger.info(f"Player {request.player_name} joined game {request.game_id}")
        
        return JoinGameResponse(player_id=player_id, team_id=team_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to join game: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to join game")

@router.get("/game-state", response_model=GameState)
async def get_game_state(
    game_id: str,
    player_id: str
) -> GameState:
    """
    Fetch the current game state for a specific player.
    
    Args:
        game_id: The game identifier
        player_id: The player identifier
        
    Returns:
        GameState: The current game state with player-specific information
        
    Raises:
        HTTPException: If game or player not found
    """
    try:
        # Validate game exists
        if not game_state_manager.game_exists(game_id):
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Get game state
        game_state = game_state_manager.get_game_state(game_id)
        
        # Validate player exists in game
        player_exists = any(player.id == player_id for player in game_state.players)
        if not player_exists:
            raise HTTPException(status_code=404, detail="Player not found in game")
        
        # Filter game state for this specific player
        filtered_game_state = player_service.filter_game_state_for_player(
            game_state, player_id
        )
        
        return filtered_game_state
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get game state: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get game state")

@router.post("/start-game", response_model=StartGameResponse)
async def start_game(request: StartGameRequest) -> StartGameResponse:
    """
    Start the game if all conditions are met.
    
    Args:
        request: Contains game_id and player_id
        
    Returns:
        StartGameResponse: Confirmation of game start
        
    Raises:
        HTTPException: If game cannot be started
    """
    try:
        # Validate game exists
        if not game_state_manager.game_exists(request.game_id):
            raise HTTPException(status_code=404, detail="Game not found")
        
        # Get game state
        game_state = game_state_manager.get_game_state(request.game_id)
        
        # Validate player exists in game
        player_exists = any(player.id == request.player_id for player in game_state.players)
        if not player_exists:
            raise HTTPException(status_code=404, detail="Player not found in game")
        
        # Check if game is in lobby state
        if game_state.status != "lobby":
            raise HTTPException(status_code=400, detail="Game has already started or finished")
        
        # Check if we have exactly 6 players
        if len(game_state.players) != 6:
            raise HTTPException(
                status_code=400, 
                detail=f"Need exactly 6 players to start game. Currently have {len(game_state.players)}"
            )
        
        # Start the game
        game_service.start_game(game_state)
        
        # Save updated game state
        game_state_manager.save_game_state(request.game_id, game_state)
        
        logger.info(f"Game {request.game_id} started by player {request.player_id}")
        
        return StartGameResponse(ok=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start game: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start game")

@router.get("/games", response_model=Dict[str, Any])
async def list_games() -> Dict[str, Any]:
    """
    List all active games (for debugging/admin purposes).
    
    Returns:
        Dict containing active games information
    """
    try:
        active_games = game_state_manager.get_all_games_info()
        return {"active_games": active_games}
        
    except Exception as e:
        logger.error(f"Failed to list games: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list games")

@router.delete("/game/{game_id}")
async def delete_game(game_id: str) -> Dict[str, str]:
    """
    Delete a game (for cleanup/admin purposes).
    
    Args:
        game_id: The game identifier
        
    Returns:
        Confirmation message
        
    Raises:
        HTTPException: If game not found
    """
    try:
        if not game_state_manager.game_exists(game_id):
            raise HTTPException(status_code=404, detail="Game not found")
        
        game_state_manager.delete_game(game_id)
        
        logger.info(f"Game {game_id} deleted")
        
        return {"message": f"Game {game_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete game: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete game")

@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {"status": "healthy", "service": "half-suit-game-api"}

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "HTTP_ERROR", "message": exc.detail}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
    )