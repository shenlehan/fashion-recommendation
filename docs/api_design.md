**Fashion Recommendation API 文档**

---

## 1. **API 概述**

这是一个智能穿搭推荐系统的后端 API，支持用户注册、衣物上传、穿搭推荐等功能。

- **基础 URL**: `http://localhost:8000`
- **API 版本**: v1
- **内容类型**: `application/json`

---

## 2. **API 端点列表**

### **1. 用户管理**

#### `POST /api/v1/users/register`
**功能**: 用户注册

**请求体**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "body_type": "string",  // 体型 (如: "slim", "average", "curvy")
  "city": "string"        // 城市 (如: "Beijing")
}
```

**响应**:
```json
{
  "id": 1,
  "username": "string",
  "email": "string",
  "body_type": "string",
  "city": "string"
}
```

**示例请求**:
```bash
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "body_type": "slim",
    "city": "Beijing"
  }'
```

---

#### `GET /api/v1/users/profile`
**功能**: 获取用户信息

**查询参数**:
- `user_id` (integer): 用户ID

**响应**:
```json
{
  "id": 1,
  "username": "string",
  "email": "string",
  "body_type": "string",
  "city": "string"
}
```

**示例请求**:
```bash
curl "http://localhost:8000/api/v1/users/profile?user_id=1"
```

---

### **2. 衣物管理**

#### `POST /api/v1/clothes/upload`
**功能**: 上传衣物图片

**参数**:
- `user_id` (integer): 用户ID
- `file` (file): 衣物图片文件 (multipart/form-data)

**响应**:
```json
{
  "message": "衣物上传成功",
  "item_id": 1
}
```

**示例请求** (使用 FormData):
```bash
curl -X POST "http://localhost:8000/api/v1/clothes/upload" \
  -F "user_id=1" \
  -F "file=@path/to/clothes.jpg"
```

---

#### `GET /api/v1/clothes/wardrobe`
**功能**: 获取用户衣橱列表

**查询参数**:
- `user_id` (integer): 用户ID

**响应**:
```json
[
  {
    "id": 1,
    "name": "clothes.jpg",
    "category": "top",
    "color": "blue",
    "season": "spring,summer",
    "material": "cotton",
    "image_path": "uploads/clothes.jpg"
  }
]
```

**示例请求**:
```bash
curl "http://localhost:8000/api/v1/clothes/wardrobe?user_id=1"
```

---

### **3. 推荐服务**

#### `GET /api/v1/recommend/outfits`
**功能**: 获取穿搭推荐

**查询参数**:
- `user_id` (integer): 用户ID

**响应**:
```json
{
  "outfits": [
    {
      "items": [1, 2],  // 衣物ID列表
      "reason": "适合晴天"
    }
  ],
  "missing_items": ["winter coat"]  // 缺少的衣物类型
}
```

**示例请求**:
```bash
curl "http://localhost:8000/api/v1/recommend/outfits?user_id=1"
```

---

### **4. 系统接口**

#### `GET /`
**功能**: 服务状态检查

**响应**:
```json
{
  "message": "Fashion Recommendation Backend is running!"
}
```

#### `GET /health`
**功能**: 健康检查

**响应**:
```json
{
  "status": "healthy"
}
```

#### `GET /docs`
**功能**: API 文档界面 (Swagger UI)

---

## 3. **数据模型**

### **User (用户)**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 用户ID |
| username | string | 用户名 |
| email | string | 邮箱 |
| body_type | string | 体型 |
| city | string | 城市 |

### **WardrobeItem (衣橱物品)**
| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 物品ID |
| name | string | 物品名称 |
| category | string | 类别 (top, bottom, outerwear 等) |
| color | string | 颜色 |
| season | string | 适用季节 (逗号分隔) |
| material | string | 材质 |
| image_path | string | 图片路径 |

---

## 4. **错误处理**

所有错误响应格式:
```json
{
  "detail": "错误信息"
}
```

常见 HTTP 状态码:
- `200`: 成功
- `400`: 请求错误 (参数错误)
- `404`: 资源不存在
- `500`: 服务器内部错误

---

## 5. **前端集成建议**

### **用户注册流程**
1. 调用 `POST /api/v1/users/register`
2. 保存返回的用户ID
3. 使用用户ID进行后续操作

### **衣物上传流程**
1. 用户选择图片文件
2. 调用 `POST /api/v1/clothes/upload` 上传
3. 上传成功后可以调用 `GET /api/v1/clothes/wardrobe` 刷新衣橱

### **获取推荐流程**
1. 调用 `GET /api/v1/recommend/outfits`
2. 显示返回的穿搭建议和缺少的衣物

---

## 6. **测试工具**

- **API 文档**: `http://localhost:8000/docs` (Swagger UI)
- **Postman**: 可导入此文档进行测试
- **Curl**: 如上示例所示