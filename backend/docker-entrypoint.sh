#!/bin/bash
set -e

echo "=========================================="
echo "Fashion Recommendation Backend Starting"
echo "=========================================="

# Wait for database to be ready (if using external DB)
# For SQLite, this is not necessary but kept for future compatibility
sleep 2

# Initialize database if it doesn't exist
if [ ! -f "/app/fashion.db" ]; then
    echo "📊 Database not found. Initializing..."
    python scripts/init_db.py
    echo "✓ Database initialized"
else
    echo "✓ Database already exists"
fi

# Create uploads directory if it doesn't exist
mkdir -p /app/uploads
echo "✓ Uploads directory ready"

# Create lora_adapters directory if it doesn't exist
mkdir -p /app/ml/lora_adapters
echo "✓ LoRA adapters directory ready"

# Check for LoRA adapters
if [ -d "/app/ml/lora_adapters/final" ] || [ -d "/app/ml/lora_adapters/checkpoint-"* ]; then
    echo "✓ LoRA adapters found - will use fine-tuned model"
else
    echo "ℹ️  No LoRA adapters found - will use base model"
    echo "   To fine-tune: docker exec -it fashion-backend python ml/finetune/train_lora.py"
fi

# Check GPU availability
if command -v nvidia-smi &> /dev/null; then
    echo "🎮 GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo "💻 Running on CPU mode"
fi

echo ""
echo "🚀 Starting FastAPI server..."
echo "   API: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "=========================================="
echo ""

# Execute the main command
exec "$@"
