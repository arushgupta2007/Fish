from typing import List, Optional, Dict, Union
from pydantic import BaseModel, Field, validator
from enum import Enum

from .enums import GameStatus

from .enums import ClaimOutcome

class Card(BaseModel):
    rank: str  # '2'-'A', 'Joker'
    suit: str  # 'Spades', 'Hearts', 'Diamonds', 'Clubs', 'Joker'
    half_suit_id: int  # 0-8, assigned based on card properties
    unique_id: str  # Unique identifier like "2S-1", "Joker-A"

    @validator('rank')
    def validate_rank(cls, v):
        valid_ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', 'Joker']
        if v not in valid_ranks:
            raise ValueError(f'Invalid rank: {v}')
        return v

    @validator('suit')
    def validate_suit(cls, v):
        valid_suits = ['Spades', 'Hearts', 'Diamonds', 'Clubs', 'Joker']
        if v not in valid_suits:
            raise ValueError(f'Invalid suit: {v}')
        return v

    @validator('half_suit_id')
    def validate_half_suit_id(cls, v):
        if v < 0 or v > 8:
            raise ValueError(f'Invalid half_suit_id: {v}. Must be 0-8.')
        return v

class Player(BaseModel):
    id: str
    name: str
    team_id: int
    hand: List[Card] = Field(default_factory=list)  # Empty for other players
    num_cards: int = 0  # Publicly visible card count
    is_connected: bool = True

    @validator('team_id')
    def validate_team_id(cls, v):
        if v not in [1, 2]:
            raise ValueError(f'Invalid team_id: {v}. Must be 1 or 2.')
        return v

class Team(BaseModel):
    id: int
    name: str
    score: int = 0
    players: List[str] = Field(default_factory=list)  # List of player IDs

    @validator('id')
    def validate_team_id(cls, v):
        if v not in [1, 2]:
            raise ValueError(f'Invalid team id: {v}. Must be 1 or 2.')
        return v

    @validator('score')
    def validate_score(cls, v):
        if v < 0 or v > 9:
            raise ValueError(f'Invalid score: {v}. Must be 0-9.')
        return v

class HalfSuit(BaseModel):
    id: int
    name: str
    cards: List[Card] = Field(default_factory=list)  # The 6 cards belonging to this half-suit
    claimed_by: Optional[int] = None  # ID of the team that successfully claimed this half-suit
    out_of_play: bool = False  # True if claimed and discarded

    @validator('id')
    def validate_half_suit_id(cls, v):
        if v < 0 or v > 8:
            raise ValueError(f'Invalid half_suit id: {v}. Must be 0-8.')
        return v

    @validator('cards')
    def validate_cards_count(cls, v):
        if len(v) != 6:
            raise ValueError(f'Half suit must have exactly 6 cards, got {len(v)}')
        return v

class AskRecord(BaseModel):
    turn: int
    asker: str  # Player ID of the asker
    respondent: str  # Player ID of the respondent
    card: Card  # The card that was asked for
    success: bool  # True if the respondent had the card

    @validator('turn')
    def validate_turn(cls, v):
        if v < 1:
            raise ValueError(f'Invalid turn: {v}. Must be >= 1.')
        return v

class ClaimRecord(BaseModel):
    turn: int
    claimant: str  # Player ID of the claimant
    half_suit_id: int  # ID of the half-suit being claimed
    assignments: Dict[str, str]  # Mapping of card.unique_id -> player_id
    outcome: ClaimOutcome
    point_to: int  # Team ID that won the point
    is_for_other_team: bool = False  # True if claiming for the other team
    counter_claimant: Optional[str] = None  # Player ID of counter-claimant if applicable

    @validator('turn')
    def validate_turn(cls, v):
        if v < 1:
            raise ValueError(f'Invalid turn: {v}. Must be >= 1.')
        return v

    @validator('half_suit_id')
    def validate_half_suit_id(cls, v):
        if v < 0 or v > 8:
            raise ValueError(f'Invalid half_suit_id: {v}. Must be 0-8.')
        return v

    @validator('point_to')
    def validate_point_to(cls, v):
        if v not in [1, 2]:
            raise ValueError(f'Invalid point_to: {v}. Must be 1 or 2.')
        return v

    @validator('assignments')
    def validate_assignments(cls, v):
        if len(v) != 6:
            raise ValueError(f'Assignments must have exactly 6 entries, got {len(v)}')
        return v

class GameState(BaseModel):
    game_id: str
    players: List[Player] = Field(default_factory=list)
    teams: List[Team] = Field(default_factory=list)
    half_suits: List[HalfSuit] = Field(default_factory=list)
    ask_history: List[AskRecord] = Field(default_factory=list)
    claim_history: List[ClaimRecord] = Field(default_factory=list)
    current_team: int = 1  # ID of the team whose turn it is
    current_player: Optional[str] = None  # ID of the player currently taking the turn
    status: GameStatus = GameStatus.LOBBY
    turn_number: int = 1
    awaiting_counter_claim: bool = False
    pending_claim: Optional[ClaimRecord] = None  # For counter-claim scenarios

    @validator('current_team')
    def validate_current_team(cls, v):
        if v not in [1, 2]:
            raise ValueError(f'Invalid current_team: {v}. Must be 1 or 2.')
        return v

    @validator('turn_number')
    def validate_turn_number(cls, v):
        if v < 1:
            raise ValueError(f'Invalid turn_number: {v}. Must be >= 1.')
        return v

    @validator('players')
    def validate_players_count(cls, v):
        if len(v) > 6:
            raise ValueError(f'Cannot have more than 6 players, got {len(v)}')
        return v

    @validator('teams')
    def validate_teams_count(cls, v):
        if len(v) > 2:
            raise ValueError(f'Cannot have more than 2 teams, got {len(v)}')
        return v

    @validator('half_suits')
    def validate_half_suits_count(cls, v):
        if len(v) > 9:
            raise ValueError(f'Cannot have more than 9 half suits, got {len(v)}')
        return v

    def get_player_by_id(self, player_id: str) -> Optional[Player]:
        """Get a player by their ID."""
        for player in self.players:
            if player.id == player_id:
                return player
        return None

    def get_team_by_id(self, team_id: int) -> Optional[Team]:
        """Get a team by their ID."""
        for team in self.teams:
            if team.id == team_id:
                return team
        return None

    def get_half_suit_by_id(self, half_suit_id: int) -> Optional[HalfSuit]:
        """Get a half suit by its ID."""
        for half_suit in self.half_suits:
            if half_suit.id == half_suit_id:
                return half_suit
        return None

    def get_eligible_players(self, team_id: int) -> List[Player]:
        """Get players with cards who can take a turn."""
        eligible_players = []
        for player in self.players:
            if player.team_id == team_id and player.num_cards > 0:
                eligible_players.append(player)
        return eligible_players

    def get_available_half_suits(self) -> List[HalfSuit]:
        """Get half suits that are still in play (not claimed)."""
        return [hs for hs in self.half_suits if not hs.out_of_play]

    def is_game_finished(self) -> bool:
        """Check if the game is finished (all half suits claimed)."""
        return len(self.get_available_half_suits()) == 0

    def get_winning_team(self) -> Optional[Team]:
        """Get the winning team if the game is finished."""
        if not self.is_game_finished():
            return None
        
        team1 = self.get_team_by_id(1)
        team2 = self.get_team_by_id(2)
        
        if team1 and team2:
            if team1.score > team2.score:
                return team1
            elif team2.score > team1.score:
                return team2
        
        return None

# Request/Response Models for API

class CreateGameRequest(BaseModel):
    creator_name: str

    @validator('creator_name')
    def validate_creator_name(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Creator name cannot be empty')
        if len(v) > 50:
            raise ValueError('Creator name cannot exceed 50 characters')
        return v.strip()

class CreateGameResponse(BaseModel):
    game_id: str

class JoinGameRequest(BaseModel):
    game_id: str
    player_name: str

    @validator('player_name')
    def validate_player_name(cls, v):
        if len(v.strip()) == 0:
            raise ValueError('Player name cannot be empty')
        if len(v) > 50:
            raise ValueError('Player name cannot exceed 50 characters')
        return v.strip()

class JoinGameResponse(BaseModel):
    player_id: str
    team_id: int

class StartGameRequest(BaseModel):
    game_id: str
    player_id: str

class GameStateRequest(BaseModel):
    game_id: str
    player_id: str

# WebSocket Event Models

class AskAction(BaseModel):
    from_id: str
    to_id: str
    card: Card

class ClaimAction(BaseModel):
    player_id: str
    half_suit_id: int
    assignments: Dict[str, str]  # card.unique_id -> player_id
    is_for_other_team: bool = False

class CounterClaimAction(BaseModel):
    player_id: str
    half_suit_id: int
    assignments: Dict[str, str]  # card.unique_id -> player_id

class WebSocketEvent(BaseModel):
    event_type: str
    payload: Dict
    recipients: List[str] = Field(default_factory=list)  # Empty means all players

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict] = None