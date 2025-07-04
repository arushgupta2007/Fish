# Half Suit Card Game - API Documentation

## Overview

The Half Suit card game API provides both REST endpoints and WebSocket connections for real-time multiplayer gameplay. The backend is built with FastAPI and uses WebSockets for real-time state synchronization.

**Base URL:** `http://localhost:8000` (development) or your deployed URL

## Authentication

Currently, no authentication is required. Players are identified by `player_id` generated when joining a game.

## REST API Endpoints

### 1. Create Game

Create a new game lobby.

**Endpoint:** `POST /create-game`

**Request Body:**
```json
{
  "creator_name": "string"
}
```

**Response:**
```json
{
  "game_id": "string",
  "player_id": "string",
  "team_id": 0
}
```

**Status Codes:**
- `200 OK` - Game created successfully
- `400 Bad Request` - Invalid request body
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl -X POST "http://localhost:8000/create-game" \
  -H "Content-Type: application/json" \
  -d '{"creator_name": "Alice"}'
```

### 2. Join Game

Join an existing game lobby.

**Endpoint:** `POST /join-game`

**Request Body:**
```json
{
  "game_id": "string",
  "player_name": "string"
}
```

**Response:**
```json
{
  "player_id": "string",
  "team_id": 0
}
```

**Status Codes:**
- `200 OK` - Successfully joined game
- `400 Bad Request` - Invalid game ID or player name
- `404 Not Found` - Game not found
- `409 Conflict` - Game is full or already started
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl -X POST "http://localhost:8000/join-game" \
  -H "Content-Type: application/json" \
  -d '{"game_id": "abc123", "player_name": "Bob"}'
```

### 3. Get Game State

Retrieve current game state for a player.

**Endpoint:** `GET /game-state`

**Query Parameters:**
- `game_id` (required): Game identifier
- `player_id` (required): Player identifier

**Response:**
```json
{
  "game_id": "string",
  "players": [
    {
      "id": "string",
      "name": "string",
      "team_id": 0,
      "hand": [
        {
          "rank": "string",
          "suit": "string",
          "half_suit_id": 0,
          "unique_id": "string"
        }
      ],
      "num_cards": 0
    }
  ],
  "teams": [
    {
      "id": 0,
      "name": "string",
      "score": 0,
      "players": ["string"]
    }
  ],
  "half_suits": [
    {
      "id": 0,
      "name": "string",
      "cards": [
        {
          "rank": "string",
          "suit": "string",
          "half_suit_id": 0,
          "unique_id": "string"
        }
      ],
      "claimed_by": 0,
      "out_of_play": false
    }
  ],
  "ask_history": [
    {
      "turn": 0,
      "asker": "string",
      "respondent": "string",
      "card": {
        "rank": "string",
        "suit": "string",
        "half_suit_id": 0,
        "unique_id": "string"
      },
      "success": false
    }
  ],
  "claim_history": [
    {
      "turn": 0,
      "claimant": "string",
      "half_suit_id": 0,
      "assignments": {
        "card_unique_id": "player_id"
      },
      "outcome": "string",
      "point_to": 0
    }
  ],
  "current_team": 0,
  "current_player": "string",
  "status": "string"
}
```

**Status Codes:**
- `200 OK` - Game state retrieved successfully
- `400 Bad Request` - Missing or invalid parameters
- `404 Not Found` - Game or player not found
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl "http://localhost:8000/game-state?game_id=abc123&player_id=player456"
```

### 4. Start Game

Start a game in lobby status (requires 6 players).

**Endpoint:** `POST /start-game`

**Request Body:**
```json
{
  "game_id": "string",
  "player_id": "string"
}
```

**Response:**
```json
{
  "ok": true
}
```

**Status Codes:**
- `200 OK` - Game started successfully
- `400 Bad Request` - Invalid request or game cannot be started
- `403 Forbidden` - Player not authorized to start game
- `404 Not Found` - Game not found
- `409 Conflict` - Game already started or not enough players
- `500 Internal Server Error` - Server error

**Example:**
```bash
curl -X POST "http://localhost:8000/start-game" \
  -H "Content-Type: application/json" \
  -d '{"game_id": "abc123", "player_id": "player456"}'
```

## WebSocket Connection

### Connection

**Endpoint:** `ws://localhost:8000/ws/{game_id}/{player_id}`

**Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/abc123/player456');
```

### WebSocket Events

All WebSocket messages are JSON objects with the following structure:

```json
{
  "type": "event_type",
  "data": { /* event-specific data */ }
}
```

#### 1. Ask Event

Sent when a player asks for a card.

**Client to Server:**
```json
{
  "type": "ask",
  "data": {
    "from_id": "string",
    "to_id": "string",
    "card": {
      "rank": "string",
      "suit": "string",
      "half_suit_id": 0,
      "unique_id": "string"
    }
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
    "card": {
      "rank": "string",
      "suit": "string",
      "half_suit_id": 0,
      "unique_id": "string"
    },
    "success": true,
    "turn": 1
  }
}
```

#### 2. Claim Event

Sent when a player makes a claim.

**Client to Server:**
```json
{
  "type": "claim",
  "data": {
    "player_id": "string",
    "half_suit_id": 0,
    "assignments": {
      "card_unique_id": "player_id"
    },
    "claim_for_other_team": false
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
    "outcome": "own_team_correct",
    "point_to": 0,
    "turn": 1,
    "claim_for_other_team": false
  }
}
```

#### 3. Counter Claim Event

Sent when a team makes a counter-claim.

**Client to Server:**
```json
{
  "type": "counter_claim",
  "data": {
    "player_id": "string",
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
  "type": "counter_claim",
  "data": {
    "player_id": "string",
    "half_suit_id": 0,
    "assignments": {
      "card_unique_id": "player_id"
    },
    "outcome": "counter_correct",
    "point_to": 1,
    "turn": 1
  }
}
```

#### 4. State Update Event

Sent after every game action to synchronize state.

**Server to All Clients:**
```json
{
  "type": "state_update",
  "data": {
    /* Full GameState object */
  }
}
```

#### 5. Error Event

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

#### 6. Player Left Event

Sent when a player disconnects.

**Server to All Clients:**
```json
{
  "type": "player_left",
  "data": {
    "player_id": "string"
  }
}
```

#### 7. Game Started Event

Sent when a game begins.

**Server to All Clients:**
```json
{
  "type": "game_started",
  "data": {
    "game_id": "string",
    "starting_team": 0,
    "starting_player": "string"
  }
}
```

#### 8. Game Ended Event

Sent when a game finishes.

**Server to All Clients:**
```json
{
  "type": "game_ended",
  "data": {
    "winning_team": 0,
    "final_scores": {
      "0": 5,
      "1": 4
    }
  }
}
```

#### 9. Counter Claim Required Event

Sent when a counter-claim is needed.

**Server to All Clients:**
```json
{
  "type": "counter_claim_required",
  "data": {
    "team_id": 0,
    "half_suit_id": 0,
    "original_claim": {
      "player_id": "string",
      "assignments": {
        "card_unique_id": "player_id"
      }
    }
  }
}
```

## Data Models

### Card
```json
{
  "rank": "string",  // '2'-'A', 'Joker'
  "suit": "string",  // 'Spades', 'Hearts', 'Diamonds', 'Clubs', 'Joker'
  "half_suit_id": 0, // 0-8
  "unique_id": "string" // e.g., "2S-1", "Joker-A"
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

## Claim Outcomes

- `own_team_correct` - Claimant's team had all cards and claim was correct
- `own_team_incorrect` - Claimant's team had all cards but claim was incorrect
- `counter_correct` - Opposing team had all cards and counter-claim was correct
- `counter_incorrect` - Opposing team had all cards but counter-claim was incorrect
- `other_team_correct` - "Claim for other team" was correct
- `other_team_incorrect` - "Claim for other team" was incorrect
- `split_auto_incorrect` - Cards were split between teams (regular claim automatically fails)

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

2. **Active Phase** (`status: "active"`)
   - Players take turns asking for cards or making claims
   - WebSocket events handle real-time gameplay
   - State updates broadcast to all players

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

1. **Create Game:**
   ```bash
   curl -X POST "http://localhost:8000/create-game" \
     -H "Content-Type: application/json" \
     -d '{"creator_name": "Alice"}'
   ```

2. **Join Game:**
   ```bash
   curl -X POST "http://localhost:8000/join-game" \
     -H "Content-Type: application/json" \
     -d '{"game_id": "abc123", "player_name": "Bob"}'
   ```

3. **Connect WebSocket:**
   ```javascript
   const ws = new WebSocket('ws://localhost:8000/ws/abc123/player456');
   ```

4. **Make an Ask:**
   ```javascript
   ws.send(JSON.stringify({
     type: "ask",
     data: {
       from_id: "player456",
       to_id: "player789",
       card: {
         rank: "2",
         suit: "Spades",
         half_suit_id: 0,
         unique_id: "2S-1"
       }
     }
   }));
   ```

5. **Make a Claim:**
   ```javascript
   ws.send(JSON.stringify({
     type: "claim",
     data: {
       player_id: "player456",
       half_suit_id: 0,
       assignments: {
         "2S-1": "player123",
         "3S-1": "player456",
         "4S-1": "player789",
         "5S-1": "player123",
         "6S-1": "player456",
         "7S-1": "player789"
       },
       claim_for_other_team: false
     }
   }));
   ```

This completes the API documentation for the Half Suit card game. The API supports full game functionality including lobby management, real-time gameplay, and complex claim mechanics.