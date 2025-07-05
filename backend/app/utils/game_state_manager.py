from typing import Dict, List, Optional, Any
import json
import logging
from datetime import datetime, timedelta, timezone
import threading
from ..models.game_models import GameState, Player, Team, Card, HalfSuit, AskRecord, ClaimRecord

logger = logging.getLogger(__name__)

class GameStateManager:
    """
    Manages game state persistence and retrieval.
    
    In production, this would be backed by Redis or a database.
    For now, using in-memory storage with thread safety.
    """
    
    def __init__(self, cleanup_interval_minutes: int = 60):
        """
        Initialize the game state manager.
        
        Args:
            cleanup_interval_minutes: How often to clean up expired games
        """
        self._games: Dict[str, GameState] = {}
        self._game_metadata: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._cleanup_interval = timedelta(minutes=cleanup_interval_minutes)
        self._game_timeout = timedelta(hours=24)  # Games expire after 24 hours
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_expired_games, daemon=True)
        self._cleanup_thread.start()
        
        logger.info("GameStateManager initialized")
    
    def create_game(self, game_id: str, game_state: GameState) -> bool:
        """
        Create a new game with the given state.
        
        Args:
            game_id: Unique identifier for the game
            game_state: Initial game state
            
        Returns:
            bool: True if game was created successfully
            
        Raises:
            ValueError: If game_id already exists
        """
        with self._lock:
            if game_id in self._games:
                raise ValueError(f"Game with ID {game_id} already exists")
            
            self._games[game_id] = game_state
            self._game_metadata[game_id] = {
                "created_at": datetime.now(timezone.utc),
                "last_updated": datetime.now(timezone.utc),
                "player_count": len(game_state.players),
                "status": game_state.status
            }
            
            logger.info(f"Game {game_id} created successfully")
            return True
    
    def game_exists(self, game_id: str) -> bool:
        """
        Check if a game exists.
        
        Args:
            game_id: Game identifier to check
            
        Returns:
            bool: True if game exists
        """
        with self._lock:
            return game_id in self._games
    
    def get_game_state(self, game_id: str) -> Optional[GameState]:
        """
        Retrieve game state by ID.
        
        Args:
            game_id: Game identifier
            
        Returns:
            GameState or None if not found
        """
        with self._lock:
            if game_id not in self._games:
                logger.warning(f"Game {game_id} not found")
                return None
            
            # Update last accessed time
            self._game_metadata[game_id]["last_updated"] = datetime.now(timezone.utc)
            
            # Return a copy to prevent external modification
            return self._deep_copy_game_state(self._games[game_id])
    
    def save_game_state(self, game_id: str, game_state: GameState) -> bool:
        """
        Save/update game state.
        
        Args:
            game_id: Game identifier
            game_state: Updated game state
            
        Returns:
            bool: True if saved successfully
        """
        with self._lock:
            if game_id not in self._games:
                logger.warning(f"Attempting to save non-existent game {game_id}")
                return False
            
            # Store a copy to prevent external modification
            self._games[game_id] = self._deep_copy_game_state(game_state)
            
            # Update metadata
            self._game_metadata[game_id].update({
                "last_updated": datetime.now(timezone.utc),
                "player_count": len(game_state.players),
                "status": game_state.status
            })
            
            logger.debug(f"Game {game_id} state saved")
            return True
    
    def delete_game(self, game_id: str) -> bool:
        """
        Delete a game and its metadata.
        
        Args:
            game_id: Game identifier
            
        Returns:
            bool: True if deleted successfully
        """
        with self._lock:
            if game_id not in self._games:
                logger.warning(f"Attempting to delete non-existent game {game_id}")
                return False
            
            del self._games[game_id]
            del self._game_metadata[game_id]
            
            logger.info(f"Game {game_id} deleted")
            return True
    
    def get_all_games_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all active games.
        
        Returns:
            Dict with game IDs as keys and game info as values
        """
        with self._lock:
            return {
                game_id: {
                    "game_id": game_id,
                    "status": self._games[game_id].status,
                    "player_count": len(self._games[game_id].players),
                    "team_scores": [team.score for team in self._games[game_id].teams],
                    "created_at": metadata["created_at"].isoformat(),
                    "last_updated": metadata["last_updated"].isoformat()
                }
                for game_id, metadata in self._game_metadata.items()
            }
    
    def get_games_by_status(self, status: str) -> List[str]:
        """
        Get list of game IDs by status.
        
        Args:
            status: Game status to filter by ('lobby', 'active', 'finished')
            
        Returns:
            List of game IDs matching the status
        """
        with self._lock:
            return [
                game_id for game_id, game_state in self._games.items()
                if game_state.status == status
            ]
    
    def get_player_game(self, player_id: str) -> Optional[str]:
        """
        Find which game a player is in.
        
        Args:
            player_id: Player identifier
            
        Returns:
            Game ID if found, None otherwise
        """
        with self._lock:
            for game_id, game_state in self._games.items():
                if any(player.id == player_id for player in game_state.players):
                    return game_id
            return None
    
    def get_game_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics about managed games.
        
        Returns:
            Dictionary with various statistics
        """
        with self._lock:
            total_games = len(self._games)
            
            status_counts = {}
            for game_state in self._games.values():
                status = game_state.status
                status_counts[status] = status_counts.get(status, 0) + 1
            
            total_players = sum(len(game_state.players) for game_state in self._games.values())
            
            return {
                "total_games": total_games,
                "total_players": total_players,
                "games_by_status": status_counts,
                "average_players_per_game": total_players / total_games if total_games > 0 else 0
            }
    
    def cleanup_finished_games(self, max_age_hours: int = 1) -> int:
        """
        Clean up finished games older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours for finished games
            
        Returns:
            Number of games cleaned up
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        games_to_remove = []
        
        with self._lock:
            for game_id, metadata in self._game_metadata.items():
                game_state = self._games[game_id]
                if (game_state.status == "finished" and 
                    metadata["last_updated"] < cutoff_time):
                    games_to_remove.append(game_id)
            
            for game_id in games_to_remove:
                del self._games[game_id]
                del self._game_metadata[game_id]
        
        if games_to_remove:
            logger.info(f"Cleaned up {len(games_to_remove)} finished games")
        
        return len(games_to_remove)
    
    def _cleanup_expired_games(self):
        """
        Background thread to periodically clean up expired games.
        """
        while True:
            try:
                # Sleep for cleanup interval
                import time
                time.sleep(self._cleanup_interval.total_seconds())
                
                # TODO: Reuse function above
                # Clean up expired games
                cutoff_time = datetime.now(timezone.utc) - self._game_timeout
                games_to_remove = []
                
                with self._lock:
                    for game_id, metadata in self._game_metadata.items():
                        if metadata["last_updated"] < cutoff_time:
                            games_to_remove.append(game_id)
                    
                    for game_id in games_to_remove:
                        del self._games[game_id]
                        del self._game_metadata[game_id]
                
                if games_to_remove:
                    logger.info(f"Cleaned up {len(games_to_remove)} expired games")
                    
            except Exception as e:
                logger.error(f"Error in cleanup thread: {e}")
    
    def _deep_copy_game_state(self, game_state: GameState) -> GameState:
        """
        Create a deep copy of game state to prevent external modifications.
        
        Args:
            game_state: Original game state
            
        Returns:
            Deep copy of the game state
        """
        # Use Pydantic's built-in copy method for deep copying
        return game_state.model_copy(deep=True)
    
    def export_game_state(self, game_id: str) -> Optional[Dict[str, Any]]:
        """
        Export game state as a dictionary (for debugging/logging).
        
        Args:
            game_id: Game identifier
            
        Returns:
            Game state as dictionary or None if not found
        """
        with self._lock:
            if game_id not in self._games:
                return None
            
            game_state = self._games[game_id]
            return {
                "game_state": game_state.model_dump(),
                "metadata": self._game_metadata[game_id].copy()
            }
    
    def import_game_state(self, game_id: str, game_data: Dict[str, Any]) -> bool:
        """
        Import game state from a dictionary (for restoration/debugging).
        
        Args:
            game_id: Game identifier
            game_data: Game data dictionary
            
        Returns:
            True if imported successfully
        """
        try:
            with self._lock:
                # Reconstruct game state from dictionary
                game_state = GameState(**game_data["game_state"])
                
                self._games[game_id] = game_state
                self._game_metadata[game_id] = game_data.get("metadata", {
                    "created_at": datetime.now(timezone.utc),
                    "last_updated": datetime.now(timezone.utc),
                    "player_count": len(game_state.players),
                    "status": game_state.status
                })
                
                logger.info(f"Game {game_id} imported successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to import game {game_id}: {e}")
            return False
    
    def get_active_player_count(self) -> int:
        """
        Get the total number of active players across all games.
        
        Returns:
            Total number of active players
        """
        with self._lock:
            return sum(
                len(game_state.players) 
                for game_state in self._games.values()
                if game_state.status in ["lobby", "active"]
            )
    
    def is_player_in_game(self, player_id: str, game_id: str) -> bool:
        """
        Check if a specific player is in a specific game.
        
        Args:
            player_id: Player identifier
            game_id: Game identifier
            
        Returns:
            True if player is in the game
        """
        with self._lock:
            if game_id not in self._games:
                return False
            
            game_state = self._games[game_id]
            return any(player.id == player_id for player in game_state.players)
    
    def get_game_age(self, game_id: str) -> Optional[timedelta]:
        """
        Get the age of a game since creation.
        
        Args:
            game_id: Game identifier
            
        Returns:
            Time since game creation or None if game not found
        """
        with self._lock:
            if game_id not in self._game_metadata:
                return None
            
            return datetime.now(timezone.utc) - self._game_metadata[game_id]["created_at"]
