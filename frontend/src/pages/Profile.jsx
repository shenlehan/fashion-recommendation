import { useState, useEffect, useRef } from 'react';
import { getUserProfile, updateUserProfile } from '../services/api';
import './Profile.css';

function Profile({ user, onUpdateUser }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const errorTimerRef = useRef(null); // 错误提示定时器
  
  // 编辑模式状态
  const [editMode, setEditMode] = useState('view'); // 'view' | 'edit-info' | 'edit-password'
  
  // 表单数据
  const [formData, setFormData] = useState({
    gender: '',
    age: '',
    height: '',
    weight: '',
    city: '',
    new_password: '',
    confirm_password: ''
  });
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  // 监听error变化，5秒后自动清除
  useEffect(() => {
    if (error) {
      // 清除之前的定时器
      if (errorTimerRef.current) {
        clearTimeout(errorTimerRef.current);
      }
      // 设置新的定时器
      errorTimerRef.current = setTimeout(() => {
        setError('');
      }, 5000);
    }
    return () => {
      if (errorTimerRef.current) {
        clearTimeout(errorTimerRef.current);
      }
    };
  }, [error]);

  useEffect(() => {
    fetchUserProfile();
  }, [user.id]);

  const fetchUserProfile = async () => {
    try {
      setLoading(true);
      const data = await getUserProfile(user.id);
      setProfile(data);
      
      // 设置照片预览
      if (data.profile_photo) {
        const photoUrl = `/uploads/${data.profile_photo}`;
        setPhotoPreview(photoUrl);
      } else {
        setPhotoPreview(null);
      }
    } catch (err) {
      setError('加载用户资料失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // 进入编辑信息模式
  const handleEditInfo = () => {
    setFormData({
      gender: profile.gender || '',
      age: profile.age !== null && profile.age !== undefined && profile.age !== 0 ? profile.age : '',
      height: profile.height !== null && profile.height !== undefined && profile.height !== 0 ? profile.height : '',
      weight: profile.weight !== null && profile.weight !== undefined && profile.weight !== 0 ? profile.weight : '',
      city: profile.city || '',
      new_password: '',
      confirm_password: ''
    });
    setEditMode('edit-info');
    setError('');
    setSuccess(false);
  };

  // 进入修改密码模式
  const handleEditPassword = () => {
    setFormData({
      gender: '',
      age: '',
      height: '',
      weight: '',
      city: '',
      new_password: '',
      confirm_password: ''
    });
    setEditMode('edit-password');
    setError('');
    setSuccess(false);
  };

  // 取消编辑
  const handleCancel = () => {
    setEditMode('view');
    setPhotoFile(null);
    setError('');
    setSuccess(false);
    // 重置照片预览
    if (profile.profile_photo) {
      setPhotoPreview(`/uploads/${profile.profile_photo}`);
    } else {
      setPhotoPreview(null);
    }
  };

  const handlePhotoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPhotoFile(file);
      setPhotoPreview(URL.createObjectURL(file));
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  // 提交信息修改
  const handleSubmitInfo = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setSaving(true);

    try {
      const formDataToSend = new FormData();
      
      // 添加普通字段
      if (formData.gender) formDataToSend.append('gender', formData.gender);
      if (formData.age !== null && formData.age !== undefined && formData.age !== '') {
        formDataToSend.append('age', formData.age);
      }
      if (formData.height !== null && formData.height !== undefined && formData.height !== '') {
        formDataToSend.append('height', formData.height);
      }
      if (formData.weight !== null && formData.weight !== undefined && formData.weight !== '') {
        formDataToSend.append('weight', formData.weight);
      }
      if (formData.city) formDataToSend.append('city', formData.city);
      
      // 添加照片文件
      if (photoFile) {
        formDataToSend.append('profile_photo', photoFile);
      }

      const result = await updateUserProfile(user.id, formDataToSend);
      
      setSuccess(true);
      await fetchUserProfile();
      setPhotoFile(null);
      
      setTimeout(() => {
        setSuccess(false);
        setEditMode('view');
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || '更新资料失败');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  // 提交密码修改
  const handleSubmitPassword = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setSaving(true);

    try {
      // 校验密码
      if (!formData.new_password || !formData.confirm_password) {
        setError('请输入新密码');
        setSaving(false);
        return;
      }
      if (formData.new_password !== formData.confirm_password) {
        setError('两次输入的密码不一致');
        setSaving(false);
        return;
      }
      if (formData.new_password.length < 6) {
        setError('密码长度至少为6位');
        setSaving(false);
        return;
      }

      const formDataToSend = new FormData();
      formDataToSend.append('new_password', formData.new_password);

      await updateUserProfile(user.id, formDataToSend);
      
      setSuccess(true);
      
      setTimeout(() => {
        setSuccess(false);
        setEditMode('view');
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || '修改密码失败');
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

  if (!profile) {
    return (
      <div className="profile-container">
        <div className="error-message">无法加载用户资料</div>
      </div>
    );
  }

  // ========== 查看模式 ==========
  if (editMode === 'view') {
    return (
      <div className="profile-container">
        <div className="profile-header">
          <h1>个人资料</h1>
          <p className="profile-subtitle">完善你的信息，获得更精准的穿搭推荐</p>
        </div>

        <div className="profile-card">
          {error && <div className="error-message">{error}</div>}
          
          {/* 账户信息 */}
          <div className="info-section">
            <h2>账户信息</h2>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">用户名</span>
                <span className="info-value">{profile.username}</span>
              </div>
              <div className="info-item">
                <span className="info-label">邮箱</span>
                <span className="info-value">{profile.email}</span>
              </div>
              <div className="info-item">
                <span className="info-label">密码</span>
                <span className="info-value">********</span>
              </div>
            </div>
          </div>

          {/* 基本信息 */}
          <div className="info-section">
            <h2>基本信息</h2>
            <div className="info-grid">
              <div className="info-item">
                <span className="info-label">性别（必填）</span>
                <span className="info-value">
                  {profile.gender ? 
                    (profile.gender === 'male' ? '男' : profile.gender === 'female' ? '女' : '其他') 
                    : <span className="not-filled">待填写</span>}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">年龄（必填）</span>
                <span className="info-value">
                  {profile.age && profile.age !== 0 ? `${profile.age}岁` : <span className="not-filled">待填写</span>}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">身高（必填）</span>
                <span className="info-value">
                  {profile.height && profile.height !== 0 ? `${profile.height}cm` : <span className="not-filled">待填写</span>}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">体重（必填）</span>
                <span className="info-value">
                  {profile.weight && profile.weight !== 0 ? `${profile.weight}kg` : <span className="not-filled">待填写</span>}
                </span>
              </div>
              <div className="info-item">
                <span className="info-label">所在城市</span>
                <span className="info-value">
                  {profile.city || <span className="not-filled">待填写</span>}
                </span>
              </div>
            </div>
          </div>

          {/* 个人照片 */}
          <div className="info-section">
            <h2>个人正面照</h2>
            <div className="photo-display-container">
              {photoPreview ? (
                <div className="photo-preview">
                  <img src={photoPreview} alt="个人照片" />
                </div>
              ) : (
                <div className="photo-placeholder">
                  <span className="not-filled">未上传</span>
                </div>
              )}
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="action-buttons">
            <button className="btn-primary" onClick={handleEditInfo}>
              修改个人信息
            </button>
            <button className="btn-secondary" onClick={handleEditPassword}>
              修改密码
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ========== 编辑信息模式 ==========
  if (editMode === 'edit-info') {
    return (
      <div className="profile-container">
        <div className="profile-header">
          <h1>修改个人信息</h1>
          <p className="profile-subtitle">更新你的基本信息和个人照片</p>
        </div>

        <div className="profile-card">
          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">信息更新成功！</div>}

          <form onSubmit={handleSubmitInfo}>
            <div className="form-section">
              <h2>基本信息</h2>

              <div className="form-group">
                <label htmlFor="gender">性别（必填）</label>
                <select
                  id="gender"
                  name="gender"
                  value={formData.gender}
                  onChange={handleChange}
                  disabled={saving}
                  required
                >
                  <option value="">请选择</option>
                  <option value="male">男</option>
                  <option value="female">女</option>
                  <option value="other">其他</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="age">年龄（必填）</label>
                <input
                  type="number"
                  id="age"
                  name="age"
                  value={formData.age}
                  onChange={handleChange}
                  placeholder="例如：25"
                  min="1"
                  max="120"
                  disabled={saving}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="height">
                  身高（必填）
                  <span className="label-hint">单位：cm</span>
                </label>
                <input
                  type="number"
                  id="height"
                  name="height"
                  value={formData.height}
                  onChange={handleChange}
                  placeholder="例如：170"
                  min="100"
                  max="250"
                  disabled={saving}
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="weight">
                  体重（必填）
                  <span className="label-hint">单位：kg</span>
                </label>
                <input
                  type="number"
                  id="weight"
                  name="weight"
                  value={formData.weight}
                  onChange={handleChange}
                  placeholder="例如：65"
                  min="30"
                  max="200"
                  disabled={saving}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="city">
                  所在城市
                  <span className="label-hint">用于天气推荐</span>
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

            {/* 个人照片 */}
            <div className="form-section">
              <h2>个人正面照</h2>
              <p className="section-hint">上传一张正面人像照，用于虚拟试衣功能</p>
              
              <div className="form-group">
                <div className="photo-upload-container">
                  {photoPreview && (
                    <div className="photo-preview">
                      <img src={photoPreview} alt="个人照片" />
                    </div>
                  )}
                  <input
                    type="file"
                    id="profile_photo"
                    accept="image/*"
                    onChange={handlePhotoChange}
                    disabled={saving}
                    style={{ display: 'none' }}
                  />
                  <label htmlFor="profile_photo" className="btn-secondary upload-btn">
                    {photoPreview ? '更换照片' : '上传照片'}
                  </label>
                  {photoPreview && (
                    <p className="photo-hint">已上传照片，可以更换新照片</p>
                  )}
                </div>
              </div>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={saving}>
                {saving ? '保存中...' : '保存更改'}
              </button>
              <button type="button" className="btn-secondary" onClick={handleCancel} disabled={saving}>
                取消
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  // ========== 修改密码模式 ==========
  if (editMode === 'edit-password') {
    return (
      <div className="profile-container">
        <div className="profile-header">
          <h1>修改密码</h1>
          <p className="profile-subtitle">设置一个新的登录密码</p>
        </div>

        <div className="profile-card">
          {error && <div className="error-message">{error}</div>}
          {success && <div className="success-message">密码修改成功！</div>}

          <form onSubmit={handleSubmitPassword}>
            <div className="form-section">
              <h2>密码设置</h2>

              <div className="form-group">
                <label htmlFor="new_password">新密码</label>
                <input
                  type="password"
                  id="new_password"
                  name="new_password"
                  value={formData.new_password}
                  onChange={handleChange}
                  placeholder="请输入新密码（至少6位）"
                  disabled={saving}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="confirm_password">确认密码</label>
                <input
                  type="password"
                  id="confirm_password"
                  name="confirm_password"
                  value={formData.confirm_password}
                  onChange={handleChange}
                  placeholder="再次输入新密码"
                  disabled={saving}
                  required
                />
              </div>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn-primary" disabled={saving}>
                {saving ? '保存中...' : '确认修改'}
              </button>
              <button type="button" className="btn-secondary" onClick={handleCancel} disabled={saving}>
                取消
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return null;
}

export default Profile;
