# LoRA Fine-tuning Quick Start

Get your fashion model fine-tuned in 3 simple steps! ⚡

## Prerequisites

- Python 3.8+
- 12GB+ GPU (recommended) or 16GB+ RAM (CPU)
- 50GB free disk space

## Step 1: Install Dependencies (2 minutes)

```bash
cd backend/ml/finetune
pip install -r requirements_lora.txt
```

## Step 2: Generate Training Data (1 minute)

```bash
cd ../training_data
python generate_from_db.py
```

This creates training examples from your existing database.

**Expected output:**
```
✓ Generated 50+ training examples
✓ Saved to: training_data.json
```

## Step 3: Start Training (30-120 minutes)

```bash
cd ../finetune
python train_lora.py
```

**What to expect:**
- **GPU (RTX 3060+)**: ~1-2 hours
- **CPU**: ~4-8 hours

**You'll see:**
```
🚀 LoRA Fine-tuning for Fashion Recommendation System
✓ Loaded 50 training examples
🎯 Starting training...
Epoch 1/3: 100%|████████| 50/50 [10:23<00:00]
```

## Step 4: Test Your Model (2 minutes)

```bash
python test_lora.py
```

This tests the fine-tuned model on sample fashion tasks.

## Step 5: Deploy (30 seconds)

Restart your backend server - that's it! The model automatically loads the fine-tuned adapters.

```bash
cd ../../..
uvicorn app.main:app --reload
```

**Look for in logs:**
```
✅ LoRA fine-tuned model loaded successfully!
```

## Troubleshooting

### Out of Memory?

Edit `config.yaml`:
```yaml
lora:
  r: 8  # Reduce from 16
training:
  per_device_train_batch_size: 1
  gradient_accumulation_steps: 8  # Increase from 4
```

### Need More Training Data?

Edit `training_data/training_data.json` and add more examples. Aim for 100-500 examples for best results.

### Model Not Improving?

Check `config.yaml`:
```yaml
training:
  learning_rate: 5.0e-4  # Increase from 2.0e-4
  num_train_epochs: 5    # Increase from 3
```

## Next Steps

- 📖 Read full documentation: [README.md](README.md)
- ⚙️ Customize configuration: [config.yaml](config.yaml)
- 📊 Add more training data: [data_format.json](../training_data/data_format.json)

## Expected Results

After fine-tuning:
- ✅ More detailed fashion analysis
- ✅ Better outfit recommendations
- ✅ Consistent output format
- ✅ Improved style advice

**Compare before/after:**

### Before (Base Model)
```
Recommendation: This outfit looks good for the weather.
```

### After (Fine-tuned)
```
Recommendation: For 15°C partly cloudy weather with your athletic build,
I recommend pairing the white cotton t-shirt with blue jeans and the black
leather jacket. This creates a balanced streetwear aesthetic while providing
adequate warmth. The leather jacket's structured shoulders complement your
frame, and the neutral color palette maintains versatility.
```

## Support

- Full guide: `finetune/README.md`
- Issues: GitHub issues
- Questions: Check troubleshooting section in README.md

Happy fine-tuning! 🎉
