export const ApiEvent = {
    NEW_CONNECTION: "new_connection",
    PLAYER_JOINED: "player_join",
    PLAYER_LEFT: "player_left",
    HAND: "hand",
    GAME_START: "game_start",
    ASK_REQUEST: "ask",
    CLAIM: "claim",
    CLAIM_OPP: "claim_opp",
    CLAIM_OPP_PASS: "claim_opp_pass",
    CLAIM_OPP_UNOPP: "claim_opp_unopp",
    CLAIM_COUNTER: "claim_counter",
    GAME_FINISHED: "game_finished",
    ERROR: "error"
};
export type ApiEvent = (typeof ApiEvent)[keyof typeof ApiEvent];

export const TeamID = {
  TEAM_1: 0,
  TEAM_2: 1
}
export type TeamID = (typeof TeamID)[keyof typeof TeamID];

export const CardSuit = {
  SPADES: "Spades",
  HEARTS: "Hearts",
  DIAMONDS: "Diamonds",
  CLUBS: "Clubs",
  JOKER: "Joker"
} as const
export type CardSuit = (typeof CardSuit)[keyof typeof CardSuit];

export const CardRank = {
  TWO: "2",
  THREE: "3",
  FOUR: "4",
  FIVE: "5",
  SIX: "6",
  SEVEN: "7",
  EIGHT: "8",
  NINE: "9",
  TEN: "10",
  JACK: "J",
  QUEEN: "Q",
  KING: "K",
  ACE: "A",
  JOKER: "Joker",
  CUT: "Cut",
} as const
export type CardRank = (typeof CardRank)[keyof typeof CardRank];

export const HalfSuits = {
    SPADES_LOW: 0,    // 2-7 of Spades
    SPADES_HIGH: 1,   // 9-A of Spades
    HEARTS_LOW: 2,    // 2-7 of Hearts
    HEARTS_HIGH: 3,   // 9-A of Hearts
    DIAMONDS_LOW: 4,  // 2-7 of Diamonds
    DIAMONDS_HIGH: 5, // 9-A of Diamonds
    CLUBS_LOW: 6,     // 2-7 of Clubs
    CLUBS_HIGH: 7,    // 9-A of Clubs
    SPECIAL: 8,       // Four 8s + Two Jokers
}
export type HalfSuits = (typeof HalfSuits)[keyof typeof HalfSuits];
