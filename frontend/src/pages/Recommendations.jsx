import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

import { getOutfitRecommendations, adjustOutfit, selectOutfit, getUserSessions, getSessionDetail, deleteConversationMessage, deleteSession, deleteAllSessions, API_ORIGIN, virtualTryOn, fetchImageAsBlob, getUserProfile } from '../services/api';
import './Recommendations.css';

// ===== 中英文映射字典 =====
const CATEGORY_MAP = {
  'underwear': '内衣',
  'inner_top': '内层上衣',
  'mid_top': '中层上衣',
  'outer_top': '外层上衣',
  'bottom': '下装',
  'full_body': '全身装',
  'shoes': '鞋子',
  'socks': '袜子',
  'accessories': '配饰',
  'unknown': '未知'
};

const OCCASION_MAP = {
  'Daily': '日常',
  'Work': '通勤',
  'Business': '商务',
  'Formal': '正式',
  'Party': '聚会',
  'Date': '约会',
  'Travel': '旅行',
  'Outdoor': '户外',
  'Home': '居家'
};

const STYLE_MAP = {
  'Classic': '经典',
  'Modern': '现代',
  'Minimalist': '极简',
  'Elegant': '优雅',
  'Casual': '休闲',
  'Street': '街头',
  'Trendy': '潮流',
  'Vintage': '复古',
  'Athletic': '运动',
  'Preppy': '学院'
};

const COLOR_MAP = {
  'Neutral': '中性色调',
  'Warm': '暖色调',
  'Cool': '冷色调'
};

const WEATHER_MAP = {
  // 晴朗天气
  'Sunny': '晴',
  'Clear': '晴朗',
  
  // 云层相关
  'Cloudy': '多云',
  'Overcast': '阴',
  'Partly Cloudy': '局部多云',
  
  // 降雨相关（按中国气象标准细分）
  'Rainy': '雨',
  'Light Rain': '小雨',
  'Moderate Rain': '中雨',
  'Heavy Rain': '大雨',
  'Rainstorm': '暴雨',
  'Drizzle': '毛毛雨',
  'Thunderstorm': '雷阵雨',
  'Sleet': '雨夹雪',
  
  // 降雪相关（按中国气象标准细分）
  'Snowy': '雪',
  'Light Snow': '小雪',
  'Moderate Snow': '中雪',
  'Heavy Snow': '大雪',
  'Snowstorm': '暴雪',
  
  // 雾霾相关
  'Foggy': '雾',
  'Hazy': '霾',
  'Dusty': '沙尘',
  
  // 风相关
  'Windy': '有风',
  
  // 极端天气
  'Extreme': '极端天气'
};

const translateCategory = (category) => {
  return CATEGORY_MAP[category?.toLowerCase()] || category || '未分类';
};

const translateOccasion = (occasion) => {
  return OCCASION_MAP[occasion] || occasion;
};

const translateStyle = (style) => {
  return STYLE_MAP[style] || style;
};

const translateColor = (color) => {
  return COLOR_MAP[color] || color;
};

const translateWeather = (condition) => {
  if (!condition) return '未知';
  
  // 如果已经是中文趋势格式（如"多云转晴"），直接返回
  if (condition.includes('转')) {
    return condition;
  }
  
  // 判断是否为纯中文（已翻译）
  const hasChinese = /[\u4e00-\u9fff]/.test(condition);
  if (hasChinese) {
    return condition;  // 已经是中文，直接返回
  }
  
  // 英文 → 中文翻译
  return WEATHER_MAP[condition] || condition;
};

function Recommendations({ user, isUploading }) {
  const navigate = useNavigate();
  
  // --- 从 localStorage 恢复状态 ---
  const getStoredState = (key, defaultValue) => {
    try {
      const stored = localStorage.getItem(`recommendations_${user.id}_${key}`);
      return stored ? JSON.parse(stored) : defaultValue;
    } catch {
      return defaultValue;
    }
  };

  // --- 原有状态（添加持久化） ---
  const [recommendations, setRecommendations] = useState(() => getStoredState('recommendations', null));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const errorTimerRef = useRef(null); // 错误提示定时器
  const [preferences, setPreferences] = useState(() => getStoredState('preferences', {
    occasion: '',
    style: '',
    color_preference: '',
    custom_request: ''
  }));
  const [showPreferences, setShowPreferences] = useState(false);
  const [savedPreferences, setSavedPreferences] = useState(() => getStoredState('savedPreferences', null)); // 暂存的要求

  // --- 新增：多轮对话状态 ---
  const [sessionId, setSessionId] = useState(() => getStoredState('sessionId', null));
  const [conversationHistory, setConversationHistory] = useState(() => getStoredState('conversationHistory', []));
  const [adjustmentInput, setAdjustmentInput] = useState('');
  const [isAdjusting, setIsAdjusting] = useState(false);
  const historyEndRef = useRef(null);
  
  // 新增：会话列表状态
  const [showSessionList, setShowSessionList] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [loadingSessions, setLoadingSessions] = useState(false);
  
  // 新增：对话历史展开/折叠状态
  const [collapsedMessages, setCollapsedMessages] = useState(new Set());
  const [itemsMap, setItemsMap] = useState(() => getStoredState('itemsMap', {})); // 存储outfit_ids对应的衣物信息

  // --- ⚠️ 新增：虚拟试衣相关状态 ---
  const [personImage, setPersonImage] = useState(null);
  const [personPreview, setPersonPreview] = useState(null);
  const [hasProfilePhoto, setHasProfilePhoto] = useState(false); // 是否有个人资料照片
  const [tryOnResult, setTryOnResult] = useState(null);
  const [isTryingOn, setIsTryingOn] = useState(false);

  // --- 持久化状态到 localStorage ---
  useEffect(() => {
    if (recommendations) {
      localStorage.setItem(`recommendations_${user.id}_recommendations`, JSON.stringify(recommendations));
    }
  }, [recommendations, user.id]);

  useEffect(() => {
    localStorage.setItem(`recommendations_${user.id}_preferences`, JSON.stringify(preferences));
  }, [preferences, user.id]);

  useEffect(() => {
    if (savedPreferences) {
      localStorage.setItem(`recommendations_${user.id}_savedPreferences`, JSON.stringify(savedPreferences));
    }
  }, [savedPreferences, user.id]);

  // 新增：持久化会话状态
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem(`recommendations_${user.id}_sessionId`, sessionId);
    }
  }, [sessionId, user.id]);

  // 组件挂载时恢复会话状态
  useEffect(() => {
    const savedSessionId = localStorage.getItem(`recommendations_${user.id}_sessionId`);
    const savedHistory = localStorage.getItem(`recommendations_${user.id}_conversationHistory`);
    const savedRecs = localStorage.getItem(`recommendations_${user.id}_recommendations`);
    
    if (savedSessionId) {
      setSessionId(savedSessionId);
    }
    if (savedHistory) {
      try {
        setConversationHistory(JSON.parse(savedHistory));
      } catch (e) {
        console.error('恢复对话历史失败:', e);
      }
    }
    if (savedRecs) {
      try {
        setRecommendations(JSON.parse(savedRecs));
      } catch (e) {
        console.error('恢复推荐失败:', e);
      }
    }
  }, [user.id]);

  useEffect(() => {
    localStorage.setItem(`recommendations_${user.id}_conversationHistory`, JSON.stringify(conversationHistory));
    // 自动滚动到最新消息
    if (historyEndRef.current) {
      historyEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [conversationHistory, user.id]);
  
  // 新增：持久化itemsMap
  useEffect(() => {
    if (itemsMap && Object.keys(itemsMap).length > 0) {
      localStorage.setItem(`recommendations_${user.id}_itemsMap`, JSON.stringify(itemsMap));
    }
  }, [itemsMap, user.id]);

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

  // --- 原有辅助函数 ---
  const getImageUrl = (path) => {
    if (!path) return '';
    if (path.startsWith('http')) return path;
    return `${API_ORIGIN}/${path.replace(/^\//, '')}`;
  };

  // 加载用户资料照片
  useEffect(() => {
    loadUserProfilePhoto();
    // 同时加载会话列表，用于判断是否显示按钮
    loadSessions();
  }, [user.id]);

  const loadUserProfilePhoto = async () => {
    try {
      const profile = await getUserProfile(user.id);
      console.log('用户资料:', profile);
      if (profile.profile_photo) {
        // 使用API_ORIGIN确保路径一致性
        const photoUrl = `${API_ORIGIN}/uploads/${profile.profile_photo}`;
        console.log('个人照片URL:', photoUrl);
        setPersonPreview(photoUrl);
        setHasProfilePhoto(true);
      } else {
        console.warn('用户未上传个人照片');
        setHasProfilePhoto(false);
      }
    } catch (err) {
      console.error('加载用户照片失败:', err);
    }
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
    if (!personPreview) {
      alert(hasProfilePhoto 
        ? '未加载个人照片，请刷新页面' 
        : '请先去个人资料页面上传一张正面照，或者在页面顶部临时上传照片'
      );
      return;
    }

    // 如果有profile_photo但是personImage为空，说明是从个人资料加载的，需要转换为Blob
    let personBlob = personImage;
    if (!personImage && personPreview) {
      try {
        console.log('正在加载个人照片:', personPreview);
        const response = await fetch(personPreview, {
          mode: 'cors',
          cache: 'no-cache'
        });
        console.log('照片响应状态:', response.status, response.statusText);
        if (!response.ok) {
          throw new Error(`照片加载失败: ${response.status}`);
        }
        personBlob = await response.blob();
        console.log('照片Blob大小:', personBlob.size, 'bytes, 类型:', personBlob.type);
      } catch (err) {
        console.error('加载个人照片错误:', err);
        alert('加载个人照片失败，请重新上传');
        return;
      }
    }

    try {
      setIsTryingOn(true);
      setError('');
      
      // 1. 将推荐的衣服 URL 转为二进制 Blob (跨域请求)
      const clothBlob = await fetchImageAsBlob(getImageUrl(item.image_path));
      
      // 2. 调用后端代理接口转发给 CatVTON (8001端口)
      const resultBlob = await virtualTryOn(personBlob, clothBlob, 'upper_body');
      
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
      
      // 保存会话ID
      if (data.session_id) {
        setSessionId(data.session_id);
        // 清空对话历史（新会话）
        setConversationHistory([]);
        // 清空itemsMap（新会话）
        setItemsMap({});
      }
      
      // 构建初始的itemsMap（从推荐结果中提取）
      if (data.outfits && data.outfits.length > 0) {
        const initialItemsMap = {};
        data.outfits.forEach(outfit => {
          if (outfit.items) {
            outfit.items.forEach(item => {
              if (item.id) {
                initialItemsMap[item.id] = {
                  id: item.id,
                  name: item.name,
                  category: item.category,
                  color: item.color,
                  image_path: item.image_path
                };
              }
            });
          }
        });
        setItemsMap(initialItemsMap);
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || '加载推荐失败';
      
      // 检查是否是缺少必填字段错误
      if (err.response?.status === 400 && errorMsg.includes('个人资料')) {
        // 显示提示并引导用户去填写
        setError(
          <div>
            <p>{errorMsg}</p>
            <button 
              className="btn-secondary" 
              onClick={() => navigate('/profile')}
              style={{ marginTop: '1rem' }}
            >
              去填写个人资料
            </button>
          </div>
        );
      } else {
        setError(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  // 新增：调整穿搭逻辑
  const handleAdjustOutfit = async () => {
    if (!adjustmentInput.trim()) {
      setError('请输入调整要求');
      return;
    }
    
    if (!sessionId) {
      setError('请先生成初始推荐');
      return;
    }

    // 防止并发请求
    if (isAdjusting) {
      return;
    }

    try {
      setIsAdjusting(true);
      setError('');
      
      const result = await adjustOutfit(sessionId, adjustmentInput, user.id);
      
      // 更新推荐结果
      const newRecommendations = {
        ...recommendations,
        outfits: result.outfits
      };
      setRecommendations(newRecommendations);
      
      // 更新对话历史和items_map
      if (result.conversation_history) {
        setConversationHistory(result.conversation_history);
      }
      if (result.items_map) {
        setItemsMap(prevMap => ({
          ...prevMap,
          ...result.items_map
        }));
      }
      
      // 确保sessionId持久化
      if (result.session_id && result.session_id !== sessionId) {
        setSessionId(result.session_id);
      }
      
      // 清空输入
      setAdjustmentInput('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || '调整失败';
      
      // 检查会话过期
      if (err.response?.status === 404 && errorMsg.includes('会话')) {
        setError('会话已过期，请重新生成推荐');
        handleNewConversation();
      } else if (err.response?.status === 410) {
        // 410 Gone - 会话过期
        setError(errorMsg);
        handleNewConversation();
      } else {
        setError(errorMsg);
      }
    } finally {
      setIsAdjusting(false);
    }
  };

  const handleRegenerateWithPreferences = () => {
    const filteredPrefs = Object.fromEntries(
      Object.entries(preferences).filter(([_, value]) => value !== '')
    );
    setSavedPreferences(filteredPrefs); // 暂存要求
    setShowPreferences(false); // 关闭面板
  };

  const handleRegenerate = () => {
    // 检查是否有衣物上传中
    if (isUploading) {
      setError('有衣物正在上传中，请等待上传完成后再生成推荐');
      return;
    }
    // 使用暂存的要求生成推荐
    fetchRecommendations(savedPreferences || {});
  };

  // 新增：清空会话开始新对话
  const handleNewConversation = () => {
    setSessionId(null);
    setConversationHistory([]);
    setRecommendations(null);
    setSavedPreferences({});
    setItemsMap({});
    localStorage.removeItem(`recommendations_${user.id}_sessionId`);
    localStorage.removeItem(`recommendations_${user.id}_conversationHistory`);
    localStorage.removeItem(`recommendations_${user.id}_recommendations`);
    localStorage.removeItem(`recommendations_${user.id}_savedPreferences`);
    localStorage.removeItem(`recommendations_${user.id}_itemsMap`);
  };
  
  // 新增：加载会话列表
  const loadSessions = async () => {
    try {
      setLoadingSessions(true);
      const data = await getUserSessions(user.id, 10);
      setSessions(data.sessions || []);
    } catch (err) {
      console.error('加载会话列表失败:', err);
      setError('加载会话列表失败');
    } finally {
      setLoadingSessions(false);
    }
  };
  
  // 新增：切换到指定会话
  const switchToSession = async (newSessionId) => {
    try {
      setLoading(true);
      const data = await getSessionDetail(newSessionId, user.id);
      
      // 更新状态
      setSessionId(data.session_id);
      setConversationHistory(data.conversation_history || []);
      setItemsMap(data.items_map || {});
      
      // 恢复偏好
      if (data.preferences) {
        setSavedPreferences(data.preferences);
      }
      
      // 构造虚拟的recommendations对象以保持UI可用
      setRecommendations({
        session_id: data.session_id,
        outfits: [],
        weather: null
      });
      
      setShowSessionList(false);
    } catch (err) {
      console.error('切换会话失败:', err);
      setError('切换会话失败');
    } finally {
      setLoading(false);
    }
  };
  
  // 新增：切换消息折叠状态
  const toggleMessageCollapse = (index) => {
    const newCollapsed = new Set(collapsedMessages);
    if (newCollapsed.has(index)) {
      newCollapsed.delete(index);
    } else {
      newCollapsed.add(index);
    }
    setCollapsedMessages(newCollapsed);
  };
  
  // 新增：删除特定消息
  const handleDeleteMessage = async (messageIndex) => {
    if (!sessionId) return;
    
    // 二次确认
    if (!window.confirm('确定要删除这条对话记录吗？')) {
      return;
    }
    
    try {
      await deleteConversationMessage(sessionId, messageIndex, user.id);
      
      // 更新本地状态
      const updatedHistory = conversationHistory.filter((_, index) => index !== messageIndex);
      setConversationHistory(updatedHistory);
      
      // 如果删除后折叠集合中有大于删除索引的，需要更新
      const newCollapsed = new Set();
      collapsedMessages.forEach(idx => {
        if (idx < messageIndex) {
          newCollapsed.add(idx);
        } else if (idx > messageIndex) {
          newCollapsed.add(idx - 1);
        }
      });
      setCollapsedMessages(newCollapsed);
      
    } catch (err) {
      const errorMsg = err.response?.data?.detail || '删除消息失败';
      setError(errorMsg);
    }
  };
  
  // 新增：删除整个会话
  // 新增：删除整个会话
  const handleDeleteSession = async (targetSessionId) => {
    // 二次确认
    if (!window.confirm('确定要删除此会话吗？所有对话历史将被永久删除！')) {
      return;
    }
    
    try {
      // 先乐观更新前端状态（立即从列表中移除）
      setSessions(prevSessions => 
        prevSessions.filter(s => s.session_id !== targetSessionId)
      );
      
      // 调用后端删除
      await deleteSession(targetSessionId, user.id);
      
      // 如果删除的是当前会话，清空状态
      if (targetSessionId === sessionId) {
        handleNewConversation();
      }
      
      // 如果删除后没有会话了，关闭会话列表
      const remainingSessions = sessions.filter(s => s.session_id !== targetSessionId);
      if (remainingSessions.length === 0) {
        setShowSessionList(false);
      }
      
    } catch (err) {
      const errorMsg = err.response?.data?.detail || '删除会话失败';
      setError(errorMsg);
      // 删除失败，重新加载会话列表恢复状态
      await loadSessions();
    }
  };
  
  // 新增：清空所有会话
  const handleDeleteAllSessions = async () => {
    // 二次确认（严格确认）
    if (!window.confirm('⚠️ 确定要清空所有会话吗？\n\n这将永久删除您的所有对话历史，无法恢复！')) {
      return;
    }
    
    try {
      // 先乐观更新前端状态
      setSessions([]);
      setShowSessionList(false);
      
      // 调用后端删除
      const result = await deleteAllSessions(user.id);
      
      // 清空当前会话状态
      handleNewConversation();
      
      // 显示成功消息
      setError(`已成功清空 ${result.deleted_count} 个会话`);
      
    } catch (err) {
      const errorMsg = err.response?.data?.detail || '清空会话失败';
      setError(errorMsg);
      // 失败时重新加载会话列表
      await loadSessions();
    }
  };
  
  // 新增：选择某组推荐作为会话基础
  const handleSelectOutfit = async (outfitIndex, outfit) => {
    if (!sessionId) {
      setError('会话不存在，请先生成推荐');
      return;
    }
    
    try {
      setLoading(true);
      const result = await selectOutfit(sessionId, outfitIndex, outfit, user.id);
      
      // 更新会话历史和衣物映射
      setConversationHistory(result.conversation_history || []);
      setItemsMap(result.items_map || {});
      
      // 显示成功消息
      setError(`✅ ${result.message}`);
      
      // 3秒后清空成功消息
      setTimeout(() => {
        setError('');
      }, 3000);
      
    } catch (err) {
      const errorMsg = err.response?.data?.detail || '选择推荐失败';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="recommendations-container">
      <div className="recommendations-header">
        <h1>穿搭推荐</h1>
        <div className="header-actions">
          {(sessionId || (sessions && sessions.length > 0)) && (
            <>
              <button
                className="btn-secondary"
                onClick={() => {
                  setShowSessionList(!showSessionList);
                  if (!showSessionList) loadSessions();
                }}
                disabled={loading}
                title="查看和切换历史会话"
              >
                会话列表
              </button>
              {sessionId && (
                <button
                  className="btn-secondary"
                  onClick={handleNewConversation}
                  disabled={loading}
                  title="清空当前会话，开始新的推荐"
                >
                  新建会话
                </button>
              )}
            </>
          )}
          {!showPreferences && (
            <button
              className="btn-secondary"
              onClick={() => setShowPreferences(true)}
              disabled={loading}
            >
              我的要求
            </button>
          )}
          <button 
            className="btn-primary" 
            onClick={handleRegenerate} 
            disabled={loading}
          >
            {loading ? '生成中...' : '生成推荐'}
          </button>
        </div>
      </div>

      {/* ⚠️ 新增：试衣结果弹出层 (Modal) */}
      {tryOnResult && (
        <div className="vton-modal-overlay" onClick={() => setTryOnResult(null)}>
          <div className="vton-modal-content" onClick={e => e.stopPropagation()}>
            <button className="close-modal" onClick={() => setTryOnResult(null)}>&times;</button>
            <h2>虚拟试衣效果</h2>
            <div className="vton-result-container">
              <img src={tryOnResult} alt="虚拟试衣效果" />
            </div>
            <div className="modal-footer">
              <p>由 CatVTON 图像生成技术驱动</p>
              <button className="btn-primary" onClick={() => window.open(tryOnResult)}>保存图片</button>
            </div>
          </div>
        </div>
      )}

      {/* 要求面板 */}
      {showPreferences && (
        <div className="preferences-panel">
          <h2>自定义要求</h2>
          <p className="preferences-subtitle">告诉我你的穿搭要求，生成更精准的推荐</p>
          <div className="preferences-form">
            <div className="form-group">
              <label htmlFor="occasion">场合</label>
              <select
                id="occasion"
                value={preferences.occasion}
                onChange={(e) => setPreferences({ ...preferences, occasion: e.target.value })}
              >
                <option value="">任意</option>
                <option value="Daily">日常</option>
                <option value="Work">通勤</option>
                <option value="Business">商务</option>
                <option value="Formal">正式</option>
                <option value="Party">聚会</option>
                <option value="Date">约会</option>
                <option value="Travel">旅行</option>
                <option value="Outdoor">户外</option>
                <option value="Home">居家</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="style">风格</label>
              <select
                id="style"
                value={preferences.style}
                onChange={(e) => setPreferences({ ...preferences, style: e.target.value })}
              >
                <option value="">任意</option>
                <option value="Classic">经典</option>
                <option value="Modern">现代</option>
                <option value="Minimalist">极简</option>
                <option value="Elegant">优雅</option>
                <option value="Casual">休闲</option>
                <option value="Street">街头</option>
                <option value="Trendy">潮流</option>
                <option value="Vintage">复古</option>
                <option value="Athletic">运动</option>
                <option value="Preppy">学院</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="color_preference">色调</label>
              <select
                id="color_preference"
                value={preferences.color_preference}
                onChange={(e) => setPreferences({ ...preferences, color_preference: e.target.value })}
              >
                <option value="">任意</option>
                <option value="Neutral">中性色调</option>
                <option value="Warm">暖色调</option>
                <option value="Cool">冷色调</option>
              </select>
            </div>
            <div className="form-group">
              <label htmlFor="custom_request">特殊要求</label>
              <input
                type="text"
                id="custom_request"
                value={preferences.custom_request}
                onChange={(e) => setPreferences({ ...preferences, custom_request: e.target.value })}
                placeholder="例如：我要去参加前女友的婚礼..."
              />
            </div>
            <button
              className="btn-primary"
              onClick={handleRegenerateWithPreferences}
              disabled={loading}
            >
              应用要求
            </button>
          </div>
        </div>
      )}

      {/* 显示已暂存的要求 */}
      {savedPreferences && Object.keys(savedPreferences).length > 0 && (
        <div className="saved-preferences-display">
          <h3>当前要求：</h3>
          <div className="saved-preferences-tags">
            {savedPreferences.occasion && <span className="pref-tag">场合：{translateOccasion(savedPreferences.occasion)}</span>}
            {savedPreferences.style && <span className="pref-tag">风格：{translateStyle(savedPreferences.style)}</span>}
            {savedPreferences.color_preference && <span className="pref-tag">色调：{translateColor(savedPreferences.color_preference)}</span>}
            {savedPreferences.custom_request && <span className="pref-tag">特殊要求：{savedPreferences.custom_request}</span>}
          </div>
        </div>
      )}

      {error && <div className="error-message">{error}</div>}

      {/* 新增：对话历史和调整区域 */}
      {sessionId && recommendations && (
        <div className="conversation-section">
          <div className="conversation-header">
            <h2>对话调整</h2>
            <button
              className="btn-secondary"
              onClick={() => {
                setShowSessionList(!showSessionList);
                if (!showSessionList) loadSessions();
              }}
            >
              {showSessionList ? '关闭会话列表' : '查看历史会话'}
            </button>
          </div>
          
          {/* 会话列表侧边栏 */}
          {showSessionList && (
            <div className="session-list-panel">
              <div className="session-list-header">
                <h3>我的会话</h3>
                {sessions.length > 0 && (
                  <button
                    className="btn-danger-small"
                    onClick={handleDeleteAllSessions}
                    title="清空所有会话"
                  >
                    清空全部
                  </button>
                )}
              </div>
              {loadingSessions ? (
                <p>加载中...</p>
              ) : sessions.length > 0 ? (
                <div className="session-list">
                  {sessions.map((session) => (
                    <div
                      key={session.session_id}
                      className={`session-item ${session.session_id === sessionId ? 'active' : ''}`}
                    >
                      <div 
                        className="session-content"
                        onClick={() => switchToSession(session.session_id)}
                      >
                        <div className="session-preview">
                          {session.preview && session.preview.length > 30
                            ? session.preview.substring(0, 30) + '...'
                            : session.preview || '新会话'}
                        </div>
                        <div className="session-meta">
                          <span>{session.message_count} 条消息</span>
                          <span>{new Date(session.updated_at).toLocaleDateString()}</span>
                        </div>
                        {session.preferences && Object.keys(session.preferences).length > 0 && (
                          <div className="session-tags">
                            {session.preferences.occasion && <span>{translateOccasion(session.preferences.occasion)}</span>}
                            {session.preferences.style && <span>{translateStyle(session.preferences.style)}</span>}
                          </div>
                        )}
                      </div>
                      <button
                        className="delete-session-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDeleteSession(session.session_id);
                        }}
                        title="删除此会话"
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="no-sessions">暂无历史会话</p>
              )}
            </div>
          )}
          
          {/* 对话历史 */}
          {conversationHistory.length > 0 && (
            <div className="conversation-history">
              <h3>对话历史</h3>
              <div className="history-messages">
                {conversationHistory.map((msg, index) => {
                  const isCollapsed = collapsedMessages.has(index);
                  const hasOutfitIds = msg.outfit_ids && msg.outfit_ids.length > 0;
                  
                  return (
                    <div key={index} className={`message ${msg.role}`}>
                      <div className="message-header">
                        <div className="message-role">
                          {msg.role === 'user' ? '你' : 'AI'}
                        </div>
                        <div className="message-actions">
                          {hasOutfitIds && (
                            <button
                              className="collapse-toggle"
                              onClick={() => toggleMessageCollapse(index)}
                              title={isCollapsed ? '展开衣物' : '折叠衣物'}
                            >
                              {isCollapsed ? '▼ 展开' : '▲ 折叠'}
                            </button>
                          )}
                          <button
                            className="delete-message-btn"
                            onClick={() => handleDeleteMessage(index)}
                            title="删除这条消息"
                          >
                            ×
                          </button>
                        </div>
                      </div>
                      <div className="message-content">{msg.content}</div>
                      
                      {/* 展示衣物缩略图 */}
                      {hasOutfitIds && !isCollapsed && (
                        <div className="message-outfit-items">
                          {msg.outfit_ids.map((itemId) => {
                            const item = itemsMap[itemId];
                            if (!item) return null;
                            
                            return (
                              <div key={itemId} className="history-outfit-item">
                                {item.image_path ? (
                                  <img
                                    src={getImageUrl(item.image_path)}
                                    alt={item.name}
                                    title={item.name}
                                  />
                                ) : (
                                  <div className="no-image-tiny">
                                    {translateCategory(item.category)}
                                  </div>
                                )}
                                <p>{item.name}</p>
                              </div>
                            );
                          })}
                        </div>
                      )}
                      
                      <div className="message-timestamp">
                        {new Date(msg.timestamp).toLocaleString()}
                      </div>
                    </div>
                  );
                })}
                <div ref={historyEndRef} />
              </div>
            </div>
          )}
          
          {/* 调整输入框 */}
          <div className="adjustment-input-area">
            <h3>继续调整穿搭</h3>
            <div className="adjustment-examples">
              <p>你可以说：</p>
              <div className="example-tags">
                <span onClick={() => setAdjustmentInput('把外套换成夹克')}>'把外套换成夹克'</span>
                <span onClick={() => setAdjustmentInput('换个暖色系的')}>'换个暖色系的'</span>
                <span onClick={() => setAdjustmentInput('更休闲一些')}>'更休闲一些'</span>
                <span onClick={() => setAdjustmentInput('换双运动鞋')}>'换双运动鞋'</span>
              </div>
            </div>
            <div className="adjustment-input-wrapper">
              <input
                type="text"
                value={adjustmentInput}
                onChange={(e) => setAdjustmentInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAdjustOutfit()}
                placeholder="告诉我你想怎么调整穿搭..."
                disabled={isAdjusting || loading}
              />
              <button
                className="btn-primary"
                onClick={handleAdjustOutfit}
                disabled={isAdjusting || loading || !adjustmentInput.trim()}
              >
                {isAdjusting ? (
                  <>
                    <span className="spinner-small"></span>
                    AI思考中...
                  </>
                ) : '调整穿搭'}
              </button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>AI 正在为你生成专属推荐...</p>
          <p className="loading-subtext">这可能需要 30-60 秒</p>
        </div>
      ) : recommendations ? (
        <div className="recommendations-content">
          {/* 原有天气模块 */}
          <div className="weather-info">
            <h2>生成本次推荐时{user.city || '你所在城市'}的天气</h2>
            <div className="weather-details">
              <p>温度：{recommendations.weather?.temp_min || '未知'}~{recommendations.weather?.temp_max || '未知'}°C</p>
              <p>天气：{translateWeather(recommendations.weather?.condition) || '未知'}</p>
              {recommendations.weather?.humidity && (
                <p>湿度：{recommendations.weather.humidity}%</p>
              )}
              {recommendations.weather?.wind_speed !== undefined && (
                <p>风速：{recommendations.weather.wind_speed} m/s</p>
              )}
              {recommendations.weather?.rain_prob !== undefined && recommendations.weather.rain_prob > 0 && (
                <p>降水概率：{recommendations.weather.rain_prob}%</p>
              )}
            </div>
          </div>

          <div className="outfits-section">
            <h2>推荐搭配</h2>
            {recommendations.outfits && recommendations.outfits.length > 0 ? (
              <div className="outfits-grid">
                {recommendations.outfits.map((outfit, index) => (
                  <div key={index} className="outfit-card">
                    <div className="outfit-card-header">
                      <h3>方案 {index + 1}</h3>
                      {sessionId && conversationHistory.length === 0 && (
                        <button
                          className="btn-select-outfit"
                          onClick={() => handleSelectOutfit(index, outfit)}
                          disabled={loading}
                          title="选择此方案并开始对话调整"
                        >
                          使用这组
                        </button>
                      )}
                    </div>
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
                              <div className="no-image-small">{translateCategory(item.category)}</div>
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
              <p className="no-outfits">暂无推荐搭配</p>
            )}
          </div>

          {/* 原有缺失单品模块 */}
          {recommendations.missing_items && recommendations.missing_items.length > 0 && (
            <div className="missing-items-section">
              <h2>建议购买以下单品完善你的衣橱</h2>
              <div className="missing-items-list">
                {recommendations.missing_items.map((item, index) => (
                  <div key={index} className="missing-item">
                    <div>
                      <h4>{typeof item === 'string' ? translateCategory(item) : translateCategory(item.category)}</h4>
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
            <h2>获取个性化穿搭推荐</h2>
            <p>点击上方 <strong>「生成推荐」</strong> 按钮开始</p>
            <ul>
              <li>基于你的衣橱</li>
              <li>结合当前天气</li>
              <li>AI 智能搭配</li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}

export default Recommendations;