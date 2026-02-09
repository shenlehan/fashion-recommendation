# RAG向量检索使用指南

## 📦 功能概述

已成功集成**语义向量检索**功能，实现衣橱智能化检索，解决大衣橱场景下Prompt过载问题。

### 核心优势
- ✅ **性能优化**：从全量查询改为Top-K检索，最多返回15件最相关衣物
- ✅ **语义理解**：基于sentence-transformers，支持中英文语义匹配
- ✅ **降级保障**：向量检索失败时自动降级为全量查询
- ✅ **自动同步**：上传/删除衣物时自动维护向量库

---

## 🚀 快速开始

### 1. 安装依赖

```powershell
cd backend
pip install -r requirements.txt
```

首次安装会下载：
- `sentence-transformers` 模型（~420MB）
- `chromadb` 向量数据库

### 2. 数据迁移（首次使用）

为现有衣物生成向量：

```powershell
cd backend
python migrate_embeddings.py
```

输出示例：
```
================================================================================
开始向量化迁移任务...
================================================================================

📊 找到 23 件衣物需要向量化
================================================================================

[1/23] 处理: 藏青色牛仔夹克 (ID: 1)
✅ 向量生成成功
  ✅ 成功

...

================================================================================
迁移完成!
================================================================================
总计: 23 件
成功: 23 件
失败: 0 件
成功率: 100.0%
================================================================================

📊 ChromaDB中当前共有 23 条向量记录
```

### 3. 测试向量检索

```powershell
python test_vector_search.py
```

会测试4个场景：
- 冬季寒冷天气
- 夏季休闲
- 商务正式
- 约会浪漫风格

---

## 📖 工作原理

### 向量生成流程

```
衣物上传 → Qwen3-VL分析 → 保存数据库 → 生成语义向量 → 存入ChromaDB
                ↓
    name_en + color_en + material_en + season + category
                ↓
    sentence-transformers编码（384维向量）
```

### 推荐检索流程

```
用户请求推荐
    ↓
构建查询文本："{temperature}C {condition} {occasion} {style}"
    ↓
生成查询向量（384维）
    ↓
ChromaDB余弦相似度检索
    ↓
返回Top-15最相关衣物ID
    ↓
从数据库批量查询完整信息
    ↓
传给Qwen3-VL生成搭配推荐
```

---

## 🔧 技术细节

### 使用的模型
- **Embedding模型**：`paraphrase-multilingual-mpnet-base-v2`
  - 支持中英文
  - 向量维度：384
  - 相似度度量：余弦距离

### 数据存储
- **向量数据库**：ChromaDB（本地持久化）
- **存储路径**：`backend/chroma_data/`
- **元数据索引**：
  - `user_id`：用户ID（用于过滤）
  - `category`：衣物类别
  - `season`：适用季节
  - `color_en`：颜色

### 性能指标
- **向量生成速度**：50-100ms/件（CPU）
- **检索速度**：<10ms（1000件衣物规模）
- **内存占用**：~500MB（模型加载）

---

## 📊 对比效果

### 改造前
```python
# 全量查询，返回所有衣物
wardrobe = db.query(WardrobeItem).filter(WardrobeItem.user_id == user_id).all()
# 问题：衣橱超过50件时Prompt超2K tokens，推荐质量下降
```

### 改造后
```python
# 向量检索，返回Top-15相关衣物
relevant_items = embedding_service.search_similar_items(
    query_text="7C Sunny casual",
    user_id=user_id,
    top_k=15
)
# 优势：Prompt控制在800 tokens以内，推荐精准度提升
```

---

## 🛠️ 维护操作

### 重建向量库
如果向量库损坏或需要重新生成：

```powershell
# 删除旧数据
rm -r chroma_data

# 重新迁移
python migrate_embeddings.py
```

### 查看向量库状态
```powershell
python test_vector_search.py
```

### 手动添加单个衣物向量
```python
from app.services.embedding_service import get_embedding_service

embedding_service = get_embedding_service()
embedding_service.add_item(item_id=123, item={
    "user_id": 1,
    "name_en": "Black Sweater",
    "color_en": "black",
    "material_en": "wool",
    "season": "fall/winter",
    "category": "top"
})
```

---

## ⚠️ 注意事项

1. **首次启动慢**：第一次调用会下载sentence-transformers模型（~420MB），需等待2-5分钟
2. **向量库路径**：`chroma_data/` 目录已加入 `.gitignore`，不要提交到Git
3. **降级策略**：向量检索失败会自动降级为全量查询，不影响主流程
4. **用户隔离**：向量检索自动按user_id过滤，不会跨用户推荐

---

## 🎯 下一步优化

- [ ] **季节智能过滤**：根据温度自动推断季节（0-10°C → fall/winter）
- [ ] **多模态检索**：集成CLIP图像向量（需额外500MB显存）
- [ ] **用户历史偏好**：记录用户喜欢的搭配，个性化推荐
- [ ] **时尚规则库**：硬编码搭配规则（蓝色+白色、正式场合避免运动鞋）

---

## 📞 问题排查

### Q1: 提示"模型下载失败"
```
export HF_ENDPOINT=https://hf-mirror.com
pip install sentence-transformers --upgrade
```

### Q2: ChromaDB初始化报错
```powershell
pip install chromadb --upgrade
rm -r chroma_data  # 删除损坏的数据
```

### Q3: 向量检索无结果
- 检查是否运行过 `migrate_embeddings.py`
- 确认衣物有 `name_en`, `color_en` 等英文字段
- 运行 `test_vector_search.py` 查看向量库状态

---

**技术支持**: 查看 [embedding_service.py](app/services/embedding_service.py) 源码
