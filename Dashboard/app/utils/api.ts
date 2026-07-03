import axios from 'axios';
import { clearAccessToken, getAccessToken } from './tokenStorage';
import { notifyUnauthorized } from './authEvents';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:9000',
  timeout: 10000,
});

api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const status = error.response.status;

      if (status === 401) {
        clearAccessToken();
        notifyUnauthorized();
      } else if (status >= 500) {
        console.error('Server Error:', error.response.data || error.message);
      }
    }
    return Promise.reject(error);
  },
);

export default api;
