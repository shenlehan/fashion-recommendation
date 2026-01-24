import { useState, useEffect } from "react";
import { getUserWardrobe, uploadClothingItem, deleteClothingItem, API_ORIGIN } from "../services/api";
import "./Wardrobe.css";

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
      setError("请选择一个文件");
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
      setError(err.response?.data?.detail || "上传单品失败");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (itemId) => {
    if (!window.confirm("确定要删除这件衣服吗？")) {
      return;
    }

    try {
      await deleteClothingItem(itemId);
      fetchWardrobe(); // Refresh wardrobe
    } catch (err) {
      setError("删除失败");
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
          {showUploadForm ? "取消" : "+ 添加单品"}
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {showUploadForm && (
        <div className="upload-form">
          <h2>上传服装单品</h2>
          <form onSubmit={handleUploadSubmit}>
            <div className="form-group">
              <label htmlFor="name">单品名称</label>
              <input
                type="text"
                id="name"
                value={uploadForm.name}
                onChange={(e) => setUploadForm({ ...uploadForm, name: e.target.value })}
                placeholder="例如：深蓝牛仔夹克"
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
                <p className="file-preview">已选择： {uploadForm.file.name}</p>
              )}
            </div>

            <button type="submit" className="btn-primary" disabled={uploading}>
              {uploading ? "正在上传..." : "上传单品"}
            </button>
          </form>
        </div>
      )}

      {loading ? (
        <div className="loading">正在加载衣橱...</div>
      ) : wardrobe.length === 0 ? (
        <div className="empty-wardrobe">
          <p>您的衣橱是空的。快来添加您的第一件衣服吧！</p>
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
                  <div className="no-image">暂无图片</div>
                )}
              </div>
              <div className="item-details">
                <h3>{item.name}</h3>
                <div className="item-info">
                  <span className="badge">{item.category || "未知"}</span>
                  {item.color && <span className="badge color">{item.color}</span>}
                </div>
                {item.season && <p className="season">季节： {item.season}</p>}
                {item.material && <p className="material">材质： {item.material}</p>}
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
