import React, { useState, useEffect } from 'react';
import { User, UserRole } from '../types';
import { ChefHat, Lock, User as UserIcon, UserPlus, ArrowLeft, ShieldCheck } from 'lucide-react';

interface LoginProps {
  onLogin: (user: User) => void;
}

interface StoredUser extends User {
  password: string;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>(UserRole.KITCHEN);
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');

  const USERS_STORAGE_KEY = 'saka_kds_users';

  const getStoredUsers = (): StoredUser[] => {
    const stored = localStorage.getItem(USERS_STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  };

  const handleAuth = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (isLogin) {
      // Logic for Login
      const storedUsers = getStoredUsers();
      const foundUser = storedUsers.find(u => u.username === username && u.password === password);

      if (username === 'admin' && password === 'admin123') {
        onLogin({ username: 'Admin User', role: UserRole.ADMIN });
      } else if (username === 'cozinha' && password === '123') {
        onLogin({ username: 'Equipe Cozinha', role: UserRole.KITCHEN });
      } else if (foundUser) {
        onLogin({ username: foundUser.username, role: foundUser.role });
      } else {
        setError('Credenciais inválidas. Tente admin/admin123 ou cozinha/123');
      }
    } else {
      // Logic for Registration
      if (!username || !password || !fullName) {
        setError('Por favor, preencha todos os campos.');
        return;
      }

      const storedUsers = getStoredUsers();
      if (storedUsers.some(u => u.username === username)) {
        setError('Este nome de usuário já está em uso.');
        return;
      }

      const newUser: StoredUser = {
        username: fullName,
        role: role,
        password: password
      };

      localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify([...storedUsers, newUser]));
      onLogin({ username: newUser.username, role: newUser.role });
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-950 p-4 font-sans">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-8 transition-all duration-300">
        <div className="flex flex-col items-center mb-8">
          <div className="p-4 bg-purple-600 rounded-full mb-4 shadow-lg shadow-purple-500/20">
            {isLogin ? <ChefHat size={40} className="text-white" /> : <UserPlus size={40} className="text-white" />}
          </div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Saka Delivery KDS</h1>
          <p className="text-slate-400 mt-2">{isLogin ? 'Gestão de Cozinha' : 'Criar Nova Conta'}</p>
        </div>

        <form onSubmit={handleAuth} className="space-y-5">
          {!isLogin && (
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Nome Completo</label>
              <div className="relative">
                <UserIcon className="absolute left-3 top-3 text-slate-500" size={18} />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg py-2.5 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                  placeholder="Ex: Carlos Silva"
                  required
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-400 mb-2">Usuário / Login</label>
            <div className="relative">
              <UserIcon className="absolute left-3 top-3 text-slate-500" size={18} />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 text-white rounded-lg py-2.5 pl-10 pr-4 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                placeholder="Ex: carlossilva"
                required
              />
            </div>
          </div>

          {!isLogin && (
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-2">Cargo / Acesso</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setRole(UserRole.KITCHEN)}
                  className={`flex items-center justify-center gap-2 py-2.5 rounded-lg border transition-all ${role === UserRole.KITCHEN
                      ? 'bg-purple-600/20 border-purple-500 text-purple-300'
                      : 'bg-slate-800 border-slate-700 text-slate-500 hover:border-slate-600'
                    }`}
                >
                  <ChefHat size={16} />
                  Cozinha
                </button>
                <button
                  type="button"
                  onClick={() => setRole(UserRole.ADMIN)}
                  className={`flex items-center justify-center gap-2 py-2.5 rounded-lg border transition-all ${role === UserRole.ADMIN
                      ? 'bg-purple-600/20 border-purple-500 text-purple-300'
                      : 'bg-slate-800 border-slate-700 text-slate-500 hover:border-slate-600'
                    }`}
                >
                  <ShieldCheck size={16} />
                  Admin
                </button>
              </div>
            </div>
          )}

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
                required
              />
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm text-center animate-pulse">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 rounded-lg transition-all active:scale-95 shadow-lg shadow-purple-500/20"
          >
            {isLogin ? 'Entrar no Sistema' : 'Criar Conta e Entrar'}
          </button>
        </form>

        <div className="mt-6 flex flex-col items-center gap-4">
          <button
            onClick={() => {
              setIsLogin(!isLogin);
              setError('');
            }}
            className="text-purple-400 hover:text-purple-300 text-sm font-medium transition-colors flex items-center gap-2"
          >
            {isLogin ? (
              <>
                <UserPlus size={16} />
                Não tem uma conta? Criar conta
              </>
            ) : (
              <>
                <ArrowLeft size={16} />
                Já tem uma conta? Fazer login
              </>
            )}
          </button>

          <div className="text-center text-[10px] text-slate-600 uppercase tracking-widest">
            Saka KDS v1.1.0 • Sistema Seguro
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;