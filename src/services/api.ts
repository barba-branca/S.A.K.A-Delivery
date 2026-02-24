import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: { 'Content-Type': 'application/json' },
});

// JWT interceptor
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('saka_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('saka_token');
            localStorage.removeItem('saka_user');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// ============== Auth ==============

export const loginAPI = async (username: string, password: string) => {
    const res = await api.post('/auth/login', { username, password });
    return res.data;
};

export const registerAPI = async (data: {
    username: string;
    email?: string;
    full_name: string;
    password: string;
}) => {
    const res = await api.post('/auth/register', data);
    return res.data;
};

export const getMeAPI = async () => {
    const res = await api.get('/auth/me');
    return res.data;
};

// ============== Pacotes ==============

export const comprarPacoteAPI = async (tipo: string = 'padrao') => {
    const res = await api.post('/pacotes/comprar', { tipo });
    return res.data;
};

export const listarPacotesAPI = async () => {
    const res = await api.get('/pacotes');
    return res.data;
};

// ============== Pedidos SaaS ==============

export const criarPedidoAPI = async (via_arnaldo: boolean = false) => {
    const res = await api.post('/pedidos', { via_arnaldo });
    return res.data;
};

export const listarPedidosAPI = async (limit: number = 50) => {
    const res = await api.get(`/pedidos?limit=${limit}`);
    return res.data;
};

// ============== Repasse ==============

export const getRepasseMensalAPI = async () => {
    const res = await api.get('/repasse/mensal');
    return res.data;
};

export const pagarRepasseAPI = async () => {
    const res = await api.post('/repasse/pagar');
    return res.data;
};

// ============== KDS Orders ==============

export const getKDSOrdersAPI = async () => {
    const res = await api.get('/orders?active_only=true');
    return res.data;
};

export const updateKDSOrderStatusAPI = async (orderId: string, status: string, driverName?: string) => {
    const res = await api.patch(`/orders/${orderId}/status`, { status, driver_name: driverName });
    return res.data;
};

export default api;
