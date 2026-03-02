import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { comprarPacoteAPI, listarPedidosAPI, getRepasseMensalAPI } from '../services/api';
import {
    Wallet, ShoppingBag, TrendingUp, Package, Clock,
    CheckCircle, AlertCircle, ArrowUpRight
} from 'lucide-react';
import {
    Chart as ChartJS,
    CategoryScale, LinearScale, BarElement,
    Title, Tooltip, Legend
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

interface PedidoItem {
    id: number;
    valor_consumido: number;
    via_arnaldo: boolean;
    data: string;
    status: string;
}

const DashboardPage: React.FC = () => {
    const { user, refreshUser } = useAuth();
    const [pedidos, setPedidos] = useState<PedidoItem[]>([]);
    const [repasse, setRepasse] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [buyingPackage, setBuyingPackage] = useState(false);
    const [successMsg, setSuccessMsg] = useState('');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const isAdmin = user?.role === 'SUPER_ADMIN' || user?.role === 'ADMIN';
            const [pedidosData, repasseData] = await Promise.all([
                listarPedidosAPI(5),
                isAdmin ? getRepasseMensalAPI().catch(() => null) : Promise.resolve(null),
            ]);
            setPedidos(pedidosData);
            setRepasse(repasseData);
            await refreshUser();
        } catch (err) {
            console.error('Erro ao carregar dados:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleComprarPacote = async () => {
        setBuyingPackage(true);
        try {
            await comprarPacoteAPI('padrao');
            setSuccessMsg('Pacote de R$5.000 comprado com sucesso! 🎉');
            await loadData();
            setTimeout(() => setSuccessMsg(''), 4000);
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Erro ao comprar pacote');
        } finally {
            setBuyingPackage(false);
        }
    };

    const saldo = user?.saldoCredito || 0;
    const pedidosRestantes = Math.floor(saldo / 5);

    // Chart data
    const chartData = {
        labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4'],
        datasets: [
            {
                label: 'Pedidos',
                data: [
                    Math.floor(pedidos.length * 1.5),
                    Math.floor(pedidos.length * 2),
                    Math.floor(pedidos.length * 1.8),
                    pedidos.length,
                ],
                backgroundColor: 'rgba(147, 51, 234, 0.5)',
                borderColor: 'rgb(147, 51, 234)',
                borderWidth: 2,
                borderRadius: 8,
            },
        ],
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            title: {
                display: true,
                text: 'Uso Mensal',
                color: '#94a3b8',
                font: { size: 14 },
            },
        },
        scales: {
            y: { ticks: { color: '#64748b' }, grid: { color: '#1e293b' } },
            x: { ticks: { color: '#64748b' }, grid: { display: false } },
        },
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
                    <h1 className="text-2xl font-bold text-white">Dashboard</h1>
                    <p className="text-slate-400 text-sm">Bem-vindo, {user?.fullName || user?.username} 👋</p>
                </div>
                <button
                    onClick={handleComprarPacote}
                    disabled={buyingPackage}
                    className="flex items-center gap-2 bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-500 hover:to-emerald-600 text-white px-5 py-2.5 rounded-xl font-medium transition-all shadow-lg shadow-emerald-500/20 disabled:opacity-50"
                >
                    {buyingPackage ? (
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    ) : (
                        <Package size={18} />
                    )}
                    Comprar Pacote (R$5.000)
                </button>
            </div>

            {/* Success message */}
            {successMsg && (
                <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-sm flex items-center gap-2 animate-pulse">
                    <CheckCircle size={18} /> {successMsg}
                </div>
            )}

            {/* Stats Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Saldo */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 hover:border-purple-500/30 transition-colors group">
                    <div className="flex items-center justify-between mb-3">
                        <div className="p-2 bg-purple-500/10 rounded-lg">
                            <Wallet size={20} className="text-purple-400" />
                        </div>
                        <ArrowUpRight size={16} className="text-slate-600 group-hover:text-purple-400 transition-colors" />
                    </div>
                    <p className="text-sm text-slate-400">Saldo Crédito</p>
                    <p className="text-2xl font-bold text-white mt-1">
                        R$ {saldo.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                    </p>
                </div>

                {/* Pedidos Restantes */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 hover:border-blue-500/30 transition-colors group">
                    <div className="flex items-center justify-between mb-3">
                        <div className="p-2 bg-blue-500/10 rounded-lg">
                            <ShoppingBag size={20} className="text-blue-400" />
                        </div>
                        <ArrowUpRight size={16} className="text-slate-600 group-hover:text-blue-400 transition-colors" />
                    </div>
                    <p className="text-sm text-slate-400">Pedidos Restantes</p>
                    <p className="text-2xl font-bold text-white mt-1">{pedidosRestantes.toLocaleString()}</p>
                </div>

                {/* Economia Gerada - Apenas para Clientes (não admins) */}
                {user?.role === 'CLIENTE' && (
                    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 hover:border-emerald-500/30 transition-colors group">
                        <div className="flex items-center justify-between mb-3">
                            <div className="p-2 bg-emerald-500/10 rounded-lg">
                                <TrendingUp size={20} className="text-emerald-400" />
                            </div>
                            <ArrowUpRight size={16} className="text-slate-600 group-hover:text-emerald-400 transition-colors" />
                        </div>
                        <p className="text-sm text-slate-400">Economia Estimada</p>
                        <div className="mt-1 flex items-baseline gap-2">
                            <p className="text-2xl font-bold text-white">
                                R$ {(pedidos.length * (15 - 5)).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                            </p>
                            <span className="text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                                vs. Marketplace
                            </span>
                        </div>
                    </div>
                )}

                {/* Total Pedidos */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 hover:border-emerald-500/30 transition-colors group">
                    <div className="flex items-center justify-between mb-3">
                        <div className="p-2 bg-emerald-500/10 rounded-lg">
                            <CheckCircle size={20} className="text-emerald-400" />
                        </div>
                        <ArrowUpRight size={16} className="text-slate-600 group-hover:text-emerald-400 transition-colors" />
                    </div>
                    <p className="text-sm text-slate-400">Pedidos Realizados</p>
                    <p className="text-2xl font-bold text-white mt-1">{pedidos.length}</p>
                </div>
            </div>

            {/* Bottom section: recent orders + chart */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Últimos 5 Pedidos */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
                    <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                        <Clock size={18} className="text-purple-400" />
                        Últimos Pedidos
                    </h3>
                    {pedidos.length === 0 ? (
                        <div className="text-center py-8 text-slate-500">
                            <AlertCircle className="mx-auto mb-2" size={24} />
                            <p>Nenhum pedido ainda</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {pedidos.map((p) => (
                                <div key={p.id} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg hover:bg-slate-800 transition-colors">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-2 h-2 rounded-full ${p.status === 'ATIVO' ? 'bg-emerald-400' : 'bg-slate-500'}`}></div>
                                        <div>
                                            <p className="text-sm font-medium text-white">Pedido #{p.id}</p>
                                            <p className="text-xs text-slate-500">
                                                {new Date(p.data).toLocaleDateString('pt-BR')} •{' '}
                                                {(user?.role === 'SUPER_ADMIN' || user?.role === 'ADMIN') ? (
                                                    p.via_arnaldo && <span className="text-purple-400">S.A.K.A. Express</span>
                                                ) : (
                                                    <span className="text-purple-400">Entrega Inteligente AI</span>
                                                )}
                                            </p>
                                        </div>
                                    </div>
                                    <span className="text-sm font-medium text-white">
                                        R$ {p.valor_consumido.toFixed(2)}
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Chart */}
                <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
                    <div style={{ height: '280px' }}>
                        <Bar data={chartData} options={chartOptions} />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DashboardPage;
