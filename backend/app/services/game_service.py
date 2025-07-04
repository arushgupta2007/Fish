from typing import Dict, List, Optional, Tuple, Any
import logging
import random
from datetime import datetime

from ..models.game_models import (
    GameState, Player, Team, Card, HalfSuit, 
    AskRecord, ClaimRecord
)
from ..utils.game_state_manager import GameStateManager
from ..core.deck_manager import DeckManager
from ..core.claim_validator import ClaimValidator
from ..core.half_suit_definitions import HalfSuitDefinitions

logger = logging.getLogger(__name__)

class GameService:
    """
    Service class for managing game business logic.
    
    Handles game creation, starting, turn management, and game flow.
    """
    
    def __init__(self, game_state_manager: GameStateManager):
        """
        Initialize the game service.
        
        Args:
            game_state_manager: Game state persistence manager
        """
        self.game_state_manager = game_state_manager
        self.deck_manager = DeckManager()
        self.claim_validator = ClaimValidator()
        self.half_suit_definitions = HalfSuitDefinitions()
        
        logger.info("GameService initialized")
    
    def create_game(self, game_id: str, creator_name: str) -> GameState:
        """
        Create a new game with the creator as the first player.
        
        Args:
            game_id: Unique identifier for the game
            creator_name: Name of the player creating the game
            
        Returns:
            GameState: Initial game state
            
        Raises:
            ValueError: If game creation fails
        """
        try:
            # Create initial teams
            teams = [
                Team(id=1, name="Team 1", score=0, players=[]),
                Team(id=2, name="Team 2", score=0, players=[])
            ]
            
            # Create creator as first player
            creator_id = f"player_{random.randint(1000, 9999)}"
            creator = Player(
                id=creator_id,
                name=creator_name,
                team_id=1,  # Creator goes to Team 1
                hand=[],
                num_cards=0
            )
            
            # Add creator to team
            teams[0].players.append(creator_id)
            
            # Create half suits (initially all in play)
            half_suits = self.half_suit_definitions.create_half_suits()
            
            # Create initial game state
            game_state = GameState(
                game_id=game_id,
                players=[creator],
                teams=teams,
                half_suits=half_suits,
                ask_history=[],
                claim_history=[],
                current_team=1,  # Will be randomized when game starts
                current_player=None,  # Will be set when game starts
                status="lobby"
            )
            
            # Save to state manager
            self.game_state_manager.create_game(game_id, game_state)
            
            logger.info(f"Game {game_id} created by {creator_name}")
            return game_state
            
        except Exception as e:
            logger.error(f"Failed to create game {game_id}: {e}")
            raise ValueError(f"Failed to create game: {e}")
    
    def start_game(self, game_state: GameState) -> GameState:
        """
        Start the game by dealing cards and setting up initial state.
        
        Args:
            game_state: Current game state
            
        Returns:
            GameState: Updated game state with dealt cards
            
        Raises:
            ValueError: If game cannot be started
        """
        if game_state.status != "lobby":
            raise ValueError("Game has already started or finished")
        
        if len(game_state.players) != 6:
            raise ValueError(f"Need exactly 6 players to start. Have {len(game_state.players)}")
        
        try:
            # Deal cards to all players
            self._deal_cards(game_state)
            
            # Randomize starting team and player
            starting_team = random.choice([1, 2])
            team_players = [p for p in game_state.players if p.team_id == starting_team]
            starting_player = random.choice(team_players)
            
            # Update game state
            game_state.current_team = starting_team
            game_state.current_player = starting_player.id
            game_state.status = "active"
            
            logger.info(f"Game {game_state.game_id} started. First turn: Team {starting_team}, Player {starting_player.name}")
            return game_state
            
        except Exception as e:
            logger.error(f"Failed to start game {game_state.game_id}: {e}")
            raise ValueError(f"Failed to start game: {e}")
    
    def process_ask(self, game_state: GameState, asker_id: str, target_id: str, card: Card) -> Tuple[GameState, bool]:
        """
        Process an ask action between players.
        
        Args:
            game_state: Current game state
            asker_id: ID of the player asking
            target_id: ID of the player being asked
            card: Card being asked for
            
        Returns:
            Tuple of (updated_game_state, success)
            
        Raises:
            ValueError: If ask is invalid
        """
        # Validate ask
        self._validate_ask(game_state, asker_id, target_id, card)
        
        # Find players
        asker = self._find_player(game_state, asker_id)
        target = self._find_player(game_state, target_id)
        
        # Check if target has the card
        target_has_card = any(
            c.rank == card.rank and c.suit == card.suit 
            for c in target.hand
        )
        
        # Create ask record
        ask_record = AskRecord(
            turn=len(game_state.ask_history) + len(game_state.claim_history) + 1,
            asker=asker_id,
            respondent=target_id,
            card=card,
            success=target_has_card
        )
        
        # Add to history
        game_state.ask_history.append(ask_record)
        
        if target_has_card:
            # Transfer card
            self._transfer_card(game_state, target, asker, card)
            # Turn continues with same team
            logger.info(f"Ask successful: {asker.name} got {card.rank} of {card.suit} from {target.name}")
            return game_state, True
        else:
            # Turn passes to other team
            self._pass_turn(game_state)
            logger.info(f"Ask failed: {target.name} doesn't have {card.rank} of {card.suit}")
            return game_state, False
    
    def process_claim(self, game_state: GameState, claimant_id: str, half_suit_id: int, 
                     assignments: Dict[str, str], claim_for_other_team: bool = False) -> GameState:
        """
        Process a claim action.
        
        Args:
            game_state: Current game state
            claimant_id: ID of the player making the claim
            half_suit_id: ID of the half suit being claimed
            assignments: Dictionary mapping card unique_id to player_id
            claim_for_other_team: Whether this is a "claim for other team"
            
        Returns:
            GameState: Updated game state
            
        Raises:
            ValueError: If claim is invalid
        """
        # Validate claim
        self._validate_claim(game_state, claimant_id, half_suit_id, assignments)
        
        # Find claimant
        claimant = self._find_player(game_state, claimant_id)
        
        # Get half suit
        half_suit = next(hs for hs in game_state.half_suits if hs.id == half_suit_id)
        
        # Validate claim using claim validator
        claim_result = self.claim_validator.validate_claim(
            game_state, claimant_id, half_suit_id, assignments, claim_for_other_team
        )
        
        # Create claim record
        claim_record = ClaimRecord(
            turn=len(game_state.ask_history) + len(game_state.claim_history) + 1,
            claimant=claimant_id,
            half_suit_id=half_suit_id,
            assignments=assignments,
            outcome=claim_result.outcome,
            point_to=claim_result.winning_team
        )
        
        # Add to history
        game_state.claim_history.append(claim_record)
        
        # Update scores
        winning_team = next(team for team in game_state.teams if team.id == claim_result.winning_team)
        winning_team.score += 1
        
        # Mark half suit as claimed and remove cards
        half_suit.claimed_by = claim_result.winning_team
        half_suit.out_of_play = True
        
        # Remove cards from players' hands
        self._remove_half_suit_cards(game_state, half_suit)
        
        # Handle turn logic based on claim result
        if claim_result.outcome in ["own_team_incorrect", "counter_incorrect", "split_auto_incorrect"]:
            # Turn passes to other team
            self._pass_turn(game_state)
        # Otherwise turn continues with same team
        
        # Check if game is finished
        if self._is_game_finished(game_state):
            game_state.status = "finished"
            logger.info(f"Game {game_state.game_id} finished")
        
        logger.info(f"Claim processed: {claimant.name} claimed half suit {half_suit_id}, outcome: {claim_result.outcome}")
        return game_state
    
    def process_counter_claim(self, game_state: GameState, counter_claimant_id: str, 
                            half_suit_id: int, assignments: Dict[str, str]) -> GameState:
        """
        Process a counter-claim action.
        
        Args:
            game_state: Current game state
            counter_claimant_id: ID of the player making the counter-claim
            half_suit_id: ID of the half suit being counter-claimed
            assignments: Dictionary mapping card unique_id to player_id
            
        Returns:
            GameState: Updated game state
            
        Raises:
            ValueError: If counter-claim is invalid
        """
        # Find the original claim that triggered this counter-claim
        last_claim = game_state.claim_history[-1] if game_state.claim_history else None
        
        if not last_claim or last_claim.half_suit_id != half_suit_id:
            raise ValueError("No valid claim to counter")
        
        # Validate counter-claim
        counter_result = self.claim_validator.validate_counter_claim(
            game_state, counter_claimant_id, half_suit_id, assignments
        )
        
        # Update the last claim record with counter-claim outcome
        last_claim.outcome = counter_result.outcome
        last_claim.point_to = counter_result.winning_team
        
        # Update scores
        winning_team = next(team for team in game_state.teams if team.id == counter_result.winning_team)
        winning_team.score += 1
        
        # Mark half suit as claimed and remove cards
        half_suit = next(hs for hs in game_state.half_suits if hs.id == half_suit_id)
        half_suit.claimed_by = counter_result.winning_team
        half_suit.out_of_play = True
        
        # Remove cards from players' hands
        self._remove_half_suit_cards(game_state, half_suit)
        
        # Handle turn logic
        if counter_result.outcome == "counter_incorrect":
            # Turn passes to original claiming team
            original_claimant = self._find_player(game_state, last_claim.claimant)
            game_state.current_team = original_claimant.team_id
        # Otherwise turn continues with counter-claiming team
        
        # Check if game is finished
        if self._is_game_finished(game_state):
            game_state.status = "finished"
            logger.info(f"Game {game_state.game_id} finished")
        
        logger.info(f"Counter-claim processed for half suit {half_suit_id}, outcome: {counter_result.outcome}")
        return game_state
    
    def get_valid_asks(self, game_state: GameState, player_id: str) -> List[Dict[str, Any]]:
        """
        Get list of valid cards a player can ask for.
        
        Args:
            game_state: Current game state
            player_id: ID of the player
            
        Returns:
            List of valid ask options
        """
        player = self._find_player(game_state, player_id)
        
        if not player.hand:
            return []
        
        valid_asks = []
        
        # Get all cards in player's hand by half suit
        player_half_suits = set()
        for card in player.hand:
            player_half_suits.add(card.half_suit_id)
        
        # For each half suit the player has cards in
        for half_suit_id in player_half_suits:
            half_suit = next(hs for hs in game_state.half_suits if hs.id == half_suit_id)
            
            # Don't ask for cards from claimed half suits
            if half_suit.out_of_play:
                continue
            
            # Get all cards in this half suit that the player doesn't have
            for card in half_suit.cards:
                if not any(c.unique_id == card.unique_id for c in player.hand):
                    valid_asks.append({
                        "card": card,
                        "half_suit_name": half_suit.name,
                        "possible_targets": [
                            p.id for p in game_state.players 
                            if p.team_id != player.team_id and p.num_cards > 0
                        ]
                    })
        
        return valid_asks
    
    def get_valid_claims(self, game_state: GameState, player_id: str) -> List[Dict[str, Any]]:
        """
        Get list of valid half suits a player can claim.
        
        Args:
            game_state: Current game state
            player_id: ID of the player
            
        Returns:
            List of valid claim options
        """
        valid_claims = []
        
        for half_suit in game_state.half_suits:
            if not half_suit.out_of_play:
                valid_claims.append({
                    "half_suit_id": half_suit.id,
                    "half_suit_name": half_suit.name,
                    "cards": half_suit.cards
                })
        
        return valid_claims
    
    def _deal_cards(self, game_state: GameState) -> None:
        """
        Deal cards to all players in the game.
        
        Args:
            game_state: Game state to update with dealt cards
        """
        # Create and shuffle deck
        deck = self.deck_manager.create_deck()
        random.shuffle(deck)
        
        # Deal 9 cards to each player
        cards_per_player = 9
        for i, player in enumerate(game_state.players):
            start_idx = i * cards_per_player
            end_idx = start_idx + cards_per_player
            player.hand = deck[start_idx:end_idx]
            player.num_cards = len(player.hand)
        
        logger.info(f"Dealt {cards_per_player} cards to each of {len(game_state.players)} players")
    
    def _validate_ask(self, game_state: GameState, asker_id: str, target_id: str, card: Card) -> None:
        """
        Validate an ask action.
        
        Args:
            game_state: Current game state
            asker_id: ID of the asking player
            target_id: ID of the target player
            card: Card being asked for
            
        Raises:
            ValueError: If ask is invalid
        """
        # Check if it's the asker's turn
        if game_state.current_player != asker_id:
            raise ValueError("Not your turn")
        
        # Find players
        asker = self._find_player(game_state, asker_id)
        target = self._find_player(game_state, target_id)
        
        # Check if asker has cards
        if not asker.hand:
            raise ValueError("Cannot ask when you have no cards")
        
        # Check if target is on opposing team
        if asker.team_id == target.team_id:
            raise ValueError("Cannot ask teammate for cards")
        
        # Check if target has cards
        if target.num_cards == 0:
            raise ValueError("Cannot ask player with no cards")
        
        # Check if asker has at least one card from the same half suit
        card_half_suit_id = card.half_suit_id
        asker_has_half_suit = any(c.half_suit_id == card_half_suit_id for c in asker.hand)
        
        if not asker_has_half_suit:
            raise ValueError("Must have at least one card from the same half suit to ask")
        
        # Check if half suit is still in play
        half_suit = next((hs for hs in game_state.half_suits if hs.id == card_half_suit_id), None)
        if not half_suit or half_suit.out_of_play:
            raise ValueError("Cannot ask for cards from claimed half suit")
    
    def _validate_claim(self, game_state: GameState, claimant_id: str, half_suit_id: int, 
                       assignments: Dict[str, str]) -> None:
        """
        Validate a claim action.
        
        Args:
            game_state: Current game state
            claimant_id: ID of the claiming player
            half_suit_id: ID of the half suit being claimed
            assignments: Card assignments
            
        Raises:
            ValueError: If claim is invalid
        """
        # Check if it's the claimant's turn
        if game_state.current_player != claimant_id:
            raise ValueError("Not your turn")
        
        # Check if half suit exists and is still in play
        half_suit = next((hs for hs in game_state.half_suits if hs.id == half_suit_id), None)
        if not half_suit:
            raise ValueError("Invalid half suit")
        
        if half_suit.out_of_play:
            raise ValueError("Half suit already claimed")
        
        # Check if all 6 cards are assigned
        if len(assignments) != 6:
            raise ValueError("Must assign all 6 cards in the half suit")
        
        # Check if all assigned players exist
        for player_id in assignments.values():
            if not any(p.id == player_id for p in game_state.players):
                raise ValueError(f"Invalid player ID: {player_id}")
        
        # Check if all card IDs are valid for this half suit
        half_suit_card_ids = {card.unique_id for card in half_suit.cards}
        for card_id in assignments.keys():
            if card_id not in half_suit_card_ids:
                raise ValueError(f"Invalid card ID for this half suit: {card_id}")
    
    def _find_player(self, game_state: GameState, player_id: str) -> Player:
        """
        Find a player by ID.
        
        Args:
            game_state: Current game state
            player_id: ID of the player to find
            
        Returns:
            Player object
            
        Raises:
            ValueError: If player not found
        """
        for player in game_state.players:
            if player.id == player_id:
                return player
        raise ValueError(f"Player {player_id} not found")
    
    def _transfer_card(self, game_state: GameState, from_player: Player, to_player: Player, card: Card) -> None:
        """
        Transfer a card from one player to another.
        
        Args:
            game_state: Current game state
            from_player: Player giving the card
            to_player: Player receiving the card
            card: Card to transfer
        """
        # Find the actual card in from_player's hand
        card_to_transfer = None
        for i, c in enumerate(from_player.hand):
            if c.rank == card.rank and c.suit == card.suit:
                card_to_transfer = from_player.hand.pop(i)
                break
        
        if card_to_transfer:
            # Add to receiving player's hand
            to_player.hand.append(card_to_transfer)
            
            # Update card counts
            from_player.num_cards = len(from_player.hand)
            to_player.num_cards = len(to_player.hand)
    
    def _remove_half_suit_cards(self, game_state: GameState, half_suit: HalfSuit) -> None:
        """
        Remove all cards from a half suit from players' hands.
        
        Args:
            game_state: Current game state
            half_suit: Half suit whose cards should be removed
        """
        card_ids_to_remove = {card.unique_id for card in half_suit.cards}
        
        for player in game_state.players:
            # Remove cards that belong to this half suit
            player.hand = [card for card in player.hand if card.unique_id not in card_ids_to_remove]
            player.num_cards = len(player.hand)
    
    def _pass_turn(self, game_state: GameState) -> None:
        """
        Pass the turn to the other team.
        
        Args:
            game_state: Current game state
        """
        # Switch to other team
        game_state.current_team = 2 if game_state.current_team == 1 else 1
        
        # Find a player on the new team with cards
        team_players = [p for p in game_state.players if p.team_id == game_state.current_team and p.num_cards > 0]
        
        if team_players:
            # For now, just pick the first available player
            # In a full implementation, the team would choose
            game_state.current_player = team_players[0].id
        else:
            # No players with cards on this team - game might be ending
            game_state.current_player = None
    
    def _is_game_finished(self, game_state: GameState) -> bool:
        """
        Check if the game is finished (all half suits claimed).
        
        Args:
            game_state: Current game state
            
        Returns:
            True if game is finished
        """
        return all(half_suit.out_of_play for half_suit in game_state.half_suits)
    
    def get_game_winner(self, game_state: GameState) -> Optional[Team]:
        """
        Get the winning team if the game is finished.
        
        Args:
            game_state: Current game state
            
        Returns:
            Winning team or None if game not finished
        """
        if not self._is_game_finished(game_state):
            return None
        
        # Find team with highest score
        winning_team = max(game_state.teams, key=lambda t: t.score)
        return winning_team
    
    def get_game_summary(self, game_state: GameState) -> Dict[str, Any]:
        """
        Get a summary of the current game state.
        
        Args:
            game_state: Current game state
            
        Returns:
            Dictionary with game summary information
        """
        return {
            "game_id": game_state.game_id,
            "status": game_state.status,
            "current_turn": {
                "team": game_state.current_team,
                "player": game_state.current_player,
                "player_name": next((p.name for p in game_state.players if p.id == game_state.current_player), None)
            },
            "scores": {
                "team_1": game_state.teams[0].score,
                "team_2": game_state.teams[1].score
            },
            "half_suits_remaining": len([hs for hs in game_state.half_suits if not hs.out_of_play]),
            "total_actions": len(game_state.ask_history) + len(game_state.claim_history),
            "players": [
                {
                    "id": p.id,
                    "name": p.name,
                    "team": p.team_id,
                    "cards": p.num_cards
                }
                for p in game_state.players
            ]
        }