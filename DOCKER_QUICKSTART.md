# Docker Quick Start ⚡

Get the Fashion Recommendation System running in 3 commands!

## Prerequisites

- Docker 20.10+ installed
- 16GB RAM
- 25GB free disk space

## Installation (3 Steps)

### 1. Start the Application

```bash
docker-compose up -d
```

### 2. Wait for Model Download (First Time Only)

```bash
docker-compose logs -f backend
```

**What to expect:**
- First time: ~10-20 minutes (downloads 15GB model)
- Subsequent starts: ~30 seconds

**Look for:**
```
✓ Model loaded successfully!
🚀 Starting FastAPI server...
```

Press `Ctrl+C` when you see "Model loaded successfully!"

### 3. Access the Application

- **Frontend**: http://localhost
- **API Docs**: http://localhost:8000/docs

That's it! 🎉

## Quick Commands

```bash
# View logs
docker-compose logs -f backend

# Stop everything
docker-compose down

# Restart
docker-compose restart

# Enter backend container
docker exec -it fashion-backend bash

# Check status
docker-compose ps
```

## Verify It's Working

### Test Backend

```bash
curl http://localhost:8000/health
```

Should return: `{"status":"healthy"}`

### Test Frontend

Open browser: http://localhost

Should see the login page.

## First Steps

1. **Register an account**: http://localhost → Register
2. **Upload clothing**: Go to Wardrobe → Upload images
3. **Get recommendations**: Go to Recommendations

## GPU Support (Optional)

### Check GPU

```bash
docker exec fashion-backend nvidia-smi
```

### Enable GPU

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

2. Uncomment in `docker-compose.yml`:
   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             count: 1
             capabilities: [gpu]
   ```

3. Restart:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

**Performance boost**: 5-10x faster inference!

## Troubleshooting

### Ports Already in Use?

**Error**: `port is already allocated`

**Fix**: Change ports in `docker-compose.yml`:
```yaml
services:
  backend:
    ports:
      - "8080:8000"  # Changed from 8000
  frontend:
    ports:
      - "3000:80"    # Changed from 80
```

### Container Exits Immediately?

**Check logs**:
```bash
docker-compose logs backend
```

Common fixes:
- Increase Docker memory limit (Docker Desktop → Settings)
- Check disk space: `df -h`
- Ensure ports 80 and 8000 are free

### Model Download Slow/Stuck?

**Check progress**:
```bash
docker-compose logs -f backend | grep -i download
```

**Speed up** (if you have the model cached locally):
```bash
# Copy from local cache
cp -r ~/.cache/huggingface/hub/* backend/.cache/
```

### Can't Connect to Backend?

1. **Check backend is running**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check frontend API URL**:
   ```bash
   docker logs fashion-frontend | grep VITE_API_URL
   ```

## Data Persistence

Your data is saved in:
- `backend/fashion.db` - Database
- `backend/uploads/` - Images
- `backend/ml/lora_adapters/` - Fine-tuned models
- Docker volume: `huggingface-cache` - ML model

**Safe to restart** without losing data!

## Fine-Tuning (Optional)

Improve model performance:

```bash
# 1. Generate training data
docker exec fashion-backend python ml/training_data/generate_from_db.py

# 2. Start training (1-2 hours on GPU)
docker exec fashion-backend python ml/finetune/train_lora.py

# 3. Restart to use fine-tuned model
docker-compose restart backend
```

## Stopping & Cleaning Up

```bash
# Stop (keeps data)
docker-compose down

# Stop and remove all data
docker-compose down -v
rm backend/fashion.db
rm -rf backend/uploads/*
```

## Next Steps

- **Full documentation**: [DOCKER.md](DOCKER.md)
- **Application guide**: [README.md](README.md)
- **Fine-tuning**: [backend/ml/finetune/README.md](backend/ml/finetune/README.md)

## Common Use Cases

### Development Mode

```bash
# Start with live logs
docker-compose up
```

### Production Mode

```bash
# Start in background
docker-compose up -d

# Monitor with
docker-compose logs -f
```

### Testing Changes

```bash
# Rebuild after code changes
docker-compose build
docker-compose up -d
```

## Resource Usage

**CPU Mode**:
- RAM: ~12-16GB
- Inference: 15-30 seconds

**GPU Mode**:
- VRAM: ~8GB
- Inference: 2-5 seconds

Check usage:
```bash
docker stats fashion-backend
```

## Getting Help

1. **Check logs**: `docker-compose logs -f`
2. **Read troubleshooting**: [DOCKER.md](DOCKER.md#troubleshooting)
3. **Open issue**: Include logs and `docker-compose ps` output

## Success Checklist

- [ ] Containers running: `docker-compose ps`
- [ ] Backend healthy: `curl http://localhost:8000/health`
- [ ] Frontend accessible: Open http://localhost
- [ ] Can register account
- [ ] Can upload images
- [ ] Can get recommendations

If all checked ✅ - You're good to go! 🎉
