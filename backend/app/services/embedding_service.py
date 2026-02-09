"""
向量化服务模块 - 负责生成和管理衣物的语义向量
"""
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import threading


class EmbeddingService:
    """衣橱向量化服务（单例模式）"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """延迟初始化，避免重复加载"""
        if self._initialized:
            return
            
        print("🔧 初始化向量化服务...")
        
        # 设置完全离线模式
        import os
        os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'  # 强制离线
        os.environ['HF_HUB_OFFLINE'] = '1'  # 禁用hub检查
        os.environ['HF_DATASETS_OFFLINE'] = '1'  # 禁用datasets检查
        
        # 1. 加载Sentence-Transformer模型（支持中英文）
        model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        print(f"📥 加载Embedding模型: {model_name}")
        print(f"💡 强制离线模式，从缓存加载: ~/.cache/huggingface/")
        
        try:
            # 先尝试从本地缓存目录直接加载（完全离线）
            import os
            from pathlib import Path
            cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
            model_cache_path = cache_dir / "models--sentence-transformers--paraphrase-multilingual-mpnet-base-v2" / "snapshots"
            
            if model_cache_path.exists():
                # 查找最新的snapshot目录
                snapshot_dirs = [d for d in model_cache_path.iterdir() if d.is_dir()]
                if snapshot_dirs:
                    latest_snapshot = max(snapshot_dirs, key=lambda p: p.stat().st_mtime)
                    print(f"💾 使用本地缓存: {latest_snapshot}")
                    self.encoder = SentenceTransformer(str(latest_snapshot), device='cpu')
                    self.model_available = True
                    print(f"✅ 模型加载成功，向量维度: {self.encoder.get_sentence_embedding_dimension()}")
                else:
                    raise FileNotFoundError("未找到snapshot目录")
            else:
                raise FileNotFoundError(f"未找到缓存目录: {model_cache_path}")
                
        except Exception as e:
            print(f"⚠️  Embedding模型加载失败: {e}")
            print(f"🚨 向量检索功能将被禁用，推荐将使用全量查询")
            self.encoder = None
            self.model_available = False
            # 不抛异常，允许系统降级运行
        
        # 2. 初始化ChromaDB客户端（仅当模型可用时）
        if self.model_available:
            chroma_data_path = os.path.join(os.getcwd(), "chroma_data")
            os.makedirs(chroma_data_path, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(
                path=chroma_data_path,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # 3. 创建或获取衣橱向量集合
            self.wardrobe_collection = self.chroma_client.get_or_create_collection(
                name="wardrobe_items",
                metadata={"description": "用户衣橱语义向量存储"}
            )
            
            print(f"✅ ChromaDB初始化成功，数据路径: {chroma_data_path}")
            print(f"📊 当前向量库中已有 {self.wardrobe_collection.count()} 条记录")
        else:
            self.chroma_client = None
            self.wardrobe_collection = None
            print(f"⚠️  ChromaDB未初始化，向量检索功能不可用")
        
        self._initialized = True
    
    def generate_embedding(self, item: Dict[str, Any]) -> List[float]:
        """
        为单个衣物生成语义向量
        """
        if not self.model_available:
            return []  # 模型不可用时返回空向量
        
        # 构建语义文本（使用英文字段，模型对英文理解更准确）
        text_parts = [
            item.get("name_en", item.get("name", "")),
            item.get("color_en", item.get("color", "")),
            item.get("material_en", item.get("material", "")),
            item.get("season", ""),
            item.get("category", "")
        ]
        
        # 过滤空值，拼接成语义文本
        semantic_text = " ".join([part for part in text_parts if part]).strip()
        
        if not semantic_text:
            print(f"⚠️  警告: 衣物信息为空，使用默认向量")
            semantic_text = "unknown clothing item"
        
        # 生成向量（CPU推理约50-100ms）
        embedding = self.encoder.encode(semantic_text, convert_to_numpy=True)
        return embedding.tolist()
    
    def add_item(self, item_id: int, item: Dict[str, Any]) -> bool:
        """将衣物向量添加到ChromaDB"""
        if not self.model_available:
            return True  # 模型不可用时静默返回成功
        
        try:
            embedding = self.generate_embedding(item)
            
            # 构建元数据（用于过滤查询）
            metadata = {
                "category": item.get("category", "unknown"),
                "season": item.get("season", "all"),
                "color_en": item.get("color_en", ""),
                "user_id": str(item.get("user_id", 0))
            }
            
            # 添加到ChromaDB
            self.wardrobe_collection.add(
                ids=[str(item_id)],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[item.get("name_en", item.get("name", "Unknown"))]
            )
            
            print(f"✅ 向量添加成功: item_id={item_id}, text='{item.get('name_en', '')}'")
            return True
            
        except Exception as e:
            print(f"❌ 向量添加失败: item_id={item_id}, error={e}")
            return False
    
    def delete_item(self, item_id: int) -> bool:
        """从ChromaDB删除衣物向量"""
        if not self.model_available:
            return True  # 模型不可用时静默返回成功
            
        try:
            self.wardrobe_collection.delete(ids=[str(item_id)])
            print(f"✅ 向量删除成功: item_id={item_id}")
            return True
        except Exception as e:
            print(f"❌ 向量删除失败: item_id={item_id}, error={e}")
            return False
    
    def search_similar_items(
        self,
        query_text: str,
        user_id: int,
        top_k: int = 15,
        season_filter: Optional[List[str]] = None,
        category_filter: Optional[str] = None
    ) -> List[int]:
        """基于语义检索相似衣物"""
        if not self.model_available:
            return []  # 模型不可用时返回空列表，触发降级查询
        
        try:
            # 生成查询向量
            query_embedding = self.encoder.encode(query_text, convert_to_numpy=True).tolist()
            
            # 构建过滤条件
            where_filter = {"user_id": str(user_id)}
            
            # 添加类别过滤
            if category_filter:
                where_filter["category"] = category_filter
            
            # 向量检索
            results = self.wardrobe_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k * 2,  # 多取一些，用于季节过滤
                where=where_filter
            )
            
            if not results["ids"] or not results["ids"][0]:
                return []
            
            # 提取item_id列表
            item_ids = [int(id_str) for id_str in results["ids"][0]]
            
            # 季节过滤（后处理）
            if season_filter:
                filtered_ids = []
                for i, item_id in enumerate(item_ids):
                    metadata = results["metadatas"][0][i]
                    item_seasons = metadata.get("season", "").split("/")
                    if any(s in season_filter for s in item_seasons):
                        filtered_ids.append(item_id)
                item_ids = filtered_ids[:top_k]
            else:
                item_ids = item_ids[:top_k]
            
            return item_ids
            
        except Exception as e:
            print(f"❌ 向量检索失败: error={e}")
            return []
    
    def batch_add_items(self, items: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        批量添加衣物向量（用于数据迁移）
        
        Args:
            items: 衣物列表，每个必须包含 'id' 字段
        
        Returns:
            {"success": 成功数量, "failed": 失败数量}
        """
        success_count = 0
        failed_count = 0
        
        for item in items:
            item_id = item.get("id")
            if not item_id:
                print(f"⚠️  跳过: 衣物缺少id字段")
                failed_count += 1
                continue
            
            if self.add_item(item_id, item):
                success_count += 1
            else:
                failed_count += 1
        
        print(f"\n{'='*60}")
        print(f"批量向量化完成: 成功={success_count}, 失败={failed_count}")
        print(f"{'='*60}\n")
        
        return {"success": success_count, "failed": failed_count}


# 全局单例
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """获取向量化服务单例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
