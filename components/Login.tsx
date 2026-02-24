import React, { useState } from 'react';
import { User, UserRole } from '../types';
import { ChefHat, Lock, User as UserIcon } from 'lucide-react';

interface LoginProps {
  onLogin: (user: User) => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Mock Authentication Logic
    // In a real app, this would hit a backend with bcrypt hash verification
    if (username === 'admin' && password === 'admin123') {
      onLogin({ username: 'Admin User', role: UserRole.ADMIN });
    } else if (username === 'cozinha' && password === '123') {
      onLogin({ username: 'Equipe Cozinha', role: UserRole.KITCHEN });
    } else {
      setError('Credenciais inválidas. Tente admin/admin123 ou cozinha/123');
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 p-4">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-8">
        <div className="flex flex-col items-center mb-8">
          <div className="p-4 bg-purple-600 rounded-full mb-4 shadow-lg shadow-purple-500/20">
            <ChefHat size={40} className="text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Saka Delivery KDS</h1>
          <p className="text-slate-400 mt-2">Sistema de Gestão de Cozinha</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Usuário</label>
            <div className="relative">
              <UserIcon className="absolute left-3 top-3 text-slate-500" size={18} />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg py-2.5 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                placeholder="Ex: admin"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Senha</label>
            <div className="relative">
              <Lock className="absolute left-3 top-3 text-slate-500" size={18} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg py-2.5 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                placeholder="••••••"
              />
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm text-center">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 rounded-lg transition-colors shadow-lg shadow-purple-500/20"
          >
            Entrar no Sistema
          </button>
        </form>

        <div className="mt-6 text-center text-xs text-slate-600">
          <p>Saka KDS v1.0.0 • Secure Auth</p>
        </div>
      </div>
    </div>
  );
};

export default Login;