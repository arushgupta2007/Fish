from typing import Dict, List, Optional, NamedTuple, Any
import logging

from ..models.game_models import GameState, Player, HalfSuit, Card

logger = logging.getLogger(__name__)


from ..models.enums import ClaimOutcome


class ClaimResult(NamedTuple):
    """Result of a claim validation."""
    outcome: ClaimOutcome
    winning_team: int
    requires_counter_claim: bool = False
    is_correct: bool = False


class ClaimValidator:
    """
    Validates claims and counter-claims according to Half Suit game rules.
    
    Handles all claim scenarios:
    1. All 6 cards with claiming team
    2. All 6 cards with opposing team (requires counter-claim)
    3. Cards split between teams (auto-incorrect unless "claim for other team")
    4. "Claim for other team" (special case)
    """
    
    def __init__(self):
        """Initialize the claim validator."""
        logger.info("ClaimValidator initialized")
    
    def validate_claim(self, game_state: GameState, claimant_id: str | None, half_suit_id: int, 
                      assignments: Dict[str, str], claim_for_other_team: bool = False) -> ClaimResult:
        """
        Validate a claim and determine the outcome.
        
        Args:
            game_state: Current game state
            claimant_id: ID of the player making the claim
            half_suit_id: ID of the half suit being claimed
            assignments: Dictionary mapping card unique_id to player_id
            claim_for_other_team: Whether this is a "claim for other team"
            
        Returns:
            ClaimResult with outcome and winning team
        """
        try:
            # Find the claimant and their team
            if claimant_id is None:
                raise ValueError("claimant_id required")
            claimant = self._find_player(game_state, claimant_id)
            claimant_team = claimant.team_id
            opposing_team = 2 if claimant_team == 1 else 1
            
            # Get the half suit being claimed
            half_suit = self._find_half_suit(game_state, half_suit_id)
            
            # Get actual card locations
            actual_locations = self._get_actual_card_locations(game_state, half_suit)
            
            # Analyze card distribution
            card_distribution = self._analyze_card_distribution(actual_locations, claimant_team)
            
            logger.info(f"Claim validation - Claimant: {claimant.name}, Team: {claimant_team}, "
                       f"Half suit: {half_suit.name}, For other team: {claim_for_other_team}")
            logger.info(f"Card distribution - Claiming team: {card_distribution['claiming_team']}, "
                       f"Opposing team: {card_distribution['opposing_team']}")
            
            # Handle different claim scenarios
            if claim_for_other_team:
                return self._handle_claim_for_other_team(
                    assignments, actual_locations, claimant_team, opposing_team
                )
            elif card_distribution['all_with_claiming_team']:
                return self._handle_all_cards_with_claiming_team(
                    assignments, actual_locations, claimant_team
                )
            elif card_distribution['all_with_opposing_team']:
                return self._handle_all_cards_with_opposing_team(
                    assignments, actual_locations, claimant_team, opposing_team
                )
            else:
                return self._handle_split_cards(claimant_team, opposing_team)
                
        except Exception as e:
            logger.error(f"Error validating claim: {e}")
            # Default to incorrect claim for claimant's team
            return ClaimResult(
                outcome=ClaimOutcome.OWN_TEAM_INCORRECT,
                winning_team=2 if claimant_team == 1 else 1,
                requires_counter_claim=False,
                is_correct=False
            )
    
    def validate_counter_claim(self, game_state: GameState, counter_claimant_id: str, 
                              half_suit_id: int, assignments: Dict[str, str]) -> ClaimResult:
        """
        Validate a counter-claim.
        
        Args:
            game_state: Current game state
            counter_claimant_id: ID of the player making the counter-claim
            half_suit_id: ID of the half suit being counter-claimed
            assignments: Dictionary mapping card unique_id to player_id
            
        Returns:
            ClaimResult with counter-claim outcome
        """
        try:
            # Find the counter-claimant and their team
            counter_claimant = self._find_player(game_state, counter_claimant_id)
            counter_team = counter_claimant.team_id
            original_team = 2 if counter_team == 1 else 1
            
            # Get the half suit
            half_suit = self._find_half_suit(game_state, half_suit_id)
            
            # Get actual card locations
            actual_locations = self._get_actual_card_locations(game_state, half_suit)
            
            # Validate that all cards are actually with the counter-claiming team
            cards_with_counter_team = sum(1 for loc in actual_locations.values() if loc['team'] == counter_team)
            
            if cards_with_counter_team != 6:
                logger.warning(f"Counter-claim attempted but not all cards with counter-claiming team")
                return ClaimResult(
                    outcome=ClaimOutcome.COUNTER_INCORRECT,
                    winning_team=original_team,
                    requires_counter_claim=False,
                    is_correct=False
                )
            
            # Check if counter-claim assignments are correct
            is_correct = self._check_assignments_correctness(assignments, actual_locations)
            
            if is_correct:
                logger.info(f"Counter-claim correct by {counter_claimant.name}")
                return ClaimResult(
                    outcome=ClaimOutcome.COUNTER_CORRECT,
                    winning_team=counter_team,
                    requires_counter_claim=False,
                    is_correct=True
                )
            else:
                logger.info(f"Counter-claim incorrect by {counter_claimant.name}")
                return ClaimResult(
                    outcome=ClaimOutcome.COUNTER_INCORRECT,
                    winning_team=original_team,
                    requires_counter_claim=False,
                    is_correct=False
                )
                
        except Exception as e:
            logger.error(f"Error validating counter-claim: {e}")
            # Default to incorrect counter-claim
            return ClaimResult(
                outcome=ClaimOutcome.COUNTER_INCORRECT,
                winning_team=2 if counter_team == 1 else 1,
                requires_counter_claim=False,
                is_correct=False
            )
    
    def _find_player(self, game_state: GameState, player_id: str) -> Player:
        """Find a player by ID."""
        for player in game_state.players:
            if player.id == player_id:
                return player
        raise ValueError(f"Player {player_id} not found")
    
    def _find_half_suit(self, game_state: GameState, half_suit_id: int) -> HalfSuit:
        """Find a half suit by ID."""
        for half_suit in game_state.half_suits:
            if half_suit.id == half_suit_id:
                return half_suit
        raise ValueError(f"Half suit {half_suit_id} not found")
    
    def _get_actual_card_locations(self, game_state: GameState, half_suit: HalfSuit) -> Dict[str, Dict[str, Any]]:
        """
        Get the actual locations of all cards in a half suit.
        
        Args:
            game_state: Current game state
            half_suit: Half suit to analyze
            
        Returns:
            Dictionary mapping card unique_id to location info
        """
        locations = {}
        
        for card in half_suit.cards:
            # Find which player has this card
            for player in game_state.players:
                if any(c.unique_id == card.unique_id for c in player.hand):
                    locations[card.unique_id] = {
                        'player_id': player.id,
                        'player_name': player.name,
                        'team': player.team_id
                    }
                    break
            else:
                # Card not found in any player's hand (shouldn't happen in normal play)
                logger.warning(f"Card {card.unique_id} not found in any player's hand")
                locations[card.unique_id] = {
                    'player_id': None,
                    'player_name': None,
                    'team': None
                }
        
        return locations
    
    def _analyze_card_distribution(self, actual_locations: Dict[str, Dict[str, Any]], 
                                 claiming_team: int) -> Dict[str, Any]:
        """
        Analyze how cards are distributed between teams.
        
        Args:
            actual_locations: Card locations from _get_actual_card_locations
            claiming_team: Team ID of the claiming team
            
        Returns:
            Dictionary with distribution analysis
        """
        opposing_team = 2 if claiming_team == 1 else 1
        
        cards_with_claiming_team = 0
        cards_with_opposing_team = 0
        
        for location in actual_locations.values():
            if location['team'] == claiming_team:
                cards_with_claiming_team += 1
            elif location['team'] == opposing_team:
                cards_with_opposing_team += 1
        
        return {
            'claiming_team': cards_with_claiming_team,
            'opposing_team': cards_with_opposing_team,
            'all_with_claiming_team': cards_with_claiming_team == 6,
            'all_with_opposing_team': cards_with_opposing_team == 6,
            'split_between_teams': cards_with_claiming_team > 0 and cards_with_opposing_team > 0
        }
    
    def _check_assignments_correctness(self, assignments: Dict[str, str], 
                                     actual_locations: Dict[str, Dict[str, Any]]) -> bool:
        """
        Check if the claimed assignments match the actual card locations.
        
        Args:
            assignments: Claimed assignments (card_id -> player_id)
            actual_locations: Actual card locations
            
        Returns:
            True if assignments are correct
        """
        for card_id, claimed_player_id in assignments.items():
            if card_id not in actual_locations:
                logger.warning(f"Card {card_id} not found in actual locations")
                return False
            
            actual_player_id = actual_locations[card_id]['player_id']
            if actual_player_id != claimed_player_id:
                logger.debug(f"Incorrect assignment for {card_id}: claimed {claimed_player_id}, actual {actual_player_id}")
                return False
        
        return True
    
    def _handle_all_cards_with_claiming_team(self, assignments: Dict[str, str], 
                                           actual_locations: Dict[str, Dict[str, Any]], 
                                           claiming_team: int) -> ClaimResult:
        """
        Handle case where all 6 cards are with the claiming team.
        
        Args:
            assignments: Claimed assignments
            actual_locations: Actual card locations
            claiming_team: Team making the claim
            
        Returns:
            ClaimResult
        """
        is_correct = self._check_assignments_correctness(assignments, actual_locations)
        
        if is_correct:
            logger.info("Claim correct - all cards with claiming team")
            return ClaimResult(
                outcome=ClaimOutcome.OWN_TEAM_CORRECT,
                winning_team=claiming_team,
                requires_counter_claim=False,
                is_correct=True
            )
        else:
            opposing_team = 2 if claiming_team == 1 else 1
            logger.info("Claim incorrect - all cards with claiming team but wrong assignments")
            return ClaimResult(
                outcome=ClaimOutcome.OWN_TEAM_INCORRECT,
                winning_team=opposing_team,
                requires_counter_claim=False,
                is_correct=False
            )
    
    def _handle_all_cards_with_opposing_team(self, assignments: Dict[str, str], 
                                           actual_locations: Dict[str, Dict[str, Any]], 
                                           claiming_team: int, opposing_team: int) -> ClaimResult:
        """
        Handle case where all 6 cards are with the opposing team.
        This requires a counter-claim from the opposing team.
        
        Args:
            assignments: Claimed assignments
            actual_locations: Actual card locations
            claiming_team: Team making the claim
            opposing_team: Opposing team
            
        Returns:
            ClaimResult indicating counter-claim is required
        """
        logger.info("All cards with opposing team - counter-claim required")
        return ClaimResult(
            outcome=ClaimOutcome.AWAITING_COUNTER,  # Special status for pending counter-claim
            winning_team=0,  # TBD based on counter-claim
            requires_counter_claim=True,
            is_correct=False
        )
    
    def _handle_split_cards(self, claiming_team: int, opposing_team: int) -> ClaimResult:
        """
        Handle case where cards are split between teams.
        This is automatically incorrect for regular claims.
        
        Args:
            claiming_team: Team making the claim
            opposing_team: Opposing team
            
        Returns:
            ClaimResult with automatic incorrect outcome
        """
        logger.info("Cards split between teams - claim automatically incorrect")
        return ClaimResult(
            outcome=ClaimOutcome.SPLIT_AUTO_INCORRECT,
            winning_team=opposing_team,
            requires_counter_claim=False,
            is_correct=False
        )
    
    def _handle_claim_for_other_team(self, assignments: Dict[str, str], 
                                   actual_locations: Dict[str, Dict[str, Any]], 
                                   claiming_team: int, opposing_team: int) -> ClaimResult:
        """
        Handle "claim for other team" scenario.
        
        Args:
            assignments: Claimed assignments (should be for opposing team players)
            actual_locations: Actual card locations
            claiming_team: Team making the claim
            opposing_team: Opposing team
            
        Returns:
            ClaimResult
        """
        # Validate that all assignments are for opposing team players
        # This should be validated by the calling code, but we'll check here too
        
        # Check if the assignments are correct
        is_correct = self._check_assignments_correctness(assignments, actual_locations)
        
        if is_correct:
            logger.info("Claim for other team correct")
            return ClaimResult(
                outcome=ClaimOutcome.OTHER_TEAM_CORRECT,
                winning_team=claiming_team,  # Claiming team wins even though they claimed for other team
                requires_counter_claim=False,
                is_correct=True
            )
        else:
            logger.info("Claim for other team incorrect")
            return ClaimResult(
                outcome=ClaimOutcome.OTHER_TEAM_INCORRECT,
                winning_team=opposing_team,
                requires_counter_claim=False,
                is_correct=False
            )
    
    def get_claim_requirements(self, game_state: GameState, half_suit_id: int) -> Dict[str, Any]:
        """
        Get requirements and options for claiming a specific half suit.
        
        Args:
            game_state: Current game state
            half_suit_id: ID of the half suit to analyze
            
        Returns:
            Dictionary with claim requirements and options
        """
        try:
            half_suit = self._find_half_suit(game_state, half_suit_id)
            
            # Get all players who might have cards from this half suit
            possible_holders = []
            for player in game_state.players:
                if player.num_cards > 0:
                    possible_holders.append({
                        'player_id': player.id,
                        'player_name': player.name,
                        'team': player.team_id
                    })
            
            return {
                'half_suit_id': half_suit_id,
                'half_suit_name': half_suit.name,
                'cards': [
                    {
                        'unique_id': card.unique_id,
                        'rank': card.rank,
                        'suit': card.suit,
                        'display_name': f"{card.rank} of {card.suit}"
                    }
                    for card in half_suit.cards
                ],
                'possible_holders': possible_holders,
                'claim_options': [
                    'regular_claim',
                    'claim_for_other_team'
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting claim requirements: {e}")
            return {
                'error': f"Failed to get claim requirements: {e}"
            }
    
    def validate_claim_assignments(self, game_state: GameState, half_suit_id: int, 
                                 assignments: Dict[str, str], claim_for_other_team: bool = False) -> Dict[str, Any]:
        """
        Validate claim assignments without actually processing the claim.
        
        Args:
            game_state: Current game state
            half_suit_id: ID of the half suit being claimed
            assignments: Dictionary mapping card unique_id to player_id
            claim_for_other_team: Whether this is a "claim for other team"
            
        Returns:
            Dictionary with validation results
        """
        try:
            half_suit = self._find_half_suit(game_state, half_suit_id)
            
            errors = []
            warnings = []
            
            # Check if all cards are assigned
            if len(assignments) != 6:
                errors.append(f"Must assign all 6 cards. Currently assigned: {len(assignments)}")
            
            # Check if all card IDs are valid
            valid_card_ids = {card.unique_id for card in half_suit.cards}
            for card_id in assignments.keys():
                if card_id not in valid_card_ids:
                    errors.append(f"Invalid card ID: {card_id}")
            
            # Check if all player IDs are valid
            valid_player_ids = {player.id for player in game_state.players}
            for player_id in assignments.values():
                if player_id not in valid_player_ids:
                    errors.append(f"Invalid player ID: {player_id}")
            
            # If claim for other team, check that all assigned players are on opposing team
            if claim_for_other_team and not errors:
                # This would need the claimant ID to determine opposing team
                # For now, just add a warning
                warnings.append("Claiming for other team - ensure all assignments are for opposing team players")
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }
            
        except Exception as e:
            logger.error(f"Error validating claim assignments: {e}")
            return {
                'valid': False,
                'errors': [f"Validation error: {e}"],
                'warnings': []
            }
