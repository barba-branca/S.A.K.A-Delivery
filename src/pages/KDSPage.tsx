import React, { useState } from 'react';
import KanbanBoard from '../../components/KanbanBoard';
import DriverPayouts from '../../components/DriverPayouts';
import NewOrderModal from '../../components/NewOrderModal';
import { useAuth } from '../contexts/AuthContext';
import { useOrders } from '../hooks/useOrders';
import { RefreshCw, Plus, Wallet, Wifi, WifiOff } from 'lucide-react';

/**
 * KDS Page – Refactored using custom hooks (Clean Code).
 * The UI is decoupled from the data fetching rules.
 */
const KDSPage: React.FC = () => {
    const { user } = useAuth();
    
    // Custom Hook handles all the complex business logic & data state
    const { 
        orders, 
        loading, 
        connected, 
        updateOrderStatus, 
        payDriver, 
        createOrder, 
        simulateNewOrder, 
        refresh 
    } = useOrders(15000);

    // UI State only
    const [showPayouts, setShowPayouts] = useState(false);
    const [showNewOrderModal, setShowNewOrderModal] = useState(false);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full bg-slate-950">
                <div className="w-10 h-10 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin"></div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full bg-slate-950 text-slate-100 overflow-hidden">
            {/* Top Bar */}
            <header className="h-14 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-5 shrink-0">
                <div className="flex items-center gap-3">
                    <h1 className="font-bold text-lg tracking-tight text-white">Kitchen Display</h1>
                    <span className="px-2 py-0.5 bg-slate-800 rounded text-xs text-slate-400 border border-slate-700">
                        {user?.role || 'USER'} VIEW
                    </span>
                    <div className={`flex items-center gap-1.5 px-2 py-0.5 rounded text-xs ${connected
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        }`}>
                        {connected ? <Wifi size={12} /> : <WifiOff size={12} />}
                        {connected ? 'Online' : 'Offline'}
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    {user?.role === 'ADMIN' && (
                        <button
                            onClick={() => setShowPayouts(true)}
                            className="flex items-center gap-2 text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg transition-colors border border-slate-700 text-sm"
                        >
                            <Wallet size={16} />
                            <span className="hidden sm:inline">Financeiro</span>
                        </button>
                    )}

                    <button
                        onClick={refresh}
                        className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                        title="Atualizar"
                    >
                        <RefreshCw size={18} />
                    </button>

                    <button
                        onClick={() => setShowNewOrderModal(true)}
                        className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-3 py-1.5 rounded-lg text-sm font-semibold transition-colors shadow-lg shadow-purple-900/20"
                    >
                        <Plus size={14} />
                        <span className="hidden sm:inline">Novo Pedido</span>
                    </button>
                </div>
            </header>

            {/* Main Board */}
            <KanbanBoard orders={orders} onUpdateStatus={updateOrderStatus} />

            {/* Driver Payouts Modal */}
            {showPayouts && (
                <DriverPayouts
                    orders={orders}
                    onPayDriver={payDriver}
                    onClose={() => setShowPayouts(false)}
                />
            )}

            {/* New Order Modal */}
            {showNewOrderModal && (
                <NewOrderModal
                    onClose={() => setShowNewOrderModal(false)}
                    onCreateOrder={createOrder}
                    onSimulateOrder={simulateNewOrder}
                />
            )}
        </div>
    );
};

export default KDSPage;
