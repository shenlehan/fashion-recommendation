# Fashion Recommendation System - Startup Guide

## Quick Start

### Start All Services
```bash
bash start.sh
```

This will:
- Stop any existing services
- Start backend (FastAPI + Qwen3-VL) on port 8000
- Start frontend (React + Vite) on port 3000
- Perform health checks

**Note**: The Qwen3-VL model (8B parameters) loads on first image upload, which takes ~2 minutes.

### Stop All Services
```bash
bash stop.sh
```

### View Logs
```bash
# Backend logs
tail -f /tmp/backend.log

# Frontend logs
tail -f /tmp/frontend.log

# Both at once
tail -f /tmp/backend.log /tmp/frontend.log
```

## Access Points

- **Frontend**: http://YOUR_IP:3000
- **Backend API**: http://YOUR_IP:8000
- **API Docs**: http://YOUR_IP:8000/docs
- **Health Check**: http://YOUR_IP:8000/health

## Manual Start (Alternative)

### Backend
```bash
cd backend
source ~/miniconda3/etc/profile.d/conda.sh
conda activate pytorch
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
source ~/.nvm/nvm.sh
npm run dev
```

## Troubleshooting

### Services won't start
Check if ports are already in use:
```bash
netstat -tlnp | grep -E "3000|8000"
# or
ss -tlnp | grep -E "3000|8000"
```

### Out of memory
The Qwen3-VL model requires:
- **GPU**: ~16GB VRAM (with float16)
- **RAM**: ~5-8GB additional

If multiple upload requests come simultaneously, the thread-safe loading prevents multiple model loads.

### Frontend can't connect to backend
Make sure:
1. Backend is running: `curl http://localhost:8000/health`
2. Ports 3000 and 8000 are open in security group
3. Frontend .env points to correct backend URL

## System Requirements

- **OS**: Linux (Ubuntu recommended)
- **GPU**: NVIDIA GPU with 16GB+ VRAM (A10/V100/A100)
- **RAM**: 30GB+ recommended
- **Python**: 3.10+ (via conda pytorch environment)
- **Node.js**: v18+ (via nvm)

## Files Generated

- `/tmp/backend.log` - Backend application logs
- `/tmp/frontend.log` - Frontend development server logs
- `backend/fashion.db` - SQLite database
- `backend/uploads/` - Uploaded clothing images

