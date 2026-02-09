"""
测试脚本：验证向量检索效果
"""
import sys
from pathlib import Path

# 将backend目录添加到Python路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.services.embedding_service import get_embedding_service


def test_vector_search():
    """测试向量检索功能"""
    print("="*80)
    print("向量检索测试")
    print("="*80)
    
    try:
        # 1. 初始化向量服务
        print("\n📥 初始化向量化服务...")
        embedding_service = get_embedding_service()
        
        # 2. 查看当前向量库状态
        total_count = embedding_service.wardrobe_collection.count()
        print(f"✅ 当前向量库中有 {total_count} 条记录")
        
        if total_count == 0:
            print("\n⚠️  向量库为空，请先运行 migrate_embeddings.py 进行数据迁移")
            return
        
        # 3. 测试不同场景的检索
        test_cases = [
            {
                "name": "冬季寒冷天气",
                "query": "0C cold winter outerwear",
                "top_k": 5
            },
            {
                "name": "夏季休闲",
                "query": "28C sunny casual summer",
                "top_k": 5
            },
            {
                "name": "商务正式",
                "query": "formal business meeting",
                "top_k": 5
            },
            {
                "name": "约会浪漫风格",
                "query": "date romantic style",
                "top_k": 5
            }
        ]
        
        for idx, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*80}")
            print(f"测试场景 {idx}: {test_case['name']}")
            print(f"查询文本: \"{test_case['query']}\"")
            print(f"{'='*80}")
            
            # 执行检索（假设user_id=1）
            # 注意：实际使用时需要传入真实的user_id
            try:
                # 这里使用全局搜索（不过滤user_id）来演示
                results = embedding_service.wardrobe_collection.query(
                    query_texts=[test_case['query']],
                    n_results=test_case['top_k']
                )
                
                if results['ids'] and results['ids'][0]:
                    print(f"\n✅ 检索到 {len(results['ids'][0])} 件相关衣物:")
                    for i, (item_id, document, metadata) in enumerate(
                        zip(results['ids'][0], results['documents'][0], results['metadatas'][0]), 1
                    ):
                        print(f"  {i}. ID={item_id}: {document}")
                        print(f"     类别={metadata.get('category')}, 季节={metadata.get('season')}, 颜色={metadata.get('color_en')}")
                else:
                    print(f"⚠️  未检索到相关衣物")
                    
            except Exception as e:
                print(f"❌ 检索失败: {e}")
        
        # 4. 测试相似度对比
        print(f"\n{'='*80}")
        print("相似度测试：对比不同查询的向量距离")
        print(f"{'='*80}")
        
        queries = [
            "black jacket",
            "dark outerwear",
            "white shirt"
        ]
        
        print("\n生成查询向量...")
        for query in queries:
            embedding = embedding_service.encoder.encode(query)
            print(f"  \"{query}\": 维度={len(embedding)}, 前5维={embedding[:5]}")
        
        print("\n✅ 向量检索测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试过程发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_vector_search()
