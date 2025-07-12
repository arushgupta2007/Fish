import { CardRank, CardSuit, HalfSuits } from "@/types/enums";

export const rank_is_lower = (rank: CardRank) => {
  return ["2", "3", "4", "5", "6", "7"].includes(rank)
}

export const half_suit_id = (rank: CardRank, suit: CardSuit) => {
  switch (suit) {
    case CardSuit.JOKER:
      return HalfSuits.SPECIAL
    case CardSuit.SPADES:
      if (rank == CardRank.EIGHT)
        return HalfSuits.SPECIAL
      if (rank_is_lower(rank))
        return HalfSuits.SPADES_LOW
      return HalfSuits.SPADES_HIGH
    case CardSuit.HEARTS:
      if (rank == CardRank.EIGHT)
        return HalfSuits.SPECIAL
      if (rank_is_lower(rank))
        return HalfSuits.HEARTS_LOW
      return HalfSuits.HEARTS_HIGH
    case CardSuit.DIAMONDS:
      if (rank == CardRank.EIGHT)
        return HalfSuits.SPECIAL
      if (rank_is_lower(rank))
        return HalfSuits.DIAMONDS_LOW
      return HalfSuits.DIAMONDS_HIGH
    case CardSuit.CLUBS:
      if (rank == CardRank.EIGHT)
        return HalfSuits.SPECIAL
      if (rank_is_lower(rank))
        return HalfSuits.CLUBS_LOW
      return HalfSuits.CLUBS_HIGH
  }
}
