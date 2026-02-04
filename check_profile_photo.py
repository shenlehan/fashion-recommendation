#!/usr/bin/env python3
"""
个人照片诊断脚本 - 检查照片存储和访问路径
"""
import os
import sys
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent
BACKEND_DIR = PROJECT_ROOT / "backend"

print("=" * 60)
print("个人照片诊断工具")
print("=" * 60)
print()

# 1. 检查uploads目录位置
print("【1】检查 uploads 目录...")
possible_dirs = [
    BACKEND_DIR / "uploads",
    PROJECT_ROOT / "uploads",
]

uploads_dir = None
for dir_path in possible_dirs:
    if dir_path.exists():
        uploads_dir = dir_path
        print(f"✓ 找到 uploads 目录: {dir_path}")
        break

if not uploads_dir:
    print("✗ 未找到 uploads 目录！")
    print("  预期位置:")
    for dir_path in possible_dirs:
        print(f"    - {dir_path}")
    print()
    print("  建议：运行后端服务后会自动创建该目录")
    sys.exit(1)

print()

# 2. 列出uploads目录中的个人照片
print("【2】扫描个人照片文件...")
profile_photos = []
for file_path in uploads_dir.glob("profile_*"):
    if file_path.is_file() and file_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        size_kb = file_path.stat().st_size / 1024
        profile_photos.append({
            'name': file_path.name,
            'path': file_path,
            'size': f"{size_kb:.2f} KB"
        })

if profile_photos:
    print(f"✓ 找到 {len(profile_photos)} 个个人照片:")
    for photo in profile_photos:
        print(f"    - {photo['name']} ({photo['size']})")
else:
    print("✗ 未找到任何个人照片文件（以 profile_ 开头）")
    print("  建议：去个人资料页面重新上传照片")

print()

# 3. 检查数据库中的照片记录
print("【3】检查数据库照片记录...")
try:
    # 导入数据库模块
    sys.path.insert(0, str(BACKEND_DIR))
    from app.core.database import SessionLocal
    from app.models.user import User
    
    db = SessionLocal()
    users_with_photos = db.query(User).filter(User.profile_photo.isnot(None)).all()
    
    if users_with_photos:
        print(f"✓ 数据库中有 {len(users_with_photos)} 个用户上传了照片:")
        for user in users_with_photos:
            print(f"    - 用户 {user.username} (ID: {user.id})")
            print(f"      照片文件名: {user.profile_photo}")
            
            # 检查文件是否存在
            photo_path = uploads_dir / user.profile_photo
            if photo_path.exists():
                print(f"      状态: ✓ 文件存在")
            else:
                print(f"      状态: ✗ 文件缺失！")
                print(f"      预期路径: {photo_path}")
    else:
        print("⚠ 数据库中没有用户上传照片记录")
    
    db.close()
except Exception as e:
    print(f"✗ 无法读取数据库: {e}")
    print("  建议：确保后端服务至少运行过一次")

print()

# 4. 检查后端静态文件配置
print("【4】检查后端配置...")
main_py = BACKEND_DIR / "app" / "main.py"
if main_py.exists():
    with open(main_py, 'r', encoding='utf-8') as f:
        content = f.read()
        if 'app.mount("/uploads"' in content:
            print("✓ 后端已配置 /uploads 路由")
        else:
            print("✗ 后端未正确配置静态文件路由")
else:
    print(f"✗ 找不到 {main_py}")

print()

# 5. 生成测试URL
print("【5】访问路径测试...")
if profile_photos:
    photo_name = profile_photos[0]['name']
    print("  如果后端运行在 http://localhost:6008，照片应该可以通过以下URL访问:")
    print(f"    http://localhost:6008/uploads/{photo_name}")
    print()
    print("  前端API配置检查:")
    print("    - 如果使用代理：API_ORIGIN = '' （相对路径）")
    print("    - 如果直连：API_ORIGIN = 'http://localhost:6008'")

print()
print("=" * 60)
print("诊断完成")
print("=" * 60)
