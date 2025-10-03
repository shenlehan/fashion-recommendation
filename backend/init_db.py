"""
数据库初始化脚本
用于创建所有数据库表
"""
from app.core.database import engine, Base
from app.models.user import User
from app.models.wardrobe import WardrobeItem

def init_database():
    print("正在创建数据库表...")
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建完成！")
        print("数据库文件：fashion.db")
        
        # 检查表是否创建成功
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"✅ 当前数据库中的表：{tables}")
        
        # 检查是否有 users 表
        if 'users' in tables:
            print("✅ users 表已存在")
        else:
            print("❌ users 表不存在！")
            
        if 'wardrobe_items' in tables:
            print("✅ wardrobe_items 表已存在")
        else:
            print("❌ wardrobe_items 表不存在！")
            
    except Exception as e:
        print(f"❌ 创建数据库表失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    init_database()
