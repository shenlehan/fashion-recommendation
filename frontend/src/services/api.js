import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// User Authentication
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

// Wardrobe Management
export const uploadClothingItem = async (userId, formData) => {
  const response = await api.post(`/clothes/upload?user_id=${userId}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
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

// Recommendations
export const getOutfitRecommendations = async (userId, preferences = {}) => {
  const params = new URLSearchParams({ user_id: userId, ...preferences });
  const response = await api.get(`/recommend/outfits?${params}`);
  return response.data;
};

export default api;
