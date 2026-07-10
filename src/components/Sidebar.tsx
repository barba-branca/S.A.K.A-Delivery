import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
    LayoutDashboard, ShoppingBag, ChefHat, LogOut, Wallet, CreditCard, Shield
} from 'lucide-react';

const Sidebar: React.FC = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const isAdmin = user?.role === 'ADMIN' || user?.role === 'SUPER_ADMIN';

    const navItems = [
        { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { to: '/pedidos', label: 'Pedidos', icon: ShoppingBag },
        { to: '/kds', label: 'KDS', icon: ChefHat },
        ...(isAdmin ? [{ to: '/admin', label: 'Admin', icon: Shield }] : []),
    ];

    return (
        <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-full shrink-0">
            {/* Logo */}
            <div className="h-16 flex items-center gap-3 px-5 border-b border-slate-800">
                <div className="w-9 h-9 bg-gradient-to-br from-purple-600 to-purple-800 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/20">
                    <span className="font-bold text-white text-sm">S</span>
                </div>
                <div>
                    <h1 className="font-bold text-white text-sm tracking-tight">S.A.K.A Delivery</h1>
                    <p className="text-xs text-slate-500">SaaS Management</p>
                </div>
            </div>

            {/* Nav */}
            <nav className="flex-1 py-4 px-3 space-y-1">
                {navItems.map((item) => (
                    <NavLink
                        key={item.to}
                        to={item.to}
                        className={({ isActive }) =>
                            `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${isActive
                                ? 'bg-purple-600/10 text-purple-400 border border-purple-500/20'
                                : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
                            }`
                        }
                    >
                        <item.icon size={18} />
                        {item.label}
                    </NavLink>
                ))}
            </nav>

            {/* User section */}
            <div className="p-3 border-t border-slate-800">

                {/* User info + logout */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 min-w-0">
                        <div className="w-8 h-8 bg-slate-800 rounded-full flex items-center justify-center shrink-0">
                            <span className="text-xs font-bold text-purple-400">
                                {(user?.username || 'U')[0].toUpperCase()}
                            </span>
                        </div>
                        <div className="min-w-0">
                            <p className="text-sm font-medium text-white truncate">{user?.username}</p>
                            <p className="text-xs text-slate-500">{user?.role}</p>
                        </div>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-950/30 rounded-lg transition-colors"
                        title="Sair"
                    >
                        <LogOut size={16} />
                    </button>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;
