import axios from 'axios';

// Можно переопределить через REACT_APP_API_URL
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000/api',
  withCredentials: false,
});

// Перед каждым запросом кладём токен из localStorage
api.interceptors.request.use((config) => {
  const t = localStorage.getItem('token');
  if (t) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${t}`;
  }
  return config;
});

export default api;
