import React, { useState } from 'react';
import { Order, OrderStatus } from '../types';
import OrderCard from './OrderCard';
import { ClipboardList, ChefHat, CheckCircle, Truck } from 'lucide-react';

interface KanbanBoardProps {
  orders: Order[];
  onUpdateStatus: (id: string, newStatus: OrderStatus) => void;
}

const KanbanBoard: React.FC<KanbanBoardProps> = ({ orders, onUpdateStatus }) => {
  const [dragOverColumn, setDragOverColumn] = useState<OrderStatus | null>(null);

  const columns = [
    {
      id: OrderStatus.RECEIVED,
      title: 'Recebido',
      icon: <ClipboardList size={20} className="text-blue-400" />,
      color: 'border-blue-500/30'
    },
    {
      id: OrderStatus.PREPARING,
      title: 'Em Preparo',
      icon: <ChefHat size={20} className="text-orange-400" />,
      color: 'border-orange-500/30'
    },
    {
      id: OrderStatus.READY,
      title: 'Pronto',
      icon: <CheckCircle size={20} className="text-green-400" />,
      color: 'border-green-500/30'
    },
    {
      id: OrderStatus.DELIVERY,
      title: 'Saiu p/ Entrega',
      icon: <Truck size={20} className="text-purple-400" />,
      color: 'border-purple-500/30'
    },
  ];

  const handleDragStart = (e: React.DragEvent<HTMLDivElement>, orderId: string) => {
    e.dataTransfer.setData('orderId', orderId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>, status: OrderStatus) => {
    e.preventDefault(); // Necessary to allow dropping
    if (dragOverColumn !== status) {
      setDragOverColumn(status);
    }
  };

  const handleDragLeave = () => {
    setDragOverColumn(null);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>, status: OrderStatus) => {
    e.preventDefault();
    setDragOverColumn(null);
    const orderId = e.dataTransfer.getData('orderId');
    if (orderId) {
      onUpdateStatus(orderId, status);
    }
  };

  return (
    <div className="flex-grow p-4 overflow-x-auto min-h-0">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 min-w-[1000px] h-full items-start">
        {columns.map((col) => {
          const colOrders = orders.filter(o => o.status === col.id);
          const isDragOver = dragOverColumn === col.id;

          return (
            <div
              key={col.id}
              onDragOver={(e) => handleDragOver(e, col.id)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, col.id)}
              className={`flex flex-col bg-[#101204] rounded-[12px] max-h-full border transition-colors duration-200 ${isDragOver ? 'border-[#85B8FF] bg-[#1C2126]' : 'border-[#A1BDD914]'
                }`}
            >
              {/* Column Header */}
              <div className="px-3 py-2.5 flex justify-between items-center bg-transparent rounded-t-[12px] sticky top-0 z-10 shrink-0">
                <div className="flex items-center gap-2">
                  {col.icon}
                  <h2 className={`text-[14px] font-semibold transition-colors ${isDragOver ? 'text-[#85B8FF]' : 'text-[#DFE1E6]'}`}>
                    {col.title}
                  </h2>
                </div>
                <span className="bg-[#A1BDD914] text-[#9FADBC] text-[11px] font-semibold px-2 py-0.5 rounded-[20px]">
                  {colOrders.length}
                </span>
              </div>

              {/* Column Content */}
              <div className="flex-1 px-1.5 pb-2 overflow-y-auto space-y-2 min-h-0 custom-scrollbar">
                {colOrders.length === 0 ? (
                  <div className={`h-32 flex items-center justify-center text-slate-600 text-sm border-2 border-dashed rounded-lg transition-colors ${isDragOver ? 'border-purple-500/50 bg-purple-500/10 text-purple-300' : 'border-slate-800'
                    }`}>
                    {isDragOver ? 'Soltar aqui' : 'Vazio'}
                  </div>
                ) : (
                  colOrders.map(order => (
                    <OrderCard
                      key={order.id}
                      order={order}
                      onAdvance={onUpdateStatus}
                      onDragStart={handleDragStart}
                    />
                  ))
                )}
                {/* Visual placeholder for drop area at bottom of list */}
                {isDragOver && colOrders.length > 0 && (
                  <div className="h-24 rounded-lg border-2 border-dashed border-purple-500/50 bg-purple-500/10 flex items-center justify-center text-purple-300 text-sm animate-pulse">
                    Soltar aqui
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default KanbanBoard;