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
    color_preference: '',
    custom_request: ''
  });
  const [showPreferences, setShowPreferences] = useState(false);

  const getImageUrl = (path) => {
    if (!path) return '';
    if (path.startsWith('http')) return path;
    return `${API_ORIGIN}/${path.replace(/^\//, '')}`;
  };
  // NOTE: Removed useEffect - no auto-fetching!
  // Recommendations are only generated when user clicks "Regenerate"

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
            {loading ? 'Loading...' : '生成新推荐'}
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
                onChange={(e) =>
                  setPreferences({ ...preferences, style: e.target.value })
                }
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
              <label htmlFor="color_preference">Color Preference</label>
              <input
                type="text"
                id="color_preference"
                value={preferences.color_preference}
                onChange={(e) =>
                  setPreferences({ ...preferences, color_preference: e.target.value })
                }
                placeholder="e.g., blue, black, neutral"
              />
            </div>
            <div className="form-group">
              <label htmlFor="custom_request">特殊要求 (Custom Request)</label>
              <input
                type="text"
                id="custom_request"
                value={preferences.custom_request}
                onChange={(e) =>
                  setPreferences({ ...preferences, custom_request: e.target.value })
                }
                placeholder="ex:我要去参加前妻的婚礼，让我穿的比新郎还帅"
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
                No outfits suggested. Try adding more items to your wardrobe!
              </p>
            )}
          </div>

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
        <div className="no-recommendations">
          <div className="welcome-message">
            <h2>👔 Get Personalized Outfit Recommendations</h2>
            <p>Click the <strong>"Regenerate"</strong> button above to get AI-powered outfit suggestions based on:</p>
            <ul>
              <li>✅ Your wardrobe items</li>
              <li>✅ Current weather in {user.city || 'your city'}</li>
              <li>✅ Your body type and style preferences</li>
              <li>✅ Complete head-to-toe outfit combinations</li>
            </ul>
            <p className="tip">💡 提示: 使用“我的偏好风格”来获得更加个性化的推荐~</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default Recommendations;
