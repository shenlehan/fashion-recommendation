import axios from 'axios';

// 确保与后端 main.py 的前缀一致
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

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

// --- 衣柜管理 ---
export const uploadClothingItem = async (userId, formData) => {
  const response = await api.post(`/clothes/upload?user_id=${userId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
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

// --- 推荐功能 ---
export const getOutfitRecommendations = async (userId, preferences = {}) => {
  const params = new URLSearchParams({ user_id: userId, ...preferences });
  const response = await api.get(`/recommend/outfits?${params}`);
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

export default api;