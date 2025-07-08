from random import choice
from string import ascii_lowercase

from .constants import GAME_ID_LENGTH

def valid_id(id: str) -> bool:
    """Checks if given player id is valid"""
    return ' ' not in id and id.isascii() and id.isalnum() and 1 <= len(id) <= 50

def valid_name(name: str) -> bool:
    """Checks if given player name is valid"""
    return name == name.strip() and name.isascii() and name.isalnum() and 1 <= len(name) <= 50

def create_small_id() -> str:
    return "".join(choice(ascii_lowercase) for _ in range(GAME_ID_LENGTH))
