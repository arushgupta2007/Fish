import { id_to_rank_suit, unique_card_id } from "@/utils/utils";
import { CardSuit, HalfSuits, CardRank } from "./enums"
import { half_suit_id } from "@/utils/card";

export class Card {
  rank: CardRank;
  suit: CardSuit;
  half_suit_id: HalfSuits;
  id: string;

  constructor(id: string) {
    const res = id_to_rank_suit(id)
    if (!res.success) throw new Error("Invalid Card ID")

    this.rank = res.data!.rank
    this.suit = res.data!.suit
    this.half_suit_id = half_suit_id(this.rank, this.suit)
    this.id = id
  }

  cmp = (other: Card) => {
    if (this.half_suit_id != other.half_suit_id) return 0
    if (this.id == other.id) return 0

    const mapp: Record<CardRank, number> = {
      [CardRank.TWO]: 2,
      [CardRank.THREE]: 3,
      [CardRank.FOUR]: 4,
      [CardRank.FIVE]: 5,
      [CardRank.SIX]: 6,
      [CardRank.SEVEN]: 7,
      [CardRank.EIGHT]: 8,
      [CardRank.NINE]: 9,
      [CardRank.TEN]: 10,
      [CardRank.JACK]: 11,
      [CardRank.QUEEN]: 12,
      [CardRank.KING]: 13,
      [CardRank.ACE]: 14,
      [CardRank.CUT]: 15,
      [CardRank.JOKER]: 16,
    }
    if (mapp[this.rank] == mapp[other.rank]) return this.suit < other.suit ? -1 : 1
    return mapp[this.rank] < mapp[other.rank] ? -1 : 1
  }
}

export function create_all_cards() {
  var cards: Card[] = []
  for (const rank of Object.values(CardRank)) {
    if (rank != CardRank.JOKER && rank != CardRank.CUT) {
      for (const suit of Object.values(CardSuit)) {
        if (suit != CardSuit.JOKER)
          cards.push(new Card(unique_card_id(rank, suit)))
      }
    } else
      cards.push(new Card(unique_card_id(rank, CardSuit.JOKER)))
  }
  return cards
}
