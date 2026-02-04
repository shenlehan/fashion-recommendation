import { useState, useEffect } from "react";
import { getUserWardrobe, uploadClothingItem, uploadClothingBatch, deleteClothingItem, API_ORIGIN } from "../services/api";
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
    files: []
  });
  const [uploadProgress, setUploadProgress] = useState({ current: 0, total: 0 });

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
    const selectedFiles = Array.from(e.target.files);
    setUploadForm({
      ...uploadForm,
      files: selectedFiles
    });
  };

  const handleUploadSubmit = async (e) => {
    e.preventDefault();
    if (uploadForm.files.length === 0) {
      setError("请选择文件");
      return;
    }

    setUploading(true);
    setError("");
    setUploadProgress({ current: 0, total: uploadForm.files.length });

    try {
      const formData = new FormData();
      
      // 批量上传：使用SSE实时进度
      if (uploadForm.files.length > 1) {
        uploadForm.files.forEach(file => {
          formData.append("files", file);
        });
        
        // 使用EventSource监听SSE
        const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:6008/api/v1';
        const url = `${API_BASE_URL}/clothes/upload-batch-stream?user_id=${user.id}`;
        
        // 使用fetch手动处理SSE
        const response = await fetch(url, {
          method: 'POST',
          body: formData,
        });
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        let finalResult = { success: [], failed: [] };
        
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop(); // 保留未完成的行
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = JSON.parse(line.substring(6));
              
              if (data.type === 'start') {
                setUploadProgress({ current: 0, total: data.total });
              } else if (data.type === 'progress') {
                setUploadProgress({ current: data.current, total: data.total });
              } else if (data.type === 'complete') {
                finalResult = data;
                setUploadProgress({ current: data.total, total: data.total });
              }
            }
          }
        }
        
        // 显示结果
        if (finalResult.failed.length > 0) {
          const failedNames = finalResult.failed.map(f => f.filename).join(", ");
          setError(`部分失败：${failedNames}`);
        }
        
        if (finalResult.success.length > 0) {
          setUploadForm({ files: [] });
          setShowUploadForm(false);
          fetchWardrobe();
        }
      } else {
        // 单个上传
        setUploadProgress({ current: 0, total: 1 });
        formData.append("file", uploadForm.files[0]);
        await uploadClothingItem(user.id, formData);
        setUploadProgress({ current: 1, total: 1 });
        setUploadForm({ files: [] });
        setShowUploadForm(false);
        fetchWardrobe();
      }
    } catch (err) {
      console.error('上传错误:', err);
      setError(err.message || "上传失败");
    } finally {
      setUploading(false);
      setTimeout(() => setUploadProgress({ current: 0, total: 0 }), 1000);
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
          <p className="upload-hint">🤖 AI 将自动识别并命名衣物，支持批量上传</p>
          <form onSubmit={handleUploadSubmit}>
            <div className="form-group">
              <label htmlFor="file">上传图片 *</label>
              <input
                type="file"
                id="file"
                accept="image/*"
                multiple
                onChange={handleFileChange}
                required
                disabled={uploading}
              />
              {uploadForm.files.length > 0 && (
                <div className="file-preview-list">
                  <p className="file-count">已选择 {uploadForm.files.length} 个文件</p>
                  <ul>
                    {uploadForm.files.map((file, idx) => (
                      <li key={idx}>{file.name}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            <button type="submit" className="btn-primary" disabled={uploading}>
              {uploading 
                ? `正在处理 ${uploadProgress.current}/${uploadProgress.total} 个文件...` 
                : `上传 ${uploadForm.files.length || ''} 件衣物`
              }
            </button>
            
            {uploading && uploadProgress.total > 0 && (
              <div className="upload-progress">
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${(uploadProgress.current / uploadProgress.total) * 100}%` }}
                  ></div>
                </div>
                <p className="progress-text">
                  {uploadProgress.current}/{uploadProgress.total} 完成
                </p>
              </div>
            )}
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
