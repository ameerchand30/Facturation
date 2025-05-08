# Facturation Project

FastAPI-based facturation system.

## Setup

```bash
git reset --soft HEAD~

# to run on local machine change into configDict.py
# env_file = "../.env"

docker build -t my_fastapi_app .

# Remove existing containers and volumes
docker-compose down -v

# Remove existing poetry.lock (if any)
del poetry.lock

# Rebuild without cache
docker-compose build --no-cache

# Start services
docker-compose up -d