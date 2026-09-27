# django-minishop

A learning project: Django + DRF (basics to advanced) → microservices → AWS ECS + RDS → connection pooling experiments.

## Services (planned)
- **catalog-service**: categories, products, stock
- **order-service**: orders, order items (calls catalog over HTTP)

## Progress
Tracked step by step (0-1, 1A-1, …). Each commit message starts with the step id.

## Run with Docker / deploy to AWS
- Build: `docker build -t minishop .` (gunicorn on port 8000, settings from env vars, see `.env.example`)
- Health checks: `/health/` (process up) and `/health/db/` (database reachable + open connection count)
- AWS ECS (EC2 launch type) + RDS Postgres: task definition template in `deploy/task-definition.json`
