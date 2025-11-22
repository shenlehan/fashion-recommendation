# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Fashion Recommendation System that provides personalized clothing recommendations based on:
- User uploaded wardrobe items
- Local weather conditions
- Individual body types

The system analyzes users' wardrobes to identify missing clothing items and suggests outfits.

## Architecture

The project follows a **3-tier architecture**:

### 1. Backend (FastAPI)
- **Location**: `backend/app/`
- **Framework**: FastAPI with SQLAlchemy ORM
- **Database**: SQLite (`fashion.db`)
- **API Base URL**: `http://localhost:8000/api/v1`

Key architectural components:
- **Routes** (`backend/app/routes/`): API endpoints organized by domain (users, clothes, recommendation)
- **Models** (`backend/app/models/`): SQLAlchemy database models (User, WardrobeItem)
- **Schemas** (`backend/app/schemas/`): Pydantic validation schemas
- **Services** (`backend/app/services/`): Business logic layer
  - `image_service.py`: Calls ML models to analyze clothing images
  - `recommendation_service.py`: Generates outfit recommendations
  - `weather_api.py`: Fetches weather data by city
  - `ml_inference.py`: ML model inference wrapper
- **Core** (`backend/app/core/`): Configuration and database setup

### 2. ML Model (Qwen3-VL)
- **Location**: `ml/`
- **Architecture**: Qwen3-VL-8B-Instruct (Multimodal LLM)
- **Purpose**: Analyzes clothing images and generates outfit recommendations
- **Integration**: `ml/inference.py` provides `predict()` and `get_recommendations()` functions
- **Key Features**:
  - Image analysis: Extracts category, color, season, material from clothing images
  - Outfit recommendations: Generates personalized outfit combinations
  - Lazy loading: Model instance cached for performance

### 3. Frontend (React + Vite)
- **Status**: Fully implemented
- **Location**: `frontend/`
- **Stack**: React 19, React Router 7, Axios
- **Pages**: Login, Register, Wardrobe, Recommendations
- **Dev Server Port**: 5173 (Vite default)

## Database Schema

**Users Table**:
- id, username (unique), email (unique), hashed_password, body_type, city, created_at

**Wardrobe Items Table**:
- id, user_id (FK), name, category, color, season (comma-separated), material, image_path, created_at

## API Integration Points

The backend has **placeholder interfaces** for ML integration:
- `image_service.analyze_clothing_image()` → Returns mock data, expects `ml.inference.predict()`
- `recommendation_service.generate_outfit_recommendations()` → Returns mock data, expects `recommendation.logic.get_recommendations()`

These currently return mock data but are designed to integrate with actual ML models.

## Development Commands

### Backend Development

**Start the development server**:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Initialize/reset the database**:
```bash
cd backend
python init_db.py
```

**Install dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

**Access API documentation**:
- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### ML Model Development

**Install ML dependencies**:
```bash
cd ml
pip install -r requirements.txt
```

**Test the model**:
```bash
cd backend
python -m ml.test_model
```

**Requirements**:
- PyTorch with CUDA support (GPU with 16GB+ VRAM recommended)
- HuggingFace model: Qwen/Qwen3-VL-8B-Instruct (~15GB download)
- 32GB+ RAM for CPU-only usage

**Notes**:
- Model auto-downloads from HuggingFace on first use
- Uses lazy loading with global instance caching
- GPU recommended for reasonable performance (2-5s vs 15-30s per image)

## Key Design Patterns

1. **Service Layer Pattern**: Business logic isolated in `services/` directory
2. **Repository Pattern**: Database access through SQLAlchemy ORM
3. **Dependency Injection**: FastAPI's `Depends()` for database sessions
4. **Mock-First Development**: Services return mock data when ML modules unavailable

## File Upload Flow

1. POST `/api/v1/clothes/upload` with multipart/form-data
2. File saved to `uploads/` directory
3. `image_service.analyze_clothing_image()` extracts clothing attributes
4. WardrobeItem created in database with extracted metadata
5. Returns item_id to client

## Recommendation Flow

1. GET `/api/v1/recommend/outfits?user_id=X`
2. Fetch user profile (body_type, city)
3. Fetch user's wardrobe items
4. Call `weather_api.get_weather_by_city()`
5. Call `recommendation_service.generate_outfit_recommendations()`
6. Return outfit suggestions + missing item analysis

## Docker Deployment

**Build and run**:
```bash
docker build -t fashion-backend -f backend/Dockerfile .
docker run -p 8000:8000 fashion-backend
```

Note: Dockerfile expects to be run from project root.

## Known Implementation Status

- User registration ✓
- User profile retrieval ✓
- Clothing upload ✓
- Wardrobe listing ✓
- Weather API (mock) ✓
- Image analysis (Qwen3-VL) ✓
- Outfit recommendations (Qwen3-VL) ✓
- ML inference integration ✓
- Frontend (React) ✓
- Authentication/JWT ✗
- Password hashing ✗

## Important Notes

- Passwords are stored as plaintext (hashed_password field stores unhashed password) - **security issue**
- No authentication middleware - all endpoints publicly accessible
- Weather API requires API key configuration (currently mocked)
- CORS configured for `http://localhost:5173` (Vite dev server)
- Uploaded images stored locally in `uploads/` directory
- Database auto-initializes on backend startup (line 14 in main.py)
