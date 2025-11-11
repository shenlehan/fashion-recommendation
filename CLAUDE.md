# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Fashion Recommendation System that provides personalized clothing recommendations based on:
- User uploaded wardrobe items
- Local weather conditions
- Individual body types

The system uses **Qwen2-VL-7B-Instruct**, a multimodal large language model, to analyze clothing images and generate personalized outfit recommendations.

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
  - `image_service.py`: Calls Qwen2-VL ML model to analyze clothing images
  - `recommendation_service.py`: Orchestrates outfit recommendation generation
  - `recommendation_logic.py`: Wraps ML model inference for recommendations
  - `weather_api.py`: Returns mock weather data (hardcoded: 25°C, sunny)
- **Core** (`backend/app/core/`): Configuration and database setup
- **Scripts** (`backend/scripts/`): Utility scripts
  - `init_db.py`: Database initialization script
- **Uploads** (`backend/uploads/`): User-uploaded clothing images storage

### 2. ML Model (Qwen2-VL-7B-Instruct)
- **Location**: `backend/ml/`
- **Model**: Qwen/Qwen2-VL-7B-Instruct (7 billion parameters)
- **Type**: Vision-Language multimodal model from Alibaba Cloud
- **Purpose**:
  - Analyze clothing images to extract attributes (category, color, season, material)
  - Generate personalized outfit recommendations with reasoning
- **Main Module**: `backend/ml/inference.py` (342 lines)
  - `FashionQwenModel` class with lazy loading
  - `predict()` - clothing image analysis
  - `get_recommendations()` - outfit generation
- **Requirements**: PyTorch, transformers, qwen-vl-utils, accelerate
- **Device Support**: Auto-detects CUDA GPU or falls back to CPU
- **Documentation**: See `backend/ml/README.md` and `ML_SETUP_GUIDE.md`


### 3. Frontend (React + Vite)
- **Status**: ✅ **FULLY IMPLEMENTED**
- **Location**: `frontend/src/`
- **Framework**: React 19.1.1
- **Build Tool**: Vite 7.1.7
- **Dev Server**: `http://localhost:5173`
- **Routing**: React Router 7.9.5
- **HTTP Client**: Axios 1.13.1

**Implemented Pages**:
1. **Login** (`pages/Login.jsx` - 85 lines)
   - Username/password authentication
   - Error handling and success messages
   - Auto-redirect to wardrobe after login

2. **Register** (`pages/Register.jsx` - 173 lines)
   - Full registration form with validation
   - Fields: username, email, password, confirm password, body_type, city
   - Body type dropdown: slim, athletic, average, curvy, plus-size
   - Auto-redirect to login after success

3. **Wardrobe** (`pages/Wardrobe.jsx` - 174 lines)
   - Grid display of all clothing items with images
   - Upload form with file picker and name input
   - Delete functionality with confirmation dialog
   - Shows item attributes: category, color, season, material
   - Image display from backend: `http://localhost:8000/uploads/...`

4. **Recommendations** (`pages/Recommendations.jsx` - 207 lines)
   - Weather information display
   - AI-generated outfit combinations with reasoning
   - Missing items analysis
   - Customizable preferences: occasion, style, color preference
   - Regenerate recommendations button

**Features**:
- Navigation bar with user info and logout
- Protected routes (localStorage-based session)
- Responsive design with custom CSS
- Loading states and error handling
- Complete CRUD operations for wardrobe

## Database Schema

**Users Table**:
- id, username (unique), email (unique), hashed_password, body_type, city, created_at

**Wardrobe Items Table**:
- id, user_id (FK), name, category, color, season (comma-separated), material, image_path, created_at

## API Endpoints

### User Management (`/api/v1/users/`)
- `POST /register` - Create new user account
  - Body: `{ username, email, password, body_type, city }`
  - Returns: User object with ID
- `POST /login` - Authenticate user
  - Body: `{ username, password }`
  - Returns: User object (⚠️ plaintext password comparison!)
- `GET /profile?user_id={id}` - Get user profile
  - Returns: User details

### Wardrobe Management (`/api/v1/clothes/`)
- `POST /upload?user_id={id}` - Upload clothing image
  - Content-Type: `multipart/form-data`
  - Body: `file` (image file)
  - Process: Saves to `uploads/`, calls Qwen2-VL for analysis, creates DB record
  - Returns: `{ message, item_id }`
- `GET /wardrobe?user_id={id}` - Get user's wardrobe items
  - Returns: Array of WardrobeItem objects
  - **Note**: Frontend calls `/wardrobe/{user_id}` (path param) but backend expects query param
- ❌ `DELETE /{item_id}` - **MISSING ENDPOINT**
  - Frontend expects this (api.js:44) but not implemented in backend

### Recommendations (`/api/v1/recommend/`)
- `GET /outfits?user_id={id}&occasion=&style=&color_preference=` - Get outfit recommendations
  - Query params: user_id (required), occasion, style, color_preference (optional)
  - Process: Fetches wardrobe, weather, user profile → calls Qwen2-VL
  - Returns: `{ outfits: [...], missing_items: [...], weather: {...} }`

## ML Integration

The backend **FULLY INTEGRATES** with Qwen2-VL-7B:
- `image_service.analyze_clothing_image()` → Calls `ml.inference.predict()` → Uses real Qwen2-VL model
- `recommendation_service.generate_outfit_recommendations()` → Calls `recommendation.logic.get_recommendations()` → Uses real Qwen2-VL model
- Both have try-except fallback to mock data if model loading fails

**Model Loading**:
- Lazy loading on first API call
- Global singleton instance (`_model_instance`)
- ~15GB model download on first use
- GPU: ~30s first load, 2-5s per inference
- CPU: ~60s first load, 15-30s per inference

## Docker Deployment (Recommended)

### Quick Start

```bash
# Start everything
docker-compose up -d

# Monitor startup (especially first-time model download)
docker-compose logs -f backend

# Access application
# Frontend: http://localhost
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**First time**: ~10-20 minutes (downloads 15GB model)
**Subsequent starts**: ~30 seconds

### Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart
docker-compose restart

# Shell access
docker exec -it fashion-backend bash

# Check status
docker-compose ps
```

### GPU Support

Enable in `docker-compose.yml`:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

Requires: [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

### Documentation

- **Quick Start**: [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md)
- **Full Guide**: [DOCKER.md](DOCKER.md)
- **Deployment Script**: `./deploy.sh`

## Development Commands

### Backend Development (Manual)

**Install dependencies**:
```bash
cd backend
pip install -r requirements.txt
pip install -r ml/requirements.txt  # For Qwen2-VL model
```

**Start the development server**:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Initialize/reset the database**:
```bash
cd backend
python scripts/init_db.py
```

**Access API documentation**:
- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Frontend Development

**Install dependencies**:
```bash
cd frontend
npm install
```

**Start development server**:
```bash
cd frontend
npm run dev
```
- Runs on: http://localhost:5173
- Hot reload enabled

**Build for production**:
```bash
cd frontend
npm run build
```

**Preview production build**:
```bash
cd frontend
npm run preview
```

### ML Model Setup

**Install Qwen2-VL dependencies** (see `ML_SETUP_GUIDE.md` for details):
```bash
cd backend
pip install -r ml/requirements.txt
```

**First-time model download**:
- Model auto-downloads from HuggingFace on first API call
- Size: ~15GB
- Location: `~/.cache/huggingface/hub/`


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

## Implementation Status

### ✅ Fully Implemented
- User registration and login
- User profile retrieval
- Clothing image upload with file storage
- Wardrobe listing with images
- **ML inference integration using Qwen2-VL-7B**
- **AI-powered image analysis** (category, color, season, material)
- **AI-powered outfit recommendations** with reasoning
- **Complete React frontend** with 4 pages
- Frontend-backend integration
- Preference-based recommendations (occasion, style, color)
- Missing items analysis

### ⚠️ Partially Implemented / Mock Data
- Weather API (returns hardcoded mock data: 25°C, sunny)
- Wardrobe item deletion (frontend implemented, backend endpoint missing)

### ❌ Not Implemented
- JWT/token-based authentication
- Password hashing (currently stored as plaintext!)
- Authorization middleware (anyone can access any user's data)
- Real weather API integration
- File upload validation (size, type checking)
- User profile editing
- Outfit history/favorites
- Image preview before upload
- 404 error page
- Rate limiting
- Production deployment configuration

## Known Bugs & Issues

### Critical Security Issues
1. **Plaintext Passwords**
   - `User.hashed_password` field stores actual password (no bcrypt/hashing)
   - Location: `backend/app/routes/users.py:30-31`
   - Login compares plaintext: `user.hashed_password == password`

2. **No Authentication/Authorization**
   - No JWT tokens or session management on backend
   - All API endpoints are public
   - Any user can access any other user's data by changing `user_id` query param
   - Frontend uses localStorage to store entire user object

### API Inconsistencies
1. **Missing DELETE Endpoint**
   - Frontend calls: `DELETE /api/v1/clothes/{item_id}` (`api.js:44`)
   - Backend: Endpoint doesn't exist in `routes/clothes.py`
   - Result: Delete button fails silently

2. **Wardrobe Route Mismatch**
   - Frontend expects: `GET /api/v1/clothes/wardrobe/{user_id}` (path param)
   - Backend provides: `GET /api/v1/clothes/wardrobe?user_id={id}` (query param)
   - Currently works because axios constructs URL, but inconsistent API design

### Functional Issues
1. **Mock Weather Data**
   - `weather_api.py` returns hardcoded: 25°C, sunny
   - No real API integration (OpenWeatherMap/etc.)

2. **No File Upload Validation**
   - No size limits
   - No MIME type checking
   - No duplicate filename handling

## Project Structure

```
fashion-recommendation/
├── backend/
│   ├── app/
│   │   ├── core/          # Configuration, database setup
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routes/        # API endpoints
│   │   ├── schemas/       # Pydantic schemas
│   │   └── services/      # Business logic
│   ├── ml/                # Qwen2-VL model integration
│   ├── scripts/           # Utility scripts (init_db.py)
│   ├── uploads/           # User-uploaded images
│   ├── requirements.txt
│   └── fashion.db         # SQLite database
├── frontend/
│   ├── src/
│   │   ├── pages/         # React pages
│   │   └── services/      # API client
│   ├── package.json
│   └── vite.config.js
├── docs/                  # Project documentation
├── .env.example           # Environment configuration template
├── .gitignore
├── CLAUDE.md
└── README.md
```

## Environment Configuration

The project supports environment-based configuration via `.env` file:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Configure your settings in `.env`:
   - `BACKEND_CORS_ORIGINS`: Frontend URLs (default: `http://localhost:5173,http://localhost:3000`)
   - `DATABASE_URL`: Database connection string
   - `MODEL_NAME`: Qwen2-VL model identifier
   - `DEVICE`: Computing device (auto/cuda/cpu)

See `.env.example` for full list of configurable options.

## Important Notes

- **Database**: SQLite (`fashion.db`), auto-initializes on backend startup (main.py:14)
- **Image Storage**: Local filesystem in `backend/uploads/` directory
- **Model Cache**: Qwen2-VL downloads to `~/.cache/huggingface/hub/` (~15GB)
- **Frontend Port**: Development server runs on port 5173 (Vite default)
- **CORS**: Backend configured for both ports 5173 and 3000
- **Session Management**: Frontend uses localStorage (no token refresh)
- **Mixed Language**: Comments/strings contain both English and Chinese

## Fine-Tuning with LoRA

The project includes a complete **LoRA (Low-Rank Adaptation)** fine-tuning pipeline to improve fashion-specific performance.

### ✅ What's Included

**Directory: `backend/ml/finetune/`**
- `train_lora.py` - Complete training pipeline
- `test_lora.py` - Model testing script
- `config.yaml` - Training configuration
- `requirements_lora.txt` - LoRA dependencies
- `README.md` - Comprehensive guide
- `QUICKSTART.md` - 5-step quick start

**Directory: `backend/ml/training_data/`**
- `generate_from_db.py` - Auto-generate training data from database
- `data_format.json` - Training data format examples
- `training_data.json` - Generated training examples (created on first run)

**Directory: `backend/ml/lora_adapters/`**
- Fine-tuned model adapters are saved here (~50-150MB)
- Auto-loaded by `inference.py` if available

### Quick Start

```bash
# 1. Install dependencies
cd backend/ml/finetune
pip install -r requirements_lora.txt

# 2. Generate training data
cd ../training_data
python generate_from_db.py

# 3. Train model (1-2 hours on GPU, 4-8 hours on CPU)
cd ../finetune
python train_lora.py

# 4. Test fine-tuned model
python test_lora.py

# 5. Restart backend - adapters auto-load!
cd ../../..
uvicorn app.main:app --reload
```

### Key Features

- **Parameter-Efficient**: Trains <1% of model parameters
- **Memory-Efficient**: ~12GB GPU with 4-bit quantization
- **Auto-Loading**: `inference.py` automatically detects and loads adapters
- **Fallback**: Uses base model if adapters not found
- **Data Generation**: Extract training data from your existing database
- **Configurable**: Extensive configuration options in `config.yaml`

### Expected Improvements

After fine-tuning with 100-1000 examples:
- ✅ Better fashion terminology and category recognition
- ✅ More detailed reasoning in outfit recommendations
- ✅ Consistent JSON output format
- ✅ Domain-specific style advice for body types
- ✅ Personalized to your user base

### Documentation

- **Quick Start**: `backend/ml/finetune/QUICKSTART.md`
- **Full Guide**: `backend/ml/finetune/README.md`
- **Configuration**: `backend/ml/finetune/config.yaml`
- **Data Format**: `backend/ml/training_data/data_format.json`

### Hardware Requirements

**Minimum**: 16GB RAM (CPU training)
**Recommended**: 12GB+ GPU (RTX 3060, 4060 Ti, or better)
**Optimal**: 16GB+ GPU (RTX 4080, 4090)
