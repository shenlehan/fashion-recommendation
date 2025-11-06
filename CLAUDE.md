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
  - `recommendation_service.py`: Generates outfit recommendations using Qwen2-VL
  - `weather_api.py`: Returns mock weather data (hardcoded: 25°C, sunny)
  - `ml_inference.py`: Placeholder class (not currently used)
- **Core** (`backend/app/core/`): Configuration and database setup

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

**Legacy Training Code** (`model/`):
- Original ResNet18-based training pipeline (not used in production)
- Uses iMaterialist Fashion 2020 dataset
- Kept for reference/alternative approaches

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

## Development Commands

### Backend Development

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
python init_db.py
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

**Legacy ResNet18 Training** (optional, not used in production):
```bash
cd model
python my_model.py
```
- Requires iMaterialist Fashion 2020 dataset
- Saves checkpoints to `model/model_weights.pth`

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
   - `uploads/` directory not auto-created

3. **CORS Configuration**
   - Backend configured for `http://localhost:3000` (line in main.py)
   - Frontend actually runs on `http://localhost:5173` (Vite default)
   - Works due to permissive CORS, but should be updated

## Important Notes

- **Database**: SQLite (`fashion.db`), auto-initializes on backend startup (main.py:14)
- **Image Storage**: Local filesystem in `uploads/` directory (relative path)
- **Model Cache**: Qwen2-VL downloads to `~/.cache/huggingface/hub/` (~15GB)
- **Frontend Port**: Development server runs on port 5173 (Vite), not 3000
- **Session Management**: Frontend uses localStorage (no token refresh)
- **Mixed Language**: Comments/strings contain both English and Chinese

## Fine-Tuning with LoRA (Advanced)

The current implementation uses the **base Qwen2-VL-7B-Instruct model**. To improve fashion-specific performance, you can fine-tune using **LoRA (Low-Rank Adaptation)**:

### Why LoRA?
- **Memory Efficient**: Fine-tune 7B model on ~12GB GPU (with 4-bit quantization)
- **Fast Training**: Only trains <1% of parameters
- **Preserves Base Model**: Original weights unchanged, LoRA adapters are small (~100MB)
- **Customizable**: Improve domain-specific performance (fashion terminology, style advice)

### Required Libraries
```bash
pip install peft accelerate bitsandbytes datasets
```

### Key Steps
1. **Prepare Fashion Dataset**
   - Create training examples with wardrobe items → outfit recommendations
   - Format: `{ "input": "context", "output": "recommendation" }`
   - Need 100-1000+ quality examples
   - Can generate from existing user data

2. **Configure LoRA**
   ```python
   from peft import LoraConfig, get_peft_model

   lora_config = LoraConfig(
       r=16,  # Rank (higher = more capacity)
       lora_alpha=32,  # Scaling factor
       target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
       lora_dropout=0.05,
       bias="none",
       task_type="CAUSAL_LM"
   )
   ```

3. **Training Script Location**
   - Create: `backend/ml/finetune_lora.py`
   - Training data: `backend/ml/fashion_training_data.json`
   - Output: `backend/ml/lora_adapters/` (~100MB)

4. **Load Fine-tuned Model**
   ```python
   from peft import PeftModel

   base_model = Qwen2VLForConditionalGeneration.from_pretrained(...)
   model = PeftModel.from_pretrained(base_model, "./ml/lora_adapters")
   ```

### Training Data Strategy
- **Image Analysis Examples**: Clothing images → category/color/season/material
- **Outfit Recommendations**: Wardrobe + weather + preferences → styled outfits
- **Missing Items**: Wardrobe gaps → suggestions with reasoning
- **Style Advice**: Body type + occasion → outfit guidelines

### Performance Expectations
- **GPU (RTX 3090/4090)**: 2-4 hours for 1000 examples (3 epochs)
- **Memory**: ~12GB VRAM with 4-bit quantization
- **Adapter Size**: ~50-150MB (vs 15GB base model)
- **Inference Speed**: Nearly identical to base model

### Integration
- Modify `backend/ml/inference.py` to load LoRA adapters
- Keep fallback to base model if adapters not found
- Version control adapters separately (too large for git)

See detailed guide: `ML_SETUP_GUIDE.md` (would need to be created)
