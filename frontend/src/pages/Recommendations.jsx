import { useState } from 'react';
import { getOutfitRecommendations, API_ORIGIN, virtualTryOn, fetchImageAsBlob } from '../services/api';
import './Recommendations.css';

function Recommendations({ user }) {
  // --- 原有状态 ---
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [preferences, setPreferences] = useState({
    occasion: '',
    style: '',
    color_preference: '',
    custom_request: ''
  });
  const [showPreferences, setShowPreferences] = useState(false);

  // --- ⚠️ 新增：虚拟试衣相关状态 ---
  const [personImage, setPersonImage] = useState(null);
  const [personPreview, setPersonPreview] = useState(null);
  const [tryOnResult, setTryOnResult] = useState(null);
  const [isTryingOn, setIsTryingOn] = useState(false);

  // --- 原有辅助函数 ---
  const getImageUrl = (path) => {
    if (!path) return '';
    if (path.startsWith('http')) return path;
    return `${API_ORIGIN}/${path.replace(/^\//, '')}`;
  };

  // --- ⚠️ 新增：处理人像上传 ---
  const handlePersonChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPersonImage(file);
      setPersonPreview(URL.createObjectURL(file));
    }
  };

  // --- ⚠️ 新增：核心试衣逻辑 ---
  const handleTryOn = async (item) => {
    if (!personImage) {
      alert("请先在页面顶部上传您的人像照片，才能开始试衣哦！");
      return;
    }

    try {
      setIsTryingOn(true);
      setError('');
      
      // 1. 将推荐的衣服 URL 转为二进制 Blob (跨域请求)
      const clothBlob = await fetchImageAsBlob(getImageUrl(item.image_path));
      
      // 2. 调用后端代理接口转发给 CatVTON (8001端口)
      const resultBlob = await virtualTryOn(personImage, clothBlob, 'upper_body');
      
      // 3. 将返回的图片二进制流转为可预览的 URL
      const resultUrl = URL.createObjectURL(resultBlob);
      setTryOnResult(resultUrl);
    } catch (err) {
      console.error("Try-on error:", err);
      setError('虚拟试衣请求失败，请确保 AI 后端服务已启动。');
    } finally {
      setIsTryingOn(false);
    }
  };

  // --- 原有推荐获取逻辑 ---
  const fetchRecommendations = async (userPreferences = {}) => {
    try {
      setLoading(true);
      setError('');
      const data = await getOutfitRecommendations(user.id, userPreferences);
      setRecommendations(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerateWithPreferences = () => {
    const filteredPrefs = Object.fromEntries(
      Object.entries(preferences).filter(([_, value]) => value !== '')
    );
    fetchRecommendations(filteredPrefs);
    setShowPreferences(false);
  };

  const handleRegenerate = () => {
    fetchRecommendations();
  };

  return (
    <div className="recommendations-container">
      {/* ⚠️ 新增：顶部试衣准备区域 */}
      <div className="vton-setup-section">
        <div className="vton-setup-card">
          <div className="setup-text">
            <h3>准备您的虚拟试衣间</h3>
            <p>上传一张正面人像照，即可预览推荐衣物的上身效果</p>
          </div>
          <div className="upload-controls">
            <input 
              type="file" 
              id="person-upload" 
              accept="image/*" 
              onChange={handlePersonChange} 
              hidden 
            />
            <label htmlFor="person-upload" className="btn-secondary">
              {personPreview ? '更换照片' : '上传人像照片'}
            </label>
            {personPreview && (
              <div className="person-preview-wrapper">
                <img src={personPreview} className="person-mini-preview" alt="User" />
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="recommendations-header">
        <h1>Outfit Recommendations</h1>
        <div className="header-actions">
          <button
            className="btn-secondary"
            onClick={() => setShowPreferences(!showPreferences)}
            disabled={loading}
          >
            {showPreferences ? '隐藏偏好' : '我的偏好风格'}
          </button>
          <button className="btn-primary" onClick={handleRegenerate} disabled={loading}>
            {loading ? '生成中...' : '生成新推荐'}
          </button>
        </div>
      </div>

      {/* ⚠️ 新增：试衣结果弹出层 (Modal) */}
      {tryOnResult && (
        <div className="vton-modal-overlay" onClick={() => setTryOnResult(null)}>
          <div className="vton-modal-content" onClick={e => e.stopPropagation()}>
            <button className="close-modal" onClick={() => setTryOnResult(null)}>&times;</button>
            <h2>试衣效果预览</h2>
            <div className="vton-result-container">
              <img src={tryOnResult} alt="Virtual Try-on Result" />
            </div>
            <div className="modal-footer">
              <p>由 CatVTON 图像生成技术驱动</p>
              <button className="btn-primary" onClick={() => window.open(tryOnResult)}>下载保存</button>
            </div>
          </div>
        </div>
      )}

      {/* 原有偏好面板 */}
      {showPreferences && (
        <div className="preferences-panel">
          <h2>自定义穿搭！</h2>
          <p className="preferences-subtitle">今天你有什么特别想穿的风格呢？</p>
          <div className="preferences-form">
            <div className="form-group">
              <label htmlFor="occasion">场合</label>
              <select
                id="occasion"
                value={preferences.occasion}
                onChange={(e) => setPreferences({ ...preferences, occasion: e.target.value })}
              >
                <option value="">Any</option>
                <option value="Casual">随意</option>
                <option value="Business">商务</option>
                <option value="Formal"> 正式</option>
                <option value="Sport/Active"> 运动 </option>
                <option value="Party">狂野</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="style">风格</label>
              <select
                id="style"
                value={preferences.style}
                onChange={(e) => setPreferences({ ...preferences, style: e.target.value })}
              >
                <option value="">Any</option>
                <option value="classic">经典</option>
                <option value="trendy">潮流</option>
                <option value="minimalist">极简</option>
                <option value="bohemian">波西米亚风</option>
                <option value="street">街头风</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="color_preference">颜色偏好</label>
              <input
                type="text"
                id="color_preference"
                value={preferences.color_preference}
                onChange={(e) => setPreferences({ ...preferences, color_preference: e.target.value })}
                placeholder="e.g., blue, black, neutral"
              />
            </div>
            <div className="form-group">
              <label htmlFor="custom_request">特殊要求</label>
              <input
                type="text"
                id="custom_request"
                value={preferences.custom_request}
                onChange={(e) => setPreferences({ ...preferences, custom_request: e.target.value })}
                placeholder="ex:我要去参加前妻的婚礼..."
              />
            </div>
            <button
              className="btn-primary"
              onClick={handleRegenerateWithPreferences}
              disabled={loading}
            >
              Apply Preferences
            </button>
          </div>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>推荐生成中...</p>
          <p className="loading-subtext">This may take 30-60 seconds</p>
        </div>
      ) : recommendations ? (
        <div className="recommendations-content">
          {/* 原有天气模块 */}
          <div className="weather-info">
            <h2>Current Weather in {user.city || 'Your City'}</h2>
            <div className="weather-details">
              <p>Temperature: {recommendations.weather?.temperature || 'N/A'}°C</p>
              <p>Condition: {recommendations.weather?.condition || 'N/A'}</p>
            </div>
          </div>

          <div className="outfits-section">
            <h2>Suggested Outfits</h2>
            {recommendations.outfits && recommendations.outfits.length > 0 ? (
              <div className="outfits-grid">
                {recommendations.outfits.map((outfit, index) => (
                  <div key={index} className="outfit-card">
                    <h3>Outfit {index + 1}</h3>
                    <div className="outfit-items">
                      {outfit.items?.map((item, itemIndex) => (
                        <div key={itemIndex} className="outfit-item">
                          <div className="outfit-item-image">
                            {item.image_path ? (
                              <>
                                <img src={getImageUrl(item.image_path)} alt={item.name} />
                                {/* ⚠️ 新增：试衣按钮 */}
                                <button 
                                  className="try-on-overlay-btn"
                                  onClick={() => handleTryOn(item)}
                                  disabled={isTryingOn}
                                  title="在您的人像上预览这件衣服"
                                >
                                  {isTryingOn ? '生成中...' : '一键试穿'}
                                </button>
                              </>
                            ) : (
                              <div className="no-image-small">{item.category}</div>
                            )}
                          </div>
                          <p>{item.name}</p>
                        </div>
                      ))}
                    </div>
                    {outfit.description && <p className="outfit-description">{outfit.description}</p>}
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-outfits">No outfits suggested.</p>
            )}
          </div>

          {/* 原有缺失单品模块 */}
          {recommendations.missing_items && recommendations.missing_items.length > 0 && (
            <div className="missing-items-section">
              <h2>Suggested Items to Complete Your Wardrobe</h2>
              <div className="missing-items-list">
                {recommendations.missing_items.map((item, index) => (
                  <div key={index} className="missing-item">
                    <span className="item-icon">🛍️</span>
                    <div>
                      <h4>{item.category || item}</h4>
                      {item.reason && <p>{item.reason}</p>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        /* 原有欢迎信息 */
        <div className="no-recommendations">
          <div className="welcome-message">
            <h2>👔 Get Personalized Outfit Recommendations</h2>
            <p>Click the <strong>"Regenerate"</strong> button above...</p>
            <ul>
              <li>✅ Your wardrobe items</li>
              <li>✅ Current weather...</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

export default Recommendations;