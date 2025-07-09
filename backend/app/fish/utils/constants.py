from datetime import timedelta

from ..models.composite import GameSettings

CLEANUP_INTERVAL = timedelta(minutes=60)
GAME_TIMEOUT = timedelta(hours=24)

GAME_ID_LENGTH = 9

DebugDefaultGameSettings = GameSettings(min_players=1, max_players=100)
