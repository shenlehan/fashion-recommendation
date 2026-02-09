"""
数据迁移脚本：为现有衣橱数据生成向量
"""
import sys
from pathlib import Path

# 将backend目录添加到Python路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal
from app.models.wardrobe import WardrobeItem
from app.services.embedding_service import get_embedding_service


def migrate_embeddings():
    """为所有现有衣物生成向量"""
    print("="*80)
    print("开始向量化迁移任务...")
    print("="*80)
    
    db = SessionLocal()
    
    try:
        # 1. 查询所有衣物
        all_items = db.query(WardrobeItem).all()
        total_count = len(all_items)
        
        if total_count == 0:
            print("\n⚠️  数据库中没有衣物数据，无需迁移")
            return
        
        print(f"\n📊 找到 {total_count} 件衣物需要向量化")
        print(f"{'='*80}")
        
        # 2. 初始化向量化服务
        embedding_service = get_embedding_service()
        
        # 3. 批量处理
        success_count = 0
        failed_count = 0
        
        for idx, item in enumerate(all_items, 1):
            try:
                print(f"\n[{idx}/{total_count}] 处理: {item.name} (ID: {item.id})")
                
                # 构建衣物数据
                item_data = {
                    "id": item.id,
                    "user_id": item.user_id,
                    "name": item.name,
                    "name_en": item.name_en or "",
                    "color_en": item.color_en or "",
                    "material_en": item.material_en or "",
                    "season": item.season,
                    "category": item.category
                }
                
                # 生成并添加向量
                if embedding_service.add_item(item.id, item_data):
                    success_count += 1
                    print(f"  ✅ 成功")
                else:
                    failed_count += 1
                    print(f"  ❌ 失败")
                    
            except Exception as e:
                failed_count += 1
                print(f"  ❌ 异常: {e}")
        
        # 4. 输出统计信息
        print(f"\n{'='*80}")
        print(f"迁移完成!")
        print(f"{'='*80}")
        print(f"总计: {total_count} 件")
        print(f"成功: {success_count} 件")
        print(f"失败: {failed_count} 件")
        print(f"成功率: {success_count/total_count*100:.1f}%")
        print(f"{'='*80}")
        
        # 5. 验证ChromaDB中的记录数
        if embedding_service.wardrobe_collection is not None:
            chroma_count = embedding_service.wardrobe_collection.count()
            print(f"\n📊 ChromaDB中当前共有 {chroma_count} 条向量记录")
        else:
            print(f"\n⚠️  ChromaDB未初始化，无法统计向量记录数")
        
    except Exception as e:
        print(f"\n❌ 迁移过程发生错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    migrate_embeddings()
