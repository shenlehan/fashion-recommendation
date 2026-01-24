import { useState } from 'react';
import { getOutfitRecommendations, API_ORIGIN } from '../services/api';
import './Recommendations.css';

function Recommendations({ user }) {
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [preferences, setPreferences] = useState({
    occasion: '',
    style: '',
    color_preference: ''
  });
  const [showPreferences, setShowPreferences] = useState(false);

  const getImageUrl = (path) => {
    if (!path) return '';
    if (path.startsWith('http')) return path;
    return `${API_ORIGIN}/${path.replace(/^\//, '')}`;
  };

  const fetchRecommendations = async (userPreferences = {}) => {
    try {
      setLoading(true);
      setError('');
      const data = await getOutfitRecommendations(user.id, userPreferences);
      setRecommendations(data);
    } catch (err) {
      setError(err.response?.data?.detail || '加载推荐失败');
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
      <div className="recommendations-header">
        <h1>穿搭推荐</h1>
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

      {showPreferences && (
        <div className="preferences-panel">
          <h2>自定义穿搭！</h2>
          <p className="preferences-subtitle">
            今天你有什么特别想穿的风格呢？
          </p>

          <div className="preferences-form">
            <div className="form-group">
              <label htmlFor="occasion">场合</label>
              <select
                id="occasion"
                value={preferences.occasion}
                onChange={(e) =>
                  setPreferences({ ...preferences, occasion: e.target.value })
                }
              >
                <option value="">不限</option>
                <option value="Casual">休闲</option>
                <option value="Business">商务</option>
                <option value="Formal"> 正式</option>
                <option value="Sport/Active"> 运动 </option>
                <option value="Party">聚会</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="style">风格</label>
              <select
                id="style"
                value={preferences.style}
                onChange={(e) =>
                  setPreferences({ ...preferences, style: e.target.value })
                }
              >
                <option value="">不限</option>
                <option value="classic">经典 (Classic)</option>
                <option value="trendy">潮流 (Trendy)</option>
                <option value="minimalist">简约 (Minimalist)</option>
                <option value="bohemian">波西米亚 (Bohemian)</option>
                <option value="street">街头 (Street Style)</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="color_preference">颜色偏好</label>
              <input
                type="text"
                id="color_preference"
                value={preferences.color_preference}
                onChange={(e) =>
                  setPreferences({ ...preferences, color_preference: e.target.value })
                }
                placeholder="例如：蓝色、黑色、素色"
              />
            </div>

            <button
              className="btn-primary"
              onClick={handleRegenerateWithPreferences}
              disabled={loading}
            >
              应用偏好
            </button>
          </div>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>推荐生成中...</p>
          <p className="loading-subtext">这可能需要 30-60 秒</p>
        </div>
      ) : recommendations ? (
        <div className="recommendations-content">
          <div className="weather-info">
            <h2>{user.city || '您所在城市'}的当前天气</h2>
            <div className="weather-details">
              <p>气温： {recommendations.weather?.temperature || 'N/A'}°C</p>
              <p>天气状况： {recommendations.weather?.condition || 'N/A'}</p>
            </div>
          </div>

          <div className="outfits-section">
            <h2>建议搭配</h2>
            {recommendations.outfits && recommendations.outfits.length > 0 ? (
              <div className="outfits-grid">
                {recommendations.outfits.map((outfit, index) => (
                  <div key={index} className="outfit-card">
                    <h3>搭配方案 {index + 1}</h3>
                    <div className="outfit-items">
                      {outfit.items?.map((item, itemIndex) => (
                        <div key={itemIndex} className="outfit-item">
                          <div className="outfit-item-image">
                            {item.image_path ? (
                              <img
                                src={getImageUrl(item.image_path)}
                                alt={item.name}
                              />
                            ) : (
                              <div className="no-image-small">{item.category}</div>
                            )}
                          </div>
                          <p>{item.name}</p>
                        </div>
                      ))}
                    </div>
                    {outfit.description && (
                      <p className="outfit-description">{outfit.description}</p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="no-outfits">
                未生成穿搭建议。请尝试在衣橱中添加更多单品！
              </p>
            )}
          </div>

          {recommendations.missing_items && recommendations.missing_items.length > 0 && (
            <div className="missing-items-section">
              <h2>衣橱进阶建议</h2>
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
        <div className="no-recommendations">
          <div className="welcome-message">
            <h2>👔 获取个性化穿搭推荐</h2>
            <p>点击上方的 <strong>“生成新推荐”</strong> 按钮，AI 将根据以下内容为您提供建议：</p>
            <ul>
              <li>✅ 您的衣橱单品</li>
              <li>✅ {user.city || '您所在城市'}的实时天气</li>
              <li>✅ 您的体型和风格偏好</li>
              <li>✅ 完整的全身搭配方案</li>
            </ul>
            <p className="tip">💡 提示: 使用“我的偏好风格”来获得更加个性化的推荐~</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default Recommendations;
