import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import {
    Shield, Users, CreditCard, Trash2, Edit3, X, Check, RefreshCw,
    ChevronDown, AlertTriangle, DollarSign, UserCheck
} from 'lucide-react';
import { getAdminUsersAPI, updateUserCreditsAPI, updateUserRoleAPI, deleteUserAPI } from '../services/api';

interface AdminUser {
    id: number;
    username: string;
    email?: string;
    fullName: string;
    full_name?: string;
    role: string;
    saldoCredito: number;
    saldo_credito?: number;
    isActive: boolean;
    is_active?: boolean;
    createdAt?: string;
    created_at?: string;
}

const ROLES = ['SUPER_ADMIN', 'ADMIN', 'CLIENTE', 'KITCHEN'] as const;
const ROLE_COLORS: Record<string, string> = {
    SUPER_ADMIN: 'bg-red-500/20 text-red-400 border-red-500/30',
    ADMIN: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    CLIENTE: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
    KITCHEN: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
};

const AdminPage: React.FC = () => {
    const { user } = useAuth();
    const [users, setUsers] = useState<AdminUser[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // Edit credit modal
    const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
    const [newSaldo, setNewSaldo] = useState('');

    // Edit role modal
    const [roleEditUser, setRoleEditUser] = useState<AdminUser | null>(null);
    const [newRole, setNewRole] = useState('');

    // Delete confirmation
    const [deleteTarget, setDeleteTarget] = useState<AdminUser | null>(null);

    const loadUsers = useCallback(async () => {
        try {
            setLoading(true);
            const data = await getAdminUsersAPI();
            setUsers(data.map((u: any) => ({
                id: u.id,
                username: u.username,
                email: u.email,
                fullName: u.fullName || u.full_name || '',
                role: u.role,
                saldoCredito: u.saldoCredito ?? u.saldo_credito ?? 0,
                isActive: u.isActive ?? u.is_active ?? true,
                createdAt: u.createdAt || u.created_at,
            })));
            setError('');
        } catch {
            setError('Erro ao carregar usuários');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { loadUsers(); }, [loadUsers]);

    useEffect(() => {
        if (success) {
            const t = setTimeout(() => setSuccess(''), 3000);
            return () => clearTimeout(t);
        }
    }, [success]);

    const handleUpdateCredits = async () => {
        if (!editingUser) return;
        const valor = parseFloat(newSaldo.replace(',', '.'));
        if (isNaN(valor) || valor < 0) {
            setError('Valor inválido');
            return;
        }
        try {
            await updateUserCreditsAPI(editingUser.id, valor);
            setSuccess(`Créditos de ${editingUser.username} atualizados para R$ ${valor.toFixed(2)}`);
            setEditingUser(null);
            setNewSaldo('');
            await loadUsers();
        } catch {
            setError('Erro ao atualizar créditos');
        }
    };

    const handleUpdateRole = async () => {
        if (!roleEditUser || !newRole) return;
        try {
            await updateUserRoleAPI(roleEditUser.id, newRole);
            setSuccess(`Role de ${roleEditUser.username} atualizado para ${newRole}`);
            setRoleEditUser(null);
            setNewRole('');
            await loadUsers();
        } catch {
            setError('Erro ao atualizar role');
        }
    };

    const handleDelete = async () => {
        if (!deleteTarget) return;
        try {
            await deleteUserAPI(deleteTarget.id);
            setSuccess(`Usuário ${deleteTarget.username} excluído`);
            setDeleteTarget(null);
            await loadUsers();
        } catch {
            setError('Erro ao excluir usuário');
        }
    };

    // Guard: only ADMIN/SUPER_ADMIN
    if (user?.role !== 'ADMIN' && user?.role !== 'SUPER_ADMIN') {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center">
                    <Shield size={48} className="text-red-500 mx-auto mb-4" />
                    <h2 className="text-xl font-bold text-white mb-2">Acesso Restrito</h2>
                    <p className="text-slate-400">Apenas administradores podem acessar esta página.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="h-full overflow-auto p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <Shield size={28} className="text-purple-400" />
                    <div>
                        <h1 className="text-2xl font-bold text-white">Painel Admin</h1>
                        <p className="text-sm text-slate-400">{users.length} usuários cadastrados</p>
                    </div>
                </div>
                <button
                    onClick={loadUsers}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors"
                >
                    <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                    Atualizar
                </button>
            </div>

            {/* Alerts */}
            {error && (
                <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm flex items-center gap-2">
                    <AlertTriangle size={16} /> {error}
                    <button onClick={() => setError('')} className="ml-auto hover:text-red-300"><X size={14} /></button>
                </div>
            )}
            {success && (
                <div className="mb-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-emerald-400 text-sm flex items-center gap-2">
                    <Check size={16} /> {success}
                </div>
            )}

            {/* Stats cards */}
            <div className="grid grid-cols-4 gap-4 mb-6">
                {[
                    { label: 'Total Usuários', value: users.length, icon: Users, color: 'purple' },
                    { label: 'Clientes', value: users.filter(u => u.role === 'CLIENTE').length, icon: UserCheck, color: 'emerald' },
                    { label: 'Créditos Totais', value: `R$ ${users.reduce((s, u) => s + u.saldoCredito, 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`, icon: DollarSign, color: 'amber' },
                    { label: 'Admins', value: users.filter(u => u.role === 'ADMIN' || u.role === 'SUPER_ADMIN').length, icon: Shield, color: 'red' },
                ].map((stat, i) => (
                    <div key={i} className="bg-slate-900/60 border border-slate-800 rounded-xl p-4">
                        <div className="flex items-center gap-2 mb-2">
                            <stat.icon size={16} className={`text-${stat.color}-400`} />
                            <span className="text-xs text-slate-400">{stat.label}</span>
                        </div>
                        <p className="text-lg font-bold text-white">{stat.value}</p>
                    </div>
                ))}
            </div>

            {/* Users table */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden">
                <table className="w-full">
                    <thead>
                        <tr className="border-b border-slate-800">
                            <th className="text-left text-xs font-semibold text-slate-400 uppercase px-4 py-3">ID</th>
                            <th className="text-left text-xs font-semibold text-slate-400 uppercase px-4 py-3">Usuário</th>
                            <th className="text-left text-xs font-semibold text-slate-400 uppercase px-4 py-3">Nome</th>
                            <th className="text-left text-xs font-semibold text-slate-400 uppercase px-4 py-3">Role</th>
                            <th className="text-right text-xs font-semibold text-slate-400 uppercase px-4 py-3">Saldo</th>
                            <th className="text-center text-xs font-semibold text-slate-400 uppercase px-4 py-3">Ações</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading ? (
                            <tr><td colSpan={6} className="text-center py-12 text-slate-500">
                                <RefreshCw size={24} className="animate-spin mx-auto mb-2" />
                                Carregando...
                            </td></tr>
                        ) : users.length === 0 ? (
                            <tr><td colSpan={6} className="text-center py-12 text-slate-500">Nenhum usuário encontrado</td></tr>
                        ) : users.map((u) => (
                            <tr key={u.id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                                <td className="px-4 py-3 text-sm text-slate-500 font-mono">#{u.id}</td>
                                <td className="px-4 py-3">
                                    <div className="flex items-center gap-2">
                                        <div className="w-7 h-7 bg-slate-800 rounded-full flex items-center justify-center shrink-0">
                                            <span className="text-xs font-bold text-purple-400">{u.username[0].toUpperCase()}</span>
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-white">{u.username}</p>
                                            {u.email && <p className="text-xs text-slate-500">{u.email}</p>}
                                        </div>
                                    </div>
                                </td>
                                <td className="px-4 py-3 text-sm text-slate-300">{u.fullName}</td>
                                <td className="px-4 py-3">
                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${ROLE_COLORS[u.role] || 'bg-slate-700 text-slate-300'}`}>
                                        {u.role}
                                    </span>
                                </td>
                                <td className="px-4 py-3 text-right">
                                    <span className={`text-sm font-semibold ${u.saldoCredito > 0 ? 'text-emerald-400' : 'text-slate-500'}`}>
                                        R$ {u.saldoCredito.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                    </span>
                                </td>
                                <td className="px-4 py-3">
                                    <div className="flex items-center justify-center gap-1">
                                        <button
                                            onClick={() => { setEditingUser(u); setNewSaldo(u.saldoCredito.toString()); }}
                                            className="p-1.5 text-slate-400 hover:text-emerald-400 hover:bg-emerald-950/30 rounded-lg transition-colors"
                                            title="Editar Créditos"
                                        >
                                            <CreditCard size={15} />
                                        </button>
                                        <button
                                            onClick={() => { setRoleEditUser(u); setNewRole(u.role); }}
                                            className="p-1.5 text-slate-400 hover:text-purple-400 hover:bg-purple-950/30 rounded-lg transition-colors"
                                            title="Alterar Role"
                                        >
                                            <Edit3 size={15} />
                                        </button>
                                        {u.username !== 'admin' && (
                                            <button
                                                onClick={() => setDeleteTarget(u)}
                                                className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-950/30 rounded-lg transition-colors"
                                                title="Excluir"
                                            >
                                                <Trash2 size={15} />
                                            </button>
                                        )}
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* ===== MODAL: Editar Créditos ===== */}
            {editingUser && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 w-full max-w-md shadow-2xl">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                <CreditCard size={20} className="text-emerald-400" />
                                Editar Créditos
                            </h3>
                            <button onClick={() => setEditingUser(null)} className="text-slate-500 hover:text-white">
                                <X size={20} />
                            </button>
                        </div>
                        <p className="text-sm text-slate-400 mb-4">
                            Usuário: <span className="text-white font-medium">{editingUser.username}</span> ({editingUser.fullName})
                        </p>
                        <p className="text-sm text-slate-400 mb-2">
                            Saldo atual: <span className="text-emerald-400 font-semibold">R$ {editingUser.saldoCredito.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                        </p>
                        <div className="mb-4">
                            <label className="block text-sm text-slate-400 mb-1.5">Novo Saldo (R$)</label>
                            <div className="relative">
                                <DollarSign className="absolute left-3 top-3 text-slate-500" size={16} />
                                <input
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    value={newSaldo}
                                    onChange={(e) => setNewSaldo(e.target.value)}
                                    className="w-full bg-slate-800/50 border border-slate-700 text-white rounded-lg py-2.5 pl-9 pr-4 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                                    placeholder="0.00"
                                    autoFocus
                                />
                            </div>
                        </div>
                        {/* Quick values */}
                        <div className="flex gap-2 mb-5">
                            {[500, 1000, 5000, 10000].map(v => (
                                <button
                                    key={v}
                                    onClick={() => setNewSaldo(v.toString())}
                                    className="flex-1 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
                                >
                                    R$ {v.toLocaleString('pt-BR')}
                                </button>
                            ))}
                        </div>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setEditingUser(null)}
                                className="flex-1 py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleUpdateCredits}
                                className="flex-1 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
                            >
                                <Check size={16} /> Salvar
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ===== MODAL: Alterar Role ===== */}
            {roleEditUser && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-slate-900 border border-slate-700 rounded-2xl p-6 w-full max-w-md shadow-2xl">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                <Edit3 size={20} className="text-purple-400" />
                                Alterar Role
                            </h3>
                            <button onClick={() => setRoleEditUser(null)} className="text-slate-500 hover:text-white">
                                <X size={20} />
                            </button>
                        </div>
                        <p className="text-sm text-slate-400 mb-4">
                            Usuário: <span className="text-white font-medium">{roleEditUser.username}</span>
                            <span className={`ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${ROLE_COLORS[roleEditUser.role]}`}>
                                {roleEditUser.role}
                            </span>
                        </p>
                        <div className="mb-5">
                            <label className="block text-sm text-slate-400 mb-1.5">Novo Role</label>
                            <div className="relative">
                                <select
                                    value={newRole}
                                    onChange={(e) => setNewRole(e.target.value)}
                                    className="w-full bg-slate-800/50 border border-slate-700 text-white rounded-lg py-2.5 px-4 pr-10 focus:outline-none focus:ring-2 focus:ring-purple-500 appearance-none"
                                >
                                    {ROLES.map(r => (
                                        <option key={r} value={r}>{r}</option>
                                    ))}
                                </select>
                                <ChevronDown className="absolute right-3 top-3 text-slate-500 pointer-events-none" size={16} />
                            </div>
                        </div>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setRoleEditUser(null)}
                                className="flex-1 py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleUpdateRole}
                                className="flex-1 py-2.5 bg-purple-600 hover:bg-purple-500 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
                            >
                                <Check size={16} /> Salvar
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ===== MODAL: Confirmar Exclusão ===== */}
            {deleteTarget && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-slate-900 border border-red-500/30 rounded-2xl p-6 w-full max-w-md shadow-2xl">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="p-2 bg-red-500/10 rounded-full">
                                <AlertTriangle size={24} className="text-red-400" />
                            </div>
                            <h3 className="text-lg font-bold text-white">Confirmar Exclusão</h3>
                        </div>
                        <p className="text-sm text-slate-400 mb-5">
                            Tem certeza que deseja excluir o usuário <span className="text-white font-semibold">{deleteTarget.username}</span>?
                            Esta ação não pode ser desfeita.
                        </p>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setDeleteTarget(null)}
                                className="flex-1 py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleDelete}
                                className="flex-1 py-2.5 bg-red-600 hover:bg-red-500 text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
                            >
                                <Trash2 size={16} /> Excluir
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AdminPage;
