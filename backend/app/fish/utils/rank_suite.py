from typing import Optional, Tuple

from ..models.enums import CardRank, CardSuit, HalfSuits


def valid_card(rank: CardRank, suit: CardSuit) -> bool:
    """Checks if card is valid"""
    if rank == CardRank.JOKER or rank == CardRank.CUT:
        return suit == CardSuit.JOKER
    return suit != CardSuit.JOKER

def get_half_suit(rank: CardRank, suit: CardSuit) -> HalfSuits:
    """Given rank and suit, returns the corresponding HalfSuit. Assumes card is valid."""
    match suit:
        case CardSuit.JOKER:
            return HalfSuits.SPECIAL
        case CardSuit.SPADES:
            if rank == CardRank.EIGHT:
                return HalfSuits.SPECIAL
            if rank.is_lower:
                return HalfSuits.SPADES_LOW
            return HalfSuits.SPADES_HIGH
        case CardSuit.HEARTS:
            if rank == CardRank.EIGHT:
                return HalfSuits.SPECIAL
            if rank.is_lower:
                return HalfSuits.HEARTS_LOW
            return HalfSuits.HEARTS_HIGH
        case CardSuit.DIAMONDS:
            if rank == CardRank.EIGHT:
                return HalfSuits.SPECIAL
            if rank.is_lower:
                return HalfSuits.DIAMONDS_LOW
            return HalfSuits.DIAMONDS_HIGH
        case CardSuit.CLUBS:
            if rank == CardRank.EIGHT:
                return HalfSuits.SPECIAL
            if rank.is_lower:
                return HalfSuits.CLUBS_LOW
            return HalfSuits.CLUBS_HIGH

def unique_card_id(rank: CardRank, suit: CardSuit) -> str:
    """Returns a unique id for each card. Assumes card is valid"""
    return f"{rank.value}{suit.value[0]}"

def id_to_rank_suit(id: str) -> Optional[Tuple[CardRank, CardSuit]]:
    """
    Convert Card Id to a Tuple of Card Rank and Card Suit

    Returns None if id is invalid
    """
    rank, suit = id[:-1], id[-1]
    r = list(filter(lambda c : c == rank, CardRank))
    s = list(filter(lambda c : c[0] == suit, CardSuit))
    if len(r) != 1 or len(s) != 1:
        return None
    return (r[0], s[0])

