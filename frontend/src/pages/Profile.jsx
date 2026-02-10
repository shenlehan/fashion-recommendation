import { useState, useEffect, useRef } from 'react';
import { getUserProfile, updateUserProfile } from '../services/api';
import './Profile.css';

// 全国省市数据（二级联动）
const PROVINCE_CITY_MAP = {
  '北京': ['北京'],
  '上海': ['上海'],
  '天津': ['天津'],
  '重庆': ['重庆'],
  '河北': ['石家庄', '唐山', '秦皇岛', '邯郸', '邢台', '保定', '张家口', '承德', '沧州', '廊坊', '衡水'],
  '山西': ['太原', '大同', '阳泉', '长治', '晋城', '朔州', '晋中', '运城', '忻州', '临汾', '吕梁'],
  '内蒙古': ['呼和浩特', '包头', '乌海', '赤峰', '通辽', '鄂尔多斯', '呼伦贝尔', '巴彦淖尔', '乌兰察布', '兴安盟', '锡林郭勒盟', '阿拉善盟'],
  '辽宁': ['沈阳', '大连', '鞍山', '抚顺', '本溪', '丹东', '锦州', '营口', '阜新', '辽阳', '盘锦', '铁岭', '朝阳', '葫芦岛'],
  '吉林': ['长春', '吉林', '四平', '辽源', '通化', '白山', '松原', '白城', '延边朝鲜族自治州'],
  '黑龙江': ['哈尔滨', '齐齐哈尔', '鸡西', '鹤岗', '双鸭山', '大庆', '伊春', '佳木斯', '七台河', '牡丹江', '黑河', '绥化', '大兴安岭地区'],
  '江苏': ['南京', '无锡', '徐州', '常州', '苏州', '南通', '连云港', '淮安', '盐城', '扬州', '镇江', '泰州', '宿迁'],
  '浙江': ['杭州', '宁波', '温州', '嘉兴', '湖州', '绍兴', '金华', '衢州', '舟山', '台州', '丽水'],
  '安徽': ['合肥', '芜湖', '蚌埠', '淮南', '马鞍山', '淮北', '铜陵', '安庆', '黄山', '滁州', '阜阳', '宿州', '六安', '亳州', '池州', '宣城'],
  '福建': ['福州', '厦门', '莆田', '三明', '泉州', '漳州', '南平', '龙岩', '宁德'],
  '江西': ['南昌', '景德镇', '萍乡', '九江', '新余', '鹰潭', '赣州', '吉安', '宜春', '抚州', '上饶'],
  '山东': ['济南', '青岛', '淄博', '枣庄', '东营', '烟台', '潍坊', '济宁', '泰安', '威海', '日照', '临沂', '德州', '聊城', '滨州', '菏泽'],
  '河南': ['郑州', '开封', '洛阳', '平顶山', '安阳', '鹤壁', '新乡', '焦作', '濮阳', '许昌', '漯河', '三门峡', '南阳', '商丘', '信阳', '周口', '驻马店'],
  '湖北': ['武汉', '黄石', '十堰', '宜昌', '襄阳', '鄂州', '荆门', '孝感', '荆州', '黄冈', '咸宁', '随州', '恩施土家族苗族自治州'],
  '湖南': ['长沙', '株洲', '湘潭', '衡阳', '邵阳', '岳阳', '常德', '张家界', '益阳', '郴州', '永州', '怀化', '娄底', '湘西土家族苗族自治州'],
  '广东': ['广州', '韶关', '深圳', '珠海', '汕头', '佛山', '江门', '湛江', '茂名', '肇庆', '惠州', '梅州', '汕尾', '河源', '阳江', '清远', '东莞', '中山', '潮州', '揭阳', '云浮'],
  '广西': ['南宁', '柳州', '桂林', '梧州', '北海', '防城港', '钦州', '贵港', '玉林', '百色', '贺州', '河池', '来宾', '崇左'],
  '海南': ['海口', '三亚', '三沙', '儋州', '五指山', '琼海', '文昌', '万宁', '东方'],
  '四川': ['成都', '自贡', '攀枝花', '泸州', '德阳', '绵阳', '广元', '遂宁', '内江', '乐山', '南充', '眉山', '宜宾', '广安', '达州', '雅安', '巴中', '资阳', '阿坝藏族羌族自治州', '甘孜藏族自治州', '凉山彝族自治州'],
  '贵州': ['贵阳', '六盘水', '遵义', '安顺', '毕节', '铜仁', '黔西南布依族苗族自治州', '黔东南苗族侗族自治州', '黔南布依族苗族自治州'],
  '云南': ['昆明', '曲靖', '玉溪', '保山', '昭通', '丽江', '普洱', '临沧', '楚雄彝族自治州', '红河哈尼族彝族自治州', '文山壮族苗族自治州', '西双版纳傣族自治州', '大理白族自治州', '德宏傣族景颇族自治州', '怒江傈僳族自治州', '迪庆藏族自治州'],
  '西藏': ['拉萨', '日喀则', '昌都', '林芝', '山南', '那曲', '阿里地区'],
  '陕西': ['西安', '铜川', '宝鸡', '咸阳', '渭南', '延安', '汉中', '榆林', '安康', '商洛'],
  '甘肃': ['兰州', '嘉峪关', '金昌', '白银', '天水', '武威', '张掖', '平凉', '酒泉', '庆阳', '定西', '陇南', '临夏回族自治州', '甘南藏族自治州'],
  '青海': ['西宁', '海东', '海北藏族自治州', '黄南藏族自治州', '海南藏族自治州', '果洛藏族自治州', '玉树藏族自治州', '海西蒙古族藏族自治州'],
  '宁夏': ['银川', '石嘴山', '吴忠', '固原', '中卫'],
  '新疆': ['乌鲁木齐', '克拉玛依', '吐鲁番', '哈密', '昌吉回族自治州', '博尔塔拉蒙古自治州', '巴音郭楞蒙古自治州', '阿克苏地区', '克孜勒苏柯尔克孜自治州', '喀什地区', '和田地区', '伊犁哈萨克自治州', '塔城地区', '阿勒泰地区'],
  '香港': ['香港'],
  '澳门': ['澳门'],
  '台湾': ['台北', '高雄', '台中', '台南', '基隆', '新竹', '嘉义']
};

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
  const [selectedProvince, setSelectedProvince] = useState(''); // 选中的省份
  const [availableCities, setAvailableCities] = useState([]); // 可选城市列表
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
    
    // 初始化省市选择器
    if (profile.city) {
      // 查找城市所属的省份
      for (const [province, cities] of Object.entries(PROVINCE_CITY_MAP)) {
        if (cities.includes(profile.city)) {
          setSelectedProvince(province);
          setAvailableCities(cities);
          break;
        }
      }
    } else {
      setSelectedProvince('');
      setAvailableCities([]);
    }
    
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
  
  // 处理省份选择
  const handleProvinceChange = (e) => {
    const province = e.target.value;
    setSelectedProvince(province);
    
    if (province) {
      setAvailableCities(PROVINCE_CITY_MAP[province] || []);
    } else {
      setAvailableCities([]);
    }
    
    // 清空城市选择
    setFormData({
      ...formData,
      city: ''
    });
  };
  
  // 处理城市选择
  const handleCityChange = (e) => {
    setFormData({
      ...formData,
      city: e.target.value
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
                <label htmlFor="province">
                  所在省份
                  <span className="label-hint">先选择省份</span>
                </label>
                <select
                  id="province"
                  name="province"
                  value={selectedProvince}
                  onChange={handleProvinceChange}
                  disabled={saving}
                >
                  <option value="">请选择省份</option>
                  {Object.keys(PROVINCE_CITY_MAP).map(province => (
                    <option key={province} value={province}>{province}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="city">
                  所在城市
                  <span className="label-hint">用于天气推荐</span>
                </label>
                <select
                  id="city"
                  name="city"
                  value={formData.city}
                  onChange={handleCityChange}
                  disabled={saving || !selectedProvince}
                >
                  <option value="">请先选择省份</option>
                  {availableCities.map(city => (
                    <option key={city} value={city}>{city}</option>
                  ))}
                </select>
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
