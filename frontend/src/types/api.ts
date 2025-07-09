export interface Player {
  id: string,
  name: string,
  isHost: boolean,
}

export interface GameSettings {
  gameCode: string,
  noPlayers: number,
}

export interface GameState {
}
