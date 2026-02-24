import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { loginAPI, registerAPI, getMeAPI } from '../services/api';

interface User {
    id: number;
    username: string;
    email?: string;
    fullName: string;
    role: string;
    saldoCredito: number;
    isActive: boolean;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (username: string, password: string) => Promise<void>;
    register: (data: { username: string; email?: string; full_name: string; password: string }) => Promise<void>;
    logout: () => void;
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const savedToken = localStorage.getItem('saka_token');
        const savedUser = localStorage.getItem('saka_user');

        if (savedToken && savedUser) {
            setToken(savedToken);
            try {
                setUser(JSON.parse(savedUser));
            } catch {
                localStorage.removeItem('saka_user');
            }
        }
        setIsLoading(false);
    }, []);

    const login = async (username: string, password: string) => {
        const data = await loginAPI(username, password);
        const userData: User = {
            id: data.user.id,
            username: data.user.username,
            email: data.user.email,
            fullName: data.user.fullName || data.user.full_name,
            role: data.user.role,
            saldoCredito: data.user.saldoCredito || data.user.saldo_credito || 0,
            isActive: data.user.isActive ?? data.user.is_active ?? true,
        };
        setUser(userData);
        setToken(data.access_token);
        localStorage.setItem('saka_token', data.access_token);
        localStorage.setItem('saka_user', JSON.stringify(userData));
    };

    const register = async (regData: { username: string; email?: string; full_name: string; password: string }) => {
        const data = await registerAPI(regData);
        const userData: User = {
            id: data.user.id,
            username: data.user.username,
            email: data.user.email,
            fullName: data.user.fullName || data.user.full_name,
            role: data.user.role,
            saldoCredito: data.user.saldoCredito || data.user.saldo_credito || 0,
            isActive: data.user.isActive ?? data.user.is_active ?? true,
        };
        setUser(userData);
        setToken(data.access_token);
        localStorage.setItem('saka_token', data.access_token);
        localStorage.setItem('saka_user', JSON.stringify(userData));
    };

    const logout = () => {
        setUser(null);
        setToken(null);
        localStorage.removeItem('saka_token');
        localStorage.removeItem('saka_user');
    };

    const refreshUser = async () => {
        try {
            const data = await getMeAPI();
            const userData: User = {
                id: data.id,
                username: data.username,
                email: data.email,
                fullName: data.fullName || data.full_name,
                role: data.role,
                saldoCredito: data.saldoCredito || data.saldo_credito || 0,
                isActive: data.isActive ?? data.is_active ?? true,
            };
            setUser(userData);
            localStorage.setItem('saka_user', JSON.stringify(userData));
        } catch {
            logout();
        }
    };

    return (
        <AuthContext.Provider value={{ user, token, isAuthenticated: !!token, isLoading, login, register, logout, refreshUser }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = (): AuthContextType => {
    const context = useContext(AuthContext);
    if (!context) throw new Error('useAuth must be used within AuthProvider');
    return context;
};
