from typing import List, Optional, Dict, Any
import logging
from copy import deepcopy

from ..models.game_models import GameState, Player, Team, Card
from ..utils.validators import validate_player_id, validate_game_id

logger = logging.getLogger(__name__)

class PlayerService:
    """Service for managing player operations in the Half Suit card game."""
    
    def __init__(self):
        """Initialize the player service."""
        pass
    
    def add_player_to_game(self, game_state: GameState, player_id: str, player_name: str) -> int:
        """
        Add a player to an existing game and assign them to a team.
        
        Args:
            game_state: Current game state
            player_id: Unique identifier for the player
            player_name: Display name for the player
            
        Returns:
            int: Team ID that the player was assigned to
            
        Raises:
            ValueError: If game is full or player already exists
        """
        try:
            # Validate inputs
            if not validate_player_id(player_id):
                raise ValueError("Invalid player ID")
            
            if not player_name or len(player_name.strip()) == 0:
                raise ValueError("Player name cannot be empty")
            
            if len(player_name) > 50:
                raise ValueError("Player name too long (max 50 characters)")
            
            # Check if game is full
            if len(game_state.players) >= 6:
                raise ValueError("Game is full (maximum 6 players)")
            
            # Check if player already exists
            existing_player = self.get_player_by_id(game_state, player_id)
            if existing_player:
                raise ValueError("Player already exists in game")
            
            # Check if player name is already taken
            existing_names = [p.name for p in game_state.players]
            if player_name in existing_names:
                raise ValueError("Player name already taken")
            
            # Determine team assignment
            team_id = self._assign_player_to_team(game_state)
            
            # Create new player
            new_player = Player(
                id=player_id,
                name=player_name.strip(),
                team_id=team_id,
                hand=[],  # Empty hand initially
                num_cards=0
            )
            
            # Add player to game state
            game_state.players.append(new_player)
            
            # Add player to team
            target_team = next(team for team in game_state.teams if team.id == team_id)
            target_team.players.append(player_id)
            
            logger.info(f"Player {player_name} ({player_id}) added to game {game_state.game_id} on team {team_id}")
            
            return team_id
            
        except Exception as e:
            logger.error(f"Failed to add player to game: {str(e)}")
            raise
    
    def _assign_player_to_team(self, game_state: GameState) -> int:
        """
        Assign a player to a team, balancing team sizes.
        
        Args:
            game_state: Current game state
            
        Returns:
            int: Team ID to assign the player to
        """
        # Count players per team
        team_counts = {}
        for team in game_state.teams:
            team_counts[team.id] = len(team.players)
        
        # Assign to team with fewer players
        if team_counts[0] <= team_counts[1]:
            return 0
        else:
            return 1
    
    def get_player_by_id(self, game_state: GameState, player_id: str) -> Optional[Player]:
        """
        Get a player by their ID.
        
        Args:
            game_state: Current game state
            player_id: Player identifier
            
        Returns:
            Player object if found, None otherwise
        """
        for player in game_state.players:
            if player.id == player_id:
                return player
        return None
    
    def get_player_by_name(self, game_state: GameState, player_name: str) -> Optional[Player]:
        """
        Get a player by their name.
        
        Args:
            game_state: Current game state
            player_name: Player name
            
        Returns:
            Player object if found, None otherwise
        """
        for player in game_state.players:
            if player.name == player_name:
                return player
        return None
    
    def get_players_by_team(self, game_state: GameState, team_id: int) -> List[Player]:
        """
        Get all players on a specific team.
        
        Args:
            game_state: Current game state
            team_id: Team identifier
            
        Returns:
            List of Player objects on the team
        """
        return [player for player in game_state.players if player.team_id == team_id]
    
    def get_opponent_players(self, game_state: GameState, player_id: str) -> List[Player]:
        """
        Get all players on the opposing team.
        
        Args:
            game_state: Current game state
            player_id: Reference player identifier
            
        Returns:
            List of Player objects on the opposing team
        """
        reference_player = self.get_player_by_id(game_state, player_id)
        if not reference_player:
            return []
        
        opposing_team_id = 1 - reference_player.team_id  # 0 becomes 1, 1 becomes 0
        return self.get_players_by_team(game_state, opposing_team_id)
    
    def get_teammate_players(self, game_state: GameState, player_id: str) -> List[Player]:
        """
        Get all players on the same team (excluding the reference player).
        
        Args:
            game_state: Current game state
            player_id: Reference player identifier
            
        Returns:
            List of Player objects on the same team
        """
        reference_player = self.get_player_by_id(game_state, player_id)
        if not reference_player:
            return []
        
        teammates = self.get_players_by_team(game_state, reference_player.team_id)
        return [player for player in teammates if player.id != player_id]
    
    def filter_game_state_for_player(self, game_state: GameState, player_id: str) -> GameState:
        """
        Filter game state to only show information that a specific player should see.
        
        Args:
            game_state: Full game state
            player_id: Player identifier
            
        Returns:
            GameState with filtered information (private cards hidden)
        """
        # Deep copy to avoid modifying original state
        filtered_state = deepcopy(game_state)
        
        # Clear all player hands except for the requesting player
        for player in filtered_state.players:
            if player.id != player_id:
                player.hand = []  # Hide other players' cards
            # num_cards remains visible for all players
        
        return filtered_state
    
    def update_player_hand(self, game_state: GameState, player_id: str, new_hand: List[Card]):
        """
        Update a player's hand and card count.
        
        Args:
            game_state: Current game state
            player_id: Player identifier
            new_hand: New hand of cards
        """
        player = self.get_player_by_id(game_state, player_id)
        if player:
            player.hand = new_hand
            player.num_cards = len(new_hand)
    
    def remove_card_from_player(self, game_state: GameState, player_id: str, card: Card):
        """
        Remove a specific card from a player's hand.
        
        Args:
            game_state: Current game state
            player_id: Player identifier
            card: Card to remove
            
        Returns:
            bool: True if card was removed, False if not found
        """
        player = self.get_player_by_id(game_state, player_id)
        if not player:
            return False
        
        # Find and remove the card
        for i, player_card in enumerate(player.hand):
            if player_card.unique_id == card.unique_id:
                player.hand.pop(i)
                player.num_cards = len(player.hand)
                return True
        
        return False
    
    def add_card_to_player(self, game_state: GameState, player_id: str, card: Card):
        """
        Add a card to a player's hand.
        
        Args:
            game_state: Current game state
            player_id: Player identifier
            card: Card to add
        """
        player = self.get_player_by_id(game_state, player_id)
        if player:
            player.hand.append(card)
            player.num_cards = len(player.hand)
    
    def player_has_card(self, game_state: GameState, player_id: str, card: Card) -> bool:
        """
        Check if a player has a specific card.
        
        Args:
            game_state: Current game state
            player_id: Player identifier
            card: Card to check for
            
        Returns:
            bool: True if player has the card, False otherwise
        """
        player = self.get_player_by_id(game_state, player_id)
        if not player:
            return False
        
        return any(player_card.unique_id == card.unique_id for player_card in player.hand)
    
    def player_has_cards_in_half_suit(self, game_state: GameState, player_id: str, half_suit_id: int) -> bool:
        """
        Check if a player has any cards in a specific half suit.
        
        Args:
            game_state: Current game state
            player_id: Player identifier
            half_suit_id: Half suit identifier
            
        Returns:
            bool: True if player has cards in the half suit, False otherwise
        """
        player = self.get_player_by_id(game_state, player_id)
        if not player:
            return False
        
        return any(card.half_suit_id == half_suit_id for card in player.hand)
    
    def get_eligible_players_for_turn(self, game_state: GameState, team_id: int) -> List[Player]:
        """
        Get players on a team who are eligible to take a turn (have cards).
        
        Args:
            game_state: Current game state
            team_id: Team identifier
            
        Returns:
            List of Player objects who can take a turn
        """
        team_players = self.get_players_by_team(game_state, team_id)
        return [player for player in team_players if player.num_cards > 0]
    
    def get_eligible_players_for_ask(self, game_state: GameState, team_id: int) -> List[Player]:
        """
        Get players on a team who are eligible to ask for cards (have cards).
        Same as get_eligible_players_for_turn but kept separate for clarity.
        
        Args:
            game_state: Current game state
            team_id: Team identifier
            
        Returns:
            List of Player objects who can ask for cards
        """
        return self.get_eligible_players_for_turn(game_state, team_id)
    
    def get_all_players_for_claim(self, game_state: GameState, team_id: int) -> List[Player]:
        """
        Get all players on a team who can make claims (including those with 0 cards).
        
        Args:
            game_state: Current game state
            team_id: Team identifier
            
        Returns:
            List of Player objects who can make claims
        """
        return self.get_players_by_team(game_state, team_id)
    
    def validate_player_can_ask(self, game_state: GameState, player_id: str) -> bool:
        """
        Validate that a player can ask for cards.
        
        Args:
            game_state: Current game state
            player_id: Player identifier
            
        Returns:
            bool: True if player can ask, False otherwise
        """
        player = self.get_player_by_id(game_state, player_id)
        if not player:
            return False
        
        # Player must have at least one card to ask
        return player.num_cards > 0
    
    def validate_player_can_claim(self, game_state: GameState, player_id: str) -> bool:
        """
        Validate that a player can make claims.
        
        Args:
            game_state: Current game state
            player_id: Player identifier
            
        Returns:
            bool: True if player can claim, False otherwise
        """
        player = self.get_player_by_id(game_state, player_id)
        if not player:
            return False
        
        # Players can claim even with 0 cards
        return True
    
    def get_player_stats(self, game_state: GameState, player_id: str) -> Dict[str, Any]:
        """
        Get statistics for a specific player.
        
        Args:
            game_state: Current game state
            player_id: Player identifier
            
        Returns:
            Dict containing player statistics
        """
        player = self.get_player_by_id(game_state, player_id)
        if not player:
            return {}
        
        # Count cards by half suit
        half_suit_counts = {}
        for card in player.hand:
            half_suit_counts[card.half_suit_id] = half_suit_counts.get(card.half_suit_id, 0) + 1
        
        return {
            "player_id": player.id,
            "name": player.name,
            "team_id": player.team_id,
            "num_cards": player.num_cards,
            "half_suit_counts": half_suit_counts,
            "can_ask": self.validate_player_can_ask(game_state, player_id),
            "can_claim": self.validate_player_can_claim(game_state, player_id)
        }
    
    def remove_player_from_game(self, game_state: GameState, player_id: str):
        """
        Remove a player from the game (for disconnect handling).
        
        Args:
            game_state: Current game state
            player_id: Player identifier
        """
        # Remove from players list
        game_state.players = [p for p in game_state.players if p.id != player_id]
        
        # Remove from teams
        for team in game_state.teams:
            if player_id in team.players:
                team.players.remove(player_id)
        
        # If this was the current player, clear current player
        if game_state.current_player == player_id:
            game_state.current_player = None
        
        logger.info(f"Player {player_id} removed from game {game_state.game_id}")