import { Order, OrderStatus, OrderSource } from '../types';

// Initial mock data to populate the "DB"
const INITIAL_ORDERS: Order[] = [
  {
    id: '1',
    displayId: 101,
    customerName: 'João Silva',
    source: OrderSource.IFOOD,
    status: OrderStatus.PREPARING,
    items: [
      { name: 'Açaí 500ml', quantity: 1, notes: 'Sem banana' },
      { name: 'Leite em pó', quantity: 1 }
    ],
    createdAt: Date.now() - 1000 * 60 * 20, // 20 mins ago
    preparingAt: Date.now() - 1000 * 60 * 15, // 15 mins ago
    deliveryFee: 5.00,
    driverName: 'Carlos Motoboy',
    isDriverPaid: false
  },
  {
    id: '2',
    displayId: 102,
    customerName: 'Maria Souza',
    source: OrderSource.WHATSAPP,
    status: OrderStatus.RECEIVED,
    items: [
      { name: 'Açaí 300ml', quantity: 2 },
      { name: 'Paçoca', quantity: 1 }
    ],
    createdAt: Date.now() - 1000 * 60 * 5, // 5 mins ago
    deliveryFee: 7.50,
    driverName: undefined, // Not assigned yet
    isDriverPaid: false
  },
  {
    id: '3',
    displayId: 103,
    customerName: 'Pedro Santos',
    source: OrderSource.IFOOD,
    status: OrderStatus.READY,
    items: [
      { name: 'Barca Grande', quantity: 1, notes: 'Capricha no leite condensado' }
    ],
    createdAt: Date.now() - 1000 * 60 * 40, // 40 mins ago
    preparingAt: Date.now() - 1000 * 60 * 30, // 30 mins ago
    readyAt: Date.now() - 1000 * 60 * 10, // 10 mins ago
    deliveryFee: 0.00, // Free delivery
    driverName: 'Marcos Entregas',
    isDriverPaid: false
  },
  {
    id: '4',
    displayId: 104,
    customerName: 'Ana Clara',
    source: OrderSource.UBER,
    status: OrderStatus.DELIVERY,
    items: [
      { name: 'Suco de Laranja', quantity: 2 }
    ],
    createdAt: Date.now() - 1000 * 60 * 60, // 60 mins ago
    preparingAt: Date.now() - 1000 * 60 * 50, // 50 mins ago
    readyAt: Date.now() - 1000 * 60 * 30, // 30 mins ago
    deliveryAt: Date.now() - 1000 * 60 * 15, // 15 mins ago
    deliveryFee: 6.00,
    driverName: 'Carlos Motoboy',
    isDriverPaid: false
  },
  {
    id: '5',
    displayId: 105,
    customerName: 'Roberto Firmino',
    source: OrderSource.WHATSAPP,
    status: OrderStatus.DELIVERY,
    items: [
      { name: 'Açaí 700ml', quantity: 1 }
    ],
    createdAt: Date.now() - 1000 * 60 * 70, // 70 mins ago
    preparingAt: Date.now() - 1000 * 60 * 60, // 60 mins ago
    readyAt: Date.now() - 1000 * 60 * 40, // 40 mins ago
    deliveryAt: Date.now() - 1000 * 60 * 20, // 20 mins ago
    deliveryFee: 8.00,
    driverName: 'Carlos Motoboy',
    isDriverPaid: true // Already paid
  },
  {
    id: '6',
    displayId: 106,
    customerName: 'Fernanda Lima',
    source: OrderSource.FOOD99,
    status: OrderStatus.RECEIVED,
    items: [
      { name: 'Açaí com Morango', quantity: 1 },
      { name: 'Creme de Cupuaçu', quantity: 1 }
    ],
    createdAt: Date.now() - 1000 * 60 * 5, // 5 mins ago
    deliveryFee: 4.50,
    driverName: undefined,
    isDriverPaid: false
  }
];

const STORAGE_KEY = 'saka_kds_orders';
const RESET_DATE_KEY = 'saka_kds_last_reset_day';

export const getOrders = (): Order[] => {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === null) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(INITIAL_ORDERS));
    return INITIAL_ORDERS;
  }
  return JSON.parse(stored);
};

export const resetOrders = (): Order[] => {
  localStorage.setItem(STORAGE_KEY, JSON.stringify([]));
  return [];
};

export const deleteOrder = (orderId: string): Order[] => {
  const orders = getOrders();
  const updatedOrders = orders.filter(order => order.id !== orderId);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedOrders));
  return updatedOrders;
};

export const checkAndPerformDailyReset = (): boolean => {
  const today = new Date().toISOString().split('T')[0];
  const lastReset = localStorage.getItem(RESET_DATE_KEY);

  if (lastReset !== today) {
    resetOrders();
    localStorage.setItem(RESET_DATE_KEY, today);
    return true;
  }
  return false;
};

export const updateOrderStatus = (orderId: string, newStatus: OrderStatus): Order[] => {
  const orders = getOrders();
  const updatedOrders = orders.map(order => {
    if (order.id === orderId) {
      const updates: Partial<Order> = { status: newStatus };

      // Update timestamps based on new status
      if (newStatus === OrderStatus.PREPARING && !order.preparingAt) {
        updates.preparingAt = Date.now();
      } else if (newStatus === OrderStatus.READY && !order.readyAt) {
        updates.readyAt = Date.now();
      } else if (newStatus === OrderStatus.DELIVERY && !order.deliveryAt) {
        updates.deliveryAt = Date.now();
        // Auto-assign driver if moving to DELIVERY and no driver assigned (Simulation)
        if (!order.driverName) {
          updates.driverName = Math.random() > 0.5 ? 'Carlos Motoboy' : 'Marcos Entregas';
        }
      }

      return { ...order, ...updates };
    }
    return order;
  });
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedOrders));
  return updatedOrders;
};

export const createOrder = (order: Order): Order[] => {
  const orders = getOrders();
  const newOrders = [...orders, order];
  localStorage.setItem(STORAGE_KEY, JSON.stringify(newOrders));
  return newOrders;
};

export const markDriverAsPaid = (driverName: string): Order[] => {
  const orders = getOrders();
  const updatedOrders = orders.map(order =>
    (order.driverName === driverName && order.status === OrderStatus.DELIVERY)
      ? { ...order, isDriverPaid: true }
      : order
  );
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedOrders));
  return updatedOrders;
};