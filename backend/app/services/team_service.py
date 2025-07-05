from typing import List, Optional, Dict, Any, Set
import logging
from copy import deepcopy

from ..models.game_models import GameState, Player, Team, Card, HalfSuit
from ..utils.validators import validate_game_id

logger = logging.getLogger(__name__)

class TeamService:
    """Service for managing team operations in the Half Suit card game."""
    
    def __init__(self):
        """Initialize the team service."""
        pass
    
    def create_teams(self, game_state: GameState):
        """
        Create two empty teams for a new game.
        
        Args:
            game_state: Current game state to add teams to
        """
        # Create Team 0
        team_0 = Team(
            id=0,
            name="Team 1",
            score=0,
            players=[]
        )
        
        # Create Team 1
        team_1 = Team(
            id=1,
            name="Team 2",
            score=0,
            players=[]
        )
        
        game_state.teams = [team_0, team_1]
        
        logger.info(f"Teams created for game {game_state.game_id}")
    
    def get_team_by_id(self, game_state: GameState, team_id: int) -> Optional[Team]:
        """
        Get a team by its ID.
        
        Args:
            game_state: Current game state
            team_id: Team identifier (0 or 1)
            
        Returns:
            Team object if found, None otherwise
        """
        for team in game_state.teams:
            if team.id == team_id:
                return team
        return None
    
    def get_opposing_team(self, game_state: GameState, team_id: int) -> Optional[Team]:
        """
        Get the opposing team.
        
        Args:
            game_state: Current game state
            team_id: Reference team identifier
            
        Returns:
            Opposing team object if found, None otherwise
        """
        opposing_team_id = 1 - team_id  # 0 becomes 1, 1 becomes 0
        return self.get_team_by_id(game_state, opposing_team_id)
    
    def add_point_to_team(self, game_state: GameState, team_id: int):
        """
        Add a point to a team's score.
        
        Args:
            game_state: Current game state
            team_id: Team identifier
            
        Raises:
            ValueError: If team not found
        """
        team = self.get_team_by_id(game_state, team_id)
        if not team:
            raise ValueError(f"Team {team_id} not found")
        
        team.score += 1
        logger.info(f"Point added to team {team_id}. New score: {team.score}")
    
    def get_team_score(self, game_state: GameState, team_id: int) -> int:
        """
        Get a team's current score.
        
        Args:
            game_state: Current game state
            team_id: Team identifier
            
        Returns:
            Team score, or 0 if team not found
        """
        team = self.get_team_by_id(game_state, team_id)
        return team.score if team else 0
    
    def get_winning_team(self, game_state: GameState) -> Optional[int]:
        """
        Determine the winning team based on scores.
        
        Args:
            game_state: Current game state
            
        Returns:
            Winning team ID, or None if game not finished or tied
        """
        if len(game_state.teams) != 2:
            return None
        
        team_0_score = self.get_team_score(game_state, 0)
        team_1_score = self.get_team_score(game_state, 1)
        
        # Check if all 9 half suits have been claimed
        claimed_half_suits = sum(1 for hs in game_state.half_suits if hs.out_of_play)
        if claimed_half_suits < 9:
            return None  # Game not finished
        
        # Since there are 9 half suits, ties are impossible
        if team_0_score > team_1_score:
            return 0
        elif team_1_score > team_0_score:
            return 1
        else:
            # This shouldn't happen with 9 half suits
            logger.warning("Unexpected tie in Half Suit game")
            return None
    
    def get_team_players(self, game_state: GameState, team_id: int) -> List[Player]:
        """
        Get all players on a specific team.
        
        Args:
            game_state: Current game state
            team_id: Team identifier
            
        Returns:
            List of Player objects on the team
        """
        team = self.get_team_by_id(game_state, team_id)
        if not team:
            return []
        
        team_players = []
        for player_id in team.players:
            player = next((p for p in game_state.players if p.id == player_id), None)
            if player:
                team_players.append(player)
        
        return team_players
    
    def get_team_cards(self, game_state: GameState, team_id: int) -> List[Card]:
        """
        Get all cards held by a team.
        
        Args:
            game_state: Current game state
            team_id: Team identifier
            
        Returns:
            List of all cards held by the team
        """
        team_cards = []
        team_players = self.get_team_players(game_state, team_id)
        
        for player in team_players:
            team_cards.extend(player.hand)
        
        return team_cards
    
    def get_team_cards_by_half_suit(self, game_state: GameState, team_id: int, half_suit_id: int) -> List[Card]:
        """
        Get all cards in a specific half suit held by a team.
        
        Args:
            game_state: Current game state
            team_id: Team identifier
            half_suit_id: Half suit identifier
            
        Returns:
            List of cards in the half suit held by the team
        """
        team_cards = self.get_team_cards(game_state, team_id)
        return [card for card in team_cards if card.half_suit_id == half_suit_id]
    
    def count_team_cards_in_half_suit(self, game_state: GameState, team_id: int, half_suit_id: int) -> int:
        """
        Count how many cards in a half suit a team has.
        
        Args:
            game_state: Current game state
            team_id: Team identifier
            half_suit_id: Half suit identifier
            
        Returns:
            Number of cards in the half suit held by the team
        """
        return len(self.get_team_cards_by_half_suit(game_state, team_id, half_suit_id))
    
    def get_team_card_distribution(self, game_state: GameState, team_id: int, half_suit_id: int) -> Dict[str, List[Card]]:
        """
        Get the distribution of cards in a half suit across team members.
        
        Args:
            game_state: Current game state
            team_id: Team identifier
            half_suit_id: Half suit identifier
            
        Returns:
            Dict mapping player_id to list of cards they have in the half suit
        """
        distribution = {}
        team_players = self.get_team_players(game_state, team_id)
        
        for player in team_players:
            player_cards = [card for card in player.hand if card.half_suit_id == half_suit_id]
            if player_cards:  # Only include players who have cards in this half suit
                distribution[player.id] = player_cards
        
        return distribution
    
    def team_has_all_cards_in_half_suit(self, game_state: GameState, team_id: int, half_suit_id: int) -> bool:
        """
        Check if a team has all 6 cards in a half suit.
        
        Args:
            game_state: Current game state
            team_id: Team identifier
            half_suit_id: Half suit identifier
            
        Returns:
            True if team has all 6 cards, False otherwise
        """
        return self.count_team_cards_in_half_suit(game_state, team_id, half_suit_id) == 6
    
    def get_eligible_players_for_turn(self, game_state: GameState, team_id: int) -> List[Player]:
        """
        Get players on a team who are eligible to take a turn.
        
        Args:
            game_state: Current game state
            team_id: Team identifier
            
        Returns:
            List of Player objects who can take a turn
        """
        team_players = self.get_team_players(game_state, team_id)
        return [player for player in team_players if player.num_cards > 0]
    
    def get_eligible_players_for_ask(self, game_state: GameState, team_id: int) -> List[Player]:
        """
        Get players on a team who can ask for cards (must have cards).
        
        Args:
            game_state: Current game state
            team_id: Team identifier
            
        Returns:
            List of Player objects who can ask for cards
        """
        return self.get_eligible_players_for_turn(game_state, team_id)
    
    def get_eligible_players_for_claim(self, game_state: GameState, team_id: int) -> List[Player]:
        """
        Get players on a team who can make claims (all players, even with 0 cards).
        
        Args:
            game_state: Current game state
            team_id: Team identifier
            
        Returns:
            List of Player objects who can make claims
        """
        return self.get_team_players(game_state, team_id)
    
    # TODO: Voting? First come first serve? Random?
    def choose_next_player(self, game_state: GameState, team_id: int, preferred_player_id: Optional[str] = None) -> Optional[str]:
        """
        Choose the next player to take a turn for a team.
        
        Args:
            game_state: Current game state
            team_id: Team identifier
            preferred_player_id: Preferred player ID (if specified by team)
            
        Returns:
            Player ID who should take the next turn, or None if no eligible players
        """
        eligible_players = self.get_eligible_players_for_turn(game_state, team_id)
        
        if not eligible_players:
            return None
        
        # If a preferred player is specified and they're eligible, use them
        if preferred_player_id:
            for player in eligible_players:
                if player.id == preferred_player_id:
                    return preferred_player_id
        
        # Otherwise, choose the first eligible player (could be randomized in future)
        return eligible_players[0].id
    
    def get_team_statistics(self, game_state: GameState, team_id: int) -> Dict[str, Any]:
        """
        Get comprehensive statistics for a team.
        
        Args:
            game_state: Current game state
            team_id: Team identifier
            
        Returns:
            Dict containing team statistics
        """
        team = self.get_team_by_id(game_state, team_id)
        if not team:
            return {}
        
        team_players = self.get_team_players(game_state, team_id)
        team_cards = self.get_team_cards(game_state, team_id)
        
        # Count cards by half suit
        half_suit_counts = {}
        for card in team_cards:
            half_suit_counts[card.half_suit_id] = half_suit_counts.get(card.half_suit_id, 0) + 1
        
        # Count complete half suits (where team has all 6 cards)
        complete_half_suits = []
        for half_suit_id in range(9):  # 0-8 half suits
            if self.team_has_all_cards_in_half_suit(game_state, team_id, half_suit_id):
                complete_half_suits.append(half_suit_id)
        
        return {
            "team_id": team.id,
            "name": team.name,
            "score": team.score,
            "num_players": len(team_players),
            "total_cards": len(team_cards),
            "half_suit_counts": half_suit_counts,
            "complete_half_suits": complete_half_suits,
            "eligible_for_turn": len(self.get_eligible_players_for_turn(game_state, team_id)),
            "eligible_for_ask": len(self.get_eligible_players_for_ask(game_state, team_id)),
            "eligible_for_claim": len(self.get_eligible_players_for_claim(game_state, team_id))
        }
    
    def validate_team_assignment(self, game_state: GameState) -> bool:
        """
        Validate that teams are properly assigned (3 players each).
        
        Args:
            game_state: Current game state
            
        Returns:
            True if teams are valid, False otherwise
        """
        if len(game_state.teams) != 2:
            return False
        
        team_0_players = self.get_team_players(game_state, 0)
        team_1_players = self.get_team_players(game_state, 1)
        
        # Each team should have exactly 3 players
        if len(team_0_players) != 3 or len(team_1_players) != 3:
            return False
        
        # All players should be assigned to exactly one team
        all_assigned_players = set()
        for team in game_state.teams:
            for player_id in team.players:
                if player_id in all_assigned_players:
                    return False  # Player assigned to multiple teams
                all_assigned_players.add(player_id)
        
        # All game players should be assigned to a team
        game_player_ids = {player.id for player in game_state.players}
        if all_assigned_players != game_player_ids:
            return False
        
        return True
    
    def balance_teams(self, game_state: GameState):
        """
        Balance teams if they become uneven (for reconnection scenarios).
        
        Args:
            game_state: Current game state
        """
        team_0_players = self.get_team_players(game_state, 0)
        team_1_players = self.get_team_players(game_state, 1)
        
        # If teams are already balanced, do nothing
        if abs(len(team_0_players) - len(team_1_players)) <= 1:
            return
        
        # Move players from larger team to smaller team
        if len(team_0_players) > len(team_1_players):
            # Move from team 0 to team 1
            players_to_move = (len(team_0_players) - len(team_1_players)) // 2
            for i in range(players_to_move):
                if team_0_players:
                    player = team_0_players.pop()
                    player.team_id = 1
                    game_state.teams[0].players.remove(player.id)
                    game_state.teams[1].players.append(player.id)
        else:
            # Move from team 1 to team 0
            players_to_move = (len(team_1_players) - len(team_0_players)) // 2
            for i in range(players_to_move):
                if team_1_players:
                    player = team_1_players.pop()
                    player.team_id = 0
                    game_state.teams[1].players.remove(player.id)
                    game_state.teams[0].players.append(player.id)
        
        logger.info(f"Teams rebalanced for game {game_state.game_id}")
    
    def get_team_names(self, game_state: GameState) -> Dict[int, str]:
        """
        Get team names mapped by team ID.
        
        Args:
            game_state: Current game state
            
        Returns:
            Dict mapping team_id to team name
        """
        return {team.id: team.name for team in game_state.teams}
    
    def update_team_names(self, game_state: GameState, team_names: Dict[int, str]):
        """
        Update team names.
        
        Args:
            game_state: Current game state
            team_names: Dict mapping team_id to new team name
        """
        for team in game_state.teams:
            if team.id in team_names:
                team.name = team_names[team.id]
                logger.info(f"Team {team.id} renamed to '{team.name}'")
    
    def reset_team_scores(self, game_state: GameState):
        """
        Reset all team scores to 0 (for game restart scenarios).
        
        Args:
            game_state: Current game state
        """
        for team in game_state.teams:
            team.score = 0
        
        logger.info(f"Team scores reset for game {game_state.game_id}")
    
    def get_team_turn_order(self, game_state: GameState) -> List[int]:
        """
        Get the turn order for teams.
        
        Args:
            game_state: Current game state
            
        Returns:
            List of team IDs in turn order
        """
        # Teams alternate turns: 0, 1, 0, 1, ...
        return [0, 1]
    
    def get_next_team_turn(self, current_team_id: int) -> int:
        """
        Get the next team to take a turn.
        
        Args:
            current_team_id: Current team's ID
            
        Returns:
            Next team's ID
        """
        return 1 - current_team_id  # 0 becomes 1, 1 becomes 0
