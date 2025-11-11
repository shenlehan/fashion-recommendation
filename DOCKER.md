# Docker Deployment Guide

Complete guide to running the Fashion Recommendation System with Docker.

## 🚀 Quick Start (3 Commands)

```bash
# 1. Start everything
docker-compose up -d

# 2. Wait for model download (first time only, ~15GB)
docker-compose logs -f backend

# 3. Access the application
# Frontend: http://localhost
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

That's it! The application is now running.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Usage](#usage)
4. [GPU Support](#gpu-support)
5. [Configuration](#configuration)
6. [Data Persistence](#data-persistence)
7. [Fine-Tuning with Docker](#fine-tuning-with-docker)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Topics](#advanced-topics)

## 🔧 Prerequisites

### Required
- **Docker**: 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: 2.0+ (included with Docker Desktop)
- **Disk Space**: 25GB free (15GB for model, 5GB for images, 5GB for containers)
- **RAM**: 16GB minimum (CPU mode) or 8GB (GPU mode)

### Optional (for GPU acceleration)
- **NVIDIA GPU**: 8GB+ VRAM
- **NVIDIA Docker Runtime**: ([Install Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html))
- **CUDA**: 11.8+ compatible drivers

### Check Prerequisites

```bash
# Check Docker
docker --version
# Should show: Docker version 20.10.x or higher

# Check Docker Compose
docker-compose --version
# Should show: Docker Compose version 2.x.x or higher

# Check GPU (optional)
nvidia-smi
# Should show your GPU if NVIDIA drivers installed
```

## 📦 Installation

### Step 1: Clone Repository

```bash
git clone <your-repo-url>
cd fashion-recommendation
```

### Step 2: Configure Environment (Optional)

```bash
# Copy environment template
cp .env.docker .env

# Edit if needed (optional for quick start)
nano .env
```

Default configuration works out of the box!

### Step 3: Start Services

```bash
docker-compose up -d
```

**What happens:**
- ✅ Builds backend image (~5 minutes first time)
- ✅ Builds frontend image (~3 minutes first time)
- ✅ Creates database
- ✅ Downloads ML model (~10-20 minutes first time, 15GB)
- ✅ Starts services

### Step 4: Monitor Startup

```bash
# Watch backend logs (especially during first model download)
docker-compose logs -f backend

# You'll see:
# - Database initialization
# - Model download progress
# - "Model loaded successfully!" when ready
```

### Step 5: Access Application

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🎮 Usage

### Starting the Application

```bash
# Start all services
docker-compose up -d

# Start and view logs
docker-compose up

# Start specific service
docker-compose up -d backend
```

### Stopping the Application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose down -v
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Restarting Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

### Checking Status

```bash
# Show running containers
docker-compose ps

# Show resource usage
docker stats fashion-backend fashion-frontend
```

## 🎮 GPU Support

### Enable GPU Acceleration

1. **Install NVIDIA Container Toolkit**:
   ```bash
   # Ubuntu/Debian
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
     sudo tee /etc/apt/sources.list.d/nvidia-docker.list

   sudo apt-get update
   sudo apt-get install -y nvidia-container-toolkit
   sudo systemctl restart docker
   ```

2. **Enable in docker-compose.yml**:
   ```yaml
   services:
     backend:
       deploy:
         resources:
           reservations:
             devices:
               - driver: nvidia
                 count: 1  # or 'all' for all GPUs
                 capabilities: [gpu]
   ```

3. **Restart services**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. **Verify GPU usage**:
   ```bash
   docker exec fashion-backend nvidia-smi
   ```

### Performance Comparison

| Mode | First Load | Inference | Memory |
|------|------------|-----------|--------|
| CPU | ~60s | ~15-30s | 16GB RAM |
| GPU (RTX 3060) | ~30s | ~2-5s | 8GB VRAM |
| GPU (RTX 4090) | ~20s | ~1-2s | 8GB VRAM |

## ⚙️ Configuration

### Environment Variables

Edit `.env` file:

```bash
# Backend
DATABASE_URL=sqlite:///./fashion.db
BACKEND_CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:80

# ML Model
MODEL_NAME=Qwen/Qwen2-VL-7B-Instruct
DEVICE=auto  # auto, cuda, cpu

# Frontend
VITE_API_URL=http://localhost:8000
```

### Port Configuration

Change ports in `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8080:8000"  # Change 8080 to your preferred port

  frontend:
    ports:
      - "3000:80"    # Change 3000 to your preferred port
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

## 💾 Data Persistence

### What is Persisted

The following data persists between container restarts:

1. **Database**: `./backend/fashion.db`
   - User accounts
   - Wardrobe items
   - All application data

2. **Uploaded Images**: `./backend/uploads/`
   - User clothing photos

3. **LoRA Adapters**: `./backend/ml/lora_adapters/`
   - Fine-tuned model weights

4. **Model Cache**: Docker volume `huggingface-cache`
   - Downloaded ML model (~15GB)
   - Shared between restarts

### Backup Data

```bash
# Backup database
cp backend/fashion.db backend/fashion.db.backup

# Backup uploads
tar -czf uploads-backup.tar.gz backend/uploads/

# Backup everything
docker-compose down
tar -czf fashion-backup.tar.gz backend/
```

### Restore Data

```bash
# Restore database
cp backend/fashion.db.backup backend/fashion.db

# Restore uploads
tar -xzf uploads-backup.tar.gz

# Restart
docker-compose up -d
```

### Reset Everything

```bash
# Stop services
docker-compose down -v

# Remove data
rm backend/fashion.db
rm -rf backend/uploads/*
rm -rf backend/ml/lora_adapters/*

# Start fresh
docker-compose up -d
```

## 🎯 Fine-Tuning with Docker

### Inside Running Container

```bash
# 1. Enter container
docker exec -it fashion-backend bash

# 2. Install LoRA dependencies (if not already installed)
pip install -r ml/finetune/requirements_lora.txt

# 3. Generate training data
cd ml/training_data
python generate_from_db.py

# 4. Start fine-tuning
cd ../finetune
python train_lora.py

# 5. Exit container
exit

# 6. Restart backend to load fine-tuned model
docker-compose restart backend
```

### Using Docker Exec (One-liner)

```bash
# Generate training data
docker exec fashion-backend python ml/training_data/generate_from_db.py

# Start training
docker exec fashion-backend python ml/finetune/train_lora.py
```

### Monitor Training

```bash
# Watch training logs
docker exec fashion-backend tail -f ml/finetune/logs/training.log

# Check GPU usage during training
watch -n 1 docker exec fashion-backend nvidia-smi
```

## 🔍 Troubleshooting

### Container Won't Start

**Symptom**: Container exits immediately

**Check logs**:
```bash
docker-compose logs backend
```

**Common causes**:
1. Port already in use
   ```bash
   # Check what's using port 8000
   lsof -i :8000
   # Change port in docker-compose.yml
   ```

2. Insufficient memory
   ```bash
   # Check Docker memory limit
   docker info | grep Memory
   # Increase in Docker Desktop settings
   ```

### Model Download Fails

**Symptom**: "Failed to download model" in logs

**Solutions**:
```bash
# 1. Check internet connection
curl -I https://huggingface.co

# 2. Manually download model
docker exec -it fashion-backend bash
cd /root/.cache/huggingface
huggingface-cli download Qwen/Qwen2-VL-7B-Instruct

# 3. Check disk space
df -h
```

### Frontend Can't Connect to Backend

**Symptom**: API calls fail in browser console

**Check**:
1. Backend is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. CORS configuration:
   ```bash
   docker exec fashion-backend cat app/core/config.py
   # Should include your frontend URL
   ```

3. Network connectivity:
   ```bash
   docker network inspect fashion-network
   ```

### Database Locked Error

**Symptom**: "database is locked" errors

**Solution**:
```bash
# Stop all services
docker-compose down

# Remove database lock
rm backend/fashion.db-shm backend/fashion.db-wal

# Restart
docker-compose up -d
```

### Out of Memory During Model Load

**Symptom**: Container killed during startup

**Solutions**:
1. Increase Docker memory limit (Docker Desktop → Settings → Resources)
2. Use CPU mode instead of GPU (set `DEVICE=cpu` in `.env`)
3. Close other applications to free RAM

### GPU Not Detected

**Check NVIDIA runtime**:
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu20.04 nvidia-smi
```

If fails:
```bash
# Reinstall NVIDIA Container Toolkit
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

## 🔬 Advanced Topics

### Multi-Container Logs

```bash
# Install ctop for monitoring
docker run --rm -ti -v /var/run/docker.sock:/var/run/docker.sock quay.io/vektorlab/ctop:latest
```

### Custom Network

```yaml
# docker-compose.yml
networks:
  fashion-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.25.0.0/16
```

### Production Deployment

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d
```

### Scaling

```bash
# Run multiple backend instances (requires load balancer)
docker-compose up -d --scale backend=3
```

### Health Monitoring

```bash
# Check health status
docker inspect --format='{{.State.Health.Status}}' fashion-backend

# Get detailed health info
docker inspect fashion-backend | jq '.[0].State.Health'
```

### Build Cache Management

```bash
# Clear build cache
docker builder prune

# Rebuild without cache
docker-compose build --no-cache

# Remove all unused images
docker image prune -a
```

### Export/Import Images

```bash
# Export images
docker save -o fashion-backend.tar fashion-backend
docker save -o fashion-frontend.tar fashion-frontend

# Import images on another machine
docker load -i fashion-backend.tar
docker load -i fashion-frontend.tar
```

## 📊 Resource Requirements

### Minimum Configuration
- **CPU**: 4 cores
- **RAM**: 16GB
- **Disk**: 25GB
- **Network**: 50 Mbps (for initial model download)

### Recommended Configuration
- **CPU**: 8 cores
- **RAM**: 32GB
- **GPU**: NVIDIA with 8GB+ VRAM
- **Disk**: 50GB SSD
- **Network**: 100 Mbps

### Container Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 16G
        reservations:
          cpus: '2'
          memory: 8G
```

## 🛡️ Security Notes

- Default configuration is for **development only**
- For production:
  - [ ] Change default secrets in `.env`
  - [ ] Enable HTTPS
  - [ ] Use non-root user (already configured)
  - [ ] Implement authentication
  - [ ] Use secrets management
  - [ ] Enable firewall rules
  - [ ] Regular security updates

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker)
- [HuggingFace Models](https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct)

## 🤝 Support

For issues:
1. Check logs: `docker-compose logs`
2. Check this troubleshooting guide
3. Open a GitHub issue with logs and configuration

## 📝 Quick Reference

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Logs
docker-compose logs -f

# Restart
docker-compose restart

# Rebuild
docker-compose build

# Shell access
docker exec -it fashion-backend bash

# Clean everything
docker-compose down -v && docker system prune -af
```
