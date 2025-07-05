import re
from typing import Optional, Dict, List, Any, Union
from pydantic import ValidationError
import uuid

# Import models (these would be implemented in their respective files)
from ..models.game_models import GameState, Player, Team, Card, AskRecord, ClaimRecord
from ..models.enums import GameStatus, CardRank, CardSuit

class GameValidationError(Exception):
    """Custom validation error for game-specific validation failures."""
    pass

class GameValidators:
    """Validators for game-related operations."""
    
    # Game ID validation
    @staticmethod
    def validate_game_id(game_id: str) -> bool:
        """
        Validate game ID format.
        
        Args:
            game_id: The game identifier to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            ValidationError: If game_id is invalid
        """
        if not game_id:
            raise ValidationError("Game ID cannot be empty")
        
        if not isinstance(game_id, str):
            raise ValidationError("Game ID must be a string")
        
        # Game ID should be 8 characters, alphanumeric, uppercase
        if not re.match(r'^[A-Z0-9]{8}$', game_id):
            raise ValidationError("Game ID must be 8 uppercase alphanumeric characters")
        
        return True
    
    # Player ID validation
    @staticmethod
    def validate_player_id(player_id: str) -> bool:
        """
        Validate player ID format.
        
        Args:
            player_id: The player identifier to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            ValidationError: If player_id is invalid
        """
        if not player_id:
            raise ValidationError("Player ID cannot be empty")
        
        if not isinstance(player_id, str):
            raise ValidationError("Player ID must be a string")
        
        # Player ID should be a valid UUID format
        try:
            uuid.UUID(player_id)
        except ValueError:
            raise ValidationError("Player ID must be a valid UUID")
        
        return True
    
    # Player name validation
    @staticmethod
    def validate_player_name(player_name: str) -> bool:
        """
        Validate player name format and content.
        
        Args:
            player_name: The player name to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            ValidationError: If player_name is invalid
        """
        if not player_name:
            raise ValidationError("Player name cannot be empty")
        
        if not isinstance(player_name, str):
            raise ValidationError("Player name must be a string")
        
        # Strip whitespace for validation
        player_name = player_name.strip()
        
        if len(player_name) < 1:
            raise ValidationError("Player name cannot be empty after trimming")
        
        if len(player_name) > 50:
            raise ValidationError("Player name cannot exceed 50 characters")
        
        # Check for valid characters (letters, numbers, spaces, basic punctuation)
        if not re.match(r'^[a-zA-Z0-9\s\-_\.]+$', player_name):
            raise ValidationError("Player name contains invalid characters")
        
        return True
    
    # Team ID validation
    @staticmethod
    def validate_team_id(team_id: int) -> bool:
        """
        Validate team ID.
        
        Args:
            team_id: The team identifier to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            ValidationError: If team_id is invalid
        """
        if not isinstance(team_id, int):
            raise ValidationError("Team ID must be an integer")
        
        if team_id not in [1, 2]:
            raise ValidationError("Team ID must be 1 or 2")
        
        return True

class GameStateValidators:
    """Validators for game state operations."""
    
    @staticmethod
    def validate_game_state(game_state: GameState) -> bool:
        """
        Validate the entire game state for consistency.
        
        Args:
            game_state: The game state to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            ValidationError: If game state is invalid
        """
        # Validate basic structure
        if not isinstance(game_state, GameState):
            raise ValidationError("Invalid game state object")
        
        # Validate game ID
        GameValidators.validate_game_id(game_state.game_id)
        
        # Validate players
        GameStateValidators._validate_players(game_state.players)
        
        # Validate teams
        GameStateValidators._validate_teams(game_state.teams, game_state.players)
        
        # Validate half suits
        GameStateValidators._validate_half_suits(game_state.half_suits)
        
        # Validate game status
        GameStateValidators._validate_game_status(game_state.status)
        
        # Validate current turn info
        GameStateValidators._validate_turn_info(game_state)
        
        return True
    
    @staticmethod
    def _validate_players(players: List[Player]) -> bool:
        """Validate players list."""
        if not isinstance(players, list):
            raise ValidationError("Players must be a list")
        
        if len(players) > 6:
            raise ValidationError("Cannot have more than 6 players")
        
        player_ids = set()
        player_names = set()
        
        for player in players:
            # Validate player ID uniqueness
            if player.id in player_ids:
                raise ValidationError(f"Duplicate player ID: {player.id}")
            player_ids.add(player.id)
            
            # Validate player name uniqueness
            if player.name in player_names:
                raise ValidationError(f"Duplicate player name: {player.name}")
            player_names.add(player.name)
            
            # Validate individual player
            GameValidators.validate_player_id(player.id)
            GameValidators.validate_player_name(player.name)
            GameValidators.validate_team_id(player.team_id)
            
            # Validate card count
            if player.num_cards < 0:
                raise ValidationError(f"Player {player.name} cannot have negative cards")
            
            if player.num_cards > 9:
                raise ValidationError(f"Player {player.name} cannot have more than 9 cards")
        
        return True
    
    @staticmethod
    def _validate_teams(teams: List[Team], players: List[Player]) -> bool:
        """Validate teams list."""
        if not isinstance(teams, list):
            raise ValidationError("Teams must be a list")
        
        if len(teams) != 2:
            raise ValidationError("Must have exactly 2 teams")
        
        team_ids = {team.id for team in teams}
        if team_ids != {1, 2}:
            raise ValidationError("Teams must have IDs 1 and 2")
        
        for team in teams:
            # Validate team score
            if team.score < 0:
                raise ValidationError(f"Team {team.id} cannot have negative score")
            
            if team.score > 9:
                raise ValidationError(f"Team {team.id} cannot have score > 9")
            
            # Validate team players
            if len(team.players) > 3:
                raise ValidationError(f"Team {team.id} cannot have more than 3 players")
            
            # Validate all team player IDs exist in players list
            player_ids = {player.id for player in players}
            for player_id in team.players:
                if player_id not in player_ids:
                    raise ValidationError(f"Team {team.id} references non-existent player {player_id}")
        
        return True
    
    @staticmethod
    def _validate_half_suits(half_suits: List[Any]) -> bool:
        """Validate half suits list."""
        if not isinstance(half_suits, list):
            raise ValidationError("Half suits must be a list")
        
        if len(half_suits) != 9:
            raise ValidationError("Must have exactly 9 half suits")
        
        # Check for duplicate half suit IDs
        half_suit_ids = {hs.id for hs in half_suits}
        if len(half_suit_ids) != 9:
            raise ValidationError("Half suit IDs must be unique")
        
        # Validate each half suit has 6 cards
        for hs in half_suits:
            if len(hs.cards) != 6:
                raise ValidationError(f"Half suit {hs.id} must have exactly 6 cards")
        
        return True
    
    @staticmethod
    def _validate_game_status(status: str) -> bool:
        """Validate game status."""
        valid_statuses = ["lobby", "active", "finished"]
        if status not in valid_statuses:
            raise ValidationError(f"Invalid game status: {status}")
        
        return True
    
    @staticmethod
    def _validate_turn_info(game_state: GameState) -> bool:
        """Validate current turn information."""
        # Validate current team
        if game_state.current_team not in [1, 2]:
            raise ValidationError("Current team must be 1 or 2")
        
        # If game is active, must have a current player
        if game_state.status == "active":
            if not game_state.current_player:
                raise ValidationError("Active game must have a current player")
            
            # Validate current player exists
            player_ids = {player.id for player in game_state.players}
            if game_state.current_player not in player_ids:
                raise ValidationError("Current player does not exist in game")
        
        return True

class ActionValidators:
    """Validators for game actions (ask, claim)."""
    
    @staticmethod
    def validate_ask_action(asker_id: str, target_id: str, card: Card, game_state: GameState) -> bool:
        """
        Validate an ask action.
        
        Args:
            asker_id: ID of the player asking
            target_id: ID of the player being asked
            card: The card being asked for
            game_state: Current game state
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            ValidationError: If ask action is invalid
        """
        # Validate player IDs
        GameValidators.validate_player_id(asker_id)
        GameValidators.validate_player_id(target_id)
        
        # Get player objects
        asker = next((p for p in game_state.players if p.id == asker_id), None)
        target = next((p for p in game_state.players if p.id == target_id), None)
        
        if not asker:
            raise ValidationError("Asker not found in game")
        
        if not target:
            raise ValidationError("Target player not found in game")
        
        # Validate it's the asker's turn
        if game_state.current_player != asker_id:
            raise ValidationError("It's not your turn")
        
        # Validate teams are different
        if asker.team_id == target.team_id:
            raise ValidationError("Cannot ask teammate for cards")
        
        # Validate asker has cards
        if asker.num_cards == 0:
            raise ValidationError("Cannot ask for cards when you have no cards")
        
        # Validate card format
        ActionValidators._validate_card(card)
        
        # Validate asker has at least one card from the same half suit
        # (This would require checking the asker's actual hand - implementation depends on game engine)
        
        return True
    
    @staticmethod
    def validate_claim_action(claimant_id: str, half_suit_id: int, assignments: Dict[str, str], game_state: GameState) -> bool:
        """
        Validate a claim action.
        
        Args:
            claimant_id: ID of the player making the claim
            half_suit_id: ID of the half suit being claimed
            assignments: Mapping of card unique_id to player_id
            game_state: Current game state
            
        Returns:
            bool: True if valid, False otherwise
            
        Raises:
            ValidationError: If claim action is invalid
        """
        # Validate player ID
        GameValidators.validate_player_id(claimant_id)
        
        # Get claimant
        claimant = next((p for p in game_state.players if p.id == claimant_id), None)
        if not claimant:
            raise ValidationError("Claimant not found in game")
        
        # Validate it's the claimant's turn (or their team's turn)
        current_player = next((p for p in game_state.players if p.id == game_state.current_player), None)
        if not current_player or current_player.team_id != claimant.team_id:
            raise ValidationError("It's not your team's turn")
        
        # Validate half suit ID
        if half_suit_id < 0 or half_suit_id > 8:
            raise ValidationError("Invalid half suit ID")
        
        # Validate half suit is still in play
        half_suit = next((hs for hs in game_state.half_suits if hs.id == half_suit_id), None)
        if not half_suit:
            raise ValidationError("Half suit not found")
        
        if half_suit.out_of_play:
            raise ValidationError("Half suit is already out of play")
        
        # Validate assignments
        ActionValidators._validate_claim_assignments(assignments, half_suit, game_state)
        
        return True
    
    @staticmethod
    def _validate_card(card: Card) -> bool:
        """Validate a card object."""
        if not isinstance(card, Card):
            raise ValidationError("Invalid card object")
        
        # Validate rank
        valid_ranks = [rank.value for rank in CardRank]

        if card.rank not in valid_ranks:
            raise ValidationError(f"Invalid card rank: {card.rank}")
        
        # Validate suit
        # valid_suits = ['Spades', 'Hearts', 'Diamonds', 'Clubs', 'Joker']
        valid_suits = [suit.value for suit in CardSuit]
        if card.suit not in valid_suits:
            raise ValidationError(f"Invalid card suit: {card.suit}")
        
        # Validate joker consistency
        if card.rank == CardRank.JOKER and card.suit != CardSuit.JOKER:
            raise ValidationError("Joker card must have Joker suit")
        if card.rank == CardRank.CUT and card.suit != CardSuit.JOKER:
            raise ValidationError("Joker card must have Joker suit")
        
        if card.suit == CardSuit.JOKER and card.rank != CardRank.JOKER and card.rank != CardRank.CUT:
            raise ValidationError("Joker suit must have Joker or Cut rank")
        
        return True
    
    @staticmethod
    def _validate_claim_assignments(assignments: Dict[str, str], half_suit: Any, game_state: GameState) -> bool:
        """Validate claim assignments."""
        if not isinstance(assignments, dict):
            raise ValidationError("Assignments must be a dictionary")
        
        # Must assign exactly 6 cards
        if len(assignments) != 6:
            raise ValidationError("Must assign exactly 6 cards")
        
        # Validate all card unique_ids are from the half suit
        half_suit_card_ids = {card.unique_id for card in half_suit.cards}
        for card_id in assignments.keys():
            if card_id not in half_suit_card_ids:
                raise ValidationError(f"Card {card_id} is not in half suit {half_suit.id}")
        
        # Validate all assigned player IDs exist
        player_ids = {player.id for player in game_state.players}
        for player_id in assignments.values():
            if player_id not in player_ids:
                raise ValidationError(f"Player {player_id} does not exist in game")
        
        return True

class InputValidators:
    """Validators for general input validation."""
    
    @staticmethod
    def validate_non_empty_string(value: str, field_name: str, max_length: Optional[int] = None) -> str:
        """
        Validate a non-empty string.
        
        Args:
            value: The string to validate
            field_name: Name of the field for error messages
            max_length: Maximum allowed length
            
        Returns:
            str: The validated and trimmed string
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string")
        
        value = value.strip()
        
        if not value:
            raise ValidationError(f"{field_name} cannot be empty")
        
        if max_length and len(value) > max_length:
            raise ValidationError(f"{field_name} cannot exceed {max_length} characters")
        
        return value
    
    @staticmethod
    def validate_integer_range(value: int, field_name: str, min_val: int, max_val: int) -> int:
        """
        Validate an integer within a range.
        
        Args:
            value: The integer to validate
            field_name: Name of the field for error messages
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            
        Returns:
            int: The validated integer
            
        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(value, int):
            raise ValidationError(f"{field_name} must be an integer")
        
        if value < min_val or value > max_val:
            raise ValidationError(f"{field_name} must be between {min_val} and {max_val}")
        
        return value

# Convenience functions for common validations
def validate_game_id(game_id: str) -> bool:
    """Convenience function for game ID validation."""
    return GameValidators.validate_game_id(game_id)

def validate_player_id(player_id: str) -> bool:
    """Convenience function for player ID validation."""
    return GameValidators.validate_player_id(player_id)

def validate_player_name(player_name: str) -> bool:
    """Convenience function for player name validation."""
    return GameValidators.validate_player_name(player_name)

def validate_team_id(team_id: int) -> bool:
    """Convenience function for team ID validation."""
    return GameValidators.validate_team_id(team_id)
