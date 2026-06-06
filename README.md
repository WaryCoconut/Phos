# OpenPaxHistoria

Simulation géopolitique narrative alimentée par IA. Incarnez un pays, prenez des décisions politiques, échangez diplomatiquement avec d'autres nations via des agents IA, et consultez votre conseiller politique.

> Compatible par défaut avec l'API **[socle.ai](https://socle.ai)** (API OpenAI-compatible). Fonctionne avec n'importe quelle API compatible OpenAI.

## Fonctionnalités

- **Carte mondiale interactive** — visualisez les relations diplomatiques et la stabilité des pays
- **Scénario 2016 inclus** — 45+ pays avec données réalistes (PIB, militaire, idéologie, relations)
- **Diplomatie IA** — échangez en langage naturel avec n'importe quel pays, réponse en streaming
- **Conseiller politique IA** — obtenez analyses et recommandations stratégiques
- **Actions libres** — soumettez n'importe quelle action politique, l'IA en simule les conséquences
- **Simulation de tours** — l'IA génère des événements mondiaux à chaque tour (1 mois)
- **Scénarios personnalisés** — créez vos propres cartes et pays

## Lancement rapide (développement)

### Prérequis
- Python 3.11+
- Node.js 20+
- Une clé API socle.ai (ou toute API compatible OpenAI)

### 1. Backend (FastAPI)

```bash
cd backend

# Copier la configuration
cp .env.example .env
# → Éditer .env : renseigner PAX_API_KEY et optionnellement PAX_MODEL

# Installer les dépendances
pip install -r requirements.txt

# Lancer le serveur
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend (React + Vite)

```bash
cd frontend

npm install
npm run dev
```

Ouvrir **http://localhost:5173**

---

## Lancement avec Docker

```bash
# Copier et configurer .env
cp backend/.env.example backend/.env
# → Renseigner PAX_API_KEY dans backend/.env

docker-compose up --build
```

- Frontend : http://localhost:5173
- Backend API : http://localhost:8000
- Documentation API : http://localhost:8000/docs

---

## Configuration

Le fichier `backend/.env` (copié depuis `.env.example`) contient :

```env
# API IA — compatible OpenAI (socle.ai par défaut)
PAX_API_BASE_URL=https://api.socle.ai/v1
PAX_API_KEY=sk-votre-cle-api-ici
PAX_MODEL=gpt-4o

# Autres APIs compatibles OpenAI :
# OpenAI officiel  : PAX_API_BASE_URL=https://api.openai.com/v1
# Ollama local     : PAX_API_BASE_URL=http://localhost:11434/v1  PAX_API_KEY=ollama
# Groq             : PAX_API_BASE_URL=https://api.groq.com/openai/v1
```

---

## Architecture

```
openPaxHistoria/
├── backend/                    # Python + FastAPI
│   ├── app/
│   │   ├── main.py             # Application FastAPI + CORS
│   │   ├── config.py           # Configuration (variables d'env)
│   │   ├── models/             # Modèles Pydantic (country, game, scenario)
│   │   ├── routers/            # Endpoints API (game, diplomacy, advisor, scenarios)
│   │   ├── services/
│   │   │   ├── ai_service.py   # Client IA compatible OpenAI (streaming SSE)
│   │   │   ├── game_engine.py  # Moteur de jeu (sessions, tours, états)
│   │   │   └── scenario_loader.py
│   │   └── data/
│   │       └── scenarios/
│   │           └── default_2016.json  # Scénario Monde 2016 (45+ pays)
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/                   # React + TypeScript + Vite
│   ├── src/
│   │   ├── App.tsx             # Routing
│   │   ├── pages/
│   │   │   ├── Home.tsx        # Sélection scénario + pays
│   │   │   └── Game.tsx        # Interface principale
│   │   ├── components/
│   │   │   ├── Map/WorldMap.tsx          # Carte SVG interactive (react-simple-maps)
│   │   │   ├── Dashboard/CountryDashboard.tsx
│   │   │   ├── Diplomacy/DiplomacyPanel.tsx  # Chat diplomatique (SSE)
│   │   │   ├── Advisor/AdvisorPanel.tsx      # Conseiller IA (SSE)
│   │   │   └── UI/EventsFeed.tsx
│   │   ├── store/gameStore.ts  # État global (Zustand)
│   │   ├── api/client.ts       # Appels API + streaming SSE
│   │   └── types/index.ts
│   └── Dockerfile
│
└── docker-compose.yml
```

## API REST

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/scenarios/` | Lister les scénarios |
| `GET` | `/api/scenarios/{id}` | Détails d'un scénario |
| `POST` | `/api/game/` | Créer une partie |
| `GET` | `/api/game/{session_id}` | État du jeu |
| `POST` | `/api/game/{session_id}/action` | Soumettre une action |
| `POST` | `/api/game/{session_id}/end-turn` | Passer au tour suivant |
| `POST` | `/api/diplomacy/{session_id}/message` | Message diplomatique (SSE) |
| `POST` | `/api/advisor/{session_id}/ask` | Question au conseiller (SSE) |
| `GET` | `/api/advisor/{session_id}/briefing` | Briefing de situation (SSE) |

## Créer un scénario personnalisé

Vous pouvez créer un scénario via l'API (`POST /api/scenarios/`) en suivant le même format que `backend/app/data/scenarios/default_2016.json`. Les scénarios personnalisés sont sauvegardés dans `backend/app/data/custom_scenarios/`.

## Contribuer

Les contributions sont bienvenues ! Inspiré du jeu original [Pax Historia](https://wiki.paxhistoria.co/wiki/Main_Page).

## Licence

MIT
