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

### 2. ML Model (PyTorch)
- **Location**: `model/`
- **Architecture**: ResNet18-based multi-label classifier
- **Purpose**: Classifies clothing items by category, color, season, material
- **Data**: Uses iMaterialist Fashion 2020 dataset
- **Training**: `model/my_model.py` handles training with checkpointing
- **Data Processing**: `model/data_processing.py` handles dataset loading and preprocessing

### 3. Frontend (Planned)
- **Status**: Not yet implemented
- **Expected Stack**: React (per requirements.md)
- **Target Port**: 3000 (configured in CORS settings)

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

**Train the model**:
```bash
cd model
python my_model.py
```

**Requirements**:
- PyTorch with CUDA support (if GPU available)
- Dataset directory: `../imaterialist-fashion-2020-fgvc7`
- Model checkpoints saved to: `model/model_weights.pth`

**Notes**:
- Training auto-resumes from checkpoint if `model_weights.pth` exists
- Uses 80/20 train/validation split
- Default batch size: 128
- Default epochs: 5

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
- Image analysis (mock) ✓
- Outfit recommendations (mock) ✓
- ML model training ✓
- ML inference integration ✗
- Frontend ✗
- Authentication/JWT ✗

## Important Notes

- Passwords are stored as plaintext (hashed_password field stores unhashed password) - **security issue**
- No authentication middleware - all endpoints publicly accessible
- Weather API requires API key configuration (currently mocked)
- CORS configured for `http://localhost:3000` only
- Uploaded images stored locally in `uploads/` directory
- Database auto-initializes on backend startup (line 14 in main.py)
