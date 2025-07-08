from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..models.composite import WebSocketMessageAskRequest, WebSocketMessageClaimRequest, WebSocketMessageGeneral
from ..server.manager import GamesManager
from ..utils.constants import ApiEvent

router = APIRouter(prefix="/api")

gamesManager = GamesManager()

@router.get("/health")
def health():
    return {"status": "UP"}

@router.websocket_route("/ws/{game_id}/{plyr_id}")
async def websocket_endpoint(ws: WebSocket, game_id: str, plyr_id: str):
    await ws.accept()

    if not gamesManager.new_connection(game_id, plyr_id, ws):
        return

    try:
        while True:
            try:
                data = await ws.receive_json()
                msg = WebSocketMessageGeneral.model_validate_json(data)

                match msg.type:
                    case ApiEvent.PLAYER_LEFT:
                        await gamesManager.disconnect(game_id, plyr_id)

                    case ApiEvent.GAME_START:
                        if not gamesManager.can_start(game_id, plyr_id):
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": "You cannot the start the game" } })
                            continue

                        res = await gamesManager.start_game(game_id)
                        if not res.success:
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": f"Something went wrong: {res.error}" } })

                    case ApiEvent.ASK_REQUEST:
                        msg = WebSocketMessageAskRequest.model_validate_json(data)
                        res = await gamesManager.ask_player(game_id, plyr_id, msg.data.to_id, msg.data.card_id)

                        if not res.success:
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": f"Something went wrong: {res.error}" } })

                    case ApiEvent.CLAIM:
                        msg = WebSocketMessageClaimRequest.model_validate_json(data)
                        if msg.data.half_suit_id is None or msg.data.assignment is None:
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": "Invalid Request" } })
                            continue

                        res = await gamesManager.claim(game_id, plyr_id, msg.data.half_suit_id, msg.data.assignment)

                        if not res.success:
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": f"Something went wrong: {res.error}" } })

                    case ApiEvent.CLAIM_OPP:
                        msg = WebSocketMessageClaimRequest.model_validate_json(data)
                        if msg.data.half_suit_id is None:
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": "Invalid Request" } })
                            continue

                        res = await gamesManager.claim_opp(game_id, plyr_id, msg.data.half_suit_id)

                        if not res.success:
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": f"Something went wrong: {res.error}" } })

                    case ApiEvent.CLAIM_OPP_UNOPP:
                        msg = WebSocketMessageClaimRequest.model_validate_json(data)
                        if msg.data.assignment is None:
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": "Invalid Request" } })
                            continue

                        res = await gamesManager.claim_opp_unopposed(game_id, plyr_id, msg.data.assignment)

                        if not res.success:
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": f"Something went wrong: {res.error}" } })

                    case ApiEvent.CLAIM_OPP_PASS:
                        res = await gamesManager.claim_pass(game_id, plyr_id)

                        if not res.success:
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": f"Something went wrong: {res.error}" } })

                    case ApiEvent.CLAIM_COUNTER:
                        msg = WebSocketMessageClaimRequest.model_validate_json(data)
                        if msg.data.assignment is None:
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": "Invalid Request" } })
                            continue
                        res = await gamesManager.claim_counter(game_id, plyr_id, msg.data.assignment)

                        if not res.success:
                            await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": f"Something went wrong: {res.error}" } })

                    case _:
                        await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": "Invalid Request" } })

            except:
                await ws.send_json({ "type": ApiEvent.ERROR, "data": { "error": "Could not parse JSON" } })

    except WebSocketDisconnect:
        pass

