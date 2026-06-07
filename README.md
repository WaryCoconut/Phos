# Phos

OpenSource game inspired by the game Pax Historia

AI-powered geopolitical narrative simulation. Play as a nation, make political decisions, engage in real-time diplomacy with other countries through AI agents, and consult your political advisor.


> Compatible with **[socle.ai](https://socle.ai)** by default (OpenAI-compatible API). Works with any OpenAI-compatible endpoint.

## Features

- **Interactive world map** — visualize diplomatic relations, stability, and ideology across countries
- **Included 2016 scenario** — 45+ countries with realistic data (GDP, military, ideology, relations)
- **AI diplomacy** — negotiate in natural language with any country, streamed in real time
- **AI political advisor** — get strategic analyses and recommendations
- **Free actions** — submit any political action, the AI simulates its consequences
- **Turn simulation** — the AI generates world events each turn (1 month)
- **Custom scenarios** — build your own maps and factions from scratch (LotR, Star Wars, Warhammer 40k, Napoleonic Wars…)

## Quick start (development)

### Prerequisites
- Python 3.11+
- Node.js 20+
- An API key for socle.ai or any OpenAI-compatible provider

### 1. Backend (FastAPI)

```bash
cd backend

# Copy the config template
cp .env.example .env
# → Edit .env: set PAX_API_KEY and optionally PAX_MODEL

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend (React + Vite)

```bash
cd frontend

npm install
npm run dev
```

Open **http://localhost:5173**

---

## Docker

```bash
# Copy and configure .env
cp backend/.env.example backend/.env
# → Set PAX_API_KEY in backend/.env

docker-compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

---

## Configuration

`backend/.env` (copied from `.env.example`):

```env
# AI API — OpenAI-compatible (socle.ai by default)
PAX_API_BASE_URL=https://api.socle.ai/v1
PAX_API_KEY=sk-your-api-key-here
PAX_MODEL=gpt-4o

# Other compatible providers:
# OpenAI official : PAX_API_BASE_URL=https://api.openai.com/v1
# Local Ollama    : PAX_API_BASE_URL=http://localhost:11434/v1  PAX_API_KEY=ollama
# Groq            : PAX_API_BASE_URL=https://api.groq.com/openai/v1
```

---

## Architecture

```
phos/
├── backend/                    # Python + FastAPI
│   ├── app/
│   │   ├── main.py             # FastAPI app + CORS
│   │   ├── config.py           # Configuration (env vars)
│   │   ├── models/             # Pydantic models (country, game, scenario)
│   │   ├── routers/            # API endpoints (game, diplomacy, advisor, scenarios)
│   │   ├── services/
│   │   │   ├── ai_service.py   # OpenAI-compatible AI client (SSE streaming)
│   │   │   ├── game_engine.py  # Game engine (sessions, turns, state)
│   │   │   └── scenario_loader.py
│   │   └── data/
│   │       └── scenarios/
│   │           └── default_2016.json  # World 2016 scenario (45+ countries)
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                   # React + TypeScript + Vite
│   ├── src/
│   │   ├── App.tsx             # Routing
│   │   ├── pages/
│   │   │   ├── Home.tsx        # Scenario + country selection
│   │   │   └── Game.tsx        # Main game interface
│   │   ├── components/
│   │   │   ├── Map/WorldMap.tsx               # Interactive SVG map (react-simple-maps)
│   │   │   ├── Dashboard/CountryDashboard.tsx
│   │   │   ├── Diplomacy/DiplomacyPanel.tsx   # Diplomatic chat (SSE)
│   │   │   ├── Advisor/AdvisorPanel.tsx       # AI advisor (SSE)
│   │   │   └── UI/EventsFeed.tsx
│   │   ├── store/gameStore.ts  # Global state (Zustand)
│   │   ├── api/client.ts       # API calls + SSE streaming
│   │   └── types/index.ts
│   └── Dockerfile
│
└── docker-compose.yml
```

## REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/scenarios/` | List scenarios |
| `GET` | `/api/scenarios/{id}` | Scenario details |
| `POST` | `/api/game/` | Create a session |
| `GET` | `/api/game/{session_id}` | Game state |
| `POST` | `/api/game/{session_id}/action` | Submit an action |
| `POST` | `/api/game/{session_id}/end-turn` | End turn |
| `POST` | `/api/diplomacy/{session_id}/message` | Diplomatic message (SSE) |
| `POST` | `/api/advisor/{session_id}/ask` | Ask the advisor (SSE) |
| `GET` | `/api/advisor/{session_id}/briefing` | Situation briefing (SSE) |

## Custom scenarios

Create a scenario via the API (`POST /api/scenarios/`) following the same format as `backend/app/data/scenarios/default_2016.json`, or use the in-app scenario editor. Custom scenarios are saved in `backend/app/data/custom_scenarios/`.

## Contributing

Contributions welcome! Inspired by the original [Pax Historia](https://wiki.paxhistoria.co/wiki/Main_Page) game.

## License

MIT
