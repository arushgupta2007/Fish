# Half Suit Online Card Game

A strategic team-based card game for six players (two teams of three) played online via a web interface. Built with FastAPI backend and React frontend.

## Game Overview

Half Suit is a deduction-based card game where teams compete to claim "half suits" by correctly identifying where all cards in a suit are located. The game features:

- **6 players** in **2 teams** of 3 each
- **9 half suits** to claim (standard suits split 2-7 and 9-A, plus 8s+Jokers)
- **Strategic claiming** with counter-claims and tactical "claiming for the other team"
- **Real-time multiplayer** with WebSocket synchronization

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker (optional)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd half-suit-game
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   uvicorn app.main:app --reload
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   cp .env.example .env
   npm run dev
   ```

4. **Or use Docker**
   ```bash
   docker-compose up --build
   ```

## Game Rules

### Basic Gameplay

1. **Setup**: 6 players are randomly assigned to 2 teams of 3
2. **Cards**: Standard 52-card deck + 2 jokers, dealt 9 cards each
3. **Half Suits**: 9 half suits of 6 cards each:
   - 2-7 of each suit (4 half suits)
   - 9-A of each suit (4 half suits)  
   - All 8s + 2 jokers (1 half suit)

### Actions

- **Ask**: Request a specific card from an opponent
  - Must have at least one card of that half suit
  - If successful, continue your turn
  - If unsuccessful, turn passes to other team

- **Claim**: Declare where all 6 cards of a half suit are located
  - **Own team has all cards**: Immediate resolution (correct = point)
  - **Other team has all cards**: Other team makes counter-claim
  - **Cards split**: 
    - Regular claim = automatic failure
    - "Claim for other team" = specify other team's cards

### Winning

- Game ends when all 9 half suits are claimed
- Team with most points (5+ out of 9) wins

## API Endpoints

### REST API

- `POST /create-game` - Create new game lobby
- `POST /join-game` - Join existing game
- `GET /game-state` - Get current game state
- `POST /start-game` - Start the game

### WebSocket Events

- `ask` - Player asks for a card
- `claim` - Player claims a half suit
- `counter_claim` - Counter-claim response
- `state_update` - Game state synchronization
- `error` - Error messages

## Architecture

### Backend (FastAPI)

- **Models**: Pydantic models for type safety
- **Game Engine**: Core game logic and validation
- **WebSocket**: Real-time event broadcasting
- **Services**: Business logic separation

### Frontend (React)

- **Components**: Modular UI components
- **Hooks**: WebSocket and state management
- **Services**: API communication
- **Real-time**: Instant state synchronization

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app
│   ├── models/              # Pydantic models
│   ├── core/                # Game engine
│   ├── api/                 # REST & WebSocket
│   └── services/            # Business logic

frontend/
├── src/
│   ├── components/          # React components
│   ├── hooks/               # Custom hooks
│   ├── services/            # API services
│   └── utils/               # Utilities
```

## Deployment

### Production Build

```bash
# Build frontend
cd frontend
npm run build

# Build backend container
cd backend
docker build -t half-suit-backend .
```

### Environment Variables

**Backend**:
- `PORT` - Server port (default: 8000)
- `CORS_ORIGINS` - Allowed origins
- `SECRET_KEY` - JWT secret key

**Frontend**:
- `VITE_API_URL` - Backend API URL
- `VITE_WS_URL` - WebSocket URL

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details
