import axios from 'axios';

const portalClient = axios.create({
  baseURL: '/api/v1',
});

portalClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('portal_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

portalClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && localStorage.getItem('portal_token')) {
      localStorage.removeItem('portal_token');
      window.location.href = '/portal/login';
    }
    return Promise.reject(error);
  }
);

export default portalClient;
