"""
Initialize the database
"""
from app.core.database import engine, Base
from app.models.user import User
from app.models.wardrobe import WardrobeItem

def init_database():
    print("Creating database...")
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("Completed!")
        print("Created：fashion.db")
        
        # 检查表是否创建成功
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Current tables：{tables}")
        
        # 检查是否有 users 表
        if 'users' in tables:
            print("users already exists!")
        else:
            print("users doesn't exists!")
            
        if 'wardrobe_items' in tables:
            print("wardrobe_items already exists!")
        else:
            print("wardrobe_items doesn't exists!")
            
    except Exception as e:
        print(f"Fail to create {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    init_database()
