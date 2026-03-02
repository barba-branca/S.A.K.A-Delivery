import {
  getKDSOrdersAPI,
  createKDSOrderAPI,
  updateKDSOrderStatusAPI,
  deleteKDSOrderAPI,
  resetKDSOrdersAPI,
  payDriverAPI
} from '../src/services/api';
import { Order, OrderStatus, OrderSource } from '../types';

// Initial mock data to populate the "DB" only the VERY FIRST time
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
    createdAt: Date.now() - 1000 * 60 * 20,
    preparingAt: Date.now() - 1000 * 60 * 15,
    deliveryFee: 5.00,
    driverName: 'Carlos Motoboy',
    isDriverPaid: false
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
    createdAt: Date.now() - 1000 * 60 * 5,
    deliveryFee: 4.50,
    driverName: undefined,
    isDriverPaid: false
  }
];

const STORAGE_KEY = 'saka_kds_orders';
const RESET_DATE_KEY = 'saka_kds_last_reset_day';

// Check if user is authenticated
const isAuthenticated = (): boolean => {
  return !!localStorage.getItem('saka_token');
};

export const getOrders = async (): Promise<Order[]> => {
  if (isAuthenticated()) {
    try {
      const orders = await getKDSOrdersAPI();
      return orders;
    } catch (error) {
      console.error('Error fetching orders from API:', error);
    }
  }

  // Fallback to localStorage
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === null) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(INITIAL_ORDERS));
    return INITIAL_ORDERS;
  }
  return JSON.parse(stored);
};

export const resetOrders = async (): Promise<Order[]> => {
  if (isAuthenticated()) {
    try {
      await resetKDSOrdersAPI();
      return [];
    } catch (error) {
      console.error('Error resetting orders via API:', error);
    }
  }

  // Fallback to localStorage
  localStorage.setItem(STORAGE_KEY, JSON.stringify([]));
  return [];
};

export const deleteOrder = async (orderId: string): Promise<Order[]> => {
  if (isAuthenticated()) {
    try {
      await deleteKDSOrderAPI(orderId);
      return await getOrders();
    } catch (error) {
      console.error('Error deleting order via API:', error);
    }
  }

  // Fallback to localStorage
  const orders = await getOrders();
  const updatedOrders = orders.filter(order => order.id !== orderId);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedOrders));
  return updatedOrders;
};

export const checkAndPerformDailyReset = async (): Promise<boolean> => {
  if (isAuthenticated()) {
    try {
      return true;
    } catch (error) {
      console.error('Error checking daily reset via API:', error);
    }
  }

  // Fallback to localStorage
  const today = new Date().toISOString().split('T')[0];
  const lastReset = localStorage.getItem(RESET_DATE_KEY);

  if (lastReset !== today) {
    await resetOrders();
    localStorage.setItem(RESET_DATE_KEY, today);
    return true;
  }
  return false;
};

export const updateOrderStatus = async (orderId: string, newStatus: OrderStatus): Promise<Order[]> => {
  if (isAuthenticated()) {
    try {
      await updateKDSOrderStatusAPI(orderId, newStatus);
      return await getOrders();
    } catch (error) {
      console.error('Error updating order status via API:', error);
    }
  }

  // Fallback to localStorage
  const orders = await getOrders();
  const updatedOrders = orders.map(order => {
    if (order.id === orderId) {
      const updates: Partial<Order> = { status: newStatus };

      if (newStatus === OrderStatus.PREPARING && !order.preparingAt) {
        updates.preparingAt = Date.now();
      } else if (newStatus === OrderStatus.READY && !order.readyAt) {
        updates.readyAt = Date.now();
      } else if (newStatus === OrderStatus.DELIVERY && !order.deliveryAt) {
        updates.deliveryAt = Date.now();
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

export const createOrder = async (order: Order): Promise<Order[]> => {
  if (isAuthenticated()) {
    try {
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

      await createKDSOrderAPI(orderData);
      return await getOrders();
    } catch (error) {
      console.error('Error creating order via API:', error);
    }
  }

  // Fallback to localStorage
  const orders = await getOrders();
  const newOrders = [...orders, order];
  localStorage.setItem(STORAGE_KEY, JSON.stringify(newOrders));
  return newOrders;
};

export const markDriverAsPaid = async (driverName: string): Promise<Order[]> => {
  if (isAuthenticated()) {
    try {
      await payDriverAPI(driverName);
      return await getOrders();
    } catch (error) {
      console.error('Error marking driver as paid via API:', error);
    }
  }

  // Fallback to localStorage
  const orders = await getOrders();
  const updatedOrders = orders.map(order =>
    (order.driverName === driverName && order.status === OrderStatus.DELIVERY)
      ? { ...order, isDriverPaid: true }
      : order
  );
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updatedOrders));
  return updatedOrders;
};
