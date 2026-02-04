from app.core.database import engine, Base
from app.models.user import User
from app.models.wardrobe import WardrobeItem


def init_database():
  print("正在重建数据库...")
  try:
    # 删除所有表
    Base.metadata.drop_all(bind=engine)
    print("已删除旧表")
    
    # 重新创建所有表
    Base.metadata.create_all(bind=engine)
    print("完成！")
    print("已创建：fashion_recommendation.db")

    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"当前表：{tables}")

    if 'users' in tables:
      print("users 表已存在！")
    else:
      print("users 表不存在！")

    if 'wardrobe_items' in tables:
      print("wardrobe_items 表已存在！")
    else:
      print("wardrobe_items 表不存在！")

  except Exception as e:
    print(f"创建失败：{e}")
    import traceback
    traceback.print_exc()


if __name__ == "__main__":
  init_database()
