from typing import List, Dict

from ..models.composite import Card, HalfSuit
from ..models.enums import CardRank, CardSuit, HalfSuits


def create_all_cards() -> List[Card]:
    """Returns a list of all cards in the 54 card deck"""
    cards = []
    for rank in CardRank:
        if rank != CardRank.JOKER and rank != CardRank.CUT:
            for suit in CardSuit:
                if suit != CardSuit.JOKER:
                    cards.append(Card(rank=rank, suit=suit))
        else:
            cards.append(Card(rank=rank, suit=CardSuit.JOKER))
    return cards

def create_half_suits() -> Dict[HalfSuits, HalfSuit]:
    """Returns a dictionary of all half suits"""
    return { hs: HalfSuit(half_suit=hs) for hs in HalfSuits }


