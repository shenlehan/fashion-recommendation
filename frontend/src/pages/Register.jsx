import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { registerUser } from '../services/api';
import './Auth.css';

function Register({ onLogin }) {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    body_type: '',
    city: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

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

    if (formData.password !== formData.confirmPassword) {
      setError('两次输入的密码不匹配');
      return;
    }

    setLoading(true);

    try {
      console.log('Attempting registration...');
      const result = await registerUser({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        body_type: formData.body_type || null,
        city: formData.city || null
      });
      console.log('Registration successful:', result);

      // Registration successful
      setSuccess(true);
      setLoading(false);

      // Redirect to login page after 1.5 seconds
      setTimeout(() => {
        console.log('Navigating to login...');
        navigate('/login', { state: { message: '注册成功！请登录。' } });
      }, 1500);
    } catch (err) {
      console.error('Registration error:', err);
      const errorMsg = err.response?.data?.detail || err.message || '注册失败。请重试。';
      setError(errorMsg);
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h1>注册</h1>
        <p className="auth-subtitle">创建您的时尚穿搭推荐系统账号</p>

        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">注册成功！正在跳转至登录页面...</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">用户名 *</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">电子邮箱 *</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">密码 *</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">确认密码 *</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="body_type">体型</label>
            <select
              id="body_type"
              name="body_type"
              value={formData.body_type}
              onChange={handleChange}
              disabled={loading}
            >
              <option value="">选择体型</option>
              <option value="slim">苗条 (Slim)</option>
              <option value="athletic">健壮 (Athletic)</option>
              <option value="average">匀称 (Average)</option>
              <option value="curvy">丰满 (Curvy)</option>
              <option value="plus-size">大码 (Plus Size)</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="city">城市</label>
            <input
              type="text"
              id="city"
              name="city"
              value={formData.city}
              onChange={handleChange}
              placeholder="用于提供基于天气的穿搭推荐"
              disabled={loading}
            />
          </div>

          <button type="submit" className="btn-primary" disabled={loading || success}>
            {loading ? '正在创建账号...' : success ? '正在跳转...' : '注册'}
          </button>
        </form>

        <p className="auth-footer">
          已有账号？ <Link to="/login">点击登录</Link>
        </p>
      </div>
    </div>
  );
}

export default Register;
