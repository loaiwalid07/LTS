import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('sf_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 globally
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('sf_token');
      localStorage.removeItem('sf_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;

// ---- Auth ----
export const authApi = {
  register: (data: { email: string; password: string; name?: string }) =>
    api.post('/auth/register', data).then((r) => r.data),
  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data).then((r) => r.data),
  me: () => api.get('/auth/me').then((r) => r.data),
};

// ---- Shorts ----
export const shortsApi = {
  create: (youtubeUrl: string) =>
    api.post('/shorts/create', { youtubeUrl }).then((r) => r.data),
  list: () => api.get('/shorts').then((r) => r.data),
  get: (id: string) => api.get(`/shorts/${id}`).then((r) => r.data),
  download: (id: string) =>
    api.post(`/shorts/${id}/download`).then((r) => r.data),
  delete: (id: string) =>
    api.delete(`/shorts/${id}`).then((r) => r.data),
};

// ---- Trends ----
export const trendsApi = {
  list: () => api.get('/trends').then((r) => r.data),
  addInterest: (keyword: string) =>
    api.post('/trends/interests', { keyword }).then((r) => r.data),
  getInterests: () =>
    api.get('/trends/interests').then((r) => r.data),
  removeInterest: (id: string) =>
    api.delete(`/trends/interests/${id}`).then((r) => r.data),
};

// ---- Billing ----
export const billingApi = {
  createPayment: () =>
    api.post('/billing/create-payment').then((r) => r.data),
  createPending: (transactionId: string, method?: string) =>
    api.post('/billing/create-pending', { transactionId, method }).then((r) => r.data),
  verify: (transactionId: string) =>
    api.post('/billing/verify', { transactionId }).then((r) => r.data),
};

// ---- Settings ----
export const settingsApi = {
  getProfile: () => api.get('/settings/profile').then((r) => r.data),
  updateProfile: (data: { name?: string }) =>
    api.put('/settings/profile', data).then((r) => r.data),
  updatePassword: (currentPassword: string, newPassword: string) =>
    api.put('/settings/password', { currentPassword, newPassword }).then((r) => r.data),
};

// ---- Upload ----
export const uploadApi = {
  getPlatforms: () => api.get('/upload/platforms').then((r) => r.data),
  uploadShort: (shortId: string, platform: string, accessToken: string) =>
    api.post('/upload/short', { shortId, platform, accessToken }).then((r) => r.data),
};
