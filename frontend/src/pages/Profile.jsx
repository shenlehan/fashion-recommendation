import { useState, useEffect } from 'react';
import { getUserProfile, updateUserProfile } from '../services/api';
import './Profile.css';

function Profile({ user, onUpdateUser }) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    body_type: '',
    city: ''
  });
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    fetchUserProfile();
  }, [user.id]);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      const profile = await getUserProfile(user.id);
      setFormData({
        username: profile.username || '',
        email: profile.email || '',
        body_type: profile.body_type || '',
        city: profile.city || ''
      });
    } catch (err) {
      setError('加载用户资料失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setSaving(true);

    try {
      const updatedUser = await updateUserProfile(user.id, {
        body_type: formData.body_type || null,
        city: formData.city || null
      });
      
      setSuccess(true);
      
      // 更新父组件中的用户信息
      if (onUpdateUser) {
        onUpdateUser(updatedUser);
      }
      
      // 3秒后隐藏成功提示
      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || '更新资料失败');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="profile-container">
        <div className="loading">加载中...</div>
      </div>
    );
  }

  return (
    <div className="profile-container">
      <div className="profile-header">
        <h1>个人资料</h1>
        <p className="profile-subtitle">完善你的信息，获得更精准的穿搭推荐</p>
      </div>

      <div className="profile-card">
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">✅ 资料更新成功！</div>}

        <form onSubmit={handleSubmit}>
          {/* 基础信息（只读） */}
          <div className="form-section">
            <h2>账户信息</h2>
            <div className="form-group">
              <label htmlFor="username">用户名</label>
              <input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                disabled
                className="input-readonly"
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">邮箱</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                disabled
                className="input-readonly"
              />
            </div>
          </div>

          {/* 推荐相关信息（可编辑） */}
          <div className="form-section">
            <h2>推荐偏好</h2>
            <p className="section-hint">这些信息将用于生成个性化的穿搭推荐</p>

            <div className="form-group">
              <label htmlFor="body_type">
                体型
                <span className="label-hint">（帮助推荐更适合你身材的穿搭）</span>
              </label>
              <select
                id="body_type"
                name="body_type"
                value={formData.body_type}
                onChange={handleChange}
                disabled={saving}
              >
                <option value="">选择体型</option>
                <option value="slim">偏瘦</option>
                <option value="athletic">健美</option>
                <option value="average">标准</option>
                <option value="curvy">丰满</option>
                <option value="plus-size">大码</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="city">
                所在城市
                <span className="label-hint">（用于天气推荐）</span>
              </label>
              <input
                type="text"
                id="city"
                name="city"
                value={formData.city}
                onChange={handleChange}
                placeholder="例如：北京、上海、广州"
                disabled={saving}
              />
            </div>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? '保存中...' : '保存更改'}
            </button>
          </div>
        </form>
      </div>

      <div className="profile-tips">
        <h3>💡 小贴士</h3>
        <ul>
          <li>完善体型信息可以让AI推荐更适合你的穿搭组合</li>
          <li>填写城市信息后，系统会根据当地天气生成推荐</li>
          <li>你可以随时回来修改这些信息</li>
        </ul>
      </div>
    </div>
  );
}

export default Profile;
