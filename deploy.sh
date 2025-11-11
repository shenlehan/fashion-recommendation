#!/bin/bash
set -e

# Fashion Recommendation System - Docker Deployment Script
# This script automates the deployment process

echo "=========================================="
echo "Fashion Recommendation System Deployment"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker is installed${NC}"

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is installed${NC}"

# Check Docker daemon
if ! docker ps &> /dev/null; then
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    echo "Please start Docker Desktop or Docker service"
    exit 1
fi
echo -e "${GREEN}✓ Docker daemon is running${NC}"

# Check available disk space
AVAILABLE_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 25 ]; then
    echo -e "${YELLOW}⚠️  Warning: Low disk space (${AVAILABLE_SPACE}GB available, 25GB recommended)${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ Sufficient disk space (${AVAILABLE_SPACE}GB available)${NC}"
fi

echo ""
echo "=========================================="
echo "Deployment Options"
echo "=========================================="
echo "1. Quick Start (default configuration)"
echo "2. With GPU Support"
echo "3. Development Mode (with live logs)"
echo "4. Stop Services"
echo "5. Clean Everything (removes all data)"
echo ""
read -p "Select option (1-5): " OPTION

case $OPTION in
    1)
        echo ""
        echo -e "${BLUE}Starting services with default configuration...${NC}"
        echo ""

        # Check for .env file
        if [ ! -f .env ]; then
            echo -e "${YELLOW}No .env file found, using defaults from .env.docker${NC}"
            # Don't copy, let docker-compose use .env.docker via env_file
        fi

        # Pull latest images (if using pre-built)
        # docker-compose pull

        # Build and start
        echo "Building images (this may take 5-10 minutes first time)..."
        docker-compose build

        echo ""
        echo "Starting services..."
        docker-compose up -d

        echo ""
        echo -e "${GREEN}✓ Services started successfully!${NC}"
        echo ""
        echo "📊 Status:"
        docker-compose ps
        echo ""
        echo -e "${BLUE}📥 First-time setup: Downloading ML model (15GB, ~10-20 minutes)${NC}"
        echo ""
        echo "Monitor progress with:"
        echo "  docker-compose logs -f backend"
        echo ""
        echo "Access the application:"
        echo "  Frontend: http://localhost"
        echo "  Backend:  http://localhost:8000"
        echo "  API Docs: http://localhost:8000/docs"
        echo ""
        ;;

    2)
        echo ""
        echo -e "${BLUE}Checking GPU support...${NC}"

        # Check NVIDIA drivers
        if ! command -v nvidia-smi &> /dev/null; then
            echo -e "${RED}❌ NVIDIA drivers not found${NC}"
            echo "Please install NVIDIA drivers first"
            exit 1
        fi

        echo -e "${GREEN}✓ NVIDIA drivers found${NC}"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

        # Check NVIDIA Docker runtime
        if ! docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu20.04 nvidia-smi &> /dev/null; then
            echo -e "${RED}❌ NVIDIA Container Toolkit not configured${NC}"
            echo "Install with:"
            echo "  https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
            exit 1
        fi

        echo -e "${GREEN}✓ NVIDIA Container Toolkit configured${NC}"
        echo ""

        # Modify docker-compose.yml to enable GPU
        if ! grep -q "capabilities: \[gpu\]" docker-compose.yml; then
            echo -e "${YELLOW}Enabling GPU in docker-compose.yml...${NC}"
            echo ""
            echo "Please uncomment the GPU section in docker-compose.yml:"
            echo "  deploy:"
            echo "    resources:"
            echo "      reservations:"
            echo "        devices:"
            echo "          - driver: nvidia"
            echo "            count: 1"
            echo "            capabilities: [gpu]"
            echo ""
            read -p "Press Enter after editing the file..."
        fi

        docker-compose build
        docker-compose up -d

        echo ""
        echo -e "${GREEN}✓ Services started with GPU support!${NC}"
        echo ""
        docker-compose ps
        echo ""
        echo "Verify GPU usage:"
        echo "  docker exec fashion-backend nvidia-smi"
        ;;

    3)
        echo ""
        echo -e "${BLUE}Starting in development mode...${NC}"
        echo ""
        docker-compose build
        echo ""
        echo -e "${YELLOW}Starting with live logs (Ctrl+C to stop)...${NC}"
        echo ""
        docker-compose up
        ;;

    4)
        echo ""
        echo -e "${BLUE}Stopping services...${NC}"
        docker-compose down
        echo ""
        echo -e "${GREEN}✓ Services stopped${NC}"
        echo ""
        echo "Data preserved in:"
        echo "  - backend/fashion.db"
        echo "  - backend/uploads/"
        echo "  - backend/ml/lora_adapters/"
        ;;

    5)
        echo ""
        echo -e "${RED}⚠️  WARNING: This will remove ALL data!${NC}"
        echo ""
        echo "This will delete:"
        echo "  - All containers and volumes"
        echo "  - Database (backend/fashion.db)"
        echo "  - Uploaded images (backend/uploads/)"
        echo "  - LoRA adapters (backend/ml/lora_adapters/)"
        echo "  - Docker images"
        echo ""
        read -p "Are you sure? (type 'yes' to confirm): " CONFIRM

        if [ "$CONFIRM" != "yes" ]; then
            echo "Cancelled."
            exit 0
        fi

        echo ""
        echo "Stopping and removing containers..."
        docker-compose down -v

        echo "Removing data..."
        [ -f backend/fashion.db ] && rm backend/fashion.db && echo "  - Removed database"
        [ -d backend/uploads ] && rm -rf backend/uploads/* && echo "  - Cleared uploads"
        [ -d backend/ml/lora_adapters ] && rm -rf backend/ml/lora_adapters/* && echo "  - Cleared LoRA adapters"

        echo "Removing Docker images..."
        docker rmi fashion-backend fashion-frontend 2>/dev/null || true

        echo ""
        echo -e "${GREEN}✓ Everything cleaned${NC}"
        ;;

    *)
        echo -e "${RED}Invalid option${NC}"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Deployment Complete"
echo "=========================================="
