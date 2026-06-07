.PHONY: build up down dev dev-backend dev-frontend install logs restart

build:
	docker-compose build

up:
	@powershell -Command "if (-not (Test-Path 'backend\.env')) { Copy-Item 'backend\.env.example' 'backend\.env' }"
	docker-compose up -d
	@echo   Frontend : http://localhost:5173
	@echo   API docs : http://localhost:8000/docs

down:
	docker-compose down

# Développement local (sans Docker)
install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev-backend:
	@powershell -Command "if (-not (Test-Path 'backend\.env')) { Copy-Item 'backend\.env.example' 'backend\.env' }"
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

dev:
	make -j2 dev-backend dev-frontend

# Utilitaires
logs:
	docker-compose logs -f

restart:
	docker-compose restart
