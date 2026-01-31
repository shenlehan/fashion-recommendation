#!/usr/bin/env python3
"""
检查模型文件位置和大小
"""
import os
from pathlib import Path

print("=" * 70)
print("Qwen 模型文件检查工具")
print("=" * 70)

# 1. 检查项目内的 models 目录
project_root = Path(__file__).resolve().parent
local_model_path = project_root / "models" / "Qwen" / "Qwen3-VL-8B-Instruct"

print(f"\n📁 项目根目录: {project_root}")
print(f"📁 预期模型路径: {local_model_path}")
print(f"✅ 模型存在: {local_model_path.exists()}")

if local_model_path.exists():
    # 计算目录大小
    total_size = 0
    file_count = 0
    for root, dirs, files in os.walk(local_model_path):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.exists(file_path):
                total_size += os.path.getsize(file_path)
                file_count += 1
    
    size_gb = total_size / (1024 ** 3)
    print(f"📊 模型大小: {size_gb:.2f} GB")
    print(f"📊 文件数量: {file_count}")
    print(f"\n📝 模型文件列表:")
    for item in sorted(local_model_path.iterdir())[:20]:
        if item.is_file():
            size_mb = item.stat().st_size / (1024 ** 2)
            print(f"   - {item.name} ({size_mb:.1f} MB)")
        else:
            print(f"   - {item.name}/ (目录)")
else:
    print("❌ 本地模型不存在")

# 2. 检查 HuggingFace 缓存目录
print(f"\n{'=' * 70}")
print("🔍 检查 HuggingFace 缓存目录")
print("=" * 70)

# 常见的 HuggingFace 缓存位置
cache_locations = [
    Path.home() / ".cache" / "huggingface",
    Path.home() / ".cache" / "huggingface" / "hub",
    Path("/root/.cache/huggingface") if os.name != 'nt' else None,
    Path("/root/.cache/huggingface/hub") if os.name != 'nt' else None,
]

# 检查环境变量
hf_home = os.environ.get("HF_HOME")
if hf_home:
    cache_locations.append(Path(hf_home))

transformers_cache = os.environ.get("TRANSFORMERS_CACHE")
if transformers_cache:
    cache_locations.append(Path(transformers_cache))

found_cache = False
for cache_path in cache_locations:
    if cache_path and cache_path.exists():
        print(f"\n✅ 找到缓存目录: {cache_path}")
        found_cache = True
        
        # 查找 Qwen 相关文件
        qwen_files = []
        try:
            for root, dirs, files in os.walk(cache_path):
                if "qwen" in root.lower() or "Qwen3" in root:
                    qwen_files.append(root)
                    if len(qwen_files) >= 5:  # 最多显示5个
                        break
        except PermissionError:
            print("   ⚠️ 权限不足，无法遍历此目录")
            continue
        
        if qwen_files:
            print(f"   📦 找到 Qwen 相关文件:")
            for qf in qwen_files[:5]:
                print(f"      - {qf}")
        else:
            print("   ℹ️ 未找到 Qwen 相关文件")

if not found_cache:
    print("❌ 未找到 HuggingFace 缓存目录")

# 3. 检查磁盘空间
print(f"\n{'=' * 70}")
print("💾 磁盘空间检查")
print("=" * 70)

try:
    import shutil
    usage = shutil.disk_usage(str(project_root))
    total_gb = usage.total / (1024 ** 3)
    used_gb = usage.used / (1024 ** 3)
    free_gb = usage.free / (1024 ** 3)
    used_percent = (usage.used / usage.total) * 100
    
    print(f"总容量: {total_gb:.2f} GB")
    print(f"已使用: {used_gb:.2f} GB ({used_percent:.1f}%)")
    print(f"剩余空间: {free_gb:.2f} GB")
    
    if free_gb < 20:
        print(f"⚠️ 警告: 剩余空间不足 20GB，可能无法下载模型")
    elif free_gb < 30:
        print(f"⚠️ 注意: 剩余空间有限，建议清理后再下载模型")
    else:
        print(f"✅ 磁盘空间充足")
except Exception as e:
    print(f"无法获取磁盘信息: {e}")

print(f"\n{'=' * 70}")
print("📋 总结")
print("=" * 70)

if local_model_path.exists():
    print("✅ 模型已下载到项目目录，可以直接使用")
    print(f"   位置: {local_model_path}")
elif found_cache:
    print("⚠️ 模型可能在 HuggingFace 缓存中，但不在项目目录")
    print("   建议将缓存移动到项目目录，或修改代码使用缓存路径")
else:
    print("❌ 未找到模型文件，需要下载")
    print("   预计下载大小: ~15GB")
    print("   预计下载时间: 10-30分钟（取决于网络速度）")

print("=" * 70)
