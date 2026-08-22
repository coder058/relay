.PHONY: help install test test-backend test-frontend lint benchmark demo dev-backend dev-frontend docker-up docker-down clean

help:
	@echo "Relay Development Commands:"
	@echo "  make install        Install backend and frontend dependencies"
	@echo "  make test           Run full test suite (backend pytest + frontend build check)"
	@echo "  make lint           Check python and typescript types/lints"
	@echo "  make benchmark      Run empirical wall-clock proxy latency benchmark"
	@echo "  make demo           Run one-command automated demo scenario"
	@echo "  make dev-backend    Start FastAPI backend server on :8000"
	@echo "  make dev-frontend   Start Vite frontend dashboard on :5173"
	@echo "  make docker-up      Build and run docker-compose stack"
	@echo "  make docker-down    Stop docker-compose stack"

install:
	pip install -r backend/requirements.txt
	cd frontend && npm install

test: test-backend test-frontend

test-backend:
	cd backend && pytest tests -v

test-frontend:
	cd frontend && npm run build

lint:
	cd backend && ruff check .
	cd frontend && npm run lint

benchmark:
	python scripts/benchmark.py 25

demo:
	python scripts/run_demo.py

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

docker-up:
	docker compose up --build

docker-down:
	docker compose down -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf backend/relay.db frontend/dist
