import { CardRank, CardSuit } from "@/types/enums";
import { GAME_ID_LENGTH, MAX_NAME_LENGTH } from "./constants"

export function truncateString(str: string, maxLength: number): string {
  if (str.length <= maxLength)
    return str;
  return str.slice(0, maxLength - 3) + "...";
}

export function valid_plyr_name(id: string): boolean {
  return 1 <= id.length && id.length <= MAX_NAME_LENGTH && /^[a-zA-Z0-9]+$/.test(id)
}

export function valid_game_id(id: string): boolean {
  return id.length == GAME_ID_LENGTH && /^[a-z]+$/.test(id)
}

export function id_to_rank_suit(id: string): { success: boolean, data?: { rank: CardRank, suit: CardSuit } } {
  const rank = id.slice(0, id.length - 1)
  const suit = id[id.length - 1]

  if (!(Object.values(CardRank).includes(rank as CardRank))) return { success: false }
  if (!["S", "D", "H", "C", "J"].includes(suit)) return { success: false }

  const suit_m: Record<string, string> = {
    "S": CardSuit.SPADES,
    "D": CardSuit.DIAMONDS,
    "H": CardSuit.HEARTS,
    "C": CardSuit.CLUBS,
    "J": CardSuit.JOKER
  }

  return { success: true, data: {rank: rank as CardRank, suit: suit_m[suit] as CardSuit} }
}

export function unique_card_id(rank: CardRank, suit: CardSuit) {
  return `${rank}${suit[0]}`
}
