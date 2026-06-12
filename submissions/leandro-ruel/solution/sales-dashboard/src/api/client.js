import axios from 'axios';

const API_BASE = 'http://localhost:3001';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
});

export const opportunitiesApi = {
  getAll: (filters = {}) => api.get('/opportunities', { params: filters }),
  getById: (id) => api.get(`/opportunities/${id}`),
  getFilters: () => api.get('/filters'),
};

export const dashboardApi = {
  getStats: () => api.get('/stats'),
  getTimeOnPipeline: () => api.get('/analytics/time-on-pipeline'),
  getAccountSize: () => api.get('/analytics/account-size'),
};

export default api;
