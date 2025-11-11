# LoRA Fine-tuning Guide for Qwen2-VL Fashion Model

This guide explains how to fine-tune the Qwen2-VL-7B model using LoRA (Low-Rank Adaptation) for improved fashion recommendation performance.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Requirements](#requirements)
3. [Setup](#setup)
4. [Preparing Training Data](#preparing-training-data)
5. [Configuration](#configuration)
6. [Training](#training)
7. [Testing](#testing)
8. [Deployment](#deployment)
9. [Troubleshooting](#troubleshooting)

## 🎯 Overview

### What is LoRA?

**LoRA (Low-Rank Adaptation)** is a parameter-efficient fine-tuning technique that:
- Trains only **<1%** of model parameters (~50-150MB adapters vs 15GB full model)
- Requires **~12GB GPU memory** with 4-bit quantization (vs 40GB+ for full fine-tuning)
- Trains **5-10x faster** than full fine-tuning
- Preserves the base model (adapters are separate files)
- Can be easily switched on/off

### Why Fine-tune for Fashion?

The base Qwen2-VL model is excellent but not specialized for fashion. Fine-tuning improves:
- **Fashion terminology accuracy** (e.g., "athleisure", "business casual")
- **Style advice quality** for different body types
- **Outfit combination logic** specific to your wardrobe structure
- **Consistency** in recommendations format

### Expected Improvements

After fine-tuning with 100-1000 examples:
- ✅ Better category/material recognition
- ✅ More detailed reasoning in recommendations
- ✅ Consistent JSON output format
- ✅ Domain-specific style advice
- ✅ Personalized to your user preferences

## 💻 Requirements

### Hardware Requirements

**Minimum (CPU Training)**:
- 16GB RAM
- 50GB disk space
- Training time: ~4-8 hours for 1000 examples

**Recommended (GPU Training)**:
- NVIDIA GPU with 12GB+ VRAM (RTX 3060, 4060 Ti, or better)
- 16GB system RAM
- 50GB disk space
- Training time: ~1-2 hours for 1000 examples

**Optimal (High-end GPU)**:
- NVIDIA GPU with 16GB+ VRAM (RTX 4080, 4090, A6000)
- 32GB system RAM
- Training time: ~30-60 minutes for 1000 examples

### Software Requirements

- Python 3.8+
- PyTorch 2.0+
- CUDA 11.8+ (for GPU training)

## 🔧 Setup

### 1. Install Dependencies

```bash
cd backend/ml/finetune

# Install LoRA-specific packages
pip install -r requirements_lora.txt

# Verify installation
python -c "import peft; import bitsandbytes; print('✓ Setup complete')"
```

### 2. Verify GPU (Optional)

```bash
python -c "import torch; print('CUDA available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```

## 📊 Preparing Training Data

### Option 1: Generate from Database (Recommended)

Extract existing wardrobe data and manual examples:

```bash
cd backend/ml/training_data
python generate_from_db.py
```

This creates `training_data.json` with:
- Clothing analysis examples (from your wardrobe items)
- Outfit recommendation examples (from user profiles)
- Manual style advice examples (curated fashion knowledge)

### Option 2: Manual Creation

Create `training_data.json` following this format:

```json
[
  {
    "task_type": "clothing_analysis",
    "image_path": "path/to/image.jpg",
    "instruction": "Analyze this clothing item...",
    "output": {
      "category": "shirt",
      "color": "navy blue",
      "season": ["spring", "fall"],
      "material": "cotton"
    }
  },
  {
    "task_type": "outfit_recommendation",
    "instruction": "Suggest outfits for...",
    "output": {
      "outfits": [...],
      "missing_items": [...]
    }
  }
]
```

See `data_format.json` for complete examples.

### Data Quality Tips

**For Best Results:**
- ✅ 100-200 examples: Noticeable improvement
- ✅ 500-1000 examples: Significant improvement
- ✅ 2000+ examples: Professional-level performance

**Quality over Quantity:**
- Diverse examples across all task types
- Accurate, detailed outputs
- Representative of real use cases
- Balanced distribution (don't over-represent one task)

## ⚙️ Configuration

Edit `config.yaml` to customize training:

### Key Parameters

```yaml
lora:
  r: 16              # Rank: 8=fast/basic, 16=balanced, 32=high quality
  lora_alpha: 32     # Usually 2x of r

training:
  num_train_epochs: 3                        # Epochs: 2-5 typical
  per_device_train_batch_size: 1            # Reduce if OOM
  gradient_accumulation_steps: 4            # Effective batch size
  learning_rate: 2.0e-4                     # Standard for LoRA

model:
  load_in_4bit: true                        # Use 4-bit quantization
```

### Memory vs Quality Trade-offs

**If you have limited GPU memory (8GB)**:
```yaml
lora:
  r: 8
training:
  per_device_train_batch_size: 1
  gradient_accumulation_steps: 8
model:
  load_in_4bit: true
```

**If you have plenty of memory (16GB+)**:
```yaml
lora:
  r: 32
training:
  per_device_train_batch_size: 2
  gradient_accumulation_steps: 2
model:
  load_in_4bit: false
  load_in_8bit: true
```

## 🚀 Training

### Start Training

```bash
cd backend/ml/finetune
python train_lora.py
```

### What Happens During Training

1. **Model Loading** (~30-60 seconds)
   - Downloads base model if needed
   - Applies 4-bit quantization
   - Initializes LoRA layers

2. **Data Preparation** (~10-30 seconds)
   - Loads training examples
   - Tokenizes text
   - Splits train/validation

3. **Training Loop** (1-4 hours depending on hardware)
   - Shows progress bar with loss metrics
   - Saves checkpoints every 100 steps
   - Evaluates on validation set

4. **Final Save**
   - Saves best model to `lora_adapters/final/`
   - ~50-150MB adapter files

### Monitoring Training

**TensorBoard** (optional):
```bash
tensorboard --logdir=../lora_adapters
# Open http://localhost:6006
```

**Watch for:**
- ✅ Loss decreasing steadily
- ✅ Validation loss similar to training loss
- ⚠️ If validation loss increases → overfitting (reduce epochs)
- ⚠️ If loss not decreasing → increase learning rate

### Training Time Estimates

| Hardware | 100 examples | 500 examples | 1000 examples |
|----------|--------------|--------------|---------------|
| CPU | 1 hour | 3-4 hours | 6-8 hours |
| RTX 3060 (12GB) | 15 min | 45 min | 1.5 hours |
| RTX 4080 (16GB) | 10 min | 30 min | 1 hour |
| RTX 4090 (24GB) | 5 min | 20 min | 40 min |

## 🧪 Testing

### Test the Fine-tuned Model

```bash
cd backend/ml/finetune
python test_lora.py
```

This runs 3 test scenarios:
1. **Clothing Analysis**: Analyze a clothing item description
2. **Outfit Recommendation**: Generate outfit combinations
3. **Style Advice**: Provide styling guidance

### Compare with Base Model

Test both models side-by-side:

```bash
# Test base model
python test_lora.py --base-only

# Test fine-tuned model
python test_lora.py
```

### What to Look For

**Good signs:**
- ✅ More detailed reasoning
- ✅ Consistent output format
- ✅ Accurate fashion terminology
- ✅ Relevant suggestions

**Bad signs:**
- ❌ Repetitive text
- ❌ Nonsensical combinations
- ❌ Generic advice
- → **Solution**: Train longer or add more diverse data

## 🚢 Deployment

### Enable in Production

The fine-tuned model is automatically used if adapters are found:

```python
# In inference.py (already updated)
model = FashionQwenModel(use_lora=True)  # Auto-loads adapters
```

### Verify Deployment

```bash
# Restart backend server
cd backend
uvicorn app.main:app --reload

# Check logs for:
# "📦 Loading LoRA adapters from: ..."
# "✅ LoRA fine-tuned model loaded successfully!"
```

### Manual Control

Disable LoRA if needed:
```python
model = FashionQwenModel(use_lora=False)  # Use base model
```

### Version Control

**Do NOT commit adapters to git** (too large). Instead:

1. Store adapters separately (cloud storage, model registry)
2. Add to `.gitignore`:
   ```
   backend/ml/lora_adapters/
   !backend/ml/lora_adapters/.gitkeep
   ```
3. Document adapter version in README

## 🔧 Troubleshooting

### Out of Memory (OOM)

**Error**: `RuntimeError: CUDA out of memory`

**Solutions**:
1. Reduce batch size:
   ```yaml
   per_device_train_batch_size: 1
   gradient_accumulation_steps: 8
   ```

2. Enable 4-bit quantization:
   ```yaml
   load_in_4bit: true
   ```

3. Reduce LoRA rank:
   ```yaml
   lora:
     r: 8
   ```

4. Enable gradient checkpointing (already enabled in config)

### Training Not Improving

**Symptoms**: Loss not decreasing

**Solutions**:
1. Increase learning rate:
   ```yaml
   learning_rate: 5.0e-4
   ```

2. Check data quality (look for errors in training_data.json)

3. Increase model capacity:
   ```yaml
   lora:
     r: 32
   ```

### Model Outputs Gibberish

**Symptoms**: Nonsensical text after training

**Solutions**:
1. Reduce learning rate:
   ```yaml
   learning_rate: 1.0e-4
   ```

2. Reduce epochs (may be overfitting):
   ```yaml
   num_train_epochs: 2
   ```

3. Add more training data (especially if <100 examples)

### Adapter Not Loading

**Error**: `No LoRA adapters found`

**Check**:
```bash
ls -la backend/ml/lora_adapters/final/
# Should see: adapter_config.json, adapter_model.bin
```

If missing, training didn't complete. Check training logs.

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'peft'`

**Solution**:
```bash
pip install -r finetune/requirements_lora.txt
```

## 📚 Advanced Topics

### Multi-GPU Training

Edit `config.yaml`:
```yaml
# Use all available GPUs
training:
  ddp_find_unused_parameters: false
```

Run with:
```bash
torchrun --nproc_per_node=2 train_lora.py
```

### Weights & Biases Logging

Enable in `config.yaml`:
```yaml
logging:
  use_wandb: true
  project_name: "fashion-recommendation-lora"
```

Sign up at https://wandb.ai and login:
```bash
wandb login
```

### Merging Adapters into Base Model

For deployment without PEFT dependency:
```python
from peft import PeftModel

base_model = Qwen2VLForConditionalGeneration.from_pretrained(...)
model = PeftModel.from_pretrained(base_model, "lora_adapters/final")
merged_model = model.merge_and_unload()
merged_model.save_pretrained("merged_model/")
```

⚠️ **Warning**: Merged model is ~15GB (vs 150MB adapters)

## 📖 Resources

- [PEFT Documentation](https://huggingface.co/docs/peft)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [Qwen2-VL Documentation](https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct)
- [BitsAndBytes](https://github.com/TimDettmers/bitsandbytes)

## 🤝 Support

For issues or questions:
1. Check this README
2. Review training logs in `lora_adapters/`
3. Test with `test_lora.py`
4. Open a GitHub issue with logs

## 📝 License

This fine-tuning pipeline is part of the Fashion Recommendation System project.
