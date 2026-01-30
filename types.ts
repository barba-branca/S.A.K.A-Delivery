export enum UserRole {
  ADMIN = 'ADMIN',
  KITCHEN = 'KITCHEN'
}

export interface User {
  username: string;
  role: UserRole;
}

export enum OrderStatus {
  RECEIVED = 'RECEIVED',
  PREPARING = 'PREPARING',
  READY = 'READY',
  DELIVERY = 'DELIVERY'
}

export enum OrderSource {
  IFOOD = 'IFOOD',
  WHATSAPP = 'WHATSAPP',
  UBER = 'UBER',
  FOOD99 = 'FOOD99'
}

export interface OrderItem {
  name: string;
  quantity: number;
  notes?: string;
}

export interface Order {
  id: string;
  displayId: number;
  customerName: string;
  source: OrderSource;
  status: OrderStatus;
  items: OrderItem[];
  createdAt: number; // Timestamp quando o pedido foi RECEBIDO
  preparingAt?: number; // Timestamp quando o pedido entrou EM PREPARO
  readyAt?: number;    // Timestamp quando o pedido ficou PRONTO
  deliveryAt?: number; // Timestamp quando o pedido SAIU PARA ENTREGA
  // New fields for Driver Payments
  deliveryFee: number;
  driverName?: string;
  isDriverPaid: boolean;
}