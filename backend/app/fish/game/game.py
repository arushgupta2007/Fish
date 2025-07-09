from typing import List, Optional, Dict, Tuple
from random import shuffle, choice
from datetime import datetime, timezone
import os
import logging

from ..models.enums import CardRank, CardSuit, ClaimScenario, GameHandCompleteTurnTransfer, GameStatus, HalfSuits, TeamId
from ..models.composite import AskRecord, ClaimRecord, GameSettings, HalfSuit, Player, Team, Card
from ..utils.card import create_all_cards, create_half_suits
from ..utils.rank_suite import id_to_rank_suit, unique_card_id
from ..utils.misc import valid_name, valid_id
from ..utils.constants import DebugDefaultGameSettings

logger = logging.getLogger(__name__)


class Game:
    """Game Manager"""

    def __init__(self, settings: Optional[GameSettings] = None):
        if os.getenv("DEBUG") == "True":
            default_game_settings = DebugDefaultGameSettings
        else:
            default_game_settings = GameSettings()

        if settings is None:
            settings = default_game_settings
        self.settings = settings

        self.status = GameStatus.LOBBY
        self.cards: List[Card] = create_all_cards()
        self.players: Dict[str, Player] = {}
        self.teams: List[Team] = [
            Team(id=TeamId.TEAM_1, name="Team 1", score=0, players=[]),
            Team(id=TeamId.TEAM_2, name="Team 2", score=0, players=[]),
        ]
        self.asks: List[AskRecord] = []
        self.claims: List[ClaimRecord] = []
        self.counter_claim_passed: Optional[List[str]] = None
        self.half_suits: Dict[HalfSuits, HalfSuit] = create_half_suits()

        self.last_updated = datetime.now(timezone.utc)

        self.player_turn: Optional[str] = None
        self.turn_cnt = 0

    def _nxt_plyr_team(self):
        # Find team for new player
        if len(self.teams[0].players) > len(self.teams[1].players):
            return TeamId.TEAM_2
        return TeamId.TEAM_1

    def _find_plyr_in_team(self, id: str) -> Optional[int]:
        # Assumes player is present
        for i, p in enumerate(self.teams[self.players[id].team].players):
            if p == id:
                return i
        return None  # Plyr not found

    def _shuffle_deck(self):
        shuffle(self.cards)

    def _deal_cards(self):
        card_idx, plyr_cnt = 0, 0
        num_cards_pp, extra = divmod(54, len(self.players))
        for id in self.players:
            cnt_cards = num_cards_pp + (1 if plyr_cnt < extra else 0)
            for j in range(card_idx, card_idx + cnt_cards):
                self.players[id].add_card(self.cards[j], check=False)
            card_idx += cnt_cards
            plyr_cnt += 1

    def _valid_assignment(self, assignment: Dict[str, str], hs: HalfSuits) -> bool:
        # Check if the given assignment is valid
        common_team = None
        for (card_id, plyr_id) in assignment.items():
            rs = id_to_rank_suit(card_id)
            if rs is None:
                return False
            card = self.get_card(*rs)
            if card.half_suit != hs:
                return False

            if plyr_id not in self.players:
                return False

            if common_team is None:
                common_team = self.players[plyr_id].team

            if self.players[plyr_id].team != common_team:
                return False

        hs_cards = sorted(map(lambda c: c.id, filter(lambda c : c.half_suit == hs, self.cards)))
        return hs_cards == sorted(assignment.keys())

    def _check_assignment(self, assignment: Dict[str, str]) -> bool:
        # Check if the given assignment is correct
        for (card_id, plyr_id) in assignment.items():
            rs = id_to_rank_suit(card_id)
            if rs is None:
                return False
            card = self.get_card(*rs)

            if not self.players[plyr_id].has_card(card):
                return False

        return True

    def _remove_half_suit(self, hs: HalfSuits):
        # Remove half suit from the game
        for plyr_id in self.players:
            self.players[plyr_id].hand = list(filter(lambda c : c.half_suit != hs, self.players[plyr_id].hand))

    def _pick_playable_player(self):
        # Find playable player
        if self.player_turn is None: # Should not happen
            raise Exception("Cannot pick playable player at this stage")

        match self.settings.hand_complete_turn_transfer:
            case GameHandCompleteTurnTransfer.RANDOM:
                pick_from = list(filter(lambda p: len(self.players[p].hand) > 0, self.teams[self.players[self.player_turn].team].players))
                if len(pick_from) == 0:
                    return # Opponent team must claim all their cards now. No ask request can be made
                self.player_turn = choice(pick_from)
            case _:
                # TODO; Implement other settings
                raise Exception("Not implemented yet")

    def get_card(self, rank: CardRank, suit: CardSuit) -> Card:
        """Get Card Object from rank and suit. Raises Exception if the card is invalid"""
        id = unique_card_id(rank, suit)
        for c in self.cards:
            if c.id == id:
                return c
        raise Exception("Card not found")

    def join_player(self, id: str, name: str) -> TeamId:
        """Join Player"""
        if self.status != GameStatus.LOBBY:
            raise Exception("Players cannot join an active/finished game")

        if len(self.players) >= self.settings.max_players:
            raise Exception("Player count exceeds limit")

        if not valid_id(id) or not valid_name(name):
            raise Exception("Invalid ID / Name")

        if id in self.players:
            raise Exception("Player with ID already present in game")

        if any(plyr.name == name for plyr in self.players.values()):
            raise Exception("Player with name already present in game")

        self.last_updated = datetime.now(timezone.utc)

        team = self._nxt_plyr_team()
        self.players[id] = Player(id=id, name=name, team=team, hand=[])
        self.teams[team].players.append(id)
        return team

    def leave_player(self, id: str):
        """Remove Player. Still unsure what this means when the game is not in lobby"""
        if self.status == GameStatus.LOBBY:
            team = self.players[id].team
            idx = self._find_plyr_in_team(id)

            if idx is None:
                raise Exception("Player not found")

            self.last_updated = datetime.now(timezone.utc)
            self.teams[team].players.pop(idx)

            del self.players[id]
            return

        # TODO: What to do in this case? Abort game?
        self.status = GameStatus.FINISHED

    def has_player(self, id: str):
        """Checks if a player is present"""
        return self._find_plyr_in_team(id) is not None

    def team_swap_player(self, id: str):
        """Swap Teams for a player"""
        if self.status != GameStatus.LOBBY:
            raise Exception("Cannot swap teams during or after the game")

        team = self.players[id].team
        idx = self._find_plyr_in_team(id)

        if idx is None:
            raise Exception("Player not found")

        self.last_updated = datetime.now(timezone.utc)

        plyr = self.teams[team].players.pop(idx)
        self.teams[team.opp].players.append(plyr) 
        self.players[plyr].team = team.opp


    def start_game(self) -> str:
        """
        Start the game

        Returns the player id of the first turn

        Raises Exception when the Game is not in Lobby, or the number of players is invalid
        """
        if self.status != GameStatus.LOBBY:
            raise Exception("Cannot start a game that is not in lobby")

        if not (self.settings.min_players <= len(self.players) <= self.settings.max_players):
            raise Exception(f"Cannot start game with {len(self.players)} players")

        self.last_updated = datetime.now(timezone.utc)

        self._shuffle_deck()
        self._deal_cards()

        self.status = GameStatus.ACTIVE_ASK
        self.player_turn = choice(list(self.players.keys()))
        return self.player_turn

    def ask(self, asker_id: str, respondant_id: str, card: Card) -> AskRecord:
        """
        Manages ASK 

        Returns an AskRecord

        Raises Exception if the ask is invalid
        """
        if self.player_turn != asker_id:
            raise Exception("Not your turn")
        if self.status != GameStatus.ACTIVE_ASK:
            raise Exception("Cannot ask any questions right now")
        if asker_id not in self.players:
            raise Exception("Asker not found")
        if respondant_id not in self.players:
            raise Exception("Respondant not found")

        asker, respondant = self.players[asker_id], self.players[respondant_id]

        if asker.team == respondant.team:
            raise Exception("Cannot ask teammate")

        if not asker.has_half_suit(card.half_suit):
            raise Exception("Asker does not have card of the half suit")

        if not self.settings.allow_bluffs and asker.has_card(card):
            raise Exception("Bluffs are not allowed in this game")

        if len(respondant.hand) == 0:
            raise Exception("Cannot ask a player with no cards")


        self.last_updated = datetime.now(timezone.utc)

        self.turn_cnt += 1

        self.asks.append(AskRecord(turn_cnt=self.turn_cnt, asker=asker_id, respondant=respondant_id, card=card, success=False))
        if respondant.has_card(card):
            asker.add_card(card)
            respondant.remove_card(card)
            self.asks[-1].success = True
            return self.asks[-1]

        self.player_turn = respondant_id
        return self.asks[-1]

    def claim(self, claimant_id: str, hs: HalfSuits, assignment: Dict[str, str]) -> Tuple[ClaimRecord, str | None, bool]:
        """
        Manages Claim (for same team) 

        Returns a Tuple of ClaimRecord, the current turn's player id, and boolean indicating if the game is finished

        Raises Exception if the claim is invalid
        """
        if claimant_id not in self.players:
            raise Exception("Claimant not found")
        if self.status != GameStatus.ACTIVE_ASK:
            raise Exception("Cannot claim right now")

        claimant = self.players[claimant_id]

        if self.half_suits[hs].claimed:
            raise Exception("Cannot claim previously claimed suit")

        if not self._valid_assignment(assignment, hs):
            raise Exception("Invalid assignment")

        self.last_updated = datetime.now(timezone.utc)

        self.half_suits[hs].claimed = True
        self.half_suits[hs].claimed_team = claimant.team
        self.half_suits[hs].claimed_player = claimant_id

        self.claims.append(
            ClaimRecord(
                turn_cnt=self.turn_cnt,
                team=claimant.team,
                claimant=claimant_id,
                half_suit=hs,
                is_for_other=False,
                is_counter=False,
                success=False,
                scenario=ClaimScenario.CLAIM_WITHIN_TEAM
            )
        )
        if self._check_assignment(assignment):
            self.claims[-1].success = True
            self.teams[claimant.team].score += 1
            self.half_suits[hs].claimed_success = True
        else:
            self.claims[-1].success = False
            self.teams[claimant.team.opp].score += 1
            self.half_suits[hs].claimed_success = False
            
        self._remove_half_suit(hs)
        self.counter_claim_passed = None

        if self.player_turn is not None and len(self.players[self.player_turn].hand) == 0:
            self._pick_playable_player()

        return self.claims[-1], self.player_turn, self.teams[0].score + self.teams[1].score == 9

    def claim_opp(self, claimant_id: str, suit: HalfSuits) -> ClaimRecord:
        """
        Manages Claim (for opponent team) 

        Returns a ClaimRecord

        Raises Exception if the claim is invalid
        """
        if claimant_id not in self.players:
            raise Exception("Claimant not found")
        if self.status != GameStatus.ACTIVE_ASK:
            raise Exception("Cannot claim right now")

        claimant = self.players[claimant_id]

        if self.half_suits[suit].claimed:
            raise Exception("Cannot claim previously claimed suit")

        self.last_updated = datetime.now(timezone.utc)

        self.status = GameStatus.ACTIVE_COUNTER
        self.counter_claim_passed = []
        self.claims.append(
            ClaimRecord(
                turn_cnt=self.turn_cnt,
                team=claimant.team,
                claimant=claimant_id,
                half_suit=suit,
                is_for_other=True,
                is_counter=False,
                success=False,
                scenario=ClaimScenario.CLAIM_OPP_TEAM_AWAITING
            )
        )
        return self.claims[-1]

    def claim_opp_unopposed(self, assignment: Dict[str, str]) -> Tuple[ClaimRecord, str | None, bool]:
        """
        Manages Claim (for opponent team, when the opponent team does not counter claim) 

        Returns a Tuple of ClaimRecord, the current turn's player id, and boolean indicating if the game is finished

        Raises Exception if the claim is invalid
        """
        if self.status != GameStatus.ACTIVE_COUNTER or len(self.claims) == 0 or self.claims[-1].scenario != ClaimScenario.CLAIM_OPP_TEAM_AWAITING:
            raise Exception("Cannot proceed with non-existant claim")

        if len(self.counter_claim_passed or []) != len(self.teams[self.claims[-1].team.opp].players):
            raise Exception("Not everyone in the opposing team has agreed to pass")

        claim = self.claims[-1]
        if any(self.players[plyr_id].team == claim.team for (_, plyr_id) in assignment.items()):
            raise Exception("Cannot include teammate in claim for opponent team")

        hs = claim.half_suit

        if not self._valid_assignment(assignment, hs):
            raise Exception("Invalid assignment")

        self.last_updated = datetime.now(timezone.utc)

        claim.scenario = ClaimScenario.CLAIM_OPP_TEAM_UNOPPOSED
        claim.countered = False

        self.half_suits[hs].claimed = True
        self.half_suits[hs].claimed_team = claim.team
        self.half_suits[hs].claimed_player = claim.claimant

        if self._check_assignment(assignment):
            claim.success = True
            self.teams[claim.team].score += 1
            self.half_suits[hs].claimed_success = True
        else:
            claim.success = False
            self.teams[claim.team.opp].score += 1
            self.half_suits[hs].claimed_success = False

        self._remove_half_suit(hs)
        self.status = GameStatus.ACTIVE_ASK
        self.counter_claim_passed = None

        if self.player_turn is not None and len(self.players[self.player_turn].hand) == 0:
            self._pick_playable_player()

        return claim, self.player_turn, self.teams[0].score + self.teams[1].score == 9

    def claim_counter(self, claimant_id: str, assignment: Dict[str, str]) -> Tuple[ClaimRecord, str | None, bool]:
        """
        Manages Counter Claim

        Returns a Tuple of ClaimRecord, the current turn's player id, and boolean indicating if the game is finished

        Raises Exception if the claim is invalid
        """
        if claimant_id not in self.players:
            raise Exception("Claimant not found")
        if self.status != GameStatus.ACTIVE_COUNTER or len(self.claims) == 0 or self.claims[-1].scenario != ClaimScenario.CLAIM_OPP_TEAM_AWAITING:
            raise Exception("Cannot claim right now")

        if self.counter_claim_passed is not None and claimant_id in self.counter_claim_passed:
            raise Exception("Player has passed on the counter claim")

        self.last_updated = datetime.now(timezone.utc)

        prev_claim = self.claims[-1]
        claimant = self.players[claimant_id]
        if claimant.team == prev_claim.team:
            raise Exception("Cannot counter claim for claim by teammate")

        if not self._valid_assignment(assignment, prev_claim.half_suit):
            raise Exception("Invalid assignment")

        prev_claim.scenario = ClaimScenario.CLAIM_OPP_TEAM_OPPOSED
        prev_claim.success = False
        prev_claim.countered = True

        self.half_suits[prev_claim.half_suit].claimed = True
        self.half_suits[prev_claim.half_suit].claimed_team = claimant.team
        self.half_suits[prev_claim.half_suit].claimed_player = claimant_id

        self.claims.append(
            ClaimRecord(
                turn_cnt=self.turn_cnt,
                team=claimant.team,
                claimant=claimant_id,
                half_suit=prev_claim.half_suit,
                is_for_other=False,
                is_counter=True,
                success=False,
                scenario=ClaimScenario.CLAIM_COUNTER
            )
        )
        if self._check_assignment(assignment):
            self.claims[-1].success = True
            self.teams[claimant.team].score += 1
            self.half_suits[prev_claim.half_suit].claimed_success = True
        else:
            self.claims[-1].success = False
            self.teams[claimant.team.opp].score += 1
            self.half_suits[prev_claim.half_suit].claimed_success = False
            
        self._remove_half_suit(prev_claim.half_suit)
        self.status = GameStatus.ACTIVE_ASK
        self.counter_claim_passed = None

        if self.player_turn is not None and len(self.players[self.player_turn].hand) == 0:
            self._pick_playable_player()

        return self.claims[-1], self.player_turn, self.teams[0].score + self.teams[1].score == 9

    def claim_counter_pass(self, passer_id: str) -> bool:
        """
        Manages Counter Claim Pass

        Returns a boolean, indicating if everyone in the team has passed

        Raises Exception if the pass is invalid
        """
        if passer_id not in self.players:
            raise Exception("Claimant not found")
        if self.status != GameStatus.ACTIVE_COUNTER or len(self.claims) == 0 or self.claims[-1].scenario != ClaimScenario.CLAIM_OPP_TEAM_AWAITING:
            raise Exception("Cannot claim right now")

        if self.players[passer_id].team == self.claims[-1].team:
            raise Exception("Cannot pass on counter for a claim by teammate")

        self.last_updated = datetime.now(timezone.utc)

        self.counter_claim_passed = self.counter_claim_passed or []
        if passer_id not in self.counter_claim_passed:
            self.counter_claim_passed.append(passer_id)

        return len(self.counter_claim_passed or []) == len(self.teams[self.claims[-1].team.opp].players)

