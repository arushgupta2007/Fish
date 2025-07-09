import os
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging

from ..models.composite import WebSocketMessageAskRequest, WebSocketMessageClaimRequest, WebSocketMessageGeneral, WebSocketMessageInitialConnection
from ..server.manager import GamesManager
from ..models.enums import ApiEvent

router = APIRouter()
gamesManager = GamesManager()
logger = logging.getLogger(__name__)

@router.get("/health")
def health():
    return { "status": "healthy", "timestamp": datetime.now(timezone.utc), "version": os.getenv("FISH_VERSION") }

@router.websocket_route("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()

    game_id, plyr_id = None, None
    while game_id is None or plyr_id is None:
        try:
            initial_data = await ws.receive_text()
            logger.info(f"JSON: {initial_data}")
            msg = WebSocketMessageInitialConnection.model_validate_json(initial_data)
            if msg.type != ApiEvent.NEW_CONNECTION:
                await ws.send_json({ "type": ApiEvent.NEW_CONNECTION, "data": { "success": False, "error": "Invalid Request" } })
                continue

            game_id, plyr_id = msg.data.game_id, msg.data.player_id
            
            logger.info(f"New WebSocket Connection: GameID = {game_id}, PlayerID = {plyr_id}")
            if not await gamesManager.new_connection(game_id, plyr_id, ws):
                logger.info(f"Invalid GameID/PlayerID: GameID = {game_id}, PlayerID = {plyr_id}")
                game_id, plyr_id = None, None
        except WebSocketDisconnect:
            return
        except Exception as e:
            logger.info(f"JSON Parse error: {repr(e)}")
            try:
                await ws.send_json({ "type": ApiEvent.NEW_CONNECTION, "data": { "success": False, "error": "Invalid Request" } })
            except WebSocketDisconnect:
                return

    logger.info(f"WebSocket Connection Established: GameID = {game_id}, PlayerID = {plyr_id}")
    try:
        while True:
            try:
                data = await ws.receive_text()
                msg = WebSocketMessageGeneral.model_validate_json(data)

                logger.info(f"Recived request - {game_id} - {plyr_id} - {data}")

                match msg.type:
                    case ApiEvent.PLAYER_LEFT:
                        logger.info(f"Leave Request - {game_id} - {plyr_id}")
                        await gamesManager.disconnect(game_id, plyr_id)
                        await ws.close()
                        return

                    case ApiEvent.GAME_START:
                        logger.info(f"Start Request - {game_id} - {plyr_id}")
                        if not gamesManager.can_start(game_id, plyr_id):
                            logger.warning(f"Start Request Failed - {game_id} - {plyr_id} - Not authorized")
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": "You cannot the start the game" } })
                            continue

                        res = await gamesManager.start_game(game_id)
                        if not res.success:
                            logger.warning(f"Start Request Failed - {game_id} - {plyr_id} - {res.error}")
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": f"Something went wrong: {res.error}" } })

                    case ApiEvent.ASK_REQUEST:
                        msg = WebSocketMessageAskRequest.model_validate_json(data)

                        logger.info(f"Ask Request - {game_id} - {plyr_id} asks {msg.data.to_id} card {msg.data.card_id}")

                        res = await gamesManager.ask_player(game_id, plyr_id, msg.data.to_id, msg.data.card_id)

                        if not res.success:
                            logger.warning(f"Ask Request Failed - {game_id} - {plyr_id}")
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": f"Something went wrong: {res.error}" } })

                    case ApiEvent.CLAIM:
                        msg = WebSocketMessageClaimRequest.model_validate_json(data)
                        if msg.data.half_suit_id is None or msg.data.assignment is None:
                            logger.warning(f"Claim Request Failed - {game_id} - {plyr_id} - Invalid Request")
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": "Invalid Request" } })
                            continue

                        logger.info(f"Claim Request - {game_id} - {plyr_id} claims {msg.data.half_suit_id}")
                        res = await gamesManager.claim(game_id, plyr_id, msg.data.half_suit_id, msg.data.assignment)

                        if not res.success:
                            logger.warning(f"Claim Request Failed - {game_id} - {plyr_id} - {res.error}")
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": f"Something went wrong: {res.error}" } })

                    case ApiEvent.CLAIM_OPP:
                        msg = WebSocketMessageClaimRequest.model_validate_json(data)
                        if msg.data.half_suit_id is None:
                            logger.warning(f"Claim For Opponent Request Failed - {game_id} - {plyr_id} - Invalid Request")
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": "Invalid Request" } })
                            continue

                        logger.info(f"Claim For Opponent Request - {game_id} - {plyr_id} claims {msg.data.half_suit_id}")
                        res = await gamesManager.claim_opp(game_id, plyr_id, msg.data.half_suit_id)

                        if not res.success:
                            logger.warning(f"Claim For Opponent Request Failed - {game_id} - {plyr_id} - {res.error}")
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": f"Something went wrong: {res.error}" } })

                    case ApiEvent.CLAIM_OPP_UNOPP:
                        msg = WebSocketMessageClaimRequest.model_validate_json(data)
                        if msg.data.assignment is None:
                            logger.warning(f"Claim Request Unopposed Failed - {game_id} - {plyr_id} - Invalid Request")
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": "Invalid Request" } })
                            continue

                        logger.info(f"Claim For Opponent Unopposed Request - {game_id} - {plyr_id} claims {msg.data.half_suit_id}")
                        res = await gamesManager.claim_opp_unopposed(game_id, plyr_id, msg.data.assignment)

                        if not res.success:
                            logger.warning(f"Claim Request Unopposed Failed - {game_id} - {plyr_id} - {res.error}")
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": f"Something went wrong: {res.error}" } })

                    case ApiEvent.CLAIM_OPP_PASS:
                        logger.info(f"Claim Pass Request - {game_id} - {plyr_id}")
                        res = await gamesManager.claim_pass(game_id, plyr_id)

                        if not res.success:
                            logger.warning(f"Claim Pass Failed - {game_id} - {plyr_id} - {res.error}")
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": f"Something went wrong: {res.error}" } })

                    case ApiEvent.CLAIM_COUNTER:
                        msg = WebSocketMessageClaimRequest.model_validate_json(data)
                        if msg.data.assignment is None:
                            logger.warning(f"Claim Counter Failed - {game_id} - {plyr_id} - Invalid Request")
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": "Invalid Request" } })
                            continue

                        logger.info(f"Claim Counter Request - {game_id} - {plyr_id}")
                        res = await gamesManager.claim_counter(game_id, plyr_id, msg.data.assignment)

                        if not res.success:
                            logger.warning(f"Claim Counter Failed - {game_id} - {plyr_id} - {res.error}")
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": f"Something went wrong: {res.error}" } })

                    case _:
                        logger.warning(f"Invalid Request - {game_id} - {plyr_id}")
                        await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": "Invalid Request" } })

            except Exception as e:
                logger.warning(f"Invalid Request - {game_id} - {plyr_id}")
                await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": f"Could not parse JSON: {repr(e)}" } })

    except WebSocketDisconnect:
        logger.warning(f"Player disconnect - {game_id} - {plyr_id}")
        await gamesManager.disconnect(game_id, plyr_id)

