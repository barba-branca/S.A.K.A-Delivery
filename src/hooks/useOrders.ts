import { useState, useCallback, useEffect } from 'react';
import { Order, OrderStatus, OrderSource } from '../types';
import { getKDSOrdersAPI, updateKDSOrderStatusAPI } from '../services/api';

export function useOrders(pollingIntervalMs: number = 15000) {
    const [orders, setOrders] = useState<Order[]>([]);
    const [loading, setLoading] = useState(true);
    const [connected, setConnected] = useState(true);
    const [lastRefresh, setLastRefresh] = useState<number>(Date.now());

    const loadOrders = useCallback(async () => {
        try {
            const data = await getKDSOrdersAPI();
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
            try {
                const mockDb = await import('../services/mockDb');
                const localOrders = await mockDb.getOrders();
                setOrders(localOrders);
            } catch {
                // ignore
            }
        } finally {
            setLoading(false);
        }
    }, []);

    // Initial fetch
    useEffect(() => {
        loadOrders();
    }, [loadOrders, lastRefresh]);

    // WebSocket connection for real-time updates (Observer implementation)
    useEffect(() => {
        // Fallback tenant_id to 1 until full frontend multi-tenant UI is built
        const tenantId = 1; 
        const wsUrl = `ws://localhost:8000/ws/kds/${tenantId}`;
        let ws: WebSocket;
        let reconnectTimeout: NodeJS.Timeout;

        const connect = () => {
            ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                console.log("KDS WebSocket Connected!");
                setConnected(true);
            };

            ws.onmessage = (event) => {
                if (event.data === "pong") return; // Keepalive handling
                try {
                    const data = JSON.parse(event.data);
                    console.log("WS Data Received:", data);
                    // Any action ("ORDER_CREATED", "ORDER_UPDATED") triggers a fresh load for absolute consistency
                    loadOrders();
                } catch (e) {
                    console.error("WS Parse error", e);
                }
            };

            ws.onclose = () => {
                console.log("KDS WebSocket Disconnected. Reconnecting in 5s...");
                setConnected(false);
                reconnectTimeout = setTimeout(connect, 5000);
            };

            ws.onerror = (err) => {
                console.error("KDS WebSocket Error:", err);
                ws.close();
            };
        };

        connect();

        // Keepalive ping
        const pingInterval = setInterval(() => {
            if (ws?.readyState === WebSocket.OPEN) {
                ws.send("ping");
            }
        }, 30000);

        return () => {
            clearInterval(pingInterval);
            clearTimeout(reconnectTimeout);
            if (ws) ws.close();
        };
    }, [loadOrders]);

    // Fallback Polling effect if WS fails (optional, disabled by default if ms is 0)
    useEffect(() => {
        if (pollingIntervalMs > 0 && !connected) {
            const interval = setInterval(() => {
                setLastRefresh(Date.now());
            }, pollingIntervalMs);
            return () => clearInterval(interval);
        }
    }, [pollingIntervalMs]);

    const refresh = () => setLastRefresh(Date.now());

    const updateOrderStatus = async (orderId: string, newStatus: OrderStatus) => {
        if (connected) {
            try {
                await updateKDSOrderStatusAPI(orderId, newStatus);
                await loadOrders();
            } catch (err) {
                console.error('Erro ao atualizar status:', err);
                setOrders(prev => prev.map(o => o.id === orderId ? { ...o, status: newStatus } : o));
            }
        } else {
            try {
                const mockDb = await import('../services/mockDb');
                const updated = await mockDb.updateOrderStatus(orderId, newStatus);
                setOrders(updated);
            } catch {
                setOrders(prev => prev.map(o => o.id === orderId ? { ...o, status: newStatus } : o));
            }
        }
    };

    const payDriver = async (driverName: string) => {
        if (connected) {
            try {
                const { default: api } = await import('../services/api');
                await api.post(`/orders/drivers/${encodeURIComponent(driverName)}/pay`);
                await loadOrders();
            } catch {
                setOrders(prev => prev.map(o =>
                    o.driverName === driverName && o.status === OrderStatus.DELIVERY
                        ? { ...o, isDriverPaid: true } : o
                ));
            }
        } else {
            try {
                const mockDb = await import('../services/mockDb');
                const updated = await mockDb.markDriverAsPaid(driverName);
                setOrders(updated);
            } catch {
                // ignore
            }
        }
    };

    const createOrder = async (order: Order) => {
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
            setOrders(prev => [order, ...prev]);
        }
    };

    const simulateNewOrder = async () => {
        if (connected) {
            try {
                const { default: api } = await import('../services/api');
                const customerName = ['Ana', 'Carlos', 'Beatriz', 'Lucas'][Math.floor(Math.random() * 4)] +
                    ' ' + ['Lima', 'Pereira', 'Costa'][Math.floor(Math.random() * 3)];
                const deliveryFee = [5.0, 7.0, 10.0, 3.5][Math.floor(Math.random() * 4)];
                const subtotal = 15.0 + Math.floor(Math.random() * 30);
                
                await api.post('/orders/create', {
                    customer_name: customerName,
                    source: Math.random() > 0.5 ? 'IFOOD' : 'WHATSAPP',
                    items: [{ name: 'Açaí Tradicional', quantity: 1, unit_price: subtotal, total_price: subtotal }],
                    delivery_fee: deliveryFee,
                    subtotal: subtotal,
                    total: subtotal + deliveryFee,
                });
                await loadOrders();
                return;
            } catch {
                // Fallback handled below
            }
        }
        
        // Simulação Local
        const newOrder: Order = {
            id: Date.now().toString(),
            displayId: Math.floor(1000 + Math.random() * 9000),
            customerName: ['Ana', 'Carlos', 'Beatriz', 'Lucas'][Math.floor(Math.random() * 4)] + ' ' + ['Lima', 'Pereira', 'Costa'][Math.floor(Math.random() * 3)],
            source: Math.random() > 0.5 ? OrderSource.IFOOD : OrderSource.WHATSAPP,
            status: OrderStatus.RECEIVED,
            items: [{ name: 'Açaí Tradicional', quantity: 1, notes: Math.random() > 0.7 ? 'Capricha' : undefined }],
            createdAt: Date.now(),
            deliveryFee: [5.0, 7.0, 10.0, 3.5][Math.floor(Math.random() * 4)],
            driverName: undefined,
            isDriverPaid: false,
        };
        setOrders(prev => [newOrder, ...prev]);
    };

    return {
        orders,
        loading,
        connected,
        updateOrderStatus,
        payDriver,
        createOrder,
        simulateNewOrder,
        refresh
    };
}
