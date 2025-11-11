"""
Generate training data from existing database records
This script extracts user wardrobe items and creates training examples
"""
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.wardrobe import WardrobeItem


def generate_clothing_analysis_examples(session, output_file: str):
    """Generate training examples for clothing analysis task"""
    examples = []

    # Get all wardrobe items
    items = session.query(WardrobeItem).all()

    for item in items:
        example = {
            "task_type": "clothing_analysis",
            "image_path": item.image_path,
            "instruction": "Analyze this clothing item and provide detailed information about its category, color, season suitability, and material.",
            "output": {
                "category": item.category,
                "color": item.color,
                "season": item.season.split(",") if item.season else [],
                "material": item.material,
                "reasoning": f"This is a {item.color} {item.category} made of {item.material}, suitable for {item.season} seasons."
            }
        }
        examples.append(example)

    return examples


def generate_outfit_examples(session, output_file: str):
    """Generate training examples for outfit recommendations"""
    examples = []

    # Get all users with their wardrobes
    users = session.query(User).all()

    for user in users:
        items = session.query(WardrobeItem).filter(WardrobeItem.user_id == user.id).all()

        if len(items) < 2:
            continue  # Need at least 2 items to make an outfit

        # Format wardrobe for prompt
        wardrobe_text = "\n".join([
            f"- Item {i+1}: {item.name} ({item.category}, {item.color}, {item.material}, {item.season})"
            for i, item in enumerate(items)
        ])

        instruction = f"""Based on the following information, suggest complete outfit combinations:

User Profile:
- Body Type: {user.body_type}
- City: {user.city}

Wardrobe:
{wardrobe_text}

Weather: 20°C, sunny

Preferences:
- Occasion: casual
- Style: comfortable
- Color Preference: any"""

        example = {
            "task_type": "outfit_recommendation",
            "instruction": instruction,
            "output": {
                "outfits": [
                    {
                        "items": [item.name for item in items[:3]],  # Use first 3 items as example
                        "description": "Comfortable casual outfit for sunny weather",
                        "reasoning": "These items complement each other in color and style while being appropriate for warm weather."
                    }
                ],
                "missing_items": []
            }
        }
        examples.append(example)

    return examples


def add_manual_style_advice_examples():
    """Add manually curated style advice examples"""
    examples = [
        {
            "task_type": "style_advice",
            "instruction": "Provide style advice for a slim body type in business casual settings.",
            "output": "For slim body types in business casual:\n\n1. **Layering**: Add visual interest with layers like cardigans or blazers\n2. **Fit**: Avoid overly tight clothes; go for tailored fits\n3. **Patterns**: Horizontal stripes and checks add width\n4. **Colors**: Lighter colors can add visual volume\n5. **Structure**: Structured jackets add definition\n\nKey tip: Focus on proper fit rather than tight clothes."
        },
        {
            "task_type": "style_advice",
            "instruction": "Provide style advice for an athletic body type for casual weekend wear.",
            "output": "For athletic body types in casual settings:\n\n1. **Tops**: Fitted tees and polos highlight your build\n2. **Bottoms**: Well-fitted jeans or chinos\n3. **Layering**: Denim jackets, bomber jackets work great\n4. **Colors**: Bold colors and color blocking\n5. **Avoid**: Baggy clothes that hide your physique\n\nKey tip: Emphasize shoulder fit in all garments."
        },
        {
            "task_type": "style_advice",
            "instruction": "Provide style advice for a plus-size body type for formal events.",
            "output": "For plus-size body types in formal settings:\n\n1. **Fit**: Well-tailored clothing is crucial; avoid too tight or too loose\n2. **Cuts**: A-line dresses, wrap styles, or straight-cut suits\n3. **Colors**: Dark colors are slimming; monochrome looks elongate\n4. **Fabrics**: Choose structured fabrics that drape well\n5. **Details**: V-necks and vertical details create length\n\nKey tip: Confidence and proper fit are your best accessories."
        },
        {
            "task_type": "color_coordination",
            "instruction": "Suggest color combinations for a navy blue blazer.",
            "output": "Navy blue blazer color combinations:\n\n**Classic Combinations:**\n- White shirt + khaki pants (timeless)\n- Light blue shirt + gray trousers (professional)\n- Pink shirt + navy pants (modern)\n\n**Bold Combinations:**\n- Burgundy shirt + dark jeans (sophisticated)\n- Striped shirt + chinos (casual)\n\n**Avoid:** Black shirts (too formal), bright neon colors\n\nKey tip: Navy is versatile—it pairs with almost any color except black."
        },
        {
            "task_type": "seasonal_advice",
            "instruction": "What should I wear for spring weather (15-20°C)?",
            "output": "Spring weather (15-20°C) outfit guide:\n\n**Layers are key:**\n1. **Base**: Light long-sleeve shirt or t-shirt\n2. **Mid**: Light sweater, cardigan, or denim jacket\n3. **Bottom**: Chinos, jeans, or light trousers\n4. **Footwear**: Sneakers, loafers, or ankle boots\n\n**Fabrics**: Cotton, light wool, linen blends\n**Colors**: Pastels, earth tones, light blues and greens\n\n**Pro tip**: Carry a light jacket as temperatures fluctuate throughout the day."
        }
    ]
    return examples


def main():
    """Generate all training data"""
    # Database connection
    DATABASE_URL = "sqlite:///../../fashion.db"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        print("Generating training data from database...")

        # Generate examples
        clothing_examples = generate_clothing_analysis_examples(session, "")
        outfit_examples = generate_outfit_examples(session, "")
        style_examples = add_manual_style_advice_examples()

        # Combine all examples
        all_examples = clothing_examples + outfit_examples + style_examples

        # Save to file
        output_file = Path(__file__).parent / "training_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_examples, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Generated {len(all_examples)} training examples:")
        print(f"  - {len(clothing_examples)} clothing analysis examples")
        print(f"  - {len(outfit_examples)} outfit recommendation examples")
        print(f"  - {len(style_examples)} style advice examples")
        print(f"\n✓ Saved to: {output_file}")

        # Show statistics
        print("\n📊 Dataset Statistics:")
        task_types = {}
        for ex in all_examples:
            task_type = ex.get("task_type", "unknown")
            task_types[task_type] = task_types.get(task_type, 0) + 1

        for task_type, count in task_types.items():
            print(f"  - {task_type}: {count} examples")

        print("\n💡 Next steps:")
        print("  1. Review and edit training_data.json to improve quality")
        print("  2. Add more manual examples for better coverage")
        print("  3. Run the fine-tuning script: python finetune/train_lora.py")

    finally:
        session.close()


if __name__ == "__main__":
    main()
