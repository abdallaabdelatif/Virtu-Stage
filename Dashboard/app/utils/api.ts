import axios from 'axios';
import {
  clearAccessToken,
  getAccessToken,
} from './tokenStorage';

// 1. Base axios instance
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:9000',
  timeout: 10000,
});

// 2. Request interceptor
api.interceptors.request.use(
  (config) => {
    // Read JWT token from localStorage
    const token = getAccessToken();
    if (token) {
      // Attach as Authorization: Bearer {token} header
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 3. Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const status = error.response.status;
      
      // If 401 response → clear localStorage token and user → redirect to "/"
      if (status === 401) {
        clearAccessToken();
        if (window.location.pathname !== '/') window.location.href = '/';
      } 
      // If 500+ response → log error to console
      else if (status >= 500) {
        console.error("Server Error:", error.response.data || error.message);
      }
    }
    return Promise.reject(error);
  }
);

// 4. Export default the axios instance
export default api;
