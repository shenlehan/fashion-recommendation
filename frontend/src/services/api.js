import axios from 'axios';

// 确保与后端 main.py 的前缀一致
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:6008/api/v1';

// --- 类别优先级（用于排序）---
const CATEGORY_PRIORITY = {
  'inner_top': 10, 'mid_top': 20, 'outer_top': 30, 'bottom': 40, 'full_body': 50
};
const UNSUPPORTED_CATEGORIES = ['shoes', 'socks', 'accessories', 'underwear', 'unknown'];

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
});

// 添加响应拦截器，统一处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ECONNABORTED') {
      console.error('请求超时:', error.message);
      error.message = '请求超时，请检查网络连接';
    } else if (error.code === 'ERR_NETWORK') {
      console.error('网络错误:', error.message);
      error.message = '无法连接到服务器，请检查后端服务是否运行';
    } else if (!error.response) {
      console.error('网络错误，无响应:', error.message);
      error.message = '网络连接失败，请检查后端服务地址: ' + API_BASE_URL;
    }
    return Promise.reject(error);
  }
);

// 用于静态资源的原始地址（去除后缀）
export const API_ORIGIN = API_BASE_URL.replace(/\/api\/v1$/, '');

// --- 用户管理 ---
export const registerUser = async (userData) => {
  const response = await api.post('/users/register', userData);
  return response.data;
};

export const loginUser = async (username, password) => {
  const response = await api.post('/users/login', { username, password });
  return response.data;
};

export const getUserProfile = async (userId) => {
  const response = await api.get(`/users/profile?user_id=${userId}`);
  return response.data;
};

export const updateUserProfile = async (userId, updateData) => {
  const response = await api.put(`/users/profile?user_id=${userId}`, updateData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

// --- 衣柜管理 ---
export const uploadClothingItem = async (userId, formData) => {
  const response = await api.post(`/clothes/upload?user_id=${userId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const uploadClothingBatch = async (userId, formData) => {
  const response = await api.post(`/clothes/upload-batch?user_id=${userId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000, // 5分钟超时，批量上传需要更长时间
  });
  return response.data;
};

export const getUserWardrobe = async (userId) => {
  const response = await api.get(`/clothes/wardrobe/${userId}`);
  return response.data;
};

export const deleteClothingItem = async (itemId) => {
  const response = await api.delete(`/clothes/${itemId}`);
  return response.data;
};

export const deleteClothingBatch = async (itemIds) => {
  const response = await api.post('/clothes/delete-batch', itemIds);
  return response.data;
};

// --- 上传状态管理 ---
export const getUploadStatus = async (userId) => {
  const response = await api.get(`/clothes/upload-status/${userId}`);
  return response.data;
};

// --- 推荐功能 ---
export const getOutfitRecommendations = async (userId, preferences = {}) => {
  const params = new URLSearchParams({ user_id: userId, ...preferences });
  const response = await api.get(`/recommend/outfits?${params}`);
  return response.data;
};

// --- 多轮对话调整穿搭 ---
export const adjustOutfit = async (sessionId, adjustmentRequest, userId) => {
  const response = await api.post('/recommend/adjust', {
    session_id: sessionId,
    adjustment_request: adjustmentRequest,
    user_id: userId
  });
  return response.data;
};

export const selectOutfit = async (sessionId, outfitIndex, outfitData, userId) => {
  const response = await api.post('/recommend/select-outfit', {
    session_id: sessionId,
    outfit_index: outfitIndex,
    outfit_data: outfitData,
    user_id: userId
  });
  return response.data;
};

// --- 会话管理 ---
export const getUserSessions = async (userId, limit = 20, offset = 0) => {
  const response = await api.get(`/recommend/sessions?user_id=${userId}&limit=${limit}&offset=${offset}`);
  return response.data;
};

export const getSessionDetail = async (sessionId, userId) => {
  const response = await api.get(`/recommend/sessions/${sessionId}?user_id=${userId}`);
  return response.data;
};

export const deleteConversationMessage = async (sessionId, messageIndex, userId) => {
  const response = await api.delete(`/recommend/sessions/${sessionId}/messages/${messageIndex}?user_id=${userId}`);
  return response.data;
};

export const deleteSession = async (sessionId, userId) => {
  const response = await api.delete(`/recommend/sessions/${sessionId}?user_id=${userId}`);
  return response.data;
};

export const deleteAllSessions = async (userId) => {
  const response = await api.delete(`/recommend/sessions?user_id=${userId}`);
  return response.data;
};

// --- 虚拟试衣核心逻辑 (CatVTON) ---

/**
 * 将图片 URL 转换为 Blob
 * 增加 try-catch 避免因为图片加载失败导致前端白屏
 */
export const fetchImageAsBlob = async (url) => {
  try {
    // 如果是相对路径，补全为完整 URL
    if (!url.startsWith('http')) {
        url = `${API_BASE_URL.replace('/api/v1', '')}/${url.replace(/^\//, '')}`;
    }

    // 添加时间戳防止缓存，设置 mode: 'cors'
    const corsUrl = `${url}?t=${new Date().getTime()}`;
    
    const response = await fetch(corsUrl, {
      mode: 'cors', // 强制开启 CORS 校验
      cache: 'no-cache', // 避免读取无 CORS 头的缓存图片
    });

    if (!response.ok) {
      throw new Error(`图片下载失败: ${response.status} ${response.statusText}`);
    }
    
    return await response.blob();
  } catch (error) {
    console.error("图片转换 Blob 失败:", error);
    // 这里抛出更具体的错误，方便你在页面上看到
    throw new Error(`无法加载衣物图片，请检查跨域设置或图片是否存在。详细: ${error.message}`);
  }
};

/**
 * 发起试衣请求
 * 确保参数名与后端接收的 key (person_img, cloth_img) 匹配
 */
export const virtualTryOn = async (personImgBlob, clothImgBlob, category = 'upper_body') => {
  try {
    const formData = new FormData();
    formData.append('person_img', personImgBlob); 
    formData.append('cloth_img', clothImgBlob);
    formData.append('category', category);

    const response = await api.post('/vton/try-on', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      responseType: 'blob', // 必须设置为 blob 以接收图片流
    });
    return response.data;
  } catch (error) {
    console.error("virtualTryOn Error:", error);
    throw error;
  }
};

/**
 * 批量试穿：一次试穿多件衣服
 * @param {Blob} personImgBlob - 人像照片
 * @param {Array} clothItems - 衣物数组 [{image_path, category}, ...]
 * @param {Function} getImageUrl - URL 转换函数
 */
export const batchVirtualTryOn = async (personImgBlob, clothItems, getImageUrl) => {
  // 1. 过滤不支持的类别
  const validItems = clothItems.filter(
    item => !UNSUPPORTED_CATEGORIES.includes(item.category)
  );
  
  if (validItems.length === 0) {
    throw new Error('没有可试穿的衣物（鞋子、配饰等不支持试穿）');
  }
  
  // 2. 按优先级排序
  validItems.sort((a, b) => 
    (CATEGORY_PRIORITY[a.category] || 99) - (CATEGORY_PRIORITY[b.category] || 99)
  );
  
  // 3. 构建 FormData
  const formData = new FormData();
  formData.append('person_img', personImgBlob);
  
  for (const item of validItems) {
    const blob = await fetchImageAsBlob(getImageUrl(item.image_path));
    formData.append('cloth_imgs', blob);
  }
  
  formData.append('categories', JSON.stringify(validItems.map(i => i.category)));
  
  // 4. 发送请求
  const response = await api.post('/vton/batch-try-on', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    responseType: 'blob',
    timeout: 300000  // 5分钟超时
  });
  
  return response.data;
};

export default api;