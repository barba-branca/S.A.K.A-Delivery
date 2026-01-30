import React, { useMemo } from 'react';
import { Order, OrderStatus } from '../types';
import { Wallet, CheckCircle, Bike, X } from 'lucide-react';

interface DriverPayoutsProps {
  orders: Order[];
  onPayDriver: (driverName: string) => void;
  onClose: () => void;
}

const DriverPayouts: React.FC<DriverPayoutsProps> = ({ orders, onPayDriver, onClose }) => {
  // Group unpaid delivery orders by driver
  const driverStats = useMemo(() => {
    const stats: Record<string, { count: number; total: number; orderIds: number[] }> = {};

    orders.forEach(order => {
      // Consider only orders OUT for delivery (or delivered) that have a driver and are NOT paid
      if (
        order.status === OrderStatus.DELIVERY && 
        order.driverName && 
        !order.isDriverPaid
      ) {
        if (!stats[order.driverName]) {
          stats[order.driverName] = { count: 0, total: 0, orderIds: [] };
        }
        stats[order.driverName].count += 1;
        stats[order.driverName].total += order.deliveryFee;
        stats[order.driverName].orderIds.push(order.displayId);
      }
    });

    return stats;
  }, [orders]);

  const drivers = Object.keys(driverStats);

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-2xl rounded-2xl shadow-2xl flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-green-600/20 rounded-xl text-green-500">
              <Wallet size={24} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Acerto de Entregadores</h2>
              <p className="text-slate-400 text-sm">Pagamentos pendentes por entregas realizadas</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-slate-800 rounded-full text-slate-400 hover:text-white transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto custom-scrollbar">
          {drivers.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-slate-500 gap-4 border-2 border-dashed border-slate-800 rounded-xl">
              <CheckCircle size={48} className="text-slate-700" />
              <p>Nenhum pagamento pendente no momento.</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {drivers.map(driver => {
                const stat = driverStats[driver];
                return (
                  <div key={driver} className="bg-slate-800/50 border border-slate-700 rounded-xl p-5 flex flex-col sm:flex-row justify-between items-center gap-4 hover:border-slate-600 transition-colors">
                    <div className="flex items-center gap-4 w-full sm:w-auto">
                      <div className="w-12 h-12 bg-slate-700 rounded-full flex items-center justify-center shrink-0">
                        <Bike size={24} className="text-slate-300" />
                      </div>
                      <div>
                        <h3 className="font-bold text-lg text-white">{driver}</h3>
                        <p className="text-sm text-slate-400">
                          {stat.count} entregas pendentes (#{stat.orderIds.join(', #')})
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 w-full sm:w-auto justify-between sm:justify-end">
                      <div className="text-right mr-2">
                        <p className="text-xs text-slate-400 uppercase font-semibold">Total a Pagar</p>
                        <p className="text-2xl font-bold text-green-400">
                          {stat.total.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                        </p>
                      </div>
                      
                      <button
                        onClick={() => onPayDriver(driver)}
                        className="bg-green-600 hover:bg-green-700 text-white px-5 py-3 rounded-lg font-semibold shadow-lg shadow-green-900/20 transition-all active:scale-95 flex items-center gap-2"
                      >
                        <CheckCircle size={18} />
                        Pagar
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-950/50 border-t border-slate-800 text-center rounded-b-2xl">
          <p className="text-xs text-slate-500">
            Dica: Pagamentos confirmados movem o status financeiro do pedido para "Pago".
          </p>
        </div>
      </div>
    </div>
  );
};

export default DriverPayouts;