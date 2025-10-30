# User & Transactions Relationship Visualization

## What this is
Prototype system that stores Users and Transactions in Neo4j and visualizes relationships using a Cytoscape.js frontend. Backend is FastAPI.

## Repo structure
(brief structure)

## Requirements
- Docker & Docker Compose
- Python 3.11 (for local dev)
- Optional: Neo4j browser at http://localhost:7474

## Quick start (Docker)
1. Build and run:
- docker-compose up --build

2. Backend + Neo4j will be available:
- Backend API: http://localhost:8000
- Frontend: http://localhost:8000
- Neo4j Browser: http://localhost:7474 (user: neo4j / password123)

3. Seed example data (run inside the backend container or from host if environment configured):
- python -m backend.data_generator # or use provided script


## APIs
- `POST /users` — add/update user
- `POST /transactions` — add/update transaction
- `GET /users?limit=100` — list users
- `GET /transactions?limit=200` — list transactions
- `GET /relationships/user/{id}` — relationships for a user
- `GET /relationships/transaction/{id}` — relationships for a transaction
- `GET /export/users/csv` — export users as CSV
- `GET /export/transactions/json` — export transactions as JSON
- `GET /analytics/shortest_path?u1={id}&u2={id}` — shortest path between two users

## Example data
- `sample_data/users_sample.json`
- `sample_data/transactions_sample.json`
Run `python -m backend.data_generator` to populate DB with test data.

## Notes & limitations
- Visualization is limited (default fetch limit). For large graphs use subgraph queries.
- `analytics/shortest_path` uses Cypher `shortestPath` — OK for small graphs.

## How to demo
1. Start stack: `docker-compose up --build`
2. Seed data: `python -m backend.data_generator` (or call the API endpoint that triggers seeding)
3. Open `http://localhost:8000` and click "Load Graph" (or search a user to get subgraph)
4. Show exports and analytics endpoints via browser or curl.

## Contact
Your Name — your.email@example.com

