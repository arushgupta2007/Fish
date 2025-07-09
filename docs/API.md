# Half Suit Card Game - API Documentation

## Overview

The Half Suit card game API provides both REST endpoints and WebSocket connections for real-time multiplayer gameplay. The backend is built with FastAPI and uses WebSockets for real-time state synchronization.

**Base URL:** `http://localhost:8000` (development) or your deployed URL

## Authentication

Currently, no authentication is required. Players are identified by `player_id` generated when joining a game.

## WebSocket Connection

### Connection

A connection to this endpoint, will join the game with id `game_id` and name `player_name`. 
The game will be created if it does not exist.

**Endpoint:** `ws://localhost:8000/ws/{game_id}/{player_name}`

**Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/abcdef123/player456');
```

### WebSocket Events

All WebSocket messages are JSON objects with the following structure:

```json
{
  "type": "event_type",
  "data": { /* event-specific data */ }
}
```

#### 1. New Connection

To join a game, client must send this request after connecting to the WebSocket endpoint

**Client to Server:**
```json
{
  "type": "new_connection",
  "data": {
    "game_id": "string",
    "player_id":  "string"
  }
}
```

**Server to Client:**
```json
{
  "type": "new_connection",
  "data": {
    "players": [
      {
        "id": "string",
        "name": "string",
        "team": 0
      }
    ]
  }
}
```

#### 1. Player Joined Event

Sent when a player joins.

**Server to All Clients:**
```json
{
  "type": "player_join",
  "data": {
    "player_id": "string"
    "player_name": "string"
    "team": 0
  }
}
```

#### 2. Player Left Event

Sent when a player disconnects.

**Server to All Clients:**
```json
{
  "type": "player_left",
  "data": {
    "player_id": "string"
    "new_host": "string" | null
  }
}
```

#### 3. Game Started Event

Sent when a game begins.

**Server to All Clients:**
```json
{
  "type": "game_start",
  "data": {
    "starting_player": "string"
    "num_cards": {
        "player_id": 6
    }
  }
}
```

#### 4. Game Finished Event

Sent when a game finishes.

**Server to All Clients:**
```json
{
  "type": "game_finished",
  "data": {
    "winning_team": 0,
    "final_scores": {
      "0": 5,
      "1": 4
    }
  }
}
```

#### 5. Ask Event

Sent when a player asks for a card.

**Client to Server:**
```json
{
  "type": "ask",
  "data": {
    "to_id": "string",
    "card_id":  "string"
  }
}
```

**Server to All Clients:**
```json
{
  "type": "ask",
  "data": {
    "from_id": "string",
    "to_id": "string",
    "card_id": "string",
    "success": true,
    "turn": "string"
  }
}
```

#### 6. Claim Event

Sent when a player makes a claim.

**Client to Server:**
```json
{
  "type": "claim",
  "data": {
    "half_suit_id": 0,
    "assignments": {
      "card_unique_id": "player_id"
    },
  }
}
```

**Server to All Clients:**
```json
{
  "type": "claim",
  "data": {
    "player_id": "string",
    "half_suit_id": 0,
    "assignments": {
      "card_unique_id": "player_id"
    },
    "success": true,
    "point_to": 0,
    "turn": "string",
  }
}
```

#### 7. Claim For Other Team Event

Sent when a player wants to make a claim for the opponent team.

**Client to Server:**
```json
{
  "type": "claim_opp",
  "data": {
    "half_suit_id": 0,
  }
}
```

**Server to All Clients:**
```json
{
  "type": "claim_opp",
  "data": {
    "player_id": "string",
    "team": 0,
    "half_suit_id": 0,
  }
}
```

#### 8. Claim For Other Team Unopposed Event

Sent when a player makes a claim for the opponent team (i.e, all players in the opponent team have passed).

**Client to Server:**
```json
{
  "type": "claim_opp_unopp",
  "data": {
    "assignments": {
      "card_unique_id": "player_id"
    },
  }
}
```

**Server to All Clients:**
```json
{
  "type": "claim_opp_unopp",
  "data": {
    "player_id": "string",
    "half_suit_id": 0,
    "assignments": {
      "card_unique_id": "player_id"
    },
    "success": true,
    "point_to": 0,
    "turn": "string",
  }
}
```

#### 9. Claim Pass Event

Sent when a player passes on the opportunity to counter claim.

**Client to Server:**
```json
{
  "type": "claim_opp_pass",
}
```

**Server to All Clients:**
```json
{
  "type": "claim_opp_pass",
  "data": {
    "player_id": "string",
    "all_passed": False
  }
}
```

#### 10. Counter Claim Event

Sent when a team makes a counter-claim.

**Client to Server:**
```json
{
  "type": "claim_counter_",
  "data": {
    "half_suit_id": 0,
    "assignments": {
      "card_unique_id": "player_id"
    }
  }
}
```

**Server to All Clients:**
```json
{
  "type": "claim_counter",
  "data": {
    "player_id": "string",
    "half_suit_id": 0,
    "assignments": {
      "card_unique_id": "player_id"
    },
    "success": true,
    "point_to": 0,
    "turn": "string",
  }
}
```

#### 11. Hand Event

Initializes Hand.

**Server to All Clients:**
```json
{
  "type": "hand",
  "data": {
    "hand": [ "string" ]
  }
}
```

#### 12. Error Event

Sent when an error occurs.

**Server to Client:**
```json
{
  "type": "error",
  "data": {
    "message": "string",
    "code": "string"
  }
}
```

## Data Models

### Card
```json
{
  "rank": "string",  // '2'-'A', 'Joker', 'Cut'
  "suit": "string",  // 'Spades', 'Hearts', 'Diamonds', 'Clubs', 'Joker'
  "half_suit_id": 0, // 0-8
  "unique_id": "string" // e.g., "2S", "JokerJ"
}
```

### Player
```json
{
  "id": "string",
  "name": "string",
  "team_id": 0, // 0 or 1
  "hand": [], // Array of Card objects (only populated for the requesting player)
  "num_cards": 0 // Publicly visible card count
}
```

### Team
```json
{
  "id": 0, // 0 or 1
  "name": "string",
  "score": 0,
  "players": ["string"] // Array of player IDs
}
```

### Half Suit
```json
{
  "id": 0, // 0-8
  "name": "string",
  "cards": [], // Array of 6 Card objects
  "claimed_by": 0, // Team ID that claimed this half-suit (null if not claimed)
  "out_of_play": false // True if claimed and discarded
}
```

### Ask Record
```json
{
  "turn": 0,
  "asker": "string", // Player ID
  "respondent": "string", // Player ID
  "card": {}, // Card object
  "success": false
}
```

### Claim Record
```json
{
  "turn": 0,
  "claimant": "string", // Player ID
  "half_suit_id": 0,
  "assignments": {
    "card_unique_id": "player_id"
  },
  "outcome": "string", // See claim outcomes below
  "point_to": 0 // Team ID that received the point
}
```

## Half Suit Definitions

The 9 half suits are:
1. **2-7 of Spades** (6 cards)
2. **9-A of Spades** (6 cards)
3. **2-7 of Hearts** (6 cards)
4. **9-A of Hearts** (6 cards)
5. **2-7 of Diamonds** (6 cards)
6. **9-A of Diamonds** (6 cards)
7. **2-7 of Clubs** (6 cards)
8. **9-A of Clubs** (6 cards)
9. **All 8s + 2 Jokers** (6 cards)

## Game Flow

1. **Lobby Phase** (`status: "lobby"`)
   - Players join via `/join-game`
   - Game starts when 6 players are present via `/start-game`

2. **Active Phase** (`status: "active_ask"` or `status: "active_claim"`)
   - Players take turns asking for cards or making claims
   - WebSocket events handle real-time gameplay
   - State updates broadcast to all players
   - Status `active_claim` is when a player claims for the opponent team, and immediate action from the opponent team is needed

3. **Finished Phase** (`status: "finished"`)
   - Game ends when all 9 half suits are claimed
   - Final scores determined

## Error Handling

### Common Error Codes

- `GAME_NOT_FOUND` - Game ID doesn't exist
- `PLAYER_NOT_FOUND` - Player ID doesn't exist
- `GAME_FULL` - Game already has 6 players
- `GAME_ALREADY_STARTED` - Cannot join game in progress
- `INVALID_ACTION` - Action not allowed (wrong turn, invalid card, etc.)
- `INVALID_CLAIM` - Claim format is incorrect
- `HAND_EMPTY` - Player with no cards cannot ask
- `INVALID_HALF_SUIT` - Half suit doesn't exist or already claimed
- `WEBSOCKET_ERROR` - WebSocket connection issues

### Error Response Format

```json
{
  "error": "ERROR_CODE",
  "message": "Human readable error message",
  "details": {
    "field": "Additional error details"
  }
}
```

## Rate Limiting

- REST API: 100 requests per minute per IP
- WebSocket: 60 actions per minute per player

## Development & Testing

### Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-04T10:30:00Z",
  "version": "1.0.0"
}
```

### API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Example Game Flow

1. **Connect WebSocket:**
   ```javascript
   const ws = new WebSocket('ws://localhost:8000/ws/abc123/player456');
   ```

2. **Make an Ask:**
   ```javascript
   ws.send(JSON.stringify({
     type: "ask",
     data: {
       to_id: "player789",
       card_id: "2S"
     }
   }));
   ```

3. **Make a Claim:**
   ```javascript
   ws.send(JSON.stringify({
     type: "claim",
     data: {
       half_suit_id: 0,
       assignments: {
         "2S": "player123",
         "3S": "player456",
         "4S": "player789",
         "5S": "player123",
         "6S": "player456",
         "7S": "player789"
       },
     }
   }));
   ```

This completes the API documentation for the Half Suit card game. The API supports full game functionality including lobby management, real-time gameplay, and complex claim mechanics.
