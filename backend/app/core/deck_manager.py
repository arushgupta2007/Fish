import random
from typing import List, Dict
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
        suits = ["Spades", "Hearts", "Diamonds", "Clubs"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        
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
        
        # Add 2 jokers
        for i, joker_id in enumerate(["A", "B"]):
            card = Card(
                rank="Joker",
                suit="Joker",
                half_suit_id=8,  # 8s + Jokers half suit
                unique_id=f"Joker-{joker_id}"
            )
            deck.append(card)
        
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
        player_cards = self.dealt_