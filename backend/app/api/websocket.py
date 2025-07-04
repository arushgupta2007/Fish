"""
WebSocket handler for Half Suit Online Card Game
Handles real-time communication between server and clients
"""

import json
import logging
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from pydantic import BaseModel, ValidationError

from ..models.game_models import GameState, Card, AskRecord, ClaimRecord
from ..services.game_service import GameService
from ..utils.game_state_manager import GameStateManager

logger = logging.getLogger(__name__)

class WebSocketMessage(BaseModel):
    """Base WebSocket message structure"""
    event: str
    data: dict
    game_id: str
    player_id: str

class ConnectionManager:
    """Manages WebSocket connections for all games"""
    
    def __init__(self):
        # game_id -> {player_id -> WebSocket}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # player_id -> game_id for quick lookup
        self.player_game_mapping: Dict[str, str] = {}
        
    async def connect(self, websocket: WebSocket, game_id: str, player_id: str):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        
        if game_id not in self.active_connections:
            self.active_connections[game_id] = {}
            
        self.active_connections[game_id][player_id] = websocket
        self.player_game_mapping[player_id] = game_id
        
        logger.info(f"Player {player_id} connected to game {game_id}")
        
        # Notify other players in the game
        await self.broadcast_to_game(game_id, {
            "event": "player_connected",
            "data": {"player_id": player_id}
        }, exclude_player=player_id)

    async def disconnect(self, game_id: str, player_id: str):
        """Handle player disconnection"""
        if game_id in self.active_connections:
            if player_id in self.active_connections[game_id]:
                del self.active_connections[game_id][player_id]
                
            # Clean up empty game connections
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]
                
        if player_id in self.player_game_mapping:
            del self.player_game_mapping[player_id]
            
        logger.info(f"Player {player_id} disconnected from game {game_id}")
        
        # Notify other players
        await self.broadcast_to_game(game_id, {
            "event": "player_left",
            "data": {"player_id": player_id}
        })

    async def send_to_player(self, game_id: str, player_id: str, message: dict):
        """Send message to a specific player"""
        if (game_id in self.active_connections and 
            player_id in self.active_connections[game_id]):
            
            websocket = self.active_connections[game_id][player_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending message to {player_id}: {e}")
                    # Remove broken connection
                    await self.disconnect(game_id, player_id)

    async def broadcast_to_game(self, game_id: str, message: dict, exclude_player: Optional[str] = None):
        """Send message to all players in a game"""
        if game_id not in self.active_connections:
            return
            
        disconnected_players = []
        
        for player_id, websocket in self.active_connections[game_id].items():
            if exclude_player and player_id == exclude_player:
                continue
                
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting to {player_id}: {e}")
                    disconnected_players.append(player_id)
        
        # Clean up disconnected players
        for player_id in disconnected_players:
            await self.disconnect(game_id, player_id)

    def get_connected_players(self, game_id: str) -> List[str]:
        """Get list of connected players for a game"""
        if game_id in self.active_connections:
            return list(self.active_connections[game_id].keys())
        return []

    def is_player_connected(self, game_id: str, player_id: str) -> bool:
        """Check if a player is connected to a game"""
        return (game_id in self.active_connections and 
                player_id in self.active_connections[game_id])

# Global connection manager instance
connection_manager = ConnectionManager()

class WebSocketHandler:
    """Handles WebSocket events and game actions"""
    
    def __init__(self, game_service: GameService, state_manager: GameStateManager):
        self.game_service = game_service
        self.state_manager = state_manager

    async def handle_message(self, websocket: WebSocket, game_id: str, player_id: str, message: dict):
        """Handle incoming WebSocket messages"""
        try:
            event = message.get("event")
            data = message.get("data", {})
            
            if event == "ask":
                await self.handle_ask(game_id, player_id, data)
            elif event == "claim":
                await self.handle_claim(game_id, player_id, data)
            elif event == "counter_claim":
                await self.handle_counter_claim(game_id, player_id, data)
            elif event == "choose_current_player":
                await self.handle_choose_current_player(game_id, player_id, data)
            elif event == "ping":
                await self.handle_ping(game_id, player_id)
            else:
                await self.send_error(game_id, player_id, f"Unknown event: {event}")
                
        except ValidationError as e:
            await self.send_error(game_id, player_id, f"Invalid message format: {e}")
        except Exception as e:
            logger.error(f"Error handling message from {player_id}: {e}")
            await self.send_error(game_id, player_id, "Internal server error")

    async def handle_ask(self, game_id: str, player_id: str, data: dict):
        """Handle ask action"""
        try:
            target_player_id = data.get("target_player_id")
            card_data = data.get("card")
            
            if not target_player_id or not card_data:
                await self.send_error(game_id, player_id, "Missing required fields for ask")
                return
                
            # Create Card object
            card = Card(**card_data)
            
            # Validate and process ask through game service
            result = await self.game_service.process_ask(game_id, player_id, target_player_id, card)
            
            if result["success"]:
                # Create ask record
                ask_record = AskRecord(
                    turn=result["turn"],
                    asker=player_id,
                    respondent=target_player_id,
                    card=card,
                    success=result["card_transferred"]
                )
                
                # Broadcast ask result to all players
                await connection_manager.broadcast_to_game(game_id, {
                    "event": "ask",
                    "data": {
                        "from_id": player_id,
                        "to_id": target_player_id,
                        "card": card.dict(),
                        "success": result["card_transferred"],
                        "turn": result["turn"]
                    }
                })
                
                # Send updated game state
                await self.broadcast_game_state(game_id)
                
            else:
                await self.send_error(game_id, player_id, result["error"])
                
        except Exception as e:
            logger.error(f"Error processing ask: {e}")
            await self.send_error(game_id, player_id, "Failed to process ask")

    async def handle_claim(self, game_id: str, player_id: str, data: dict):
        """Handle claim action"""
        try:
            half_suit_id = data.get("half_suit_id")
            assignments = data.get("assignments", {})
            claim_for_other_team = data.get("claim_for_other_team", False)
            
            if half_suit_id is None or not assignments:
                await self.send_error(game_id, player_id, "Missing required fields for claim")
                return
                
            # Validate and process claim through game service
            result = await self.game_service.process_claim(
                game_id, player_id, half_suit_id, assignments, claim_for_other_team
            )
            
            if result["success"]:
                claim_record = ClaimRecord(
                    turn=result["turn"],
                    claimant=player_id,
                    half_suit_id=half_suit_id,
                    assignments=assignments,
                    outcome=result["outcome"],
                    point_to=result["point_to"]
                )
                
                # Broadcast claim result
                await connection_manager.broadcast_to_game(game_id, {
                    "event": "claim",
                    "data": {
                        "player_id": player_id,
                        "half_suit_id": half_suit_id,
                        "assignments": assignments,
                        "outcome": result["outcome"],
                        "point_to": result["point_to"],
                        "turn": result["turn"],
                        "claim_for_other_team": claim_for_other_team
                    }
                })
                
                # Check if counter-claim is needed
                if result.get("requires_counter_claim"):
                    await self.handle_counter_claim_prompt(game_id, result["opposing_team_id"])
                
                # Send updated game state
                await self.broadcast_game_state(game_id)
                
            else:
                await self.send_error(game_id, player_id, result["error"])
                
        except Exception as e:
            logger.error(f"Error processing claim: {e}")
            await self.send_error(game_id, player_id, "Failed to process claim")

    async def handle_counter_claim(self, game_id: str, player_id: str, data: dict):
        """Handle counter-claim action"""
        try:
            half_suit_id = data.get("half_suit_id")
            assignments = data.get("assignments", {})
            
            if half_suit_id is None or not assignments:
                await self.send_error(game_id, player_id, "Missing required fields for counter-claim")
                return
                
            # Process counter-claim through game service
            result = await self.game_service.process_counter_claim(
                game_id, player_id, half_suit_id, assignments
            )
            
            if result["success"]:
                # Broadcast counter-claim result
                await connection_manager.broadcast_to_game(game_id, {
                    "event": "counter_claim",
                    "data": {
                        "player_id": player_id,
                        "half_suit_id": half_suit_id,
                        "assignments": assignments,
                        "outcome": result["outcome"],
                        "point_to": result["point_to"],
                        "turn": result["turn"]
                    }
                })
                
                # Send updated game state
                await self.broadcast_game_state(game_id)
                
            else:
                await self.send_error(game_id, player_id, result["error"])
                
        except Exception as e:
            logger.error(f"Error processing counter-claim: {e}")
            await self.send_error(game_id, player_id, "Failed to process counter-claim")

    async def handle_choose_current_player(self, game_id: str, player_id: str, data: dict):
        """Handle team choosing current player"""
        try:
            chosen_player_id = data.get("chosen_player_id")
            
            if not chosen_player_id:
                await self.send_error(game_id, player_id, "Missing chosen_player_id")
                return
                
            # Process through game service
            result = await self.game_service.set_current_player(game_id, player_id, chosen_player_id)
            
            if result["success"]:
                # Broadcast current player change
                await connection_manager.broadcast_to_game(game_id, {
                    "event": "current_player_changed",
                    "data": {
                        "new_current_player": chosen_player_id,
                        "chosen_by": player_id
                    }
                })
                
                # Send updated game state
                await self.broadcast_game_state(game_id)
                
            else:
                await self.send_error(game_id, player_id, result["error"])
                
        except Exception as e:
            logger.error(f"Error setting current player: {e}")
            await self.send_error(game_id, player_id, "Failed to set current player")

    async def handle_counter_claim_prompt(self, game_id: str, opposing_team_id: int):
        """Prompt opposing team to nominate a counter-claimant"""
        game_state = await self.state_manager.get_game_state(game_id)
        if not game_state:
            return
            
        # Get players from opposing team
        opposing_team = next((team for team in game_state.teams if team.id == opposing_team_id), None)
        if not opposing_team:
            return
            
        # Send prompt to all players of opposing team
        for player_id in opposing_team.players:
            await connection_manager.send_to_player(game_id, player_id, {
                "event": "counter_claim_prompt",
                "data": {
                    "message": "Your team needs to nominate a player to make a counter-claim",
                    "team_id": opposing_team_id
                }
            })

    async def handle_ping(self, game_id: str, player_id: str):
        """Handle ping message for connection health check"""
        await connection_manager.send_to_player(game_id, player_id, {
            "event": "pong",
            "data": {"timestamp": int(time.time())}
        })

    async def broadcast_game_state(self, game_id: str):
        """Send updated game state to all players"""
        game_state = await self.state_manager.get_game_state(game_id)
        if not game_state:
            return
            
        # Send personalized game state to each player
        for player in game_state.players:
            player_specific_state = await self.game_service.get_player_game_state(game_id, player.id)
            await connection_manager.send_to_player(game_id, player.id, {
                "event": "state_update",
                "data": player_specific_state.dict()
            })

    async def send_error(self, game_id: str, player_id: str, message: str):
        """Send error message to specific player"""
        await connection_manager.send_to_player(game_id, player_id, {
            "event": "error",
            "data": {"message": message}
        })

    async def notify_game_end(self, game_id: str, winning_team_id: int):
        """Notify all players when game ends"""
        game_state = await self.state_manager.get_game_state(game_id)
        if not game_state:
            return
            
        winning_team = next((team for team in game_state.teams if team.id == winning_team_id), None)
        
        await connection_manager.broadcast_to_game(game_id, {
            "event": "game_ended",
            "data": {
                "winning_team_id": winning_team_id,
                "winning_team_name": winning_team.name if winning_team else "Unknown",
                "final_scores": {team.id: team.score for team in game_state.teams}
            }
        })

# WebSocket endpoint handler
async def websocket_endpoint(websocket: WebSocket, game_id: str, player_id: str):
    """Main WebSocket endpoint for game connections"""
    from ..services.game_service import game_service
    from ..utils.game_state_manager import game_state_manager
    
    handler = WebSocketHandler(game_service, game_state_manager)
    
    await connection_manager.connect(websocket, game_id, player_id)
    
    try:
        # Send initial game state
        await handler.broadcast_game_state(game_id)
        
        # Listen for messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                await handler.handle_message(websocket, game_id, player_id, message)
            except json.JSONDecodeError:
                await handler.send_error(game_id, player_id, "Invalid JSON format")
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Unexpected error in WebSocket connection: {e}")
                await handler.send_error(game_id, player_id, "Connection error")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        await connection_manager.disconnect(game_id, player_id)

# Utility functions for external use
async def broadcast_to_game(game_id: str, message: dict, exclude_player: Optional[str] = None):
    """Utility function to broadcast message to game"""
    await connection_manager.broadcast_to_game(game_id, message, exclude_player)

async def send_to_player(game_id: str, player_id: str, message: dict):
    """Utility function to send message to specific player"""
    await connection_manager.send_to_player(game_id, player_id, message)

def get_connected_players(game_id: str) -> List[str]:
    """Utility function to get connected players"""
    return connection_manager.get_connected_players(game_id)

def is_player_connected(game_id: str, player_id: str) -> bool:
    """Utility function to check if player is connected"""
    return connection_manager.is_player_connected(game_id, player_id)