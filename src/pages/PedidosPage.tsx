import React, { useEffect, useState } from 'react';
import { criarPedidoAPI, listarPedidosAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import {
    Plus, ShoppingBag, AlertCircle, CheckCircle, XCircle, User
} from 'lucide-react';

interface PedidoItem {
    id: number;
    user_id: number;
    valor_consumido: number;
    via_arnaldo?: boolean;
    data: string;
    status: string;
}

const PedidosPage: React.FC = () => {
    const { refreshUser, user } = useAuth();
    const [pedidos, setPedidos] = useState<PedidoItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [creating, setCreating] = useState(false);
    const [successMsg, setSuccessMsg] = useState('');
    const [errorMsg, setErrorMsg] = useState('');

    useEffect(() => {
        loadPedidos();
    }, []);

    const loadPedidos = async () => {
        try {
            const data = await listarPedidosAPI(50);
            setPedidos(data);
        } catch (err) {
            console.error('Erro ao listar pedidos:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleCriarPedido = async () => {
        setCreating(true);
        setErrorMsg('');
        setSuccessMsg('');
        try {
            await criarPedidoAPI(false);
            setSuccessMsg('Pedido criado com sucesso! 🎉');
            await loadPedidos();
            await refreshUser();
            setTimeout(() => setSuccessMsg(''), 3000);
        } catch (err: any) {
            setErrorMsg(err.response?.data?.detail || 'Erro ao criar pedido');
            setTimeout(() => setErrorMsg(''), 4000);
        } finally {
            setCreating(false);
        }
    };

    const getStatusBadge = (status: string) => {
        const styles: Record<string, string> = {
            ATIVO: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
            CANCELADO: 'bg-red-500/10 text-red-400 border-red-500/30',
            FINALIZADO: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
        };
        return (
            <span className={`px-2.5 py-1 text-xs font-medium rounded-full border ${styles[status] || 'bg-slate-500/10 text-slate-400 border-slate-500/30'}`}>
                {status}
            </span>
        );
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="w-8 h-8 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin"></div>
            </div>
        );
    }

    return (
        <div className="p-6 space-y-6 overflow-y-auto h-full">
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                        <ShoppingBag size={24} className="text-purple-400" />
                        Pedidos
                    </h1>
                    <p className="text-slate-400 text-sm">{pedidos.length} pedidos realizados</p>
                </div>
                <button
                    onClick={handleCriarPedido}
                    disabled={creating}
                    className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 text-white px-5 py-2.5 rounded-xl font-medium transition-all shadow-lg shadow-purple-500/20 disabled:opacity-50"
                >
                    {creating ? (
                        <div className="w-4.5 h-4.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    ) : (
                        <Plus size={18} />
                    )}
                    {creating ? 'Criando...' : 'Novo Pedido'}
                </button>
            </div>

            {/* Success/Error messages */}
            {successMsg && (
                <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-sm flex items-center gap-2">
                    <CheckCircle size={16} /> {successMsg}
                </div>
            )}
            {errorMsg && (
                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm flex items-center gap-2">
                    <XCircle size={16} /> {errorMsg}
                </div>
            )}

            {/* Table */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="border-b border-slate-800">
                                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-5 py-3">ID</th>
                                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-5 py-3">Valor</th>
                                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-5 py-3">Data</th>
                                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-5 py-3">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                            {pedidos.length === 0 ? (
                                <tr>
                                    <td colSpan={4} className="text-center py-12 text-slate-500">
                                        <AlertCircle className="mx-auto mb-2" size={28} />
                                        <p>Nenhum pedido encontrado</p>
                                        <p className="text-xs mt-1">Clique em "Novo Pedido" para começar</p>
                                    </td>
                                </tr>
                            ) : (
                                pedidos.map((p) => (
                                    <tr key={p.id} className="hover:bg-slate-800/30 transition-colors">
                                        <td className="px-5 py-3">
                                            <span className="text-sm font-medium text-white">#{p.id}</span>
                                        </td>
                                        <td className="px-5 py-3">
                                            <span className="text-sm font-semibold text-purple-400">
                                                R$ {Number(p.valor_consumido || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                                            </span>
                                        </td>
                                        <td className="px-5 py-3">
                                            <span className="text-sm text-slate-300">
                                                {new Date(p.data).toLocaleDateString('pt-BR')}{' '}
                                                <span className="text-slate-500">{new Date(p.data).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</span>
                                            </span>
                                        </td>
                                        <td className="px-5 py-3">{getStatusBadge(p.status)}</td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default PedidosPage;
