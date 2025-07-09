from typing import Dict
from fastapi import WebSocket, WebSocketDisconnect
from threading import RLock, Thread
from datetime import datetime, timezone
import asyncio

from ..models.composite import ClaimRecord, OperationResult
from ..models.enums import GameStatus, HalfSuits, ApiEvent
from ..utils.misc import valid_id, valid_name
from ..utils.rank_suite import id_to_rank_suit
from ..utils.constants import CLEANUP_INTERVAL, GAME_ID_LENGTH, GAME_TIMEOUT
from ..game.game import Game

class GameState:
    websockets: Dict[str, WebSocket] = {}
    game: Game
    host: str | None

    def __init__(self, websockets, game, host):
        self.websockets = websockets
        self.game = game
        self.host = host

class GamesManager:
    def __init__(self):
        self.state: Dict[str, GameState] = {}
        self.lock = RLock()


        self.cleanup_thread = Thread(target=self.wrapper_clean_up, daemon=True)
        self.cleanup_thread.start()

    async def _broadcast_message(self, game_id: str, msg):
        with self.lock:
            to_rm = []
            for plyr_id, wss in self.state[game_id].websockets.items():
                try:
                    await wss.send_json(msg)
                except WebSocketDisconnect as _:
                    if self.state[game_id].game.has_player(plyr_id):
                        self.state[game_id].game.leave_player(plyr_id)
                    obj: Dict[str, str | None] = { "id": plyr_id }
                    if plyr_id == self.state[game_id].host:
                        if len(self.state[game_id].game.players) == 0:
                            self.state[game_id].host = None
                            obj["new_host"] = None
                        else:
                            self.state[game_id].host = next(iter(self.state[game_id].game.players))
                            obj["new_host"] = self.state[game_id].host
                    to_rm.append(obj)
            for plyr_id in to_rm:
                del self.state[game_id].websockets[plyr_id["id"]]

        for obj in to_rm:
            await self._brodcast_message(game_id, { "type": ApiEvent.PLAYER_LEFT, "data": obj })

    async def _claim_helper(self, game_id: str, claim_type: ApiEvent, res: ClaimRecord, turn: str | None, done: bool, assignment: Dict[str, str]):
        with self.lock:
            await self._brodcast_message(game_id, {
                "type": claim_type,
                "data": {
                    "player_id": res.claimant,
                    "half_suit_id": res.half_suit,
                    "assignment": assignment,
                    "success": res.success,
                    "point_to": res.point_to,
                    "turn": turn
                }
            })

            if done:
                t0 = self.state[game_id].game.teams[0].score
                t1 = self.state[game_id].game.teams[1].score
                await self._brodcast_message(game_id, {
                    "type": ApiEvent.GAME_FINISHED,
                    "data": {
                        "winning_team": 0 if t0 > t1 else 1,
                        "final_scores": {
                            "team1": t0,
                            "team2": t1
                        }
                    }
                })

    async def new_connection(self, game_id: str, plyr_name: str, ws: WebSocket) -> bool:
        if not valid_id(game_id) or len(game_id) != GAME_ID_LENGTH or not game_id.isascii() or not game_id.isalpha() or not game_id.islower():
            await ws.send_json({ "type": ApiEvent.NEW_CONNECTION, "data": { "success": False, "error": "Game ID is not valid" } })
            return False

        if not valid_name(plyr_name):
            await ws.send_json({ "type": ApiEvent.NEW_CONNECTION, "data": { "success": False, "error": "Player Name is not valid" } })
            return False

        with self.lock:
            if game_id not in self.state:
                self.state[game_id] = GameState({}, Game(), plyr_name)

            if self.state[game_id].host is None:
                self.state[game_id].host = plyr_name

            self.state[game_id].websockets[plyr_name] = ws
            team = self.state[game_id].game.join_player(plyr_name, plyr_name)


            players = []
            for plyr in self.state[game_id].game.players.values():
                obj: Dict[str, str | bool | int] = { "id": plyr.id, "name": plyr.name, "team": plyr.team.value }
                if plyr.id == self.state[game_id].host:
                    obj["host"] = True
                players.append(obj)

            await asyncio.gather(
                ws.send_json({ "type": ApiEvent.NEW_CONNECTION, "data": { "players": players, "success": True } }),
                self._brodcast_message(game_id, { "type": ApiEvent.PLAYER_JOINED, "data": { "id": plyr_name, "name": plyr_name, "team": team.value } })
            )
            return True

    async def disconnect(self, game_id: str, plyr_id: str):
        with self.lock:
            if game_id in self.state:
                if self.state[game_id].game.has_player(plyr_id):
                    self.state[game_id].game.leave_player(plyr_id)

                obj: Dict[str, str | None] = { "id": plyr_id }
                if plyr_id == self.state[game_id].host:
                    if len(self.state[game_id].game.players) == 0:
                        self.state[game_id].host = None
                        obj["new_host"] = None
                    else:
                        self.state[game_id].host = next(iter(self.state[game_id].game.players))
                        obj["new_host"] = self.state[game_id].host

                if plyr_id in self.state[game_id].websockets:
                    del self.state[game_id].websockets[plyr_id]
                await self._brodcast_message(game_id, { "type": ApiEvent.PLAYER_LEFT, "data": obj })

    async def swap_teams(self, game_id: str, plyr_id: str):
        # TODO
        pass

    def can_start(self, game_id: str, plyr_id: str) -> bool:
        with self.lock:
            return game_id in self.state and self.state[game_id].host == plyr_id

    async def start_game(self, game_id: str) -> OperationResult:
        with self.lock:
            if game_id not in self.state:
                return OperationResult(success=False, result=None, error="No game found")

            try:
                st_plyr = self.state[game_id].game.start_game()

                num_cards = { pid: len(plyr.hand) for pid, plyr in self.state[game_id].game.players.items() }

                promises = []
                for pid, plyr in self.state[game_id].game.players.items():
                    if pid not in self.state[game_id].websockets:
                        continue
                    ws = self.state[game_id].websockets[pid]
                    promises.append(ws.send_json({ "type": ApiEvent.HAND, "data": { "hand": [ c.id for c in plyr.hand ] } }))
                await asyncio.gather(*promises)
                await self._brodcast_message(game_id, { "type": ApiEvent.GAME_START, "data": { "starting_player": st_plyr, "num_cards": num_cards } })
                return OperationResult(success=True, result=st_plyr, error=None)
            except Exception as e:
                return OperationResult(success=False, result=None, error=str(e))

    async def ask_player(self, game_id: str, asker_id: str, respondant_id: str, card_id: str) -> OperationResult:
        with self.lock:
            if game_id not in self.state:
                return OperationResult(success=False, result=None, error="No game found")
            try:
                rs = id_to_rank_suit(card_id)
                if rs is None:
                    return OperationResult(success=False, result=None, error="Invalid card")

                card = self.state[game_id].game.get_card(*rs)
                res = self.state[game_id].game.ask(asker_id, respondant_id, card)

                asker_hand = self.state[game_id].game.players[asker_id].hand
                respondant_hand = self.state[game_id].game.players[respondant_id].hand
                await asyncio.gather(
                    self.state[game_id].websockets[asker_id].send_json({ "type": ApiEvent.HAND, "data": { "hand": [ c.id for c in asker_hand ] } }),
                    self.state[game_id].websockets[respondant_id].send_json({ "type": ApiEvent.HAND, "data": { "hand": [ c.id for c in respondant_hand ] } })
                )
                await self._brodcast_message(game_id, {
                    "type": ApiEvent.ASK_REQUEST,
                    "data": {
                        "from_id": asker_id,
                        "to_id": respondant_id,
                        "card_id": card_id,
                        "success": res.success,
                        "turn": self.state[game_id].game.player_turn
                    }
                })

                return OperationResult(success=True, result=None, error=None)
            except Exception as e:
                return OperationResult(success=False, result=None, error=str(e))

    async def claim(self, game_id: str, claimant_id: str, hs: HalfSuits, assignment: Dict[str, str]) -> OperationResult:
        with self.lock:
            if game_id not in self.state:
                return OperationResult(success=False, result=None, error="No game found")

            try:
                (res, turn, done) = self.state[game_id].game.claim(claimant_id, hs, assignment)
                await self._claim_helper(game_id, ApiEvent.CLAIM, res, turn, done, assignment)
                return OperationResult(success=True, result=None, error=None)
            except Exception as e:
                return OperationResult(success=False, result=None, error=str(e))

    async def claim_opp(self, game_id: str, claimant_id: str, hs: HalfSuits) -> OperationResult:
        with self.lock:
            if game_id not in self.state:
                return OperationResult(success=False, result=None, error="No game found")
            try:
                res = self.state[game_id].game.claim_opp(claimant_id, hs)
                await self._brodcast_message(game_id, {
                    "type": ApiEvent.CLAIM_OPP,
                    "data": {
                        "player_id": claimant_id,
                        "team": res.team,
                        "half_suit_id": res.half_suit,
                    }
                })
                return OperationResult(success=True, result=None, error=None)
            except Exception as e:
                return OperationResult(success=False, result=None, error=str(e))

    async def claim_opp_unopposed(self, game_id: str, claimant_id: str, assignment: Dict[str, str]) -> OperationResult:
        with self.lock:
            if game_id not in self.state:
                return OperationResult(success=False, result=None, error="No game found")
            game = self.state[game_id].game
            if game.status != GameStatus.ACTIVE_COUNTER or len(game.claims) == 0 or game.claims[-1].claimant != claimant_id:
                return OperationResult(success=False, result=None, error="You cannot claim right now")

            try:
                (res, turn, done) = self.state[game_id].game.claim_opp_unopposed(assignment)
                await self._claim_helper(game_id, ApiEvent.CLAIM, res, turn, done, assignment)
                return OperationResult(success=True, result=None, error=None)
            except Exception as e:
                return OperationResult(success=False, result=None, error=str(e))

    async def claim_counter(self, game_id: str, claimant_id: str, assignment: Dict[str, str]) -> OperationResult:
        with self.lock:
            if game_id not in self.state:
                return OperationResult(success=False, result=None, error="No game found")

            try:
                (res, turn, done) = self.state[game_id].game.claim_counter(claimant_id, assignment)
                await self._claim_helper(game_id, ApiEvent.CLAIM_COUNTER, res, turn, done, assignment)
                return OperationResult(success=True, result=None, error=None)
            except Exception as e:
                return OperationResult(success=False, result=None, error=str(e))

    async def claim_pass(self, game_id: str, passer_id: str) -> OperationResult:
        with self.lock:
            if game_id not in self.state:
                return OperationResult(success=False, result=None, error="No game found")

            try:
                res = self.state[game_id].game.claim_counter_pass(passer_id)
                await self._brodcast_message(game_id, {
                    "type": ApiEvent.CLAIM_OPP_PASS,
                    "data": {
                        "player_id": passer_id,
                        "all_passed": res
                    }
                })
                return OperationResult(success=True, result=None, error=None)
            except Exception as e:
                return OperationResult(success=False, result=None, error=str(e))

    def wrapper_clean_up(self):
        asyncio.run(self.cleanup_expired_games())

    async def cleanup_expired_games(self):
        """
        Background thread to periodically clean up expired games.
        """
        while True:
            try:
                # Sleep for cleanup interval
                import time
                time.sleep(CLEANUP_INTERVAL.total_seconds())
                
                # Clean up expired games
                cutoff_time = datetime.now(timezone.utc) - GAME_TIMEOUT
                games_to_remove = []
                
                with self.lock:
                    for game_id, game_state in self.state.items():
                        if game_state.game.last_updated < cutoff_time:
                            games_to_remove.append(game_id)
                    
                    for game_id in games_to_remove:
                        for plyr_id in self.state[game_id].game.players.keys():
                            if plyr_id in self.state[game_id].websockets:
                                await self.state[game_id].websockets[plyr_id].close()
                        del self.state[game_id]
                        
            except Exception as _:
                pass
