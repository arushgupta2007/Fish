from typing import List, Optional, Any, Dict
from pydantic import BaseModel, model_validator
from pydantic.fields import Field

from .enums import CardRank, CardSuit, HalfSuits, TeamId, ClaimScenario, GameHandCompleteTurnTransfer, ApiEvent
from ..utils.rank_suite import valid_card, get_half_suit, unique_card_id

class Card(BaseModel):
    """Card Class"""
    rank: CardRank
    suit: CardSuit

    @model_validator(mode="after")
    def check_valid_card(self):
        if not valid_card(self.rank, self.suit):
            raise ValueError("Invalid Card: Rank and Suit are incompatible")
        return self
    
    @property
    def is_special(self) -> bool:
        """Returns if the card is part of special half suit"""
        return self.rank.is_special

    @property
    def half_suit(self) -> HalfSuits:
        """Returns the half suit the card belongs to"""
        return get_half_suit(self.rank, self.suit)

    @property
    def id(self) -> str:
        """Returns a unique id for the card"""
        return unique_card_id(self.rank, self.suit)

class Player(BaseModel):
    """Player Class"""
    id: str
    name: str
    team: TeamId
    hand: List[Card] = Field(default_factory=list)

    @property
    def num_cards(self):
        """Returns the number of cards with the player"""
        return len(self.hand)

    def has_card(self, card: Card) -> bool:
        """Checks if the player has a particular card"""
        return any(c.id == card.id for c in self.hand)

    def has_half_suit(self, hs: HalfSuits) -> bool:
        """Checks if the player has a particular half suit"""
        return any(c.half_suit == hs for c in self.hand)

    def remove_card(self, card: Card):
        """Removes a card from the player's hand"""
        self.hand = list(filter(lambda c: c.id != card.id, self.hand))

    def add_card(self, card: Card, check=True):
        """Adds a card from the player's hand"""
        if not check or not self.has_card(card):
            self.hand.append(card)

class Team(BaseModel):
    """Team Class"""
    id: TeamId
    name: str
    score: int = Field(ge=0, le=9)
    players: List[str] = Field(default_factory=list)

class HalfSuit(BaseModel):
    """Half Suit Class"""
    half_suit: HalfSuits
    claimed: bool = False
    claimed_team: Optional[TeamId] = None
    claimed_player: Optional[str] = None
    claimed_success: Optional[bool] = None

class AskRecord(BaseModel):
    """Record Ask Queries"""
    turn_cnt: int = Field(ge=1)
    asker: str
    respondant: str
    card: Card
    success: bool

class ClaimRecord(BaseModel):
    """Record Claims"""
    turn_cnt: int = Field(ge=0)
    team: TeamId
    claimant: str
    half_suit: HalfSuits
    is_for_other: bool
    is_counter: bool
    countered: Optional[bool] = None    # Was this claim countered by the opposing team
    success: bool
    scenario: ClaimScenario

    @property
    def point_to(self) -> Optional[TeamId]:
        if not self.scenario.point_changed:
            return None
        if self.success:
            return self.team
        return self.team.opp

class GameSettings(BaseModel):
    """Game Settings"""
    min_players: int = 6
    max_players: int = 9

    allow_bluffs: bool = True

    time_per_move: Optional[int] = None        # In ms     TODO: Implement this
    time_counter: Optional[int] = None         # In ms     TODO: Implement this

    hand_complete_turn_transfer: GameHandCompleteTurnTransfer = GameHandCompleteTurnTransfer.RANDOM
    visible_ask_history: Optional[int] = 1


class OperationResult(BaseModel):
    success: bool = True
    result: Any
    error: Optional[str]


class WebSocketMessageGeneral(BaseModel):
    type: ApiEvent

class WebSocketMessageInitialConnectionData(BaseModel):
    game_id: str
    player_id: str

class WebSocketMessageInitialConnection(BaseModel):
    type: ApiEvent
    data: WebSocketMessageInitialConnectionData

class WebSocketMessageAskRequestData(BaseModel):
    to_id: str
    card_id: str

class WebSocketMessageAskRequest(BaseModel):
    type: ApiEvent
    data: WebSocketMessageAskRequestData

class WebSocketMessageClaimRequestData(BaseModel):
    half_suit_id: Optional[HalfSuits] = None
    assignment: Optional[Dict[str, str]] = None

class WebSocketMessageClaimRequest(BaseModel):
    type: ApiEvent
    data: WebSocketMessageClaimRequestData
