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
    via_arnaldo: boolean;
    data: string;
    status: string;
}

const PedidosPage: React.FC = () => {
    const { refreshUser } = useAuth();
    const [pedidos, setPedidos] = useState<PedidoItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [creating, setCreating] = useState(false);
    const [viaArnaldo, setViaArnaldo] = useState(false);
    const [showModal, setShowModal] = useState(false);
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
        try {
            await criarPedidoAPI(viaArnaldo);
            setSuccessMsg('Pedido criado com sucesso! 🎉');
            setShowModal(false);
            setViaArnaldo(false);
            await loadPedidos();
            await refreshUser();
            setTimeout(() => setSuccessMsg(''), 3000);
        } catch (err: any) {
            setErrorMsg(err.response?.data?.detail || 'Erro ao criar pedido');
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
                    onClick={() => setShowModal(true)}
                    className="flex items-center gap-2 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 text-white px-5 py-2.5 rounded-xl font-medium transition-all shadow-lg shadow-purple-500/20"
                >
                    <Plus size={18} />
                    Novo Pedido
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
                                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-5 py-3">Via Arnaldo</th>
                                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-5 py-3">Data</th>
                                <th className="text-left text-xs font-semibold text-slate-400 uppercase tracking-wider px-5 py-3">Status</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                            {pedidos.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="text-center py-12 text-slate-500">
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
                                            <span className="text-sm text-white">R$ {p.valor_consumido.toFixed(2)}</span>
                                        </td>
                                        <td className="px-5 py-3">
                                            {p.via_arnaldo ? (
                                                <span className="flex items-center gap-1 text-amber-400 text-sm">
                                                    <User size={14} /> Sim (30%)
                                                </span>
                                            ) : (
                                                <span className="text-slate-500 text-sm">Não</span>
                                            )}
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

            {/* Modal: Novo Pedido */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-md shadow-2xl">
                        <h2 className="text-xl font-bold text-white mb-4">Novo Pedido</h2>
                        <p className="text-slate-400 text-sm mb-6">
                            Cada pedido consome <strong className="text-white">R$5.00</strong> do seu saldo.
                        </p>

                        <div className="mb-6">
                            <label className="flex items-center gap-3 cursor-pointer group">
                                <input
                                    type="checkbox"
                                    checked={viaArnaldo}
                                    onChange={(e) => setViaArnaldo(e.target.checked)}
                                    className="w-5 h-5 rounded border-slate-600 bg-slate-800 text-purple-500 focus:ring-purple-500"
                                />
                                <div>
                                    <span className="text-white text-sm font-medium group-hover:text-purple-300 transition-colors">
                                        Via Arnaldo
                                    </span>
                                    <p className="text-xs text-slate-500">30% (R$1.50) será repassado ao Arnaldo</p>
                                </div>
                            </label>
                        </div>

                        {errorMsg && (
                            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
                                {errorMsg}
                            </div>
                        )}

                        <div className="flex gap-3">
                            <button
                                onClick={() => { setShowModal(false); setErrorMsg(''); }}
                                className="flex-1 px-4 py-2.5 bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleCriarPedido}
                                disabled={creating}
                                className="flex-1 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-lg hover:from-purple-500 hover:to-purple-600 transition-all font-medium disabled:opacity-50"
                            >
                                {creating ? 'Criando...' : 'Criar Pedido'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default PedidosPage;
