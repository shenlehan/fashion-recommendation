import { useState, useEffect } from "react";
import { getUserWardrobe, uploadClothingItem, deleteClothingItem, API_ORIGIN } from "../services/api";
import "./Wardrobe.css";

// ===== 中英文映射字典 =====
const CATEGORY_MAP = {
  'top': '上装',
  'bottom': '下装',
  'dress': '连衣裙',
  'outerwear': '外套',
  'shoes': '鞋履',
  'accessories': '配饰',
  'unknown': '未知'
};

const SEASON_MAP = {
  'spring': '春季',
  'summer': '夏季',
  'fall': '秋季',
  'winter': '冬季'
};

const translateCategory = (category) => {
  return CATEGORY_MAP[category?.toLowerCase()] || category || '未分类';
};

const translateSeasons = (seasonStr) => {
  if (!seasonStr) return '未知';
  return seasonStr.split(',')
    .map(s => SEASON_MAP[s.trim().toLowerCase()] || s.trim())
    .join('、');
};

function Wardrobe({ user }) {
  const [wardrobe, setWardrobe] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [uploadForm, setUploadForm] = useState({
    name: "",
    file: null
  });

  useEffect(() => {
    fetchWardrobe();
  }, [user.id]);

  const fetchWardrobe = async () => {
    try {
      setLoading(true);
      const items = await getUserWardrobe(user.id);
      setWardrobe(items);
      setError("");
    } catch (err) {
      setError("加载衣橱失败");
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    setUploadForm({
      ...uploadForm,
      file: e.target.files[0]
    });
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (!uploadForm.file) {
      setError("请选择文件");
      return;
    }

    setUploading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", uploadForm.file);
      formData.append("name", uploadForm.name || uploadForm.file.name);

      await uploadClothingItem(user.id, formData);
      setUploadForm({ name: "", file: null });
      setShowUploadForm(false);
      fetchWardrobe(); // Refresh wardrobe
    } catch (err) {
      setError(err.response?.data?.detail || "上传失败");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (itemId) => {
    if (!window.confirm("确定要删除这件衣物吗？")) {
      return;
    }

    try {
      console.log('开始删除衣物, ID:', itemId);
      const result = await deleteClothingItem(itemId);
      console.log('删除成功:', result);
      fetchWardrobe(); // Refresh wardrobe
    } catch (err) {
      console.error('删除失败详情:', err);
      console.error('响应数据:', err.response?.data);
      console.error('响应状态:', err.response?.status);
      const errorMsg = err.response?.data?.detail || err.response?.data?.error || err.message || '删除失败';
      setError(`删除失败: ${errorMsg}`);
    }
  };

  const getImageUrl = (path) => {
    if (!path) return "";
    if (path.startsWith("http")) return path;
    return `${API_ORIGIN}/${path.replace(/^\//, "")}`;
  };

  return (
    <div className="wardrobe-container">
      <div className="wardrobe-header">
        <h1>我的衣橱</h1>
        <button
          className="btn-primary"
          onClick={() => setShowUploadForm(!showUploadForm)}
        >
          {showUploadForm ? "取消" : "+ 添加衣物"}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {showUploadForm && (
        <div className="upload-form">
          <h2>上传衣物</h2>
          <form onSubmit={handleUploadSubmit}>
            <div className="form-group">
              <label htmlFor="name">衣物名称</label>
              <input
                type="text"
                id="name"
                value={uploadForm.name}
                onChange={(e) => setUploadForm({ ...uploadForm, name: e.target.value })}
                placeholder="例如：蓝色牛仔夹克"
                disabled={uploading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="file">上传图片 *</label>
              <input
                type="file"
                id="file"
                accept="image/*"
                onChange={handleFileChange}
                required
                disabled={uploading}
              />
              {uploadForm.file && (
                <p className="file-preview">已选择：{uploadForm.file.name}</p>
              )}
            </div>

            <button type="submit" className="btn-primary" disabled={uploading}>
              {uploading ? "上传中..." : "上传衣物"}
            </button>
          </form>
        </div>
      )}

      {loading ? (
        <div className="loading">加载中...</div>
      ) : wardrobe.length === 0 ? (
        <div className="empty-wardrobe">
          <p>你的衣橱还是空的，快来添加第一件衣物吧！</p>
        </div>
      ) : (
        <div className="wardrobe-grid">
          {wardrobe.map((item) => (
            <div key={item.id} className="wardrobe-item">
              <div className="item-image">
                {item.image_path ? (
                  <img
                    src={getImageUrl(item.image_path)}
                    alt={item.name}
                  />
                ) : (
                  <div className="no-image">无图片</div>
                )}
              </div>
              <div className="item-details">
                <h3>{item.name}</h3>
                <div className="item-info">
                  <span className="badge">{translateCategory(item.category)}</span>
                  {item.color && <span className="badge color">{item.color}</span>}
                </div>
                {item.season && <p className="season">季节：{translateSeasons(item.season)}</p>}
                {item.material && <p className="material">材质：{item.material}</p>}
                <button
                  className="btn-delete"
                  onClick={() => handleDelete(item.id)}
                >
                  删除
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Wardrobe;
