from enum import StrEnum, IntEnum

class CardRank(StrEnum):
    """Card rank enumeration"""
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
    CUT = "Cut"

    @property
    def is_lower(self):
        return self in ["2", "3", "4", "5", "6", "7"]

    @property
    def is_higher(self):
        return self in ["9", "10", "J", "Q", "K", "A"]

    @property
    def is_special(self):
        return self in ["8", "Joker", "Cut"]

class CardSuit(StrEnum):
    """Card suit enumeration"""
    SPADES = "Spades"
    HEARTS = "Hearts"
    DIAMONDS = "Diamonds"
    CLUBS = "Clubs"
    JOKER = "Joker"

class HalfSuits(IntEnum):
    """Half suit type enumeration with IDs"""
    SPADES_LOW = 0    # 2-7 of Spades
    SPADES_HIGH = 1   # 9-A of Spades
    HEARTS_LOW = 2    # 2-7 of Hearts
    HEARTS_HIGH = 3   # 9-A of Hearts
    DIAMONDS_LOW = 4  # 2-7 of Diamonds
    DIAMONDS_HIGH = 5 # 9-A of Diamonds
    CLUBS_LOW = 6     # 2-7 of Clubs
    CLUBS_HIGH = 7    # 9-A of Clubs
    SPECIAL = 8       # Four 8s + Two Jokers

class TeamId(IntEnum):
    """Team ID enumeration."""
    TEAM_1 = 0
    TEAM_2 = 1

    @property
    def opp(self):
        if self == 0:
            return TeamId.TEAM_2
        return TeamId.TEAM_1

class ClaimScenario(IntEnum):
    """
    Possible Scenarios of the claim
    ------------

    CLAIM_WITHIN_TEAM: Normal Scenario: Team claims within their team
    CLAIM_OPP_TEAM_OPPOSED: Player claims for other team, but other team counter claims, leaving this claim moot
    CLAIM_OPP_TEAM_UNOPPOSED: Player claims for other team; other team does not counter, so the player makes their claim
    CLAIM_OPP_TEAM_AWAITING: Player claims for other team; other team is yet to decide to counter or not
    CLAIM_COUNTER: Some player claims for other team, and the current player counters
    """
    CLAIM_WITHIN_TEAM = 0
    CLAIM_OPP_TEAM_OPPOSED = 1
    CLAIM_OPP_TEAM_UNOPPOSED = 2
    CLAIM_OPP_TEAM_AWAITING = 3
    CLAIM_COUNTER = 4

    @property
    def point_changed(self):
        return self != 1 and self != 3


class GameHandCompleteTurnTransfer(IntEnum):
    """
    Game Setting: What happens when the player whoose turn it is, runs out of cards
    -------------

    1. Random: Pick a random teammate with cards
    2. First: The first person in the team who wants to claim the turn
    """
    RANDOM = 0
    FIRST = 1    # TODO: Implement this

class GameStatus(IntEnum):
    """
    Game Status
    ------------

    LOBBY: Waiting for players to join, and decide on settings
    ACTIVE_ASK: The game is active, waiting for player to ask
    ACTIVE_COUNTER: The game is active, waiting for team to decide to counter claim or not
    FINISHED: The game is finished
    """
    LOBBY = 0
    ACTIVE_ASK = 1
    ACTIVE_COUNTER = 2
    FINISHED = 3
