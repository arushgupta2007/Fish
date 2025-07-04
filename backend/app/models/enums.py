"""
Enums and constants for the Half Suit card game.

This module defines all the enums and constants used throughout the game,
including game status, card ranks, suits, claim outcomes, and other game-related constants.
"""

from enum import Enum, IntEnum
from typing import Dict, List, Tuple


class GameStatus(str, Enum):
    """Game status enumeration."""
    LOBBY = "lobby"
    ACTIVE = "active"
    FINISHED = "finished"


class CardRank(str, Enum):
    """Card rank enumeration."""
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"
    JOKER = "Joker"


class CardSuit(str, Enum):
    """Card suit enumeration."""
    SPADES = "Spades"
    HEARTS = "Hearts"
    DIAMONDS = "Diamonds"
    CLUBS = "Clubs"
    JOKER = "Joker"


class HalfSuitType(IntEnum):
    """Half suit type enumeration with IDs."""
    SPADES_LOW = 0    # 2-7 of Spades
    SPADES_HIGH = 1   # 9-A of Spades
    HEARTS_LOW = 2    # 2-7 of Hearts
    HEARTS_HIGH = 3   # 9-A of Hearts
    DIAMONDS_LOW = 4  # 2-7 of Diamonds
    DIAMONDS_HIGH = 5 # 9-A of Diamonds
    CLUBS_LOW = 6     # 2-7 of Clubs
    CLUBS_HIGH = 7    # 9-A of Clubs
    SPECIAL = 8       # Four 8s + Two Jokers


class ClaimOutcome(str, Enum):
    """Claim outcome enumeration."""
    OWN_TEAM_CORRECT = "own_team_correct"
    OWN_TEAM_INCORRECT = "own_team_incorrect"
    COUNTER_CORRECT = "counter_correct"
    COUNTER_INCORRECT = "counter_incorrect"
    OTHER_TEAM_CORRECT = "other_team_correct"
    OTHER_TEAM_INCORRECT = "other_team_incorrect"
    SPLIT_AUTO_INCORRECT = "split_auto_incorrect"


class TeamId(IntEnum):
    """Team ID enumeration."""
    TEAM_1 = 1
    TEAM_2 = 2


class ActionType(str, Enum):
    """Action type enumeration."""
    ASK = "ask"
    CLAIM = "claim"
    COUNTER_CLAIM = "counter_claim"


class WebSocketEventType(str, Enum):
    """WebSocket event type enumeration."""
    ASK = "ask"
    CLAIM = "claim"
    COUNTER_CLAIM = "counter_claim"
    STATE_UPDATE = "state_update"
    ERROR = "error"
    PLAYER_LEFT = "player_left"
    PLAYER_JOINED = "player_joined"
    GAME_STARTED = "game_started"
    GAME_ENDED = "game_ended"
    TEAM_SELECTION = "team_selection"
    TURN_CHANGE = "turn_change"


class ErrorCode(str, Enum):
    """Error code enumeration."""
    INVALID_GAME_ID = "invalid_game_id"
    INVALID_PLAYER_ID = "invalid_player_id"
    GAME_NOT_FOUND = "game_not_found"
    PLAYER_NOT_FOUND = "player_not_found"
    GAME_FULL = "game_full"
    GAME_ALREADY_STARTED = "game_already_started"
    GAME_NOT_STARTED = "game_not_started"
    INVALID_TURN = "invalid_turn"
    INVALID_ACTION = "invalid_action"
    INVALID_CLAIM = "invalid_claim"
    INVALID_ASK = "invalid_ask"
    PLAYER_NO_CARDS = "player_no_cards"
    HALF_SUIT_OUT_OF_PLAY = "half_suit_out_of_play"
    INVALID_CARD = "invalid_card"
    INVALID_ASSIGNMENTS = "invalid_assignments"
    DUPLICATE_PLAYER_NAME = "duplicate_player_name"
    WEBSOCKET_ERROR = "websocket_error"


# Game Constants
class GameConstants:
    """Game constants."""
    
    # Game setup
    TOTAL_PLAYERS = 6
    PLAYERS_PER_TEAM = 3
    TOTAL_TEAMS = 2
    CARDS_PER_PLAYER = 9
    TOTAL_CARDS = 54  # 52 standard + 2 jokers
    TOTAL_HALF_SUITS = 9
    CARDS_PER_HALF_SUIT = 6
    
    # Game ID and Player ID formats
    GAME_ID_LENGTH = 8
    GAME_ID_PATTERN = r'^[A-Z0-9]{8}$'
    PLAYER_NAME_MAX_LENGTH = 50
    PLAYER_NAME_MIN_LENGTH = 1
    
    # Team scoring
    MAX_POSSIBLE_SCORE = 9
    WINNING_SCORE = 5  # Since there are 9 half suits, one team needs at least 5 to win
    
    # WebSocket
    WEBSOCKET_TIMEOUT = 30  # seconds
    MAX_RECONNECT_ATTEMPTS = 3
    
    # Validation
    VALID_CARD_RANKS = [rank.value for rank in CardRank]
    VALID_CARD_SUITS = [suit.value for suit in CardSuit]
    VALID_GAME_STATUSES = [status.value for status in GameStatus]
    VALID_TEAM_IDS = [team.value for team in TeamId]


# Half Suit Definitions
class HalfSuitDefinitions:
    """Half suit definitions and mappings."""
    
    # Low half suits (2-7)
    LOW_RANKS = [CardRank.TWO, CardRank.THREE, CardRank.FOUR, 
                 CardRank.FIVE, CardRank.SIX, CardRank.SEVEN]
    
    # High half suits (9-A)
    HIGH_RANKS = [CardRank.NINE, CardRank.TEN, CardRank.JACK, 
                  CardRank.QUEEN, CardRank.KING, CardRank.ACE]
    
    # Special half suit (all 8s + jokers)
    SPECIAL_RANKS = [CardRank.EIGHT, CardRank.JOKER]
    
    # Half suit definitions
    HALF_SUIT_CARDS = {
        HalfSuitType.SPADES_LOW: [
            (rank, CardSuit.SPADES) for rank in LOW_RANKS
        ],
        HalfSuitType.SPADES_HIGH: [
            (rank, CardSuit.SPADES) for rank in HIGH_RANKS
        ],
        HalfSuitType.HEARTS_LOW: [
            (rank, CardSuit.HEARTS) for rank in LOW_RANKS
        ],
        HalfSuitType.HEARTS_HIGH: [
            (rank, CardSuit.HEARTS) for rank in HIGH_RANKS
        ],
        HalfSuitType.DIAMONDS_LOW: [
            (rank, CardSuit.DIAMONDS) for rank in LOW_RANKS
        ],
        HalfSuitType.DIAMONDS_HIGH: [
            (rank, CardSuit.DIAMONDS) for rank in HIGH_RANKS
        ],
        HalfSuitType.CLUBS_LOW: [
            (rank, CardSuit.CLUBS) for rank in LOW_RANKS
        ],
        HalfSuitType.CLUBS_HIGH: [
            (rank, CardSuit.CLUBS) for rank in HIGH_RANKS
        ],
        HalfSuitType.SPECIAL: [
            (CardRank.EIGHT, CardSuit.SPADES),
            (CardRank.EIGHT, CardSuit.HEARTS),
            (CardRank.EIGHT, CardSuit.DIAMONDS),
            (CardRank.EIGHT, CardSuit.CLUBS),
            (CardRank.JOKER, CardSuit.JOKER),
            (CardRank.JOKER, CardSuit.JOKER)
        ]
    }
    
    # Half suit names for display
    HALF_SUIT_NAMES = {
        HalfSuitType.SPADES_LOW: "Spades 2-7",
        HalfSuitType.SPADES_HIGH: "Spades 9-A",
        HalfSuitType.HEARTS_LOW: "Hearts 2-7",
        HalfSuitType.HEARTS_HIGH: "Hearts 9-A",
        HalfSuitType.DIAMONDS_LOW: "Diamonds 2-7",
        HalfSuitType.DIAMONDS_HIGH: "Diamonds 9-A",
        HalfSuitType.CLUBS_LOW: "Clubs 2-7",
        HalfSuitType.CLUBS_HIGH: "Clubs 9-A",
        HalfSuitType.SPECIAL: "All 8s + Jokers"
    }
    
    @classmethod
    def get_half_suit_for_card(cls, rank: CardRank, suit: CardSuit) -> HalfSuitType:
        """
        Get the half suit type for a given card.
        
        Args:
            rank: Card rank
            suit: Card suit
            
        Returns:
            HalfSuitType: The half suit this card belongs to
        """
        # Handle special case first
        if rank == CardRank.EIGHT:
            return HalfSuitType.SPECIAL
        
        if rank == CardRank.JOKER and suit == CardSuit.JOKER:
            return HalfSuitType.SPECIAL
        
        # Handle regular suits
        if suit == CardSuit.SPADES:
            return HalfSuitType.SPADES_LOW if rank in cls.LOW_RANKS else HalfSuitType.SPADES_HIGH
        elif suit == CardSuit.HEARTS:
            return HalfSuitType.HEARTS_LOW if rank in cls.LOW_RANKS else HalfSuitType.HEARTS_HIGH
        elif suit == CardSuit.DIAMONDS:
            return HalfSuitType.DIAMONDS_LOW if rank in cls.LOW_RANKS else HalfSuitType.DIAMONDS_HIGH
        elif suit == CardSuit.CLUBS:
            return HalfSuitType.CLUBS_LOW if rank in cls.LOW_RANKS else HalfSuitType.CLUBS_HIGH
        
        raise ValueError(f"Invalid card: {rank} of {suit}")
    
    @classmethod
    def get_all_half_suits(cls) -> List[HalfSuitType]:
        """Get all half suit types."""
        return list(HalfSuitType)
    
    @classmethod
    def get_half_suit_name(cls, half_suit_type: HalfSuitType) -> str:
        """Get the display name for a half suit type."""
        return cls.HALF_SUIT_NAMES[half_suit_type]


# Message Templates
class MessageTemplates:
    """Message templates for various game events."""
    
    # Game events
    GAME_CREATED = "Game {game_id} created"
    GAME_STARTED = "Game has started!"
    GAME_ENDED = "Game ended. Team {winning_team} wins!"
    PLAYER_JOINED = "{player_name} joined the game"
    PLAYER_LEFT = "{player_name} left the game"
    
    # Turn events
    TURN_STARTED = "It's {player_name}'s turn (Team {team_id})"
    TURN_ENDED = "{player_name}'s turn ended"
    
    # Ask events
    ASK_SUCCESS = "{asker} asked {target} for {card} - Success!"
    ASK_FAILURE = "{asker} asked {target} for {card} - Card not found"
    ASK_INVALID_PLAYER = "Cannot ask teammate for cards"
    ASK_NO_CARDS = "Cannot ask for cards when you have no cards"
    
    # Claim events
    CLAIM_STARTED = "{claimant} claims {half_suit}"
    CLAIM_SUCCESS = "{claimant} successfully claimed {half_suit}!"
    CLAIM_FAILURE = "{claimant} failed to claim {half_suit}"
    COUNTER_CLAIM_NEEDED = "Counter-claim needed for {half_suit}"
    COUNTER_CLAIM_SUCCESS = "Counter-claim successful for {half_suit}"
    COUNTER_CLAIM_FAILURE = "Counter-claim failed for {half_suit}"
    
    # Error messages
    ERROR_INVALID_GAME = "Invalid game ID"
    ERROR_GAME_NOT_FOUND = "Game not found"
    ERROR_PLAYER_NOT_FOUND = "Player not found"
    ERROR_GAME_FULL = "Game is full"
    ERROR_INVALID_TURN = "Not your turn"
    ERROR_INVALID_ACTION = "Invalid action"
    ERROR_WEBSOCKET = "WebSocket connection error"


# HTTP Status Codes
class HTTPStatus:
    """HTTP status codes used in the API."""
    
    # Success
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    
    # Client errors
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    
    # Server errors
    INTERNAL_SERVER_ERROR = 500
    SERVICE_UNAVAILABLE = 503


# Export all commonly used items
__all__ = [
    # Enums
    "GameStatus",
    "CardRank", 
    "CardSuit",
    "HalfSuitType",
    "ClaimOutcome",
    "TeamId",
    "ActionType",
    "WebSocketEventType",
    "ErrorCode",
    
    # Constants and definitions
    "GameConstants",
    "HalfSuitDefinitions",
    "MessageTemplates",
    "HTTPStatus",
]