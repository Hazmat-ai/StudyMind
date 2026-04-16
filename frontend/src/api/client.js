import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

const client = axios.create({
  baseURL: BASE_URL,
});

// Interceptor to attach token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      // Redirect to login handled by useAuth or router
      window.location.href = '/auth';
    }
    return Promise.reject(error);
  }
);

export const api = {
  generateStudySet: async (content, options) => {
    const response = await client.post('/generate', { content, options });
    return response.data;
  },
  extractPdfText: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await client.post('/generate/extract-pdf', formData);
    return response.data;
  },
  saveStudySet: async (studySetData) => {
    const response = await client.post('/studysets', studySetData);
    return response.data;
  },
  login: async (email, password) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    const response = await client.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },
  register: async (email, password) => {
    const response = await client.post('/auth/register', { email, password });
    return response.data;
  }
};

export default client;
