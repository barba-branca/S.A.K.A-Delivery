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
  const getSourceLabel = (source: OrderSource) => {
    switch (source) {
      case OrderSource.WHATSAPP:
        return <div className="bg-[#164B35] text-[#86D8AB] px-2 py-0.5 rounded-[3px] text-[10px] font-semibold tracking-wide">ZAP</div>;
      case OrderSource.IFOOD:
        return <div className="bg-[#5D1F1A] text-[#FF8F85] px-2 py-0.5 rounded-[3px] text-[10px] font-semibold tracking-wide">IFOOD</div>;
      case OrderSource.FOOD99:
        return <div className="bg-[#533F04] text-[#F5CD47] px-2 py-0.5 rounded-[3px] text-[10px] font-semibold tracking-wide">99FOOD</div>;
      default:
        return <div className="bg-[#1C2B41] text-[#85B8FF] px-2 py-0.5 rounded-[3px] text-[10px] font-semibold tracking-wide">APP</div>;
    }
  };

  const getNextStatus = (current: OrderStatus): OrderStatus | null => {
    if (current === OrderStatus.RECEIVED) return OrderStatus.PREPARING;
    if (current === OrderStatus.PREPARING) return OrderStatus.READY;
    if (current === OrderStatus.READY) return OrderStatus.DELIVERY;
    return null;
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
      className="bg-[#22272B] text-[#B6C2CF] rounded-lg shadow-[0_1px_1px_rgba(0,0,0,0.5)] hover:bg-[#282E33] transition-colors flex flex-col animate-in fade-in zoom-in duration-300 relative overflow-hidden cursor-grab active:cursor-grabbing group/card outline outline-1 outline-transparent hover:outline-[#738496]"
    >
      {/* Status Bar for Payment */}
      {order.status === OrderStatus.DELIVERY && (
        <div className={`absolute top-0 left-0 w-[3px] h-full ${order.isDriverPaid ? 'bg-[#7EE218]' : 'bg-[#F5CD47]'}`} />
      )}

      <div className="p-2.5 flex flex-col gap-1.5 pl-3">
        {/* Header: Source and Timer */}
        <div className="flex justify-between items-start">
          <div className="flex gap-1.5">
            {getSourceLabel(order.source)}
          </div>
          <div className="text-[10px] font-medium bg-[#1C2126] px-1.5 py-0.5 rounded text-[#9FADBC] flex items-center gap-1">
            <TimerIcon size={10} />
            <Timer startTime={order.createdAt} />
          </div>
        </div>

        {/* Title */}
        <div className="flex items-start gap-1 mt-0.5">
          <div className="text-[#9FADBC] mt-0.5 -ml-1 opacity-0 group-hover/card:opacity-100 transition-opacity">
            <GripVertical size={14} />
          </div>
          <div>
            <h3 className="text-[13px] font-semibold text-[#DFE1E6] leading-tight">#{order.displayId} - {order.customerName}</h3>
          </div>
        </div>

        {/* Items List */}
        <div className="pl-4 text-[11px] leading-snug flex flex-col gap-0.5 mt-0.5">
          {order.items.map((item, idx) => (
            <div key={idx} className="flex flex-col">
              <span className="text-[#B6C2CF]">{item.quantity}x {item.name}</span>
              {item.notes && (
                <span className="text-[10px] text-[#F5CD47]/90 italic ml-2 border-l border-[#F5CD47]/30 pl-1.5 mt-0.5">
                  Obs: {item.notes}
                </span>
              )}
            </div>
          ))}
        </div>

        {/* Badges and Timestamps */}
        <div className="flex flex-wrap items-center gap-1.5 mt-1.5 pl-4">
          {(order.status === OrderStatus.READY || order.status === OrderStatus.DELIVERY) && (
            <div className="flex items-center gap-1 bg-[#1C2126] px-1.5 py-0.5 rounded text-[10px] border border-[#A1BDD914]">
              <DollarSign size={10} className="text-[#86D8AB]" />
              <span className="font-medium text-[#DFE1E6]">{order.deliveryFee.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</span>
            </div>
          )}
          {order.driverName && (
            <div className="flex items-center gap-1 bg-[#1C2126] px-1.5 py-0.5 rounded text-[10px] border border-[#A1BDD914]">
              <Bike size={10} className="text-[#85B8FF]" />
              <span className="truncate max-w-[60px] font-medium text-[#DFE1E6]">{order.driverName.split(' ')[0]}</span>
            </div>
          )}

          <div className="flex items-center gap-1 text-[10px] text-[#9FADBC] ml-auto">
            {order.preparingAt && <PlayCircle size={10} className="text-[#F5CD47]" title={`Prep: ${formatTime(order.preparingAt)}`} />}
            {order.readyAt && <Package size={10} className="text-[#86D8AB]" title={`Pronto: ${formatTime(order.readyAt)}`} />}
            {order.deliveryAt && <Truck size={10} className="text-[#C9372C]" title={`Saída: ${formatTime(order.deliveryAt)}`} />}
          </div>
        </div>

        {/* Action Button */}
        {nextStatus && (
          <div className="mt-1 pl-4">
            <button
              onClick={() => onAdvance(order.id, nextStatus)}
              className="w-full bg-[#A1BDD914] hover:bg-[#A1BDD929] text-[#DFE1E6] py-1 rounded-[3px] transition-colors font-semibold text-[11px] flex justify-center items-center gap-1 group"
            >
              <span>Avançar</span>
              <ChevronRight size={12} className="group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        )}

        {!nextStatus && (
          <div className="mt-1 pl-4">
            <div className={`w-full flex items-center justify-center gap-1 py-1 rounded-[3px] text-[11px] font-semibold ${order.isDriverPaid ? 'bg-[#164B35] text-[#86D8AB]' : 'bg-[#A1BDD914] text-[#9FADBC]'}`}>
              <CheckCircle2 size={12} />
              <span>{order.isDriverPaid ? 'Pago' : 'Entregue'}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OrderCard;