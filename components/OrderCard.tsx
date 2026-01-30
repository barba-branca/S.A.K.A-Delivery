import React from 'react';
import { Order, OrderStatus, OrderSource } from '../types';
import Timer from './Timer';
import { MessageCircle, ShoppingBag, Car, ChevronRight, CheckCircle2, Bike, DollarSign, UtensilsCrossed, GripVertical, Timer as TimerIcon, PlayCircle, Package, Truck } from 'lucide-react';

interface OrderCardProps {
  order: Order;
  onAdvance: (orderId: string, currentStatus: OrderStatus) => void;
  onDragStart?: (e: React.DragEvent<HTMLDivElement>, orderId: string) => void;
}

const OrderCard: React.FC<OrderCardProps> = ({ order, onAdvance, onDragStart }) => {
  const getSourceIcon = (source: OrderSource) => {
    switch (source) {
      case OrderSource.WHATSAPP:
        return <div className="flex items-center gap-1 text-green-400"><MessageCircle size={14} /> <span className="text-xs">Zap</span></div>;
      case OrderSource.IFOOD:
        return <div className="flex items-center gap-1 text-red-400"><ShoppingBag size={14} /> <span className="text-xs">iFood</span></div>;
      case OrderSource.FOOD99:
        return <div className="flex items-center gap-1 text-yellow-500"><UtensilsCrossed size={14} /> <span className="text-xs">99Food</span></div>;
      default:
        return <div className="flex items-center gap-1 text-gray-400"><Car size={14} /> <span className="text-xs">App</span></div>;
    }
  };

  const getNextStatus = (current: OrderStatus): OrderStatus | null => {
    if (current === OrderStatus.RECEIVED) return OrderStatus.PREPARING;
    if (current === OrderStatus.PREPARING) return OrderStatus.READY;
    if (current === OrderStatus.READY) return OrderStatus.DELIVERY;
    return null; // Delivery is final state in Kanban view usually
  };

  const nextStatus = getNextStatus(order.status);

  const formatTime = (timestamp?: number) => {
    if (!timestamp) return '-';
    return new Date(timestamp).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div 
      draggable={!!onDragStart}
      onDragStart={(e) => onDragStart && onDragStart(e, order.id)}
      className="bg-slate-800 rounded-lg border border-slate-700 shadow-sm hover:shadow-lg hover:border-slate-600 transition-all flex flex-col h-full animate-in fade-in zoom-in duration-300 relative overflow-hidden cursor-grab active:cursor-grabbing group/card"
    >
      {/* Status Bar for Payment */}
      {order.status === OrderStatus.DELIVERY && (
        <div className={`absolute top-0 left-0 w-1 h-full ${order.isDriverPaid ? 'bg-green-500' : 'bg-orange-500'}`} />
      )}

      {/* Header */}
      <div className="p-3 border-b border-slate-700 flex justify-between items-start bg-slate-800/50 rounded-t-lg pl-4">
        <div className="flex items-start gap-2">
            <div className="text-slate-600 mt-1 opacity-0 group-hover/card:opacity-100 transition-opacity">
               <GripVertical size={16} />
            </div>
            <div>
            <h3 className="text-lg font-bold text-white">#{order.displayId}</h3>
            <p className="text-xs text-slate-400 truncate max-w-[120px]">{order.customerName}</p>
            </div>
        </div>
        <div className="flex flex-col items-end gap-1">
          <Timer startTime={order.createdAt} />
          {getSourceIcon(order.source)}
        </div>
      </div>

      {/* Items */}
      <div className="p-3 flex-grow overflow-y-auto max-h-64 pl-4">
        <ul className="space-y-2">
          {order.items.map((item, idx) => (
            <li key={idx} className="text-sm">
              <div className="flex justify-between text-slate-200">
                <span className="font-medium">{item.quantity}x {item.name}</span>
              </div>
              {item.notes && (
                <p className="text-xs text-yellow-500/90 italic mt-0.5 ml-4 border-l-2 border-yellow-500/30 pl-2">
                  Obs: {item.notes}
                </p>
              )}
            </li>
          ))}
        </ul>
      </div>

      {/* Status Timestamps */}
      <div className="px-3 pb-2 pl-4 text-xs text-slate-500 border-t border-slate-700/50 pt-2 mx-3">
        <div className="flex items-center gap-2 mb-1">
            <TimerIcon size={12} className="text-blue-400" />
            <span>Recebido: {formatTime(order.createdAt)}</span>
        </div>
        {order.preparingAt && (
          <div className="flex items-center gap-2 mb-1">
            <PlayCircle size={12} className="text-orange-400" />
            <span>Em Preparo: {formatTime(order.preparingAt)}</span>
          </div>
        )}
        {order.readyAt && (
          <div className="flex items-center gap-2 mb-1">
            <Package size={12} className="text-green-400" />
            <span>Pronto: {formatTime(order.readyAt)}</span>
          </div>
        )}
        {order.deliveryAt && (
          <div className="flex items-center gap-2">
            <Truck size={12} className="text-purple-400" />
            <span>Saída: {formatTime(order.deliveryAt)}</span>
          </div>
        )}
      </div>

      {/* Delivery Info (Only if ready or delivery) */}
      {(order.status === OrderStatus.READY || order.status === OrderStatus.DELIVERY) && (
        <div className="px-3 pb-2 pl-4">
           <div className="flex items-center justify-between text-xs bg-slate-900/50 p-2 rounded border border-slate-700/50">
             <div className="flex items-center gap-1.5 text-slate-300">
               <DollarSign size={12} className="text-green-400" />
               <span>Taxa: {order.deliveryFee.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</span>
             </div>
             {order.driverName && (
               <div className="flex items-center gap-1.5 text-blue-300">
                 <Bike size={12} />
                 <span className="truncate max-w-[80px]">{order.driverName.split(' ')[0]}</span>
               </div>
             )}
           </div>
        </div>
      )}

      {/* Footer / Action */}
      {nextStatus && (
        <div className="p-3 pt-0 mt-auto pl-4">
          <button
            onClick={() => onAdvance(order.id, nextStatus)}
            className="w-full flex items-center justify-center gap-2 bg-slate-700 hover:bg-purple-600 text-white py-3 rounded-md transition-colors font-semibold text-sm group"
          >
            <span>Avançar</span>
            <ChevronRight size={16} className="group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      )}
      
      {!nextStatus && (
        <div className="p-3 pt-0 mt-auto pl-4">
             <div className={`w-full flex items-center justify-center gap-2 py-3 rounded-md border border-dashed text-sm ${order.isDriverPaid ? 'bg-green-900/20 border-green-700 text-green-400' : 'bg-slate-800 border-slate-700 text-slate-500'}`}>
            <CheckCircle2 size={16} />
            <span>{order.isDriverPaid ? 'Pago ao Motoboy' : 'Entregue'}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrderCard;