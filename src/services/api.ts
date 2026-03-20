import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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

export const createKDSOrderAPI = async (orderData: {
    customer_name: string;
    source: string;
    delivery_fee: number;
    items: Array<{ name: string; quantity: number; notes?: string }>;
}) => {
    const res = await api.post('/orders/create', orderData);
    return res.data;
};

export const deleteKDSOrderAPI = async (orderId: string) => {
    const res = await api.delete(`/orders/${orderId}`);
    return res.data;
};

export const resetKDSOrdersAPI = async () => {
    const res = await api.delete('/orders');
    return res.data;
};

export const payDriverAPI = async (driverName: string) => {
    const res = await api.post(`/orders/drivers/${driverName}/pay`);
    return res.data;
};

// ============== Admin ==============

export const getAdminUsersAPI = async () => {
    const res = await api.get('/auth/users');
    return res.data;
};

export const updateUserCreditsAPI = async (userId: number, saldoCredito: number) => {
    const res = await api.patch(`/auth/users/${userId}/creditos`, { saldo_credito: saldoCredito });
    return res.data;
};

export const updateUserRoleAPI = async (userId: number, role: string) => {
    const res = await api.patch(`/auth/users/${userId}/role`, { role });
    return res.data;
};

export const deleteUserAPI = async (userId: number) => {
    const res = await api.delete(`/auth/users/${userId}`);
    return res.data;
};

// ============== Payments (Mercado Pago PIX) ==============

export const createPixPaymentAPI = async (valor: number) => {
    const res = await api.post('/api/v1/payments/create', { valor });
    return res.data;
};

export const checkPaymentStatusAPI = async (transactionId: number) => {
    const res = await api.get(`/api/v1/payments/${transactionId}/status`);
    return res.data;
};

export default api;
