import random
from typing import List, Dict
from app.models.enums import CardRank, CardSuit
from app.models.game_models import Card, Player
from app.core.half_suit_definitions import get_half_suit_id

class DeckManager:
    """
    Manages deck creation, shuffling, and dealing for the Half Suit game.
    """
    
    def __init__(self):
        self.deck: List[Card] = []
        self.dealt_cards: Dict[str, List[Card]] = {}  # player_id -> cards
    
    def create_deck(self) -> List[Card]:
        """
        Create a standard 52-card deck plus 2 jokers (54 total cards).
        
        Returns:
            List of all cards in the deck
        """
        deck = []
        suits = [CardSuit.SPADES, CardSuit.HEARTS, CardSuit.DIAMONDS, CardSuit.CLUBS]
        ranks = [
            CardRank.TWO,
            CardRank.THREE,
            CardRank.FOUR,
            CardRank.FIVE,
            CardRank.SIX,
            CardRank.SEVEN,
            CardRank.NINE,
            CardRank.TEN,
            CardRank.JACK,
            CardRank.QUEEN,
            CardRank.KING,
            CardRank.ACE
        ]
        
        # Create standard 52 cards
        for suit in suits:
            for rank in ranks:
                # Create unique ID for the card
                unique_id = f"{rank}{suit[0]}"
                
                card = Card(
                    rank=rank,
                    suit=suit,
                    half_suit_id=get_half_suit_id(Card(rank=rank, suit=suit, half_suit_id=0, unique_id="")),
                    unique_id=unique_id
                )
                deck.append(card)
        
        for suit in suits:
            deck.append(Card(
                rank=CardRank.EIGHT,
                suit=CardSuit.JOKER,
                half_suit_id=8,
                unique_id=f"{CardRank.EIGHT}{CardSuit.JOKER}"
            ))

        # Add joker, cut
        deck.append(Card(
            rank=CardRank.JOKER,
            suit=CardSuit.JOKER,
            half_suit_id=8,
            unique_id=f"{CardRank.JOKER}{CardSuit.JOKER}"
        ))
        deck.append(Card(
            rank=CardRank.CUT,
            suit=CardSuit.JOKER,
            half_suit_id=8,
            unique_id=f"{CardRank.CUT}{CardSuit.JOKER}"
        ))

        # for _, joker_id in enumerate(["A", "B"]):
        #     card = Card(
        #         rank="Joker",
        #         suit="Joker",
        #         half_suit_id=8,  # 8s + Jokers half suit
        #         unique_id=f"Joker-{joker_id}"
        #     )
        #     deck.append(card)
        
        self.deck = deck
        return deck
    
    def shuffle_deck(self) -> None:
        """
        Shuffle the deck randomly.
        """
        if not self.deck:
            self.create_deck()
        
        random.shuffle(self.deck)
    
    def deal_cards(self, players: List[Player]) -> Dict[str, List[Card]]:
        """
        Deal 9 cards to each of the 6 players.
        
        Args:
            players: List of 6 players
            
        Returns:
            Dictionary mapping player_id to their dealt cards
            
        Raises:
            ValueError: If not exactly 6 players or deck not ready
        """
        if len(players) != 6:
            raise ValueError(f"Must have exactly 6 players, got {len(players)}")
        
        if len(self.deck) != 54:
            raise ValueError(f"Deck must have 54 cards, got {len(self.deck)}")
        
        # Shuffle before dealing
        self.shuffle_deck()
        
        dealt_cards = {}
        card_index = 0
        
        # Deal 9 cards to each player
        for player in players:
            player_cards = []
            for _ in range(9):
                if card_index >= len(self.deck):
                    raise ValueError("Not enough cards in deck")
                
                card = self.deck[card_index]
                player_cards.append(card)
                card_index += 1
            
            dealt_cards[player.id] = player_cards
        
        # Verify all cards were dealt
        if card_index != 54:
            raise ValueError(f"Expected to deal 54 cards, dealt {card_index}")
        
        self.dealt_cards = dealt_cards
        return dealt_cards
    
    def get_player_cards(self, player_id: str) -> List[Card]:
        """
        Get the cards dealt to a specific player.
        
        Args:
            player_id: The player's ID
            
        Returns:
            List of cards for the player
        """
        return self.dealt_cards.get(player_id, [])
    
    def find_card_holder(self, card_unique_id: str) -> str:
        """
        Find which player holds a specific card.
        
        Args:
            card_unique_id: The unique ID of the card to find
            
        Returns:
            The player ID who holds the card, or empty string if not found
        """
        for player_id, cards in self.dealt_cards.items():
            for card in cards:
                if card.unique_id == card_unique_id:
                    return player_id
        return ""
    
    def get_card_by_unique_id(self, unique_id: str) -> Card:
        """
        Get a card by its unique ID from the original deck.
        
        Args:
            unique_id: The unique ID of the card
            
        Returns:
            The card object
            
        Raises:
            ValueError: If card not found
        """
        for card in self.deck:
            if card.unique_id == unique_id:
                return card
        
        raise ValueError(f"Card with unique_id '{unique_id}' not found in deck")
    
    def transfer_card(self, card_unique_id: str, from_player_id: str, to_player_id: str) -> bool:
        """
        Transfer a card from one player to another (for ask actions).
        
        Args:
            card_unique_id: The unique ID of the card to transfer
            from_player_id: The player giving the card
            to_player_id: The player receiving the card
            
        Returns:
            True if transfer was successful, False otherwise
        """
        # Find the card in the from_player's hand
        from_cards = self.dealt_cards.get(from_player_id, [])
        card_to_transfer = None
        
        for i, card in enumerate(from_cards):
            if card.unique_id == card_unique_id:
                card_to_transfer = from_cards.pop(i)
                break
        
        if not card_to_transfer:
            return False
        
        # Add the card to the to_player's hand
        if to_player_id not in self.dealt_cards:
            self.dealt_cards[to_player_id] = []
        
        self.dealt_cards[to_player_id].append(card_to_transfer)
        return True
    
    def remove_cards_from_play(self, card_unique_ids: List[str]) -> bool:
        """
        Remove cards from all players' hands (for claimed half suits).
        
        Args:
            card_unique_ids: List of unique IDs of cards to remove
            
        Returns:
            True if all cards were found and removed
        """
        cards_found = 0
        
        for player_id in self.dealt_cards:
            cards_to_remove = []
            for i, card in enumerate(self.dealt_cards[player_id]):
                if card.unique_id in card_unique_ids:
                    cards_to_remove.append(i)
                    cards_found += 1
            
            # Remove cards in reverse order to maintain indices
            for i in reversed(cards_to_remove):
                self.dealt_cards[player_id].pop(i)
        
        return cards_found == len(card_unique_ids)
    
    def get_player_card_count(self, player_id: str) -> int:
        """
        Get the number of cards a player has.
        
        Args:
            player_id: The player's ID
            
        Returns:
            Number of cards the player has
        """
        return len(self.dealt_cards.get(player_id, []))
    
    def player_has_card(self, player_id: str, card_unique_id: str) -> bool:
        """
        Check if a player has a specific card.
        
        Args:
            player_id: The player's ID
            card_unique_id: The unique ID of the card
            
        Returns:
            True if the player has the card
        """
        player_cards = self.dealt_cards.get(player_id, [])
        return any(card.unique_id == card_unique_id for card in player_cards)
    
    def player_has_half_suit_card(self, player_id: str, half_suit_id: int) -> bool:
        """
        Check if a player has any card from a specific half suit.
        
        Args:
            player_id: The player's ID
            half_suit_id: The half suit ID to check
            
        Returns:
            True if the player has at least one card from the half suit
        """
        player_cards = self.dealt_cards.get(player_id, [])
        return any(card.half_suit_id == half_suit_id for card in player_cards)
    
    def get_half_suit_cards_in_play(self, half_suit_id: int) -> List[Card]:
        """
        Get all cards from a specific half suit that are still in play.
        
        Args:
            half_suit_id: The half suit ID
            
        Returns:
            List of cards from the half suit that are still in players' hands
        """
        cards_in_play = []
        for player_cards in self.dealt_cards.values():
            for card in player_cards:
                if card.half_suit_id == half_suit_id:
                    cards_in_play.append(card)
        return cards_in_play
    
    def get_half_suit_distribution(self, half_suit_id: int) -> Dict[str, List[Card]]:
        """
        Get the distribution of cards from a specific half suit across players.
        
        Args:
            half_suit_id: The half suit ID
            
        Returns:
            Dictionary mapping player_id to their cards from the half suit
        """
        distribution = {}
        for player_id, player_cards in self.dealt_cards.items():
            half_suit_cards = [card for card in player_cards if card.half_suit_id == half_suit_id]
            if half_suit_cards:
                distribution[player_id] = half_suit_cards
        return distribution
    
    def validate_half_suit_claim(self, half_suit_id: int, assignments: Dict[str, str]) -> Dict[str, bool]:
        """
        Validate a claim by checking if the assignments match reality.
        
        Args:
            half_suit_id: The half suit being claimed
            assignments: Dictionary mapping card_unique_id to player_id
            
        Returns:
            Dictionary with validation results:
            - 'valid': True if all assignments are correct
            - 'cards_exist': True if all claimed cards exist in the half suit
            - 'assignments_correct': True if all assignments match actual holders
        """
        # Get all cards from the half suit from the original deck
        half_suit_cards = [card for card in self.deck if card.half_suit_id == half_suit_id]
        
        if len(half_suit_cards) != 6:
            return {'valid': False, 'cards_exist': False, 'assignments_correct': False}
        
        # Check if all claimed cards exist in the half suit
        half_suit_unique_ids = {card.unique_id for card in half_suit_cards}
        claimed_unique_ids = set(assignments.keys())
        
        if claimed_unique_ids != half_suit_unique_ids:
            return {'valid': False, 'cards_exist': False, 'assignments_correct': False}
        
        # Check if assignments match actual card holders
        assignments_correct = True
        for card_unique_id, claimed_player in assignments.items():
            actual_player = self.find_card_holder(card_unique_id)
            if actual_player != claimed_player:
                assignments_correct = False
                break
        
        return {
            'valid': assignments_correct,
            'cards_exist': True,
            'assignments_correct': assignments_correct
        }
    
    def get_cards_by_team(self, half_suit_id: int, team_players: List[str]) -> List[Card]:
        """
        Get cards from a half suit that belong to a specific team.
        
        Args:
            half_suit_id: The half suit ID
            team_players: List of player IDs on the team
            
        Returns:
            List of cards from the half suit held by the team
        """
        team_cards = []
        for player_id in team_players:
            player_cards = self.dealt_cards.get(player_id, [])
            for card in player_cards:
                if card.half_suit_id == half_suit_id:
                    team_cards.append(card)
        return team_cards
    
    def is_half_suit_with_team(self, half_suit_id: int, team_players: List[str]) -> bool:
        """
        Check if all cards from a half suit are held by a specific team.
        
        Args:
            half_suit_id: The half suit ID
            team_players: List of player IDs on the team
            
        Returns:
            True if all 6 cards from the half suit are held by the team
        """
        distribution = self.get_half_suit_distribution(half_suit_id)
        
        # Check if all players holding cards from this half suit are on the team
        for player_id in distribution.keys():
            if player_id not in team_players:
                return False
        
        # Check if we have all 6 cards
        total_cards = sum(len(cards) for cards in distribution.values())
        return total_cards == 6
    
    def is_half_suit_split(self, half_suit_id: int, team1_players: List[str], team2_players: List[str]) -> bool:
        """
        Check if a half suit is split between two teams.
        
        Args:
            half_suit_id: The half suit ID
            team1_players: List of player IDs on team 1
            team2_players: List of player IDs on team 2
            
        Returns:
            True if the half suit is split between teams
        """
        team1_has_cards = bool(self.get_cards_by_team(half_suit_id, team1_players))
        team2_has_cards = bool(self.get_cards_by_team(half_suit_id, team2_players))
        
        return team1_has_cards and team2_has_cards
    
    def reset_deck(self) -> None:
        """
        Reset the deck manager to initial state.
        """
        self.deck = []
        self.dealt_cards = {}
    
    def get_deck_status(self) -> Dict[str, int]:
        """
        Get status information about the deck.
        
        Returns:
            Dictionary with deck status information
        """
        total_cards_dealt = sum(len(cards) for cards in self.dealt_cards.values())
        
        return {
            'total_cards_in_deck': len(self.deck),
            'total_cards_dealt': total_cards_dealt,
            'players_with_cards': len(self.dealt_cards),
            'cards_remaining_in_play': total_cards_dealt
        }
