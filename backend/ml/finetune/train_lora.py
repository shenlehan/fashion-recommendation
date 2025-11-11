"""
LoRA Fine-tuning Script for Qwen2-VL-7B
Trains the model on fashion-specific tasks using Parameter-Efficient Fine-Tuning
"""
import os
import sys
import json
import yaml
import torch
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass

from transformers import (
    Qwen2VLForConditionalGeneration,
    AutoProcessor,
    TrainingArguments,
    Trainer,
    BitsAndBytesConfig
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    TaskType
)
from datasets import Dataset, DatasetDict
from tqdm import tqdm


def load_config(config_path: str = "config.yaml") -> Dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config


def load_training_data(data_path: str) -> List[Dict]:
    """Load training data from JSON file"""
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def format_prompt(example: Dict) -> str:
    """Format training example into prompt format for Qwen2-VL"""
    task_type = example.get("task_type", "general")
    instruction = example.get("instruction", "")
    output = example.get("output", "")

    # Convert output to string if it's a dict
    if isinstance(output, dict):
        output = json.dumps(output, indent=2, ensure_ascii=False)

    # Qwen2 chat format
    prompt = f"""<|im_start|>system
You are a professional fashion stylist and wardrobe consultant. Provide detailed, personalized fashion advice based on user preferences, body types, and weather conditions.<|im_end|>
<|im_start|>user
{instruction}<|im_end|>
<|im_start|>assistant
{output}<|im_end|>"""

    return prompt


def prepare_dataset(data: List[Dict], config: Dict) -> DatasetDict:
    """Prepare dataset for training"""
    print("📊 Preparing dataset...")

    # Format all examples
    formatted_data = []
    for example in tqdm(data, desc="Formatting examples"):
        formatted_data.append({
            "text": format_prompt(example),
            "task_type": example.get("task_type", "general")
        })

    # Create dataset
    dataset = Dataset.from_list(formatted_data)

    # Split into train/validation
    validation_split = config["data"]["validation_split"]
    dataset = dataset.train_test_split(test_size=validation_split, seed=42)

    print(f"✓ Training examples: {len(dataset['train'])}")
    print(f"✓ Validation examples: {len(dataset['test'])}")

    return dataset


def create_model_and_tokenizer(config: Dict):
    """Create model with LoRA configuration"""
    print("🔧 Loading base model...")

    model_name = config["model"]["name"]

    # Quantization config for 4-bit training
    if config["model"]["load_in_4bit"]:
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )
    else:
        bnb_config = None

    # Load model
    model = Qwen2VLForConditionalGeneration.from_pretrained(
        model_name,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
        torch_dtype=torch.bfloat16 if config["model"]["torch_dtype"] == "bfloat16" else torch.float16,
    )

    # Load processor (tokenizer + image processor for Qwen2-VL)
    processor = AutoProcessor.from_pretrained(
        model_name,
        trust_remote_code=True
    )

    print("✓ Model loaded successfully")

    # Prepare model for k-bit training
    if bnb_config is not None:
        model = prepare_model_for_kbit_training(model)
        print("✓ Model prepared for 4-bit training")

    # Configure LoRA
    lora_config = LoraConfig(
        r=config["lora"]["r"],
        lora_alpha=config["lora"]["lora_alpha"],
        target_modules=config["lora"]["target_modules"],
        lora_dropout=config["lora"]["lora_dropout"],
        bias=config["lora"]["bias"],
        task_type=TaskType.CAUSAL_LM,
    )

    # Apply LoRA
    model = get_peft_model(model, lora_config)

    # Print trainable parameters
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"\n📊 Model Statistics:")
    print(f"  Trainable parameters: {trainable_params:,} ({100 * trainable_params / total_params:.2f}%)")
    print(f"  Total parameters: {total_params:,}")

    return model, processor


def tokenize_function(examples: Dict, processor, max_length: int):
    """Tokenize examples for training"""
    # Tokenize using the processor
    tokenized = processor(
        text=examples["text"],
        padding="max_length",
        truncation=True,
        max_length=max_length,
        return_tensors="pt"
    )

    # Set labels (for language modeling, labels = input_ids)
    tokenized["labels"] = tokenized["input_ids"].clone()

    return tokenized


def main():
    """Main training function"""
    print("=" * 60)
    print("🚀 LoRA Fine-tuning for Fashion Recommendation System")
    print("=" * 60)

    # Load configuration
    config_path = Path(__file__).parent / "config.yaml"
    config = load_config(config_path)

    # Load training data
    data_path = Path(__file__).parent.parent / "training_data" / "training_data.json"
    if not data_path.exists():
        print(f"❌ Training data not found at {data_path}")
        print("💡 Please run: python training_data/generate_from_db.py")
        sys.exit(1)

    training_data = load_training_data(data_path)
    print(f"✓ Loaded {len(training_data)} training examples")

    # Prepare dataset
    dataset = prepare_dataset(training_data, config)

    # Create model and tokenizer
    model, processor = create_model_and_tokenizer(config)

    # Tokenize dataset
    print("\n🔤 Tokenizing dataset...")
    tokenized_dataset = dataset.map(
        lambda x: tokenize_function(x, processor, config["data"]["max_seq_length"]),
        batched=True,
        remove_columns=dataset["train"].column_names,
        desc="Tokenizing"
    )

    # Training arguments
    output_dir = Path(__file__).parent.parent / config["training"]["output_dir"]
    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=config["training"]["num_train_epochs"],
        per_device_train_batch_size=config["training"]["per_device_train_batch_size"],
        gradient_accumulation_steps=config["training"]["gradient_accumulation_steps"],
        learning_rate=config["training"]["learning_rate"],
        warmup_steps=config["training"]["warmup_steps"],
        logging_steps=config["training"]["logging_steps"],
        save_steps=config["training"]["save_steps"],
        save_total_limit=config["training"]["save_total_limit"],
        bf16=config["training"]["bf16"],
        fp16=config["training"]["fp16"],
        optim=config["training"]["optim"],
        max_grad_norm=config["training"]["max_grad_norm"],
        weight_decay=config["training"]["weight_decay"],
        evaluation_strategy="steps",
        eval_steps=config["training"]["save_steps"],
        load_best_model_at_end=True,
        report_to="tensorboard" if config["logging"]["use_tensorboard"] else "none",
        gradient_checkpointing=config["advanced"]["gradient_checkpointing"],
    )

    # Create trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset["train"],
        eval_dataset=tokenized_dataset["test"],
    )

    # Start training
    print("\n🎯 Starting training...")
    print(f"  Output directory: {output_dir}")
    print(f"  Epochs: {config['training']['num_train_epochs']}")
    print(f"  Effective batch size: {config['training']['per_device_train_batch_size'] * config['training']['gradient_accumulation_steps']}")
    print(f"  Learning rate: {config['training']['learning_rate']}")
    print()

    try:
        trainer.train()

        # Save final model
        final_output_dir = output_dir / "final"
        trainer.model.save_pretrained(final_output_dir)
        processor.save_pretrained(final_output_dir)

        print("\n" + "=" * 60)
        print("✅ Training completed successfully!")
        print(f"📁 Model saved to: {final_output_dir}")
        print("=" * 60)

        print("\n💡 Next steps:")
        print("  1. Test the fine-tuned model: python finetune/test_lora.py")
        print("  2. Update inference.py to use LoRA adapters")
        print("  3. Restart the backend server to use the fine-tuned model")

    except Exception as e:
        print(f"\n❌ Training failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
