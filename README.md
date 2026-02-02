# Recommendation System API

A FastAPI-based recommendation system using FP-Growth algorithm and MongoDB.

## Prerequisites

- Docker and Docker Compose installed
- MongoDB instance (running separately, locally, or on cloud like MongoDB Atlas)

## Quick Start

### 1. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

**IMPORTANT:** Edit `.env` and update your MongoDB connection details:

```env
# For local MongoDB
MONGO_HOST=localhost
MONGO_PORT=27017
```

**Environment Variables:**
- `MONGO_HOST`: MongoDB host address (default: localhost)
- `MONGO_PORT`: MongoDB port (default: 27017)
- `MONGO_URI`: Full MongoDB connection string (overrides MONGO_HOST/PORT if set) (Optional)

> ⚠️ **Note:** Make sure to update the MongoDB connection details before running the application. The default values connect to `localhost:27017`.

### 2. Start the Application

**Option A: With external/remote MongoDB (default)**

```bash
docker compose up -d
```

**Option B: With MongoDB running locally on host machine (Linux)**

```bash
docker compose -f docker-compose-mongo-local.yaml up -d
```

This uses `network_mode: host` to connect to MongoDB running on localhost.

### 3. Verify the Application

Check API health:

```bash
curl http://localhost:8000/health
```

View logs:

```bash
docker-compose logs -f api
```

## API Endpoints

- `GET /health` - Health check endpoint
- `GET /recommendations/popular` - Get popular item recommendations
- `POST /recommendations/fpgrowth` - Get FP-Growth based recommendations

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Stop the Application

```bash
docker-compose down
```

Or with the local MongoDB configuration:

```bash
docker-compose -f docker-compose-mongo-local.yaml down
```
