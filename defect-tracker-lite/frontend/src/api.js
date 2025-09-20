import axios from 'axios';

const api = axios.create({ baseURL: 'http://localhost:5000/api' });

// Подставляем токен, чтобы не прокидывать headers в каждом вызове
api.interceptors.request.use((config) => {
  const t = localStorage.getItem('token');
  if (t) config.headers.Authorization = 'Bearer ' + t;
  return config;
});

export default api;
