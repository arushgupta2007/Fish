"""
Core game engine for Half Suit Online Card Game
Handles all game logic, turn management, and action validation
"""

import logging
import random
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from ..models.game_models import (
    Card, Player, Team, GameState, HalfSuit, AskRecord, ClaimRecord
)
from ..core.deck_manager import DeckManager
from ..core.claim_validator import ClaimValidator
from ..core.half_suit_definitions import HalfSuitDefinitions
from ..models.enums import GameStatus, ClaimOutcome

logger = logging.getLogger(__name__)

class GameEngine:
    """Core game engine handling all game logic and state management"""
    
    def __init__(self):
        self.deck_manager = DeckManager()
        self.claim_validator = ClaimValidator()
        self.half_suit_definitions = HalfSuitDefinitions()
        self.games: Dict[str, GameState] = {}
        self.pending_counter_claims: Dict[str, Dict] = {}  # game_id -> claim_data
        
    def create_game(self, game_id: str, creator_name: str) -> Dict[str, Any]:
        """Create a new game lobby"""
        try:
            if game_id in self.games:
                return {"success": False, "error": "Game already exists"}
            
            # Create initial game state
            game_state = GameState(
                game_id=game_id,
                players=[],
                teams=[
                    Team(id=1, name="Team 1", score=0, players=[]),
                    Team(id=2, name="Team 2", score=0, players=[])
                ],
                half_suits=[],
                ask_history=[],
                claim_history=[],
                current_team=1,
                current_player=None,
                status=GameStatus.LOBBY
            )
            
            self.games[game_id] = game_state
            logger.info(f"Created game {game_id}")
            
            return {"success": True, "game_state": game_state}
            
        except Exception as e:
            logger.error(f"Error creating game {game_id}: {e}")
            return {"success": False, "error": "Failed to create game"}
    
    def join_game(self, game_id: str, player_name: str) -> Dict[str, Any]:
        """Add a player to a game"""
        try:
            if game_id not in self.games:
                return {"success": False, "error": "Game not found"}
            
            game_state = self.games[game_id]
            
            if game_state.status != GameStatus.LOBBY.value:
                return {"success": False, "error": "Game already started"}
            
            if len(game_state.players) >= 6:
                return {"success": False, "error": "Game is full"}
            
            # Check if player name already exists
            if any(p.name == player_name for p in game_state.players):
                return {"success": False, "error": "Player name already taken"}
            
            # Generate unique player ID
            player_id = f"player_{len(game_state.players) + 1}_{random.randint(1000, 9999)}"
            
            # Assign to team (alternate assignment)
            team_id = 1 if len(game_state.players) % 2 == 0 else 2
            
            # Create player
            player = Player(
                id=player_id,
                name=player_name,
                team_id=team_id,
                hand=[],
                num_cards=0
            )
            
            game_state.players.append(player)
            
            # Add to team
            for team in game_state.teams:
                if team.id == team_id:
                    team.players.append(player_id)
                    break
            
            logger.info(f"Player {player_name} ({player_id}) joined game {game_id} on team {team_id}")
            
            # Auto-start if we have 6 players
            if len(game_state.players) == 6:
                start_result = self.start_game(game_id)
                if not start_result["success"]:
                    return start_result
            
            return {
                "success": True,
                "player_id": player_id,
                "team_id": team_id,
                "game_state": game_state
            }
            
        except Exception as e:
            logger.error(f"Error joining game {game_id}: {e}")
            return {"success": False, "error": "Failed to join game"}
    
    def start_game(self, game_id: str) -> Dict[str, Any]:
        """Start the game by dealing cards and setting initial state"""
        try:
            if game_id not in self.games:
                return {"success": False, "error": "Game not found"}
            
            game_state = self.games[game_id]
            
            if game_state.status != GameStatus.LOBBY.value:
                return {"success": False, "error": "Game already started"}
            
            if len(game_state.players) != 6:
                return {"success": False, "error": "Need exactly 6 players to start"}
            
            # Create deck and deal cards
            deck = self.deck_manager.create_deck()
            dealt_hands = self.deck_manager.deal_cards(deck, 6)
            
            # Assign cards to players
            for i, player in enumerate(game_state.players):
                player.hand = dealt_hands[i]
                player.num_cards = len(player.hand)
            
            # Initialize half suits
            game_state.half_suits = self.half_suit_definitions.create_half_suits(deck)
            
            # Set random starting team and player
            game_state.current_team = random.choice([1, 2])
            team_players = [p for p in game_state.players if p.team_id == game_state.current_team]
            game_state.current_player = random.choice(team_players).id
            
            game_state.status = GameStatus.ACTIVE
            
            logger.info(f"Started game {game_id} with team {game_state.current_team} going first")
            
            return {"success": True, "game_state": game_state}
            
        except Exception as e:
            logger.error(f"Error starting game {game_id}: {e}")
            return {"success": False, "error": "Failed to start game"}
    
    def process_ask(self, game_id: str, asker_id: str, target_id: str, card: Card) -> Dict[str, Any]:
        """Process an ask action"""
        try:
            if game_id not in self.games:
                return {"success": False, "error": "Game not found"}
            
            game_state = self.games[game_id]
            
            # Validate ask action
            validation_result = self._validate_ask(game_state, asker_id, target_id, card)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}
            
            asker = self._get_player(game_state, asker_id)
            target = self._get_player(game_state, target_id)
            
            # Check if target has the card
            card_found = False
            for target_card in target.hand:
                if (target_card.rank == card.rank and 
                    target_card.suit == card.suit and
                    target_card.unique_id == card.unique_id):
                    
                    # Transfer card
                    target.hand.remove(target_card)
                    asker.hand.append(target_card)
                    target.num_cards -= 1
                    asker.num_cards += 1
                    card_found = True
                    break
            
            # Create ask record
            turn_number = len(game_state.ask_history) + len(game_state.claim_history) + 1
            ask_record = AskRecord(
                turn=turn_number,
                asker=asker_id,
                respondent=target_id,
                card=card,
                success=card_found
            )
            game_state.ask_history.append(ask_record)
            
            # Handle turn passing
            if card_found:
                # Asker's turn continues - they can ask again or claim
                pass
            else:
                # Turn passes to other team
                game_state.current_team = 2 if game_state.current_team == 1 else 1
                game_state.current_player = self._choose_next_player(game_state)
            
            logger.info(f"Ask processed: {asker_id} -> {target_id} for {card.rank} of {card.suit}, success: {card_found}")
            
            return {
                "success": True,
                "card_transferred": card_found,
                "turn": turn_number,
                "game_state": game_state
            }
            
        except Exception as e:
            logger.error(f"Error processing ask: {e}")
            return {"success": False, "error": "Failed to process ask"}
    
    def process_claim(self, game_id: str, claimant_id: str, half_suit_id: int, 
                     assignments: Dict[str, str], claim_for_other_team: bool = False) -> Dict[str, Any]:
        """Process a claim action"""
        try:
            if game_id not in self.games:
                return {"success": False, "error": "Game not found"}
            
            game_state = self.games[game_id]
            
            # Validate claim action
            validation_result = self._validate_claim(game_state, claimant_id, half_suit_id, assignments)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}
            
            claimant = self._get_player(game_state, claimant_id)
            half_suit = self._get_half_suit(game_state, half_suit_id)
            
            # Validate the claim using claim validator
            claim_result = self.claim_validator.validate_claim(
                game_state, half_suit_id, assignments, claim_for_other_team
            )
            
            turn_number = len(game_state.ask_history) + len(game_state.claim_history) + 1
            
            # Handle different claim scenarios
            if claim_result["scenario"] == "all_claiming_team":
                # All cards with claiming team - resolve immediately
                outcome, point_to = self._resolve_immediate_claim(
                    game_state, claimant.team_id, claim_result["correct"]
                )
                self._finalize_claim(game_state, half_suit_id, claimant.team_id if claim_result["correct"] else 
                                   (2 if claimant.team_id == 1 else 1))
                
            elif claim_result["scenario"] == "all_opposing_team":
                # All cards with opposing team - needs counter-claim
                self.pending_counter_claims[game_id] = {
                    "claimant_id": claimant_id,
                    "half_suit_id": half_suit_id,
                    "assignments": assignments,
                    "turn": turn_number,
                    "opposing_team_id": 2 if claimant.team_id == 1 else 1
                }
                
                game_state.status = GameStatus.WAITING_FOR_COUNTER_CLAIM
                
                return {
                    "success": True,
                    "requires_counter_claim": True,
                    "opposing_team_id": 2 if claimant.team_id == 1 else 1,
                    "turn": turn_number,
                    "game_state": game_state
                }
                
            elif claim_result["scenario"] == "split_teams":
                if claim_for_other_team:
                    # Claim for other team - resolve based on accuracy
                    outcome, point_to = self._resolve_other_team_claim(
                        game_state, claimant.team_id, claim_result["correct"]
                    )
                else:
                    # Regular claim on split cards - automatically incorrect
                    outcome = ClaimOutcome.SPLIT_AUTO_INCORRECT
                    point_to = 2 if claimant.team_id == 1 else 1
                
                self._finalize_claim(game_state, half_suit_id, point_to)
            
            # Create claim record
            claim_record = ClaimRecord(
                turn=turn_number,
                claimant=claimant_id,
                half_suit_id=half_suit_id,
                assignments=assignments,
                outcome=outcome,
                point_to=point_to
            )
            game_state.claim_history.append(claim_record)
            
            # Handle turn passing after claim
            if outcome in [ClaimOutcome.OWN_TEAM_INCORRECT, ClaimOutcome.OTHER_TEAM_INCORRECT]:
                # Turn passes to other team
                game_state.current_team = 2 if game_state.current_team == 1 else 1
            
            game_state.current_player = self._choose_next_player(game_state)
            
            # Check if game is finished
            if self._is_game_finished(game_state):
                game_state.status = GameStatus.FINISHED
            
            logger.info(f"Claim processed: {claimant_id} claimed half suit {half_suit_id}, outcome: {outcome.value}")
            
            return {
                "success": True,
                "outcome": outcome.value,
                "point_to": point_to,
                "turn": turn_number,
                "game_state": game_state
            }
            
        except Exception as e:
            logger.error(f"Error processing claim: {e}")
            return {"success": False, "error": "Failed to process claim"}
    
    def process_counter_claim(self, game_id: str, counter_claimant_id: str, 
                            half_suit_id: int, assignments: Dict[str, str]) -> Dict[str, Any]:
        """Process a counter-claim action"""
        try:
            if game_id not in self.games:
                return {"success": False, "error": "Game not found"}
            
            if game_id not in self.pending_counter_claims:
                return {"success": False, "error": "No pending counter-claim"}
            
            game_state = self.games[game_id]
            pending_claim = self.pending_counter_claims[game_id]
            
            # Validate counter-claim
            counter_claimant = self._get_player(game_state, counter_claimant_id)
            if counter_claimant.team_id != pending_claim["opposing_team_id"]:
                return {"success": False, "error": "Counter-claimant not on opposing team"}
            
            # Validate the counter-claim assignments
            counter_result = self.claim_validator.validate_counter_claim(
                game_state, half_suit_id, assignments, pending_claim["opposing_team_id"]
            )
            
            # Determine outcome
            if counter_result["correct"]:
                outcome = ClaimOutcome.COUNTER_CORRECT
                point_to = pending_claim["opposing_team_id"]
            else:
                outcome = ClaimOutcome.COUNTER_INCORRECT
                point_to = self._get_player(game_state, pending_claim["claimant_id"]).team_id
            
            # Finalize the claim
            self._finalize_claim(game_state, half_suit_id, point_to)
            
            # Create claim record for the original claim
            original_claim_record = ClaimRecord(
                turn=pending_claim["turn"],
                claimant=pending_claim["claimant_id"],
                half_suit_id=half_suit_id,
                assignments=pending_claim["assignments"],
                outcome=outcome.value,
                point_to=point_to
            )
            game_state.claim_history.append(original_claim_record)
            
            # Handle turn passing
            if outcome == ClaimOutcome.COUNTER_INCORRECT:
                # Turn passes to other team
                game_state.current_team = 2 if game_state.current_team == 1 else 1
            
            game_state.current_player = self._choose_next_player(game_state)
            game_state.status = GameStatus.ACTIVE
            
            # Clean up pending counter-claim
            del self.pending_counter_claims[game_id]
            
            # Check if game is finished
            if self._is_game_finished(game_state):
                game_state.status = GameStatus.FINISHED
            
            logger.info(f"Counter-claim processed: {counter_claimant_id}, outcome: {outcome.value}")
            
            return {
                "success": True,
                "outcome": outcome.value,
                "point_to": point_to,
                "turn": pending_claim["turn"],
                "game_state": game_state
            }
            
        except Exception as e:
            logger.error(f"Error processing counter-claim: {e}")
            return {"success": False, "error": "Failed to process counter-claim"}
    
    def set_current_player(self, game_id: str, setter_id: str, chosen_player_id: str) -> Dict[str, Any]:
        """Set the current player for a team"""
        try:
            if game_id not in self.games:
                return {"success": False, "error": "Game not found"}
            
            game_state = self.games[game_id]
            setter = self._get_player(game_state, setter_id)
            chosen_player = self._get_player(game_state, chosen_player_id)
            
            # Validate that setter is on the current team
            if setter.team_id != game_state.current_team:
                return {"success": False, "error": "Not your team's turn"}
            
            # Validate that chosen player is on the same team and eligible
            if chosen_player.team_id != game_state.current_team:
                return {"success": False, "error": "Chosen player not on current team"}
            
            if chosen_player.num_cards == 0:
                return {"success": False, "error": "Chosen player has no cards"}
            
            game_state.current_player = chosen_player_id
            
            return {"success": True, "game_state": game_state}
            
        except Exception as e:
            logger.error(f"Error setting current player: {e}")
            return {"success": False, "error": "Failed to set current player"}
    
    def get_game_state(self, game_id: str) -> Optional[GameState]:
        """Get the current game state"""
        return self.games.get(game_id)
    
    def get_player_game_state(self, game_id: str, player_id: str) -> Optional[GameState]:
        """Get game state with player-specific information (own hand visible)"""
        if game_id not in self.games:
            return None
        
        game_state = self.games[game_id]
        
        # Create a copy of the game state for this player
        player_state = GameState(
            game_id=game_state.game_id,
            players=[],
            teams=game_state.teams,
            half_suits=game_state.half_suits,
            ask_history=game_state.ask_history,
            claim_history=game_state.claim_history,
            current_team=game_state.current_team,
            current_player=game_state.current_player,
            status=game_state.status
        )
        
        # Copy players but only show hand for the requesting player
        for player in game_state.players:
            if player.id == player_id:
                player_state.players.append(player)
            else:
                # Hide hand for other players
                other_player = Player(
                    id=player.id,
                    name=player.name,
                    team_id=player.team_id,
                    hand=[],
                    num_cards=player.num_cards
                )
                player_state.players.append(other_player)
        
        return player_state
    
    # Private helper methods
    
    def _validate_ask(self, game_state: GameState, asker_id: str, target_id: str, card: Card) -> Dict[str, Any]:
        """Validate an ask action"""
        # Check game status
        if game_state.status != GameStatus.ACTIVE.value:
            return {"valid": False, "error": "Game not active"}
        
        # Check if it's the asker's turn
        if game_state.current_player != asker_id:
            return {"valid": False, "error": "Not your turn"}
        
        asker = self._get_player(game_state, asker_id)
        target = self._get_player(game_state, target_id)
        
        if not asker:
            return {"valid": False, "error": "Asker not found"}
        if not target:
            return {"valid": False, "error": "Target not found"}
        
        # Check if asker has cards
        if asker.num_cards == 0:
            return {"valid": False, "error": "Cannot ask with no cards"}
        
        # Check if target is on opposing team
        if asker.team_id == target.team_id:
            return {"valid": False, "error": "Cannot ask teammate"}
        
        # Check if asker has a card of the same half suit
        card_half_suit = self.half_suit_definitions.get_half_suit_for_card(card)
        has_half_suit_card = False
        for asker_card in asker.hand:
            if self.half_suit_definitions.get_half_suit_for_card(asker_card) == card_half_suit:
                has_half_suit_card = True
                break
        
        if not has_half_suit_card:
            return {"valid": False, "error": "Must have a card of the same half suit to ask"}
        
        return {"valid": True}
    
    def _validate_claim(self, game_state: GameState, claimant_id: str, 
                       half_suit_id: int, assignments: Dict[str, str]) -> Dict[str, Any]:
        """Validate a claim action"""
        # Check game status
        if game_state.status not in [GameStatus.ACTIVE, GameStatus.WAITING_FOR_COUNTER_CLAIM]:
            return {"valid": False, "error": "Game not in valid state for claims"}
        
        # Check if it's the claimant's team's turn
        claimant = self._get_player(game_state, claimant_id)
        if not claimant:
            return {"valid": False, "error": "Claimant not found"}
        
        if game_state.current_team != claimant.team_id:
            return {"valid": False, "error": "Not your team's turn"}
        
        # Check if half suit is still available
        half_suit = self._get_half_suit(game_state, half_suit_id)
        if not half_suit:
            return {"valid": False, "error": "Half suit not found"}
        
        if half_suit.out_of_play:
            return {"valid": False, "error": "Half suit already claimed"}
        
        # Check if assignments are complete (should have 6 cards)
        if len(assignments) != 6:
            return {"valid": False, "error": "Must assign all 6 cards in half suit"}
        
        # Validate that all assigned cards belong to the half suit
        half_suit_card_ids = {card.unique_id for card in half_suit.cards}
        for card_id in assignments.keys():
            if card_id not in half_suit_card_ids:
                return {"valid": False, "error": f"Card {card_id} not in half suit"}
        
        return {"valid": True}
    
    def _resolve_immediate_claim(self, game_state: GameState, claiming_team: int, 
                               correct: bool) -> Tuple[ClaimOutcome, int]:
        """Resolve a claim that doesn't require counter-claim"""
        if correct:
            return ClaimOutcome.OWN_TEAM_CORRECT, claiming_team
        else:
            return ClaimOutcome.OWN_TEAM_INCORRECT, (2 if claiming_team == 1 else 1)
    
    def _resolve_other_team_claim(self, game_state: GameState, claiming_team: int, 
                                 correct: bool) -> Tuple[ClaimOutcome, int]:
        """Resolve a 'claim for other team' action"""
        if correct:
            return ClaimOutcome.OTHER_TEAM_CORRECT, claiming_team
        else:
            return ClaimOutcome.OTHER_TEAM_INCORRECT, (2 if claiming_team == 1 else 1)
    
    def _finalize_claim(self, game_state: GameState, half_suit_id: int, winning_team: int):
        """Finalize a claim by awarding points and removing cards"""
        # Award point to winning team
        for team in game_state.teams:
            if team.id == winning_team:
                team.score += 1
                break
        
        # Mark half suit as out of play
        half_suit = self._get_half_suit(game_state, half_suit_id)
        half_suit.out_of_play = True
        half_suit.claimed_by = winning_team
        
        # Remove cards from player hands
        for card in half_suit.cards:
            for player in game_state.players:
                for hand_card in player.hand[:]:  # Create copy to avoid modification during iteration
                    if hand_card.unique_id == card.unique_id:
                        player.hand.remove(hand_card)
                        player.num_cards -= 1
                        break
    
    def _choose_next_player(self, game_state: GameState) -> Optional[str]:
        """Choose the next player for the current team"""
        current_team_players = [p for p in game_state.players 
                               if p.team_id == game_state.current_team and p.num_cards > 0]
        
        if not current_team_players:
            # No players with cards on current team - try players with 0 cards for claiming
            current_team_players = [p for p in game_state.players 
                                   if p.team_id == game_state.current_team]
        
        if current_team_players:
            # If current player still has cards and is on current team, keep them
            if (game_state.current_player and 
                any(p.id == game_state.current_player and p.num_cards > 0 
                    for p in current_team_players)):
                return game_state.current_player
            
            # Otherwise, choose first available player
            return current_team_players[0].id
        
        return None
    
    def _is_game_finished(self, game_state: GameState) -> bool:
        """Check if the game is finished (all half suits claimed)"""
        return all(hs.out_of_play for hs in game_state.half_suits)
    
    def _get_player(self, game_state: GameState, player_id: str) -> Optional[Player]:
        """Get a player by ID"""
        for player in game_state.players:
            if player.id == player_id:
                return player
        return None
    
    def _get_half_suit(self, game_state: GameState, half_suit_id: int) -> Optional[HalfSuit]:
        """Get a half suit by ID"""
        for half_suit in game_state.half_suits:
            if half_suit.id == half_suit_id:
                return half_suit
        return None
    
    def get_winning_team(self, game_id: str) -> Optional[int]:
        """Get the winning team ID for a finished game"""
        if game_id not in self.games:
            return None
        
        game_state = self.games[game_id]
        if game_state.status != GameStatus.FINISHED.value:
            return None
        
        # Find team with highest score
        max_score = 0
        winning_team = None
        for team in game_state.teams:
            if team.score > max_score:
                max_score = team.score
                winning_team = team.id
        
        return winning_team
    
    def cleanup_game(self, game_id: str):
        """Clean up game data"""
        if game_id in self.games:
            del self.games[game_id]
        if game_id in self.pending_counter_claims:
            del self.pending_counter_claims[game_id]
        logger.info(f"Cleaned up game {game_id}")

# Global game engine instance
game_engine = GameEngine()