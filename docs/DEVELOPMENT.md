# Half Suit Card Game - Development Guide

## Overview

This guide covers the development setup, architecture, and coding standards for the Half Suit online multiplayer card game. The application uses FastAPI for the backend with WebSocket support and React for the frontend.

## Table of Contents

1. [Development Setup](#development-setup)
2. [Architecture Overview](#architecture-overview)
3. [Backend Development](#backend-development)
4. [Frontend Development](#frontend-development)
5. [WebSocket Implementation](#websocket-implementation)
6. [Game Logic Implementation](#game-logic-implementation)
7. [Testing Strategy](#testing-strategy)
8. [Code Standards](#code-standards)
9. [Development Workflow](#development-workflow)
10. [Debugging and Troubleshooting](#debugging-and-troubleshooting)

## Development Setup

### Prerequisites

- **Python 3.9+** - Backend development
- **Node.js 18+** - Frontend development
- **Docker & Docker Compose** - Containerized development
- **Git** - Version control
- **VS Code** (recommended) - IDE with Python and React extensions

### Quick Start

1. **Clone the repository**:
```bash
git clone <repository-url>
cd half-suit-game
```

2. **Set up environment files**:
```bash
# Backend environment
cp backend/.env.example backend/.env

# Frontend environment
cp frontend/.env.example frontend/.env
```

3. **Start development environment**:
```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or manually (see individual setup sections below)
```

4. **Access the application**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- WebSocket: ws://localhost:8000/ws

### Docker Development Setup

#### docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    env_file:
      - ./backend/.env
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    depends_on:
      - redis
    
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    env_file:
      - ./frontend/.env
    command: npm run dev
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### Manual Setup

#### Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Run the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Architecture Overview

### System Architecture

```
┌─────────────────┐    WebSocket/HTTP    ┌─────────────────┐
│   React Client  │◄─────────────────────►│  FastAPI Server │
│   (Frontend)    │                      │   (Backend)     │
└─────────────────┘                      └─────────────────┘
                                                    │
                                                    ▼
                                         ┌─────────────────┐
                                         │   Game Engine   │
                                         │  (In-Memory)    │
                                         └─────────────────┘
```

### Key Components

#### Backend Components
- **FastAPI Application** - REST API and WebSocket server
- **Game Engine** - Core game logic and state management
- **WebSocket Manager** - Real-time communication
- **Pydantic Models** - Data validation and serialization
- **Game State Manager** - In-memory game state persistence

#### Frontend Components
- **React Application** - User interface
- **WebSocket Client** - Real-time communication
- **Game State Hook** - Client-side state management
- **Component Library** - Reusable UI components

## Backend Development

### Project Structure Explained

```
backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── models/
│   │   ├── game_models.py      # Pydantic models (Card, Player, etc.)
│   │   └── enums.py            # Game constants and enums
│   ├── core/
│   │   ├── game_engine.py      # Core game logic
│   │   ├── deck_manager.py     # Card deck management
│   │   ├── claim_validator.py  # Claim validation logic
│   │   └── half_suit_definitions.py  # Half suit mappings
│   ├── api/
│   │   ├── routes.py           # REST API endpoints
│   │   └── websocket.py        # WebSocket handlers
│   ├── services/
│   │   ├── game_service.py     # Game business logic
│   │   ├── player_service.py   # Player management
│   │   └── team_service.py     # Team management
│   └── utils/
│       ├── game_state_manager.py  # Game state persistence
│       └── validators.py       # Input validation
```

### Core Development Guidelines

#### 1. Game Models (models/game_models.py)

```python
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum

class GameStatus(str, Enum):
    LOBBY = "lobby"
    ACTIVE = "active"
    FINISHED = "finished"

class Card(BaseModel):
    rank: str = Field(..., description="Card rank: 2-A or Joker")
    suit: str = Field(..., description="Card suit: Spades, Hearts, etc.")
    half_suit_id: int = Field(..., description="Half suit ID (0-8)")
    unique_id: str = Field(..., description="Unique card identifier")
    
    class Config:
        schema_extra = {
            "example": {
                "rank": "A",
                "suit": "Spades",
                "half_suit_id": 1,
                "unique_id": "AS-1"
            }
        }

class Player(BaseModel):
    id: str
    name: str
    team_id: int
    hand: List[Card] = Field(default_factory=list)
    num_cards: int = Field(default=0)
    is_active: bool = Field(default=True)
    
    def has_card(self, card_id: str) -> bool:
        """Check if player has a specific card"""
        return any(card.unique_id == card_id for card in self.hand)
    
    def remove_card(self, card_id: str) -> Optional[Card]:
        """Remove and return a card from player's hand"""
        for i, card in enumerate(self.hand):
            if card.unique_id == card_id:
                removed_card = self.hand.pop(i)
                self.num_cards = len(self.hand)
                return removed_card
        return None
```

#### 2. Game Engine (core/game_engine.py)

```python
from typing import Dict, List, Optional, Tuple
from .models.game_models import GameState, Player, Card, Team
from .core.deck_manager import DeckManager
from .core.claim_validator import ClaimValidator

class GameEngine:
    def __init__(self):
        self.games: Dict[str, GameState] = {}
        self.deck_manager = DeckManager()
        self.claim_validator = ClaimValidator()
    
    def create_game(self, game_id: str, creator_name: str) -> GameState:
        """Create a new game instance"""
        game_state = GameState(
            game_id=game_id,
            players=[],
            teams=[
                Team(id=1, name="Team 1", score=0, players=[]),
                Team(id=2, name="Team 2", score=0, players=[])
            ],
            half_suits=self.deck_manager.create_half_suits(),
            status=GameStatus.LOBBY,
            current_team=1,
            current_player=None
        )
        
        # Add creator as first player
        self.add_player(game_id, creator_name)
        
        self.games[game_id] = game_state
        return game_state
    
    def add_player(self, game_id: str, player_name: str) -> Player:
        """Add a player to the game"""
        game = self.games.get(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        if len(game.players) >= 6:
            raise ValueError("Game is full")
        
        # Assign to teams alternately
        team_id = 1 if len(game.players) % 2 == 0 else 2
        
        player = Player(
            id=f"player_{len(game.players) + 1}",
            name=player_name,
            team_id=team_id,
            hand=[],
            num_cards=0
        )
        
        game.players.append(player)
        game.teams[team_id - 1].players.append(player.id)
        
        return player
    
    def start_game(self, game_id: str) -> GameState:
        """Start the game with card dealing"""
        game = self.games.get(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        if len(game.players) != 6:
            raise ValueError("Need exactly 6 players to start")
        
        # Deal cards
        deck = self.deck_manager.create_deck()
        self.deck_manager.deal_cards(deck, game.players)
        
        # Set first player randomly
        import random
        game.current_team = random.choice([1, 2])
        team_players = [p for p in game.players if p.team_id == game.current_team]
        game.current_player = random.choice(team_players).id
        
        game.status = GameStatus.ACTIVE
        return game
    
    def process_ask(self, game_id: str, asker_id: str, 
                   respondent_id: str, card_id: str) -> Tuple[bool, GameState]:
        """Process an ask action"""
        game = self.games.get(game_id)
        if not game:
            raise ValueError(f"Game {game_id} not found")
        
        # Validate ask
        if not self._validate_ask(game, asker_id, respondent_id, card_id):
            raise ValueError("Invalid ask")
        
        # Find players
        asker = next(p for p in game.players if p.id == asker_id)
        respondent = next(p for p in game.players if p.id == respondent_id)
        
        # Check if respondent has the card
        card = respondent.remove_card(card_id)
        success = card is not None
        
        if success:
            # Transfer card to asker
            asker.hand.append(card)
            asker.num_cards = len(asker.hand)
            # Turn continues for the asking team
        else:
            # Turn passes to other team
            game.current_team = 3 - game.current_team  # Switch between 1 and 2
            # Select new current player from the new team
            team_players = [p for p in game.players 
                          if p.team_id == game.current_team and p.num_cards > 0]
            if team_players:
                game.current_player = team_players[0].id
        
        # Record the ask
        ask_record = AskRecord(
            turn=len(game.ask_history) + 1,
            asker=asker_id,
            respondent=respondent_id,
            card=card if card else Card(rank="", suit="", half_suit_id=-1, unique_id=card_id),
            success=success
        )
        game.ask_history.append(ask_record)
        
        return success, game
```

#### 3. WebSocket Handler (api/websocket.py)

```python
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.player_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, game_id: str, player_id: str):
        """Connect a player to a game"""
        await websocket.accept()
        
        if game_id not in self.active_connections:
            self.active_connections[game_id] = []
        
        self.active_connections[game_id].append(websocket)
        self.player_connections[player_id] = websocket
        
        # Send connection confirmation
        await self.send_personal_message({
            "type": "connection_established",
            "player_id": player_id,
            "game_id": game_id
        }, websocket)
    
    def disconnect(self, websocket: WebSocket, game_id: str, player_id: str):
        """Disconnect a player from a game"""
        if game_id in self.active_connections:
            self.active_connections[game_id].remove(websocket)
            if not self.active_connections[game_id]:
                del self.active_connections[game_id]
        
        if player_id in self.player_connections:
            del self.player_connections[player_id]
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except:
            pass  # Connection might be closed
    
    async def broadcast_to_game(self, message: dict, game_id: str):
        """Broadcast a message to all players in a game"""
        if game_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[game_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except:
                    disconnected.append(connection)
            
            # Remove disconnected connections
            for connection in disconnected:
                self.active_connections[game_id].remove(connection)
    
    async def handle_message(self, websocket: WebSocket, game_id: str, 
                           player_id: str, message: dict):
        """Handle incoming WebSocket messages"""
        try:
            message_type = message.get("type")
            
            if message_type == "ask":
                await self.handle_ask(game_id, player_id, message)
            elif message_type == "claim":
                await self.handle_claim(game_id, player_id, message)
            elif message_type == "counter_claim":
                await self.handle_counter_claim(game_id, player_id, message)
            elif message_type == "ping":
                await self.send_personal_message({"type": "pong"}, websocket)
            else:
                await self.send_personal_message({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }, websocket)
                
        except Exception as e:
            await self.send_personal_message({
                "type": "error",
                "message": str(e)
            }, websocket)
```

### Testing Backend Components

#### Unit Tests (tests/test_game_engine.py)

```python
import pytest
from app.core.game_engine import GameEngine
from app.models.game_models import GameStatus

class TestGameEngine:
    def setup_method(self):
        self.engine = GameEngine()
    
    def test_create_game(self):
        """Test game creation"""
        game = self.engine.create_game("test_game", "Player1")
        
        assert game.game_id == "test_game"
        assert len(game.players) == 1
        assert game.players[0].name == "Player1"
        assert game.status == GameStatus.LOBBY
    
    def test_add_players(self):
        """Test adding players to game"""
        game = self.engine.create_game("test_game", "Player1")
        
        # Add remaining players
        for i in range(2, 7):
            self.engine.add_player("test_game", f"Player{i}")
        
        game = self.engine.games["test_game"]
        assert len(game.players) == 6
        
        # Check team assignment
        team1_players = [p for p in game.players if p.team_id == 1]
        team2_players = [p for p in game.players if p.team_id == 2]
        assert len(team1_players) == 3
        assert len(team2_players) == 3
    
    def test_start_game(self):
        """Test game start with card dealing"""
        game = self.engine.create_game("test_game", "Player1")
        
        # Add remaining players
        for i in range(2, 7):
            self.engine.add_player("test_game", f"Player{i}")
        
        # Start game
        game = self.engine.start_game("test_game")
        
        assert game.status == GameStatus.ACTIVE
        assert all(p.num_cards == 9 for p in game.players)
        assert game.current_player is not None
    
    def test_ask_action(self):
        """Test ask action processing"""
        # Setup game with players
        game = self.engine.create_game("test_game", "Player1")
        for i in range(2, 7):
            self.engine.add_player("test_game", f"Player{i}")
        game = self.engine.start_game("test_game")
        
        # Find two players from different teams
        team1_player = next(p for p in game.players if p.team_id == 1)
        team2_player = next(p for p in game.players if p.team_id == 2)
        
        # Get a card from team2 player
        if team2_player.hand:
            card_to_ask = team2_player.hand[0].unique_id
            
            # Process ask
            success, updated_game = self.engine.process_ask(
                "test_game", team1_player.id, team2_player.id, card_to_ask
            )
            
            assert success == True
            assert len(updated_game.ask_history) == 1
            assert updated_game.ask_history[0].success == True
```

## Frontend Development

### Project Structure Explained

```
frontend/
├── src/
│   ├── components/
│   │   ├── common/           # Reusable UI components
│   │   ├── game/            # Game-specific components
│   │   ├── lobby/           # Lobby components
│   │   └── layout/          # Layout components
│   ├── hooks/               # Custom React hooks
│   ├── services/            # API and WebSocket services
│   ├── utils/               # Utility functions
│   └── styles/              # CSS files
```

### Key Frontend Components

#### 1. WebSocket Hook (hooks/useWebSocket.js)

```javascript
import { useState, useEffect, useRef, useCallback } from 'react';

const useWebSocket = (gameId, playerId) => {
  const [socket, setSocket] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (!gameId || !playerId) return;

    const wsUrl = `${process.env.VITE_WS_BASE_URL}/ws/${gameId}/${playerId}`;
    const newSocket = new WebSocket(wsUrl);

    newSocket.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setError(null);
      reconnectAttempts.current = 0;
    };

    newSocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        setLastMessage(message);
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    newSocket.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      
      // Attempt to reconnect
      if (reconnectAttempts.current < maxReconnectAttempts) {
        reconnectAttempts.current++;
        console.log(`Reconnection attempt ${reconnectAttempts.current}`);
        setTimeout(() => {
          connect();
        }, 3000 * reconnectAttempts.current);
      } else {
        setError('Unable to reconnect to game');
      }
    };

    newSocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Connection error');
    };

    setSocket(newSocket);
  }, [gameId, playerId]);

  const sendMessage = useCallback((message) => {
    if (socket && isConnected) {
      socket.send(JSON.stringify(message));
    }
  }, [socket, isConnected]);

  useEffect(() => {
    connect();
    
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [connect]);

  return {
    isConnected,
    lastMessage,
    error,
    sendMessage,
    reconnect: connect
  };
};

export default useWebSocket;
```

#### 2. Game State Hook (hooks/useGameState.js)

```javascript
import { useState, useEffect } from 'react';
import useWebSocket from './useWebSocket';
import { gameApi } from '../services/api';

const useGameState = (gameId, playerId) => {
  const [gameState, setGameState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const { isConnected, lastMessage, sendMessage } = useWebSocket(gameId, playerId);

  // Fetch initial game state
  useEffect(() => {
    const fetchGameState = async () => {
      try {
        setLoading(true);
        const state = await gameApi.getGameState(gameId, playerId);
        setGameState(state);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (gameId && playerId) {
      fetchGameState();
    }
  }, [gameId, playerId]);

  // Handle WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      switch (lastMessage.type) {
        case 'state_update':
          setGameState(lastMessage.game_state);
          break;
        case 'error':
          setError(lastMessage.message);
          break;
        case 'ask_result':
          // Handle ask result
          break;
        case 'claim_result':
          // Handle claim result
          break;
        default:
          console.log('Unknown message type:', lastMessage.type);
      }
    }
  }, [lastMessage]);

  const makeAsk = (respondentId, cardId) => {
    sendMessage({
      type: 'ask',
      respondent_id: respondentId,
      card_id: cardId
    });
  };

  const makeClaim = (halfSuitId, assignments) => {
    sendMessage({
      type: 'claim',
      half_suit_id: halfSuitId,
      assignments: assignments
    });
  };

  const makeCounterClaim = (halfSuitId, assignments) => {
    sendMessage({
      type: 'counter_claim',
      half_suit_id: halfSuitId,
      assignments: assignments
    });
  };

  return {
    gameState,
    loading,
    error,
    isConnected,
    makeAsk,
    makeClaim,
    makeCounterClaim
  };
};

export default useGameState;
```

#### 3. Game Board Component (components/game/GameBoard.jsx)

```jsx
import React, { useState } from 'react';
import PlayerHand from './PlayerHand';
import PlayerList from './PlayerList';
import ActionPanel from './ActionPanel';
import HistoryPanel from './HistoryPanel';
import ScoreBoard from './ScoreBoard';
import TurnIndicator from './TurnIndicator';
import useGameState from '../../hooks/useGameState';

const GameBoard = ({ gameId, playerId }) => {
  const {
    gameState,
    loading,
    error,
    isConnected,
    makeAsk,
    makeClaim,
    makeCounterClaim
  } = useGameState(gameId, playerId);

  const [showAskModal, setShowAskModal] = useState(false);
  const [showClaimModal, setShowClaimModal] = useState(false);

  if (loading) return <div className="loading">Loading game...</div>;
  if (error) return <div className="error">Error: {error}</div>;
  if (!gameState) return <div className="error">Game not found</div>;

  const currentPlayer = gameState.players.find(p => p.id === playerId);
  const isCurrentPlayerTurn = gameState.current_player === playerId;
  const canAsk = isCurrentPlayerTurn && currentPlayer.num_cards > 0;
  const canClaim = isCurrentPlayerTurn;

  return (
    <div className="game-board">
      <div className="game-header">
        <ScoreBoard teams={gameState.teams} />
        <TurnIndicator 
          currentTeam={gameState.current_team}
          currentPlayer={gameState.current_player}
          players={gameState.players}
        />
        <div className="connection-status">
          {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
        </div>
      </div>

      <div className="game-content">
        <div className="left-panel">
          <PlayerList 
            players={gameState.players}
            currentPlayerId={playerId}
            currentTeam={gameState.current_team}
          />
          <HistoryPanel 
            askHistory={gameState.ask_history}
            claimHistory={gameState.claim_history}
          />
        </div>

        <div className="center-panel">
          <PlayerHand 
            cards={currentPlayer.hand}
            playerId={playerId}
          />
          <ActionPanel
            canAsk={canAsk}
            canClaim={canClaim}
            onAskClick={() => setShowAskModal(true)}
            onClaimClick={() => setShowClaimModal(true)}
          />
        </div>

        <div className="right-panel">
          {/* Game statistics or additional info */}
        </div>
      </div>

      {/* Modals */}
      {showAskModal && (
        <AskModal
          players={gameState.players.filter(p => p.team_id !== currentPlayer.team_id)}
          onClose={() => setShowAskModal(false)}
          onSubmit={makeAsk}
        />
      )}

      {showClaimModal && (
        <ClaimModal
          halfSuits={gameState.half_suits.filter(hs => !hs.out_of_play)}
          players={gameState.players}
          onClose={() => setShowClaimModal(false)}
          onSubmit={makeClaim}
        />
      )}
    </div>
  );
};

export default GameBoard;
```

### Frontend Testing

#### Component Tests (using React Testing Library)

```javascript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import GameBoard from '../components/game/GameBoard';
import { gameApi } from '../services/api';

jest.mock('../services/api');
jest.mock('../hooks/useWebSocket');

describe('GameBoard', () => {
  const mockGameState = {
    game_id: 'test-game',
    players: [
      { id: 'player1', name: 'Player 1', team_id: 1, hand: [], num_cards: 5 },
      { id: 'player2', name: 'Player 2', team_id: 2, hand: [], num_cards: 4 }
    ],
    teams: [
      { id: 1, name: 'Team 1', score: 2, players: ['player1'] },
      { id: 2, name: 'Team 2', score: 1, players: ['player2'] }
    ],
    current_team: 1,
    current_player: 'player1',
    ask_history: [],
    claim_history: [],
    half_suits: []
  };

  beforeEach(() => {
    gameApi.getGameState.mockResolvedValue(mockGameState);
  });

  test('renders game board correctly', async () => {
    render(<GameBoard gameId="test-game" playerId="player1" />);
    
    await waitFor(() => {
      expect(screen.getByText('Player 1')).toBeInTheDocument();
      expect(screen.getByText('Team 1')).toBeInTheDocument();
    });
  });

  test('shows action buttons when it\'s player\'s turn', async () => {
    render(<GameBoard gameId="test-game" playerId="player1" />);
    
    await waitFor(() => {
      expect(screen.getByText('Ask')).toBeInTheDocument();
      expect(screen.getByText('Claim')).toBeInTheDocument();
    });
  });

  test('disables action buttons when it\'s not player\'s turn', async () => {
    const notCurrentPlayerState = {
      ...mockGameState,
      current_player: 'player2'
    };
    gameApi.getGameState.mockResolvedValue(notCurrentPlayerState);
    
    render(<GameBoard gameId="test-game" playerId="player1" />);
    
    await waitFor(() => {
      expect(screen.getByText('Ask')).toBeDisabled();
      expect(screen.getByText('Claim')).toBeDisabled();
    });
  });
});
```

## WebSocket Implementation

### Message Types and Flow

```javascript
// Client to Server Messages
const CLIENT_MESSAGES = {
  ASK: 'ask',
  CLAIM: 'claim',
  COUNTER_CLAIM: 'counter_claim',
  PING: 'ping'
};

// Server to Client Messages
const SERVER_MESSAGES = {
  STATE_UPDATE: 'state_update',
  ASK_RESULT: 'ask_result',
  CLAIM_RESULT: 'claim_result',
  ERROR: 'error',
  PONG: 'pong',
  PLAYER_LEFT: 'player_left'
};

// Example message formats
const askMessage = {
  type: 'ask',
  respondent_id: 'player_2',
  card_id: 'AS-1'
};

const claimMessage =