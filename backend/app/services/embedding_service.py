"""
向量化服务模块 - 负责生成和管理衣物的语义向量（多模态：文本+图像）
"""
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import threading
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor
import numpy as np


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
        
        # 设置完全离线模式（在加载任何模型之前）
        import os
        from pathlib import Path
        
        os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'  # 强制离线
        os.environ['HF_HUB_OFFLINE'] = '1'  # 禁用hub检查
        os.environ['HF_DATASETS_OFFLINE'] = '1'  # 禁用datasets检查
        os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(Path.home() / ".cache" / "huggingface")
        
        # 1. 加载文本Embedding模型（支持中英文）
        text_model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        print(f"📥 加载文本Embedding模型: {text_model_name}")
        print(f"💡 强制离线模式，从缓存加载: ~/.cache/huggingface/")
        
        try:
            # 先尝试从本地缓存目录直接加载（完全离线）
            cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
            text_cache_path = cache_dir / "models--sentence-transformers--paraphrase-multilingual-mpnet-base-v2" / "snapshots"
            
            if text_cache_path.exists():
                # 查找最新的snapshot目录
                snapshot_dirs = [d for d in text_cache_path.iterdir() if d.is_dir()]
                if snapshot_dirs:
                    latest_snapshot = max(snapshot_dirs, key=lambda p: p.stat().st_mtime)
                    print(f"💾 使用本地缓存: {latest_snapshot}")
                    
                    # 方法：从snapshot加载，但手动加载pooling配置
                    # 1) 先加载基础模型
                    from sentence_transformers import models
                    word_embedding_model = models.Transformer(str(latest_snapshot))
                    
                    # 2) 加载pooling配置
                    pooling_config_path = latest_snapshot / "1_Pooling" / "config.json"
                    if pooling_config_path.exists():
                        import json
                        with open(pooling_config_path) as f:
                            pooling_config = json.load(f)
                        # 正确解析pooling参数（config中是布尔值字段）
                        pooling_model = models.Pooling(
                            word_embedding_model.get_word_embedding_dimension(),
                            pooling_mode_mean_tokens=pooling_config.get('pooling_mode_mean_tokens', True),
                            pooling_mode_cls_token=pooling_config.get('pooling_mode_cls_token', False),
                            pooling_mode_max_tokens=pooling_config.get('pooling_mode_max_tokens', False)
                        )
                        print(f"✅ Pooling配置加载成功: mean={pooling_config.get('pooling_mode_mean_tokens')}, cls={pooling_config.get('pooling_mode_cls_token')}")
                    else:
                        # 没有pooling配置，使用默认mean pooling
                        pooling_model = models.Pooling(
                            word_embedding_model.get_word_embedding_dimension(),
                            pooling_mode_mean_tokens=True
                        )
                        print(f"⚠️  使用默认mean pooling")
                    
                    # 3) 组装完整模型
                    self.text_encoder = SentenceTransformer(modules=[word_embedding_model, pooling_model])
                    self.text_dim = self.text_encoder.get_sentence_embedding_dimension()
                    print(f"✅ 文本模型加载成功，向量维度: {self.text_dim}")
                else:
                    raise FileNotFoundError("未找到snapshot目录")
            else:
                raise FileNotFoundError(f"未找到缓存目录: {text_cache_path}")
            
            # 2. 加载CLIP图像模型
            clip_model_name = "openai/clip-vit-base-patch32"
            print(f"📥 加载CLIP图像模型: {clip_model_name}")
            
            clip_cache_path = cache_dir / "models--openai--clip-vit-base-patch32" / "snapshots"
            if clip_cache_path.exists():
                snapshot_dirs = [d for d in clip_cache_path.iterdir() if d.is_dir()]
                if snapshot_dirs:
                    latest_clip = max(snapshot_dirs, key=lambda p: p.stat().st_mtime)
                    print(f"💾 使用CLIP本地缓存: {latest_clip}")
                    # 使用safetensors格式，避免PyTorch版本限制
                    self.clip_model = CLIPModel.from_pretrained(str(latest_clip), local_files_only=True, use_safetensors=True)
                    self.clip_processor = CLIPProcessor.from_pretrained(str(latest_clip), local_files_only=True)
                else:
                    raise FileNotFoundError("CLIP缓存目录存在但无snapshot")
            else:
                raise FileNotFoundError(f"未找到CLIP缓存: {clip_cache_path}")
            
            self.clip_model.eval()  # 推理模式
            # CLIP get_image_features实际输出vision_model的hidden_size，不是projection_dim
            self.image_dim = self.clip_model.config.vision_config.hidden_size  # 768维
            print(f"✅ CLIP模型加载成功，图像向量维度: {self.image_dim}")
            
            # 计算融合向量维度
            self.total_dim = self.text_dim + self.image_dim  # 768 + 768 = 1536
            print(f"🔗 多模态融合向量总维度: {self.total_dim}")
            
            self.model_available = True
                
        except Exception as e:
            print(f"⚠️  Embedding模型加载失败: {e}")
            print(f"🚨 向量检索功能将被禁用，推荐将使用全量查询")
            self.text_encoder = None
            self.clip_model = None
            self.clip_processor = None
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
                metadata={"description": "用户衣橱语义向量存储（多模态1536维）"}
            )
            
            print(f"✅ ChromaDB初始化成功，数据路径: {chroma_data_path}")
            print(f"📊 当前向量库中已有 {self.wardrobe_collection.count()} 条记录")
        else:
            self.chroma_client = None
            self.wardrobe_collection = None
            print(f"⚠️  ChromaDB未初始化，向量检索功能不可用")
        
        self._initialized = True
    
    def generate_text_embedding(self, item: Dict[str, Any]) -> List[float]:
        """
        生成文本语义向量
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
        embedding = self.text_encoder.encode(semantic_text, convert_to_numpy=True)
        return embedding.tolist()
    
    def generate_image_embedding(self, image_path: str) -> List[float]:
        """
        生成图像语义向量（使用CLIP）
        """
        if not self.model_available or not self.clip_model:
            return []  # CLIP模型不可用时返回空向量
        
        try:
            # 加载图像
            image = Image.open(image_path).convert("RGB")
            
            # CLIP预处理
            inputs = self.clip_processor(images=image, return_tensors="pt")
            
            # 生成图像向量（使用CLIP的vision encoder）
            with torch.no_grad():
                outputs = self.clip_model.get_image_features(**inputs)
            
            # 提取真正的tensor（outputs是BaseModelOutputWithPooling对象）
            # 直接访问底层tensor数据
            if hasattr(outputs, 'last_hidden_state'):
                image_features = outputs.last_hidden_state[:, 0, :]  # 取CLS token
            elif hasattr(outputs, 'pooler_output'):
                image_features = outputs.pooler_output
            else:
                # 如果是tensor就直接用
                image_features = outputs
            
            # 归一化向量（现在是真正的tensor了）
            norm = torch.norm(image_features, p=2, dim=-1, keepdim=True)
            image_features = image_features / norm
            
            return image_features.squeeze().cpu().numpy().tolist()
            
        except Exception as e:
            print(f"❌ 图像向量生成失败: {e}")
            return []
    
    def generate_embedding(self, item: Dict[str, Any], image_path: Optional[str] = None) -> List[float]:
        """
        生成多模态融合向量（文本 + 图像）
        
        Args:
            item: 衣物信息字典
            image_path: 衣物图像路径（可选）
        
        Returns:
            融合向量 (768维文本 + 768维图像 = 1536维)
        """
        if not self.model_available:
            return []  # 模型不可用时返回空向量
        
        # 1. 生成文本向量
        text_vec = self.generate_text_embedding(item)
        
        # 2. 生成图像向量（如果提供了图像路径）
        if image_path and os.path.exists(image_path):
            image_vec = self.generate_image_embedding(image_path)
            if not image_vec:
                # 图像向量生成失败，使用零向量填充
                image_vec = [0.0] * self.image_dim
        else:
            # 无图像，使用零向量
            image_vec = [0.0] * self.image_dim
        
        # 3. 拼接融合向量
        fused_embedding = text_vec + image_vec
        
        return fused_embedding
    
    def add_item(self, item_id: int, item: Dict[str, Any], image_path: Optional[str] = None) -> bool:
        """将衣物向量添加到ChromaDB"""
        if not self.model_available:
            return True  # 模型不可用时静默返回成功
        
        try:
            # 生成多模态融合向量
            embedding = self.generate_embedding(item, image_path)
            
            # 构建元数据（用于混合检索的精确过滤）
            metadata = {
                "category": item.get("category", "unknown"),
                "season": item.get("season", "all"),
                "color_en": item.get("color_en", ""),
                "material_en": item.get("material_en", ""),  # 新增：材质
                "style": item.get("style", ""),  # 新增：风格
                "user_id": str(item.get("user_id", 0))
            }
            
            # 添加到ChromaDB
            self.wardrobe_collection.add(
                ids=[str(item_id)],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[item.get("name_en", item.get("name", "Unknown"))]
            )
            
            print(f"✅ 向量添加成功: item_id={item_id}, text='{item.get('name_en', '')}', has_image={bool(image_path)}")
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
        query_text: str = None,
        query_image_path: str = None,
        user_id: int = None,
        top_k: int = 15,
        season_filter: Optional[List[str]] = None,
        category_filter: Optional[str] = None,
        color_filter: Optional[str] = None,  # 新增：颜色过滤
        material_filter: Optional[str] = None,  # 新增：材质过滤
        min_score: float = 0.0  # 新增：最低相似度阈值
    ) -> List[int]:
        """
        混合检索策略：向量相似度 + 精确过滤 + 重排序
        
        Args:
            query_text: 文本查询（可选）
            query_image_path: 图像查询路径（可选）
            user_id: 用户ID
            top_k: 返回结果数量
            season_filter: 季节过滤
            category_filter: 类别过滤
            color_filter: 颜色过滤（模糊匹配）
            material_filter: 材质过滤（模糊匹配）
            min_score: 最低相似度阈值（0-1）
        """
        if not self.model_available:
            return []  # 模型不可用时返回空列表，触发降级查询
        
        try:
            # 生成查询向量
            query_embedding = []
            
            # 1. 文本向量
            if query_text:
                text_vec = self.text_encoder.encode(query_text, convert_to_numpy=True).tolist()
            else:
                text_vec = [0.0] * self.text_dim
            
            # 2. 图像向量
            if query_image_path and os.path.exists(query_image_path):
                image_vec = self.generate_image_embedding(query_image_path)
                if not image_vec:
                    image_vec = [0.0] * self.image_dim
            else:
                # 纯文本查询：图像维度填充中间值，降低对相似度的影响
                # 假设图像向量的平均值约为0（经过L2归一化），使用零向量最小化距离差异
                image_vec = [0.0] * self.image_dim
            
            # 3. 融合查询向量
            query_embedding = text_vec + image_vec
            
            # 构建过滤条件（ChromaDB要求多条件使用$and操作符）
            if category_filter and user_id:
                where_filter = {
                    "$and": [
                        {"user_id": str(user_id)},
                        {"category": category_filter}
                    ]
                }
            elif user_id:
                where_filter = {"user_id": str(user_id)}
            else:
                where_filter = None
            
            # 向量检索（多取2倍，用于后续过滤和重排序）
            results = self.wardrobe_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k * 3,  # 增加候选集
                where=where_filter,
                include=["metadatas", "distances"]  # 返回元数据和距离
            )
            
            if not results["ids"] or not results["ids"][0]:
                return []
            
            # 提取结果
            item_ids = [int(id_str) for id_str in results["ids"][0]]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results else [0] * len(item_ids)
            
            # 混合过滤 + 重排序
            scored_items = []
            for i, item_id in enumerate(item_ids):
                metadata = metadatas[i]
                distance = distances[i]
                
                # 1. 计算相似度得分（距离转相似度: 1 - normalized_distance）
                similarity_score = 1.0 - min(distance / 2.0, 1.0)  # 假设欧氏距离
                
                # 2. 季节过滤
                if season_filter:
                    item_seasons = metadata.get("season", "").split("/")
                    if not any(s in season_filter for s in item_seasons):
                        continue
                
                # 3. 颜色过滤（模糊匹配）
                if color_filter:
                    item_color = metadata.get("color_en", "").lower()
                    if color_filter.lower() not in item_color:
                        continue
                    else:
                        similarity_score += 0.1  # 颜色匹配加分
                
                # 4. 材质过滤（模糊匹配）
                if material_filter:
                    item_material = metadata.get("material_en", "").lower()
                    if material_filter.lower() not in item_material:
                        continue
                    else:
                        similarity_score += 0.05  # 材质匹配加分
                
                # 5. 相似度阈值过滤
                if similarity_score < min_score:
                    continue
                
                scored_items.append((item_id, similarity_score))
            
            # 按得分降序排列
            scored_items.sort(key=lambda x: x[1], reverse=True)
            
            # 返回Top-K
            final_ids = [item_id for item_id, _ in scored_items[:top_k]]
            
            print(f"🔍 混合检索: 候选{len(item_ids)}件 → 过滤{len(scored_items)}件 → 返回{len(final_ids)}件")
            return final_ids
            
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
