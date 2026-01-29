import axios from 'axios';

// 确保与后端 main.py 的前缀一致
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

export const API_ORIGIN = API_BASE_URL.replace(/\/api\/v1$/, '');

// --- 用户与衣柜管理 (保留原有) ---
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

// --- 推荐功能 (保留原有) ---
export const getOutfitRecommendations = async (userId, preferences = {}) => {
  const params = new URLSearchParams({ user_id: userId, ...preferences });
  const response = await api.get(`/recommend/outfits?${params}`);
  return response.data;
};

// --- ⚠️ 新增：虚拟试衣核心逻辑 ---

// 1. 将衣服 URL 转换为 Blob (解决跨域和文件格式问题)
export const fetchImageAsBlob = async (url) => {
  const response = await fetch(url);
  const blob = await response.blob();
  return blob;
};

// 2. 发起试衣请求
export const virtualTryOn = async (personImg, clothImg, category = 'upper_body') => {
  const formData = new FormData();
  formData.append('person_img', personImg);
  formData.append('cloth_img', clothImg);
  formData.append('category', category);

  const response = await api.post('/vton/try-on', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    responseType: 'blob', // 关键：告知接收图片流
  });
  return response.data;
};

export default api;