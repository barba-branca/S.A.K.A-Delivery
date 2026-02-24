import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { ChefHat, Lock, User as UserIcon, Mail, ArrowRight } from 'lucide-react';

const LoginPage: React.FC = () => {
    const { login, register } = useAuth();
    const [isRegister, setIsRegister] = useState(false);
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [fullName, setFullName] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            if (isRegister) {
                await register({ username, email: email || undefined, full_name: fullName, password });
            } else {
                await login(username, password);
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Erro ao autenticar. Verifique suas credenciais.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 p-4">
            {/* Glow effect */}
            <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl pointer-events-none"></div>

            <div className="w-full max-w-md bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-2xl shadow-2xl p-8 relative z-10">
                <div className="flex flex-col items-center mb-8">
                    <div className="p-4 bg-gradient-to-br from-purple-600 to-purple-800 rounded-full mb-4 shadow-lg shadow-purple-500/30">
                        <ChefHat size={40} className="text-white" />
                    </div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">S.A.K.A Delivery</h1>
                    <p className="text-slate-400 mt-2">Sistema de Gestão de Delivery</p>
                </div>

                {/* Tab switch */}
                <div className="flex mb-6 bg-slate-800/50 rounded-lg p-1">
                    <button
                        onClick={() => { setIsRegister(false); setError(''); }}
                        className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${!isRegister ? 'bg-purple-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'
                            }`}
                    >
                        Entrar
                    </button>
                    <button
                        onClick={() => { setIsRegister(true); setError(''); }}
                        className={`flex-1 py-2 text-sm font-medium rounded-md transition-all ${isRegister ? 'bg-purple-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'
                            }`}
                    >
                        Criar Conta
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1.5">Usuário</label>
                        <div className="relative">
                            <UserIcon className="absolute left-3 top-3 text-slate-500" size={18} />
                            <input
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="w-full bg-slate-800/50 border border-slate-700 text-white rounded-lg py-2.5 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all placeholder-slate-600"
                                placeholder="nome_de_usuario"
                                required
                            />
                        </div>
                    </div>

                    {isRegister && (
                        <>
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1.5">Email</label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-3 text-slate-500" size={18} />
                                    <input
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        className="w-full bg-slate-800/50 border border-slate-700 text-white rounded-lg py-2.5 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all placeholder-slate-600"
                                        placeholder="seu@email.com"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1.5">Nome Completo</label>
                                <div className="relative">
                                    <UserIcon className="absolute left-3 top-3 text-slate-500" size={18} />
                                    <input
                                        type="text"
                                        value={fullName}
                                        onChange={(e) => setFullName(e.target.value)}
                                        className="w-full bg-slate-800/50 border border-slate-700 text-white rounded-lg py-2.5 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all placeholder-slate-600"
                                        placeholder="Seu Nome"
                                        required
                                    />
                                </div>
                            </div>
                        </>
                    )}

                    <div>
                        <label className="block text-sm font-medium text-slate-400 mb-1.5">Senha</label>
                        <div className="relative">
                            <Lock className="absolute left-3 top-3 text-slate-500" size={18} />
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full bg-slate-800/50 border border-slate-700 text-white rounded-lg py-2.5 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all placeholder-slate-600"
                                placeholder="••••••"
                                required
                            />
                        </div>
                    </div>

                    {error && (
                        <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm text-center animate-pulse">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 text-white font-semibold py-3 rounded-lg transition-all shadow-lg shadow-purple-500/20 flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                        {loading ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                        ) : (
                            <>
                                {isRegister ? 'Criar Conta' : 'Entrar'}
                                <ArrowRight size={18} />
                            </>
                        )}
                    </button>
                </form>

                {!isRegister && (
                    <div className="mt-4 text-center text-xs text-slate-600">
                        <p>Demo: <span className="text-slate-400">admin/admin123</span> ou <span className="text-slate-400">cozinha/123</span></p>
                    </div>
                )}

                <div className="mt-6 text-center text-xs text-slate-600">
                    <p>S.A.K.A v2.0.0 • SaaS Delivery Management</p>
                </div>
            </div>
        </div>
    );
};

export default LoginPage;
