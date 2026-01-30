import React, { useState, useEffect } from 'react';
import Login from './components/Login';
import KanbanBoard from './components/KanbanBoard';
import DriverPayouts from './components/DriverPayouts';
import { User, Order, OrderStatus, OrderSource, UserRole } from './types';
import * as db from './services/mockDb';
import { LogOut, Plus, RefreshCw, Wallet } from 'lucide-react';

const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [lastUpdated, setLastUpdated] = useState<number>(Date.now());
  const [showPayouts, setShowPayouts] = useState(false);

  // Load orders on mount or update
  useEffect(() => {
    if (user) {
      const data = db.getOrders();
      setOrders(data);
    }
  }, [user, lastUpdated]);

  const handleLogin = (loggedInUser: User) => {
    setUser(loggedInUser);
  };

  const handleLogout = () => {
    setUser(null);
  };

  const handleStatusUpdate = (orderId: string, newStatus: OrderStatus) => {
    const updated = db.updateOrderStatus(orderId, newStatus);
    setOrders(updated);
  };

  const handlePayDriver = (driverName: string) => {
    const updated = db.markDriverAsPaid(driverName);
    setOrders(updated);
    // Don't close immediately so user can pay others
  };

  // Function to simulate a new order coming in (Demonstration purposes)
  const simulateNewOrder = () => {
    const newOrder: Order = {
      id: Date.now().toString(),
      displayId: Math.floor(1000 + Math.random() * 9000),
      customerName: ['Ana', 'Carlos', 'Beatriz', 'Lucas'][Math.floor(Math.random() * 4)] + ' ' + ['Lima', 'Pereira', 'Costa'][Math.floor(Math.random() * 3)],
      source: Math.random() > 0.5 ? OrderSource.IFOOD : OrderSource.WHATSAPP,
      status: OrderStatus.RECEIVED,
      items: [
        { name: 'Açaí Tradicional', quantity: 1, notes: Math.random() > 0.7 ? 'Capricha' : undefined }
      ],
      createdAt: Date.now(),
      deliveryFee: [5.00, 7.00, 10.00, 3.50][Math.floor(Math.random() * 4)],
      driverName: undefined,
      isDriverPaid: false
    };
    const updated = db.createOrder(newOrder);
    setOrders(updated);
  };

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div className="flex flex-col h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Top Bar */}
      <header className="h-16 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-6 shrink-0 z-20 relative">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center">
            <span className="font-bold text-white">S</span>
          </div>
          <h1 className="font-bold text-xl tracking-tight hidden md:block">Saka KDS</h1>
          <span className="px-2 py-0.5 bg-slate-800 rounded text-xs text-slate-400 border border-slate-700">
            {user.role} VIEW
          </span>
        </div>

        <div className="flex items-center gap-4">
          {user.role === UserRole.ADMIN && (
            <button
              onClick={() => setShowPayouts(true)}
              className="flex items-center gap-2 text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-3 py-2 rounded-lg transition-colors border border-slate-700"
              title="Financeiro"
            >
              <Wallet size={18} />
              <span className="hidden sm:inline text-sm font-medium">Financeiro</span>
            </button>
          )}

          <div className="h-6 w-px bg-slate-700 mx-1"></div>

          <button 
            onClick={() => setLastUpdated(Date.now())}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-full transition-colors"
            title="Atualizar"
          >
            <RefreshCw size={20} />
          </button>
          
          <button 
            onClick={simulateNewOrder}
            className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors shadow-lg shadow-purple-900/20"
          >
            <Plus size={16} />
            <span className="hidden sm:inline">Novo Pedido</span>
          </button>

          <div className="h-6 w-px bg-slate-700 mx-2"></div>

          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-medium text-white">{user.username}</p>
              <p className="text-xs text-slate-500">Logado</p>
            </div>
            <button 
              onClick={handleLogout}
              className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-950/30 rounded-full transition-colors"
              title="Sair"
            >
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Board Area */}
      <KanbanBoard orders={orders} onUpdateStatus={handleStatusUpdate} />

      {/* Driver Payouts Modal */}
      {showPayouts && (
        <DriverPayouts 
          orders={orders} 
          onPayDriver={handlePayDriver} 
          onClose={() => setShowPayouts(false)} 
        />
      )}
    </div>
  );
};

export default App;