import React, { useState, useEffect, useCallback } from 'react';
import KanbanBoard from '../../components/KanbanBoard';
import DriverPayouts from '../../components/DriverPayouts';
import NewOrderModal from '../../components/NewOrderModal';
import { Order, OrderStatus, OrderSource, UserRole } from '../../types';
import { getKDSOrdersAPI, updateKDSOrderStatusAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { RefreshCw, Plus, Wallet, Wifi, WifiOff } from 'lucide-react';

/**
 * KDS Page – connects the existing KanbanBoard to the real backend API.
 * Falls back to mock data if backend is unreachable.
 */
const KDSPage: React.FC = () => {
    const { user } = useAuth();
    const [orders, setOrders] = useState<Order[]>([]);
    const [loading, setLoading] = useState(true);
    const [connected, setConnected] = useState(true);
    const [showPayouts, setShowPayouts] = useState(false);
    const [showNewOrderModal, setShowNewOrderModal] = useState(false);
    const [lastRefresh, setLastRefresh] = useState<number>(Date.now());

    const loadOrders = useCallback(async () => {
        try {
            const data = await getKDSOrdersAPI();
            // Transform backend response to frontend Order format
            const mapped: Order[] = data.map((o: any) => ({
                id: o.id,
                displayId: o.displayId,
                customerName: o.customerName,
                source: o.source as OrderSource,
                status: o.status as OrderStatus,
                items: o.items || [],
                createdAt: o.createdAt || Date.now(),
                preparingAt: o.preparingAt || undefined,
                readyAt: o.readyAt || undefined,
                deliveryAt: o.deliveryAt || undefined,
                deliveryFee: o.deliveryFee || 0,
                driverName: o.driverName || undefined,
                isDriverPaid: o.isDriverPaid || false,
            }));
            setOrders(mapped);
            setConnected(true);
        } catch (err) {
            console.error('Erro ao carregar pedidos KDS do backend:', err);
            setConnected(false);
            // Fallback: use mockDb if backend is down
            try {
                const mockDb = await import('../../services/mockDb');
                const orders = await mockDb.getOrders();
                setOrders(orders);
            } catch {
                // ignore
            }
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadOrders();
    }, [loadOrders, lastRefresh]);

    // Auto-refresh every 15 seconds
    useEffect(() => {
        const interval = setInterval(() => {
            setLastRefresh(Date.now());
        }, 15000);
        return () => clearInterval(interval);
    }, []);

    const handleStatusUpdate = async (orderId: string, newStatus: OrderStatus) => {
        if (connected) {
            try {
                await updateKDSOrderStatusAPI(orderId, newStatus);
                await loadOrders();
            } catch (err) {
                console.error('Erro ao atualizar status:', err);
                // Fallback to local update
                setOrders(prev =>
                    prev.map(o => o.id === orderId ? { ...o, status: newStatus } : o)
                );
            }
        } else {
            // Offline: update local mock
            try {
                const mockDb = await import('../../services/mockDb');
                const updated = await mockDb.updateOrderStatus(orderId, newStatus);
                setOrders(updated);
            } catch {
                setOrders(prev =>
                    prev.map(o => o.id === orderId ? { ...o, status: newStatus } : o)
                );
            }
        }
    };

    const handlePayDriver = async (driverName: string) => {
        if (connected) {
            try {
                const { default: api } = await import('../services/api');
                await api.post(`/orders/drivers/${encodeURIComponent(driverName)}/pay`);
                await loadOrders();
            } catch {
                // Fallback
                setOrders(prev =>
                    prev.map(o =>
                        o.driverName === driverName && o.status === OrderStatus.DELIVERY
                            ? { ...o, isDriverPaid: true }
                            : o
                    )
                );
            }
        } else {
            try {
                const mockDb = await import('../../services/mockDb');
                const updated = await mockDb.markDriverAsPaid(driverName);
                setOrders(updated);
            } catch {
                // ignore
            }
        }
    };

    const simulateNewOrder = async () => {
        if (connected) {
            try {
                const { default: api } = await import('../services/api');
                const customerName =
                    ['Ana', 'Carlos', 'Beatriz', 'Lucas'][Math.floor(Math.random() * 4)] +
                    ' ' + ['Lima', 'Pereira', 'Costa'][Math.floor(Math.random() * 3)];
                const deliveryFee = [5.0, 7.0, 10.0, 3.5][Math.floor(Math.random() * 4)];
                const subtotal = 15.0 + Math.floor(Math.random() * 30);
                const newOrder = {
                    customer_name: customerName,
                    source: Math.random() > 0.5 ? 'IFOOD' : 'WHATSAPP',
                    items: [
                        { name: 'Açaí Tradicional', quantity: 1, unit_price: subtotal, total_price: subtotal },
                    ],
                    delivery_fee: deliveryFee,
                    subtotal: subtotal,
                    total: subtotal + deliveryFee,
                };
                await api.post('/orders/create', newOrder);
                await loadOrders();
            } catch {
                simulateNewOrderLocal();
            }
        } else {
            simulateNewOrderLocal();
        }
    };

    const handleCreateOrder = async (order: Order) => {
        if (connected) {
            try {
                const { default: api } = await import('../services/api');
                const orderData = {
                    customer_name: order.customerName,
                    source: order.source,
                    delivery_fee: order.deliveryFee,
                    items: order.items.map(item => ({
                        name: item.name,
                        quantity: item.quantity,
                        notes: item.notes,
                        unit_price: 0,
                        total_price: 0
                    }))
                };
                await api.post('/orders/create', orderData);
                await loadOrders();
            } catch (err) {
                console.error('Erro ao criar pedido:', err);
                setOrders(prev => [order, ...prev]);
            }
        } else {
            // Offline: add locally
            setOrders(prev => [order, ...prev]);
        }
    };

    const simulateNewOrderLocal = () => {
        const newOrder: Order = {
            id: Date.now().toString(),
            displayId: Math.floor(1000 + Math.random() * 9000),
            customerName:
                ['Ana', 'Carlos', 'Beatriz', 'Lucas'][Math.floor(Math.random() * 4)] +
                ' ' +
                ['Lima', 'Pereira', 'Costa'][Math.floor(Math.random() * 3)],
            source: Math.random() > 0.5 ? OrderSource.IFOOD : OrderSource.WHATSAPP,
            status: OrderStatus.RECEIVED,
            items: [
                {
                    name: 'Açaí Tradicional',
                    quantity: 1,
                    notes: Math.random() > 0.7 ? 'Capricha' : undefined,
                },
            ],
            createdAt: Date.now(),
            deliveryFee: [5.0, 7.0, 10.0, 3.5][Math.floor(Math.random() * 4)],
            driverName: undefined,
            isDriverPaid: false,
        };
        setOrders(prev => [newOrder, ...prev]);
    };

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
                    {/* Connection indicator */}
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
                        onClick={() => setLastRefresh(Date.now())}
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
            <KanbanBoard orders={orders} onUpdateStatus={handleStatusUpdate} />

            {/* Driver Payouts Modal */}
            {showPayouts && (
                <DriverPayouts
                    orders={orders}
                    onPayDriver={handlePayDriver}
                    onClose={() => setShowPayouts(false)}
                />
            )}

            {/* New Order Modal */}
            {showNewOrderModal && (
                <NewOrderModal
                    onClose={() => setShowNewOrderModal(false)}
                    onCreateOrder={handleCreateOrder}
                    onSimulateOrder={simulateNewOrder}
                />
            )}
        </div>
    );
};

export default KDSPage;
