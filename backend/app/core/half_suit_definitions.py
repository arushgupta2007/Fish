from typing import Dict, List, Tuple, Any
from app.models.game_models import Card, HalfSuit

# Half suit definitions based on the specification
HALF_SUIT_DEFINITIONS = {
    0: {
        "name": "2-7 of Spades",
        "ranks": ["2", "3", "4", "5", "6", "7"],
        "suits": ["Spades"]
    },
    1: {
        "name": "9-A of Spades", 
        "ranks": ["9", "10", "J", "Q", "K", "A"],
        "suits": ["Spades"]
    },
    2: {
        "name": "2-7 of Hearts",
        "ranks": ["2", "3", "4", "5", "6", "7"],
        "suits": ["Hearts"]
    },
    3: {
        "name": "9-A of Hearts",
        "ranks": ["9", "10", "J", "Q", "K", "A"],
        "suits": ["Hearts"]
    },
    4: {
        "name": "2-7 of Diamonds",
        "ranks": ["2", "3", "4", "5", "6", "7"],
        "suits": ["Diamonds"]
    },
    5: {
        "name": "9-A of Diamonds",
        "ranks": ["9", "10", "J", "Q", "K", "A"],
        "suits": ["Diamonds"]
    },
    6: {
        "name": "2-7 of Clubs",
        "ranks": ["2", "3", "4", "5", "6", "7"],
        "suits": ["Clubs"]
    },
    7: {
        "name": "9-A of Clubs",
        "ranks": ["9", "10", "J", "Q", "K", "A"],
        "suits": ["Clubs"]
    },
    8: {
        "name": "All 8s + Jokers",
        "ranks": ["8", "Joker"],
        "suits": ["Spades", "Hearts", "Diamonds", "Clubs", "Joker"]
    }
}

def get_half_suit_id(card: Card) -> int:
    """
    Determine which half suit a card belongs to based on its rank and suit.
    
    Args:
        card: The card to classify
        
    Returns:
        The half suit ID (0-8)
    """
    rank = card.rank
    suit = card.suit
    
    # Special case for 8s and Jokers
    if rank == "8" or rank == "Joker":
        return 8
    
    # For other cards, determine by rank and suit
    if rank in ["2", "3", "4", "5", "6", "7"]:
        # Low ranks (2-7)
        if suit == "Spades":
            return 0
        elif suit == "Hearts":
            return 2
        elif suit == "Diamonds":
            return 4
        elif suit == "Clubs":
            return 6
    elif rank in ["9", "10", "J", "Q", "K", "A"]:
        # High ranks (9-A)
        if suit == "Spades":
            return 1
        elif suit == "Hearts":
            return 3
        elif suit == "Diamonds":
            return 5
        elif suit == "Clubs":
            return 7
    
    raise ValueError(f"Cannot determine half suit for card: {rank} of {suit}")

def create_half_suits() -> List[HalfSuit]:
    """
    Create all 9 half suits with their cards.
    
    Returns:
        List of HalfSuit objects
    """
    half_suits = []
    
    for half_suit_id, definition in HALF_SUIT_DEFINITIONS.items():
        cards = []
        
        if half_suit_id == 8:
            # Special case for 8s + Jokers
            # Add all four 8s
            for suit in ["Spades", "Hearts", "Diamonds", "Clubs"]:
                card = Card(
                    rank="8",
                    suit=suit,
                    half_suit_id=half_suit_id,
                    unique_id=f"8{suit[0]}"
                )
                cards.append(card)
            
            # Add two jokers
            for i, joker_id in enumerate(["A", "B"]):
                card = Card(
                    rank="Joker",
                    suit="Joker",
                    half_suit_id=half_suit_id,
                    unique_id=f"Joker-{joker_id}"
                )
                cards.append(card)
        else:
            # Regular half suits
            suit = definition["suits"][0]
            for rank in definition["ranks"]:
                card = Card(
                    rank=rank,
                    suit=suit,
                    half_suit_id=half_suit_id,
                    unique_id=f"{rank}{suit[0]}"
                )
                cards.append(card)
        
        half_suit = HalfSuit(
            id=half_suit_id,
            name=definition["name"],
            cards=cards
        )
        half_suits.append(half_suit)
    
    return half_suits

def get_cards_in_half_suit(half_suit_id: int) -> List[Card]:
    """
    Get all cards that belong to a specific half suit.
    
    Args:
        half_suit_id: The half suit ID (0-8)
        
    Returns:
        List of Card objects in the half suit
    """
    if half_suit_id not in HALF_SUIT_DEFINITIONS:
        raise ValueError(f"Invalid half suit ID: {half_suit_id}")
    
    definition = HALF_SUIT_DEFINITIONS[half_suit_id]
    cards = []
    
    if half_suit_id == 8:
        # Special case for 8s + Jokers
        for suit in ["Spades", "Hearts", "Diamonds", "Clubs"]:
            card = Card(
                rank="8",
                suit=suit,
                half_suit_id=half_suit_id,
                unique_id=f"8{suit[0]}"
            )
            cards.append(card)
        
        for i, joker_id in enumerate(["A", "B"]):
            card = Card(
                rank="Joker",
                suit="Joker",
                half_suit_id=half_suit_id,
                unique_id=f"Joker-{joker_id}"
            )
            cards.append(card)
    else:
        # Regular half suits
        suit = definition["suits"][0]
        for rank in definition["ranks"]:
            card = Card(
                rank=rank,
                suit=suit,
                half_suit_id=half_suit_id,
                unique_id=f"{rank}{suit[0]}"
            )
            cards.append(card)
    
    return cards

def validate_half_suit_assignment(half_suit_id: int, assignments: Dict[str, str]) -> bool:
    """
    Validate that assignments match the expected cards for a half suit.
    
    Args:
        half_suit_id: The half suit ID being claimed
        assignments: Dictionary mapping card unique_id to player_id
        
    Returns:
        True if assignments are valid for this half suit
    """
    if half_suit_id not in HALF_SUIT_DEFINITIONS:
        return False
    
    expected_cards = get_cards_in_half_suit(half_suit_id)
    expected_unique_ids = {card.unique_id for card in expected_cards}
    assignment_unique_ids = set(assignments.keys())
    
    return expected_unique_ids == assignment_unique_ids

def get_half_suit_name(half_suit_id: int) -> str:
    """
    Get the display name for a half suit.
    
    Args:
        half_suit_id: The half suit ID (0-8)
        
    Returns:
        The half suit name
    """
    if half_suit_id not in HALF_SUIT_DEFINITIONS:
        raise ValueError(f"Invalid half suit ID: {half_suit_id}")
    
    return HALF_SUIT_DEFINITIONS[half_suit_id]["name"]

def cards_belong_to_same_half_suit(cards: List[Card]) -> bool:
    """
    Check if all cards belong to the same half suit.
    
    Args:
        cards: List of cards to check
        
    Returns:
        True if all cards belong to the same half suit
    """
    if not cards:
        return False
    
    first_half_suit = cards[0].half_suit_id
    return all(card.half_suit_id == first_half_suit for card in cards)

def get_card_display_name(card: Card) -> str:
    """
    Get a human-readable display name for a card.
    
    Args:
        card: The card to display
        
    Returns:
        Display name like "2 of Spades" or "Joker"
    """
    if card.rank == "Joker":
        return "Joker"
    
    # Handle face cards
    rank_names = {
        "J": "Jack",
        "Q": "Queen", 
        "K": "King",
        "A": "Ace"
    }
    
    rank_display = rank_names.get(card.rank, card.rank)
    
    return f"{rank_display} of {card.suit}"

def get_half_suit_progress() -> Dict[int, Dict[str, Any]]:
    """
    Get information about all half suits for UI display.
    
    Returns:
        Dictionary with half suit info including cards and display names
    """
    progress = {}
    
    for half_suit_id, definition in HALF_SUIT_DEFINITIONS.items():
        cards = get_cards_in_half_suit(half_suit_id)
        progress[half_suit_id] = {
            "name": definition["name"],
            "cards": [get_card_display_name(card) for card in cards],
            "unique_ids": [card.unique_id for card in cards],
            "total_cards": len(cards)
        }
    
    return progress