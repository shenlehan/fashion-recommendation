import { useState, useEffect } from 'react';
import { getOutfitRecommendations } from '../services/api';
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

  useEffect(() => {
    fetchRecommendations();
  }, [user.id]);

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
          >
            {showPreferences ? 'Hide Filters' : 'Customize'}
          </button>
          <button className="btn-primary" onClick={handleRegenerate} disabled={loading}>
            {loading ? 'Loading...' : 'Regenerate'}
          </button>
        </div>
      </div>

      {showPreferences && (
        <div className="preferences-panel">
          <h2>Customize Your Recommendations</h2>
          <p className="preferences-subtitle">
            Tell us what you're looking for, and we'll tailor the suggestions
          </p>

          <div className="preferences-form">
            <div className="form-group">
              <label htmlFor="occasion">Occasion</label>
              <select
                id="occasion"
                value={preferences.occasion}
                onChange={(e) =>
                  setPreferences({ ...preferences, occasion: e.target.value })
                }
              >
                <option value="">Any</option>
                <option value="casual">Casual</option>
                <option value="business">Business</option>
                <option value="formal">Formal</option>
                <option value="sport">Sport/Active</option>
                <option value="party">Party</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="style">Style</label>
              <select
                id="style"
                value={preferences.style}
                onChange={(e) =>
                  setPreferences({ ...preferences, style: e.target.value })
                }
              >
                <option value="">Any</option>
                <option value="classic">Classic</option>
                <option value="trendy">Trendy</option>
                <option value="minimalist">Minimalist</option>
                <option value="bohemian">Bohemian</option>
                <option value="street">Street Style</option>
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
        <div className="loading">Generating recommendations...</div>
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
                                src={`http://localhost:8000/${item.image_path}`}
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
          <p>Click "Regenerate" to get personalized outfit recommendations!</p>
        </div>
      )}
    </div>
  );
}

export default Recommendations;
