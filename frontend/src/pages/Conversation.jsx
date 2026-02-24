import { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  adjustOutfit, 
  getUserSessions, 
  getSessionDetail, 
  deleteConversationMessage, 
  deleteSession, 
  deleteAllSessions,
  virtualTryOn,
  batchVirtualTryOn,
  fetchImageAsBlob,
  getUserProfile,
  API_ORIGIN 
} from '../services/api';
import './Conversation.css';

// 中英文映射字典
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

const translateCategory = (category) => {
  return CATEGORY_MAP[category?.toLowerCase()] || category || '未分类';
};

function Conversation({ user, isUploading }) {
  const navigate = useNavigate();
  const location = useLocation();
  const historyEndRef = useRef(null);
  const errorTimerRef = useRef(null);
  const isInitializedRef = useRef(false); // 跟踪是否已初始化

  // 从localStorage恢复状态
  const getStoredState = (key, defaultValue) => {
    try {
      const stored = localStorage.getItem(`conversation_${user.id}_${key}`);
      return stored ? JSON.parse(stored) : defaultValue;
    } catch {
      return defaultValue;
    }
  };

  // 核心状态
  const [sessionId, setSessionId] = useState(() => {
    try {
      const stored = localStorage.getItem(`shared_${user.id}_sessionId`);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });
  const [conversationHistory, setConversationHistory] = useState(() => getStoredState('conversationHistory', []));
  const [itemsMap, setItemsMap] = useState(() => getStoredState('itemsMap', {}));
  const [adjustmentInput, setAdjustmentInput] = useState('');
  const [isAdjusting, setIsAdjusting] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [loading, setLoading] = useState(false);

  // 会话列表
  const [showSessionList, setShowSessionList] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [hasMoreSessions, setHasMoreSessions] = useState(true);
  const sessionListRef = useRef(null);

  // 消息折叠
  const [collapsedMessages, setCollapsedMessages] = useState(new Set());

  // 消息管理模式
  const [isManagingMessages, setIsManagingMessages] = useState(false);
  const [selectedMessagePairs, setSelectedMessagePairs] = useState(new Set()); // 存储成对索引

  // 虚拟试衣
  const [personPreview, setPersonPreview] = useState(null);
  const [personImage, setPersonImage] = useState(null);
  const [hasProfilePhoto, setHasProfilePhoto] = useState(false);
  const [tryOnResult, setTryOnResult] = useState(null);
  const [isTryingOn, setIsTryingOn] = useState(false);
  const [activeTryOnButton, setActiveTryOnButton] = useState(null); // 记录正在生成的按钮ID

  // 删除确认模态框
  const [deleteConfirmModal, setDeleteConfirmModal] = useState({
    show: false,
    type: null,
    targetId: null,
    title: '',
    message: ''
  });

  // 持久化状态
  useEffect(() => {
    if (sessionId) {
      localStorage.setItem(`shared_${user.id}_sessionId`, sessionId);
    }
  }, [sessionId, user.id]);

  useEffect(() => {
    localStorage.setItem(`conversation_${user.id}_conversationHistory`, JSON.stringify(conversationHistory));
    if (historyEndRef.current) {
      historyEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [conversationHistory, user.id]);

  useEffect(() => {
    if (itemsMap && Object.keys(itemsMap).length > 0) {
      localStorage.setItem(`conversation_${user.id}_itemsMap`, JSON.stringify(itemsMap));
    }
  }, [itemsMap, user.id]);

  // 错误自动清除
  useEffect(() => {
    if (error) {
      if (errorTimerRef.current) {
        clearTimeout(errorTimerRef.current);
      }
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

  // 成功消息自动清除
  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => {
        setSuccessMessage('');
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [successMessage]);

  // 初始化:加载会话列表和用户照片
  useEffect(() => {
    // 首次初始化加载会话列表和用户照片
    if (!isInitializedRef.current) {
      loadSessions();
      loadUserProfilePhoto();
      isInitializedRef.current = true;
      
      // 首次初始化时检查localStorage中的sessionId
      let parsedStoredId = null;
      try {
        const storedSessionId = localStorage.getItem(`shared_${user.id}_sessionId`);
        parsedStoredId = storedSessionId ? JSON.parse(storedSessionId) : null;
      } catch (err) {
        // localStorage读取或解析失败
      }
      
      if (parsedStoredId) {
        setSessionId(parsedStoredId);
      }
    }

    // 检查是否从推荐页面带来sessionId
    const paramSessionId = location.state?.sessionId;
    if (paramSessionId) {
      let parsedStoredId = null;
      try {
        const storedSessionId = localStorage.getItem(`shared_${user.id}_sessionId`);
        parsedStoredId = storedSessionId ? JSON.parse(storedSessionId) : null;
      } catch (err) {
        // localStorage读取失败
      }
      
      // 路由参数优先级更高，不同时才切换
      if (paramSessionId !== parsedStoredId) {
        switchToSession(paramSessionId);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user.id, location.state?.sessionId]);

  const getImageUrl = (path) => {
    if (!path) return '';
    if (path.startsWith('http')) return path;
    return `${API_ORIGIN}/${path.replace(/^\//, '')}`;
  };

  const loadUserProfilePhoto = async () => {
    try {
      const profile = await getUserProfile(user.id);
      if (profile.profile_photo) {
        const photoUrl = `${API_ORIGIN}/uploads/${profile.profile_photo}`;
        setPersonPreview(photoUrl);
        setHasProfilePhoto(true);
      } else {
        setHasProfilePhoto(false);
      }
    } catch (err) {
      console.error('加载用户照片失败:', err);
    }
  };

  const handlePersonChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPersonImage(file);
      setPersonPreview(URL.createObjectURL(file));
    }
  };

  const handleTryOn = async (item) => {
    if (!personPreview) {
      alert(hasProfilePhoto 
        ? '未加载个人照片,请刷新页面' 
        : '请先去个人资料页面上传正面照,或在页面顶部临时上传照片'
      );
      return;
    }

    let personBlob = personImage;
    if (!personImage && personPreview) {
      try {
        const response = await fetch(personPreview, {
          mode: 'cors',
          cache: 'no-cache'
        });
        if (!response.ok) {
          throw new Error(`照片加载失败: ${response.status}`);
        }
        personBlob = await response.blob();
      } catch (err) {
        console.error('加载个人照片错误:', err);
        alert('加载个人照片失败,请重新上传');
        return;
      }
    }

    try {
      setIsTryingOn(true);
      setError('');
      
      const clothBlob = await fetchImageAsBlob(getImageUrl(item.image_path));
      const resultBlob = await virtualTryOn(personBlob, clothBlob, 'upper_body');
      const resultUrl = URL.createObjectURL(resultBlob);
      setTryOnResult(resultUrl);
    } catch (err) {
      console.error("试衣错误:", err);
      setError('虚拟试衣请求失败,请确保AI后端服务已启动');
    } finally {
      setIsTryingOn(false);
    }
  };

  // --- 批量试穿逻辑 ---
  const handleBatchTryOn = async (items, messageIndex) => {
    if (!personPreview) {
      alert(hasProfilePhoto 
        ? '未加载个人照片,请刷新页面' 
        : '请先去个人资料页面上传正面照'
      );
      return;
    }
  
    let personBlob = personImage;
    if (!personImage && personPreview) {
      try {
        const response = await fetch(personPreview, { mode: 'cors', cache: 'no-cache' });
        if (!response.ok) throw new Error(`照片加载失败: ${response.status}`);
        personBlob = await response.blob();
      } catch (err) {
        alert('加载个人照片失败,请重新上传');
        return;
      }
    }
  
    try {
      setIsTryingOn(true);
      setActiveTryOnButton(`batch-${messageIndex}`); // 设置当前按钮ID
      setError('');
        
      const resultBlob = await batchVirtualTryOn(personBlob, items, getImageUrl);
      const resultUrl = URL.createObjectURL(resultBlob);
      setTryOnResult(resultUrl);
    } catch (err) {
      setError(err.message || '批量试穿失败,请确保AI后端服务已启动');
    } finally {
      setIsTryingOn(false);
      setActiveTryOnButton(null); // 清除按钮ID
    }
  };

  const loadSessions = async (append = false) => {
    try {
      setLoadingSessions(true);
      const offset = append ? sessions.length : 0;
      const data = await getUserSessions(user.id, 20, offset);
      const newSessions = data.sessions || [];
      
      if (append) {
        setSessions(prev => [...prev, ...newSessions]);
      } else {
        setSessions(newSessions);
      }
      
      setHasMoreSessions(data.has_more || false);
    } catch (err) {
      console.error('加载会话列表失败:', err);
      setError('加载会话列表失败');
    } finally {
      setLoadingSessions(false);
    }
  };
  
  const handleSessionScroll = (e) => {
    const { scrollTop, scrollHeight, clientHeight } = e.target;
    // 滚动到底部80%时加载下一批
    if (scrollHeight - scrollTop - clientHeight < 100 && hasMoreSessions && !loadingSessions) {
      loadSessions(true);
    }
  };

  const switchToSession = async (newSessionId) => {
    // 防止并发调用：正在加载时直接返回
    if (loading) return;
    
    // 防止重复切换到当前会话
    if (newSessionId === sessionId) return;
    
    try {
      setLoading(true);
      const data = await getSessionDetail(newSessionId, user.id);
      
      setSessionId(data.session_id);
      setConversationHistory(data.conversation_history || []);
      setItemsMap(data.items_map || {});
      
      setShowSessionList(false);
    } catch (err) {
      console.error('切换会话失败:', err);
      setError('切换会话失败');
    } finally {
      setLoading(false);
    }
  };

  const handleAdjustOutfit = async () => {
    if (!adjustmentInput.trim()) {
      setError('请输入调整要求');
      return;
    }
    
    if (!sessionId) {
      setError('请先在推荐页面生成初始推荐');
      return;
    }

    if (isAdjusting) return;

    // 保存用户输入
    const userInput = adjustmentInput.trim();
    
    try {
      setIsAdjusting(true);
      setError('');
      
      // 立即添加用户消息到UI
      const userMessage = {
        role: 'user',
        content: userInput,
        timestamp: new Date().toISOString()
      };
      setConversationHistory(prev => [...prev, userMessage]);
      
      // 清空输入框
      setAdjustmentInput('');
      
      const result = await adjustOutfit(sessionId, userInput, user.id);
      
      // 后端返回的conversation_history是完整的历史记录
      if (result.conversation_history) {
        setConversationHistory(result.conversation_history);
      }
      if (result.items_map) {
        setItemsMap(prevMap => ({
          ...prevMap,
          ...result.items_map
        }));
      }
      
      if (result.session_id && result.session_id !== sessionId) {
        setSessionId(result.session_id);
      }
    } catch (err) {
      console.error('调整失败:', err);
      const errorMsg = err.response?.data?.detail || '调整失败';
      
      if (err.response?.status === 404 || err.response?.status === 410) {
        setError('会话已过期,请返回推荐页面重新生成');
        clearCurrentSession();
      } else {
        setError(errorMsg);
        // 错误时移除乐观添加的用户消息
        setConversationHistory(prev => prev.slice(0, -1));
      }
    } finally {
      setIsAdjusting(false);
    }
  };

  const toggleMessageCollapse = (index) => {
    const newCollapsed = new Set(collapsedMessages);
    if (newCollapsed.has(index)) {
      newCollapsed.delete(index);
    } else {
      newCollapsed.add(index);
    }
    setCollapsedMessages(newCollapsed);
  };

  // 切换消息管理模式
  const toggleMessageManagement = () => {
    if (isManagingMessages) {
      // 退出管理模式，清空选择
      setSelectedMessagePairs(new Set());
    }
    setIsManagingMessages(!isManagingMessages);
  };

  // 切换消息对选中状态（双向联动：选中user或assistant时同时选中配对的另一条）
  const toggleMessagePairSelection = (clickedIndex) => {
    const clickedMsg = conversationHistory[clickedIndex];
    let userIndex, assistantIndex;
    
    if (clickedMsg.role === 'user') {
      userIndex = clickedIndex;
      // 查找下一条assistant消息
      assistantIndex = clickedIndex + 1;
      if (assistantIndex >= conversationHistory.length || conversationHistory[assistantIndex].role !== 'assistant') {
        assistantIndex = null;
      }
    } else {
      // 点击的是assistant，向前查找对应的user消息
      assistantIndex = clickedIndex;
      userIndex = clickedIndex - 1;
      if (userIndex < 0 || conversationHistory[userIndex].role !== 'user') {
        userIndex = null;
      }
    }
    
    // 如果找不到配对，不允许选中
    if (userIndex === null || assistantIndex === null) {
      setError('初始推荐消息不允许删除');
      return;
    }
    
    setSelectedMessagePairs(prev => {
      const newSet = new Set(prev);
      // 使用userIndex作为标识
      if (newSet.has(userIndex)) {
        newSet.delete(userIndex);
      } else {
        newSet.add(userIndex);
      }
      return newSet;
    });
  };

  // 批量删除选中的消息对
  const handleBatchDeleteMessages = async () => {
    if (selectedMessagePairs.size === 0) {
      setError('请至少选择一组消息');
      return;
    }

    setDeleteConfirmModal({
      show: true,
      type: 'batch_messages',
      targetId: null,
      title: '批量删除消息',
      message: `确定要删除 ${selectedMessagePairs.size} 组消息（包含你的提问和AI的回答）`
    });
  };

  const handleDeleteMessage = (messageIndex) => {
    if (!sessionId) return;
    
    setDeleteConfirmModal({
      show: true,
      type: 'message',
      targetId: messageIndex,
      title: '删除对话记录',
      message: '确定要删除这条对话记录'
    });
  };

  const handleDeleteSession = (targetSessionId) => {
    setDeleteConfirmModal({
      show: true,
      type: 'session',
      targetId: targetSessionId,
      title: '删除会话',
      message: '确定要删除此会话'
    });
  };

  const handleDeleteAllSessions = () => {
    setDeleteConfirmModal({
      show: true,
      type: 'all',
      targetId: null,
      title: '清空所有会话',
      message: '确定要清空所有会话'
    });
  };

  const confirmDelete = async () => {
    const { type, targetId } = deleteConfirmModal;
    setDeleteConfirmModal(prev => ({ ...prev, show: false }));

    try {
      if (type === 'message') {
        await deleteConversationMessage(sessionId, targetId, user.id);
        
        const updatedHistory = conversationHistory.filter((_, index) => index !== targetId);
        setConversationHistory(updatedHistory);
        
        const newCollapsed = new Set();
        collapsedMessages.forEach(idx => {
          if (idx < targetId) {
            newCollapsed.add(idx);
          } else if (idx > targetId) {
            newCollapsed.add(idx - 1);
          }
        });
        setCollapsedMessages(newCollapsed);
      } else if (type === 'batch_messages') {
        // 批量删除消息对：从后往前删，避免索引偏移
        const sortedIndices = Array.from(selectedMessagePairs).sort((a, b) => b - a);
        
        for (const userIndex of sortedIndices) {
          // 删除user消息
          await deleteConversationMessage(sessionId, userIndex, user.id);
          
          // 如果下一条是assistant，也删除（注意：删除user后，assistant的索引变为userIndex）
          const remainingHistory = await getSessionDetail(sessionId, user.id);
          if (remainingHistory.conversation_history[userIndex]?.role === 'assistant') {
            await deleteConversationMessage(sessionId, userIndex, user.id);
          }
        }
        
        // 重新加载完整历史
        const updated = await getSessionDetail(sessionId, user.id);
        setConversationHistory(updated.conversation_history);
        setItemsMap(updated.items_map);
        
        setSelectedMessagePairs(new Set());
        setIsManagingMessages(false);
        setSuccessMessage(`已删除 ${sortedIndices.length} 组消息`);
      } else if (type === 'session') {
        setSessions(prevSessions => 
          prevSessions.filter(s => s.session_id !== targetId)
        );
        
        await deleteSession(targetId, user.id);
        
        if (targetId === sessionId) {
          clearCurrentSession();
        }
        
        const remainingSessions = sessions.filter(s => s.session_id !== targetId);
        if (remainingSessions.length === 0) {
          setShowSessionList(false);
        }
      } else if (type === 'all') {
        setSessions([]);
        setShowSessionList(false);
        
        const result = await deleteAllSessions(user.id);
        
        clearCurrentSession();
        
        setSuccessMessage(`已成功清空 ${result.deleted_count} 个会话`);
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || '删除失败';
      setError(errorMsg);
      if (type === 'session' || type === 'all') {
        await loadSessions();
      }
    }
  };

  const cancelDelete = () => {
    setDeleteConfirmModal({
      show: false,
      type: null,
      targetId: null,
      title: '',
      message: ''
    });
  };

  const clearCurrentSession = () => {
    setSessionId(null);
    setConversationHistory([]);
    setItemsMap({});
    try {
      localStorage.removeItem(`shared_${user.id}_sessionId`);
      localStorage.removeItem(`conversation_${user.id}_conversationHistory`);
      localStorage.removeItem(`conversation_${user.id}_itemsMap`);
    } catch (err) {
      // 静默失败，不影响功能
    }
  };

  return (
    <div className="conversation-container">
      <div className="conversation-header">
        <h1>对话调整</h1>
        <div className="header-actions">
          <button
            className="btn-secondary"
            onClick={() => setShowSessionList(!showSessionList)}
            disabled={loading}
          >
            {showSessionList ? '隐藏会话列表' : '显示会话列表'}
          </button>
          <button
            className="btn-secondary"
            onClick={() => navigate('/recommendations')}
          >
            返回推荐
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}
      {successMessage && <div className="success-message">{successMessage}</div>}

      {/* 虚拟试衣结果弹窗 */}
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

      {/* 删除确认模态框 */}
      {deleteConfirmModal.show && (
        <div className="delete-confirm-overlay" onClick={cancelDelete}>
          <div className="delete-confirm-modal" onClick={e => e.stopPropagation()}>
            <h3>{deleteConfirmModal.title}</h3>
            <p>{deleteConfirmModal.message}</p>
            <p className="delete-confirm-warning">此操作不可恢复</p>
            <div className="delete-confirm-actions">
              <button className="btn-cancel" onClick={cancelDelete}>取消</button>
              <button className="btn-confirm-delete" onClick={confirmDelete}>确认删除</button>
            </div>
          </div>
        </div>
      )}

      <div className="conversation-main">
        {/* 左侧会话列表 */}
        {showSessionList && (
          <div className="session-list-sidebar" ref={sessionListRef} onScroll={handleSessionScroll}>
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
            {loadingSessions && sessions.length === 0 ? (
              // 首次加载显示骨架屏
              <>
                {[1, 2, 3].map((n) => (
                  <div key={n} className="session-skeleton">
                    <div className="skeleton-line long"></div>
                    <div className="skeleton-line short"></div>
                  </div>
                ))}
              </>
            ) : sessions.length > 0 ? (
              <>
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
                {loadingSessions && (
                  <div className="loading-more">加载中...</div>
                )}
                {!hasMoreSessions && sessions.length > 0 && (
                  <div className="no-more-sessions">没有更多会话了</div>
                )}
              </>
            ) : (
              <p className="no-sessions">暂无历史会话</p>
            )}
          </div>
        )}

        {/* 右侧对话区域 */}
        <div className="conversation-content">
          {!sessionId ? (
            <div className="no-session-placeholder">
              <h2>开始对话调整</h2>
              <p>请先在推荐页面生成初始推荐,然后选择一组方案后开始对话</p>
              <button
                className="btn-primary"
                onClick={() => navigate('/recommendations')}
              >
                去生成推荐
              </button>
            </div>
          ) : (
            <>
              {/* 对话历史 */}
              {conversationHistory.length > 0 && (
                <div className="conversation-history">
                  <div className="history-header">
                    <h3>对话历史</h3>
                    <div className="history-header-actions">
                      <button
                        className={`btn-manage ${isManagingMessages ? 'active' : ''}`}
                        onClick={toggleMessageManagement}
                      >
                        {isManagingMessages ? '取消管理' : '消息管理'}
                      </button>
                      {isManagingMessages && selectedMessagePairs.size > 0 && (
                        <button
                          className="btn-delete-selected"
                          onClick={handleBatchDeleteMessages}
                        >
                          删除选中 ({selectedMessagePairs.size})
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="history-messages">
                    {conversationHistory.map((msg, index) => {
                      const isCollapsed = collapsedMessages.has(index);
                      const hasOutfitIds = msg.outfit_ids && msg.outfit_ids.length > 0;
                      const isUserMessage = msg.role === 'user';
                      
                      // 检查消息是否有配对
                      let hasPair = false;
                      if (isUserMessage) {
                        // user消息，检查下一条是否是assistant
                        hasPair = index + 1 < conversationHistory.length && conversationHistory[index + 1].role === 'assistant';
                      } else {
                        // assistant消息，检查上一条是否是user
                        hasPair = index - 1 >= 0 && conversationHistory[index - 1].role === 'user';
                      }
                      
                      // 计算是否被选中：如果是user，直接查看；如果是assistant，查看上一条user是否被选中
                      let isSelected = false;
                      if (isUserMessage) {
                        isSelected = selectedMessagePairs.has(index);
                      } else {
                        // assistant消息，检查上一条是否是user且被选中
                        const prevIndex = index - 1;
                        if (prevIndex >= 0 && conversationHistory[prevIndex].role === 'user') {
                          isSelected = selectedMessagePairs.has(prevIndex);
                        }
                      }
                      
                      return (
                        <div key={index} className={`message ${msg.role} ${isManagingMessages ? 'manageable' : ''} ${!hasPair ? 'no-pair' : ''}`}>
                          {isManagingMessages && (
                            <div className="message-checkbox-wrapper">
                              <input
                                type="checkbox"
                                className="message-checkbox"
                                checked={isSelected}
                                onChange={() => toggleMessagePairSelection(index)}
                                disabled={!hasPair}
                                title={hasPair ? '选中此消息对' : '初始推荐消息不允许删除'}
                              />
                            </div>
                          )}
                          <div className="message-body">
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
                              </div>
                            </div>
                            <div className="message-content">{msg.content}</div>
                            
                            {hasOutfitIds && !isCollapsed && (
                              <div className="message-outfit-items">
                              <div className="outfit-items-header">
                                <button
                                  className="btn-batch-tryon-mini"
                                  onClick={() => {
                                    const items = msg.outfit_ids.map(id => itemsMap[id]).filter(Boolean);
                                    handleBatchTryOn(items, index);
                                  }}
                                  disabled={isTryingOn}
                                  title="一键试穿这组搭配的所有衣物"
                                >
                                  {activeTryOnButton === `batch-${index}` ? '生成中...' : '整套试穿'}
                                </button>
                              </div>
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
                      </div>
                      );
                    })}
                    <div ref={historyEndRef} />
                  </div>
                </div>
              )}

              {/* 调整输入区 */}
              <div className="adjustment-input-area">
                <h3>继续调整穿搭</h3>
                <div className="adjustment-examples">
                  <p>你可以说:</p>
                  <div className="example-tags">
                    <span onClick={() => setAdjustmentInput('换件厚外套')}>换件厚外套</span>
                    <span onClick={() => setAdjustmentInput('更休闲一些')}>更休闲一些</span>
                    <span onClick={() => setAdjustmentInput('颜色亮一点')}>颜色亮一点</span>
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
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default Conversation;
