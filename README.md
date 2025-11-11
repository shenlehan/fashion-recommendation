# Fashion Recommendation System

An AI-powered fashion recommendation system that provides personalized outfit suggestions based on your wardrobe, local weather, and body type.

## Features

- 👗 **Smart Wardrobe Management**: Upload and organize your clothing items with automatic AI-powered image analysis
- 🤖 **AI-Powered Recommendations**: Get personalized outfit suggestions using Qwen2-VL-7B multimodal language model
- 🌤️ **Weather-Aware Styling**: Recommendations adapt to current weather conditions
- 👤 **Personalized Advice**: Tailored suggestions based on your body type and style preferences
- 📱 **Modern Web Interface**: Clean, responsive React frontend with intuitive navigation
- 🎯 **LoRA Fine-tuning**: Complete pipeline to fine-tune the model on your fashion data

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **ML Model**: Qwen2-VL-7B-Instruct (Alibaba Cloud)
- **Image Processing**: PIL, qwen-vl-utils
- **Python**: 3.8+

### Frontend
- **Framework**: React 19.1
- **Build Tool**: Vite 7.1
- **Routing**: React Router 7.9
- **HTTP Client**: Axios 1.13

## Quick Start

### 🐳 Option 1: Docker (Recommended - Plug & Play)

**Prerequisites**: Docker 20.10+, 16GB RAM, 25GB disk space

```bash
# Start everything
docker-compose up -d

# Wait for model download (first time, ~10-20 min)
docker-compose logs -f backend

# Access the app
# Frontend: http://localhost
# API: http://localhost:8000
```

**That's it!** See [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) for details.

### 💻 Option 2: Manual Installation

**Prerequisites**: Python 3.8+, Node.js 16+, 16GB+ RAM, GPU (optional)

#### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fashion-recommendation
   ```

2. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   pip install -r ml/requirements.txt

   # Initialize database
   python scripts/init_db.py
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure environment** (optional)
   ```bash
   cp .env.example .env
   # Edit .env with your preferences
   ```

### Running the Application

1. **Start the backend server**
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   - API will be available at `http://localhost:8000`
   - API docs at `http://localhost:8000/docs`

2. **Start the frontend development server**
   ```bash
   cd frontend
   npm run dev
   ```
   - App will be available at `http://localhost:5173`

3. **First-time ML model download**
   - On first API call, Qwen2-VL model (~15GB) will auto-download
   - Cached at `~/.cache/huggingface/hub/`
   - Initial load may take 30-60 seconds

## Project Structure

```
fashion-recommendation/
├── backend/
│   ├── app/              # FastAPI application
│   │   ├── core/         # Configuration, database
│   │   ├── models/       # SQLAlchemy models
│   │   ├── routes/       # API endpoints
│   │   ├── schemas/      # Pydantic validation
│   │   └── services/     # Business logic
│   ├── ml/               # Qwen2-VL integration
│   ├── scripts/          # Utility scripts
│   ├── uploads/          # User-uploaded images
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/        # React pages
│   │   └── services/     # API client
│   └── package.json
├── docs/                 # Documentation
├── .env.example          # Environment template
└── CLAUDE.md            # Claude Code integration
```

## Usage

1. **Register an account**
   - Navigate to the registration page
   - Provide username, email, password, body type, and city

2. **Build your wardrobe**
   - Upload photos of your clothing items
   - AI automatically detects category, color, season, and material

3. **Get recommendations**
   - Navigate to the recommendations page
   - Select occasion, style preference, and color preference
   - Receive AI-generated outfit combinations with reasoning

## API Endpoints

### User Management
- `POST /api/v1/users/register` - Create account
- `POST /api/v1/users/login` - Login
- `GET /api/v1/users/profile` - Get user profile

### Wardrobe
- `POST /api/v1/clothes/upload` - Upload clothing image
- `GET /api/v1/clothes/wardrobe` - Get wardrobe items

### Recommendations
- `GET /api/v1/recommend/outfits` - Get outfit recommendations

See full API documentation at `http://localhost:8000/docs`

## Configuration

Environment variables (`.env`):

```env
# Backend
BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost:3000
DATABASE_URL=sqlite:///./fashion.db

# ML Model
MODEL_NAME=Qwen/Qwen2-VL-7B-Instruct
DEVICE=auto  # auto, cuda, cpu

# File Upload
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=10
```

## Development

### Backend Development
```bash
cd backend
uvicorn app.main:app --reload
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Database Management
```bash
# Reset database
cd backend
python scripts/init_db.py
```

## Known Limitations

- **Security**: Authentication uses plaintext passwords (not production-ready)
- **Weather**: Currently returns mock data (no real API integration)
- **File Upload**: No validation for file size/type
- **Deletion**: Backend endpoint for deleting wardrobe items not implemented

See `CLAUDE.md` for detailed technical documentation and known issues.

## Performance Notes

### ML Model Inference
- **GPU (CUDA)**: ~2-5 seconds per inference
- **CPU**: ~15-30 seconds per inference
- **First load**: 30-60 seconds (model loading)
- **Memory**: ~8GB VRAM (GPU) or ~16GB RAM (CPU)

## Fine-Tuning (Optional)

Improve model performance with LoRA fine-tuning:

```bash
# Quick start
cd backend/ml/finetune
pip install -r requirements_lora.txt
cd ../training_data && python generate_from_db.py
cd ../finetune && python train_lora.py
```

**Full documentation**: `backend/ml/finetune/README.md`

**Benefits**:
- Better fashion terminology recognition
- More detailed outfit reasoning
- Consistent output format
- Personalized to your data

**Requirements**: 12GB+ GPU (or 16GB+ RAM for CPU training)

## Contributing

This is a personal project. For issues or suggestions, please open a GitHub issue.

## License

[Add your license here]

## Acknowledgments

- **Qwen2-VL Model**: Alibaba Cloud (Qwen Team)
- **Framework**: FastAPI, React
- **ML Libraries**: PyTorch, Transformers, qwen-vl-utils
