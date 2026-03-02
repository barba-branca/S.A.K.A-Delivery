import React, { useState } from 'react';
import { X, Plus, Trash2, Zap } from 'lucide-react';
import { Order, OrderSource, OrderStatus, OrderItem } from '../types';

interface NewOrderModalProps {
    onClose: () => void;
    onCreateOrder: (order: Order) => void;
    onSimulateOrder: () => void;
}

const NewOrderModal: React.FC<NewOrderModalProps> = ({ onClose, onCreateOrder, onSimulateOrder }) => {
    const [customerName, setCustomerName] = useState('');
    const [source, setSource] = useState<OrderSource>(OrderSource.WHATSAPP);
    const [deliveryFee, setDeliveryFee] = useState<string>('5.00');
    const [items, setItems] = useState<OrderItem[]>([{ name: '', quantity: 1 }]);

    const handleAddItem = () => {
        setItems([...items, { name: '', quantity: 1 }]);
    };

    const handleRemoveItem = (index: number) => {
        setItems(items.filter((_, i) => i !== index));
    };

    const handleItemChange = (index: number, field: keyof OrderItem, value: any) => {
        const newItems = [...items];
        newItems[index] = { ...newItems[index], [field]: value };
        setItems(newItems);
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (!customerName.trim() || items.some(item => !item.name.trim())) {
            alert('Por favor, preencha o nome do cliente e pelo menos um item.');
            return;
        }

        const newOrder: Order = {
            id: Date.now().toString(),
            displayId: Math.floor(1000 + Math.random() * 9000),
            customerName: customerName.trim(),
            source,
            status: OrderStatus.RECEIVED,
            items: items.map(item => ({ ...item, name: item.name.trim() })),
            createdAt: Date.now(),
            deliveryFee: parseFloat(deliveryFee) || 0,
            isDriverPaid: false
        };

        onCreateOrder(newOrder);
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
                <div className="p-6 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                        <Plus className="text-purple-500" size={24} />
                        Novo Pedido
                    </h2>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-slate-800 rounded-full transition-colors text-slate-400 hover:text-white"
                    >
                        <X size={20} />
                    </button>
                </div>

                <div className="p-6 overflow-y-auto flex-1 space-y-6">
                    {/* Quick Simulate Option */}
                    <div className="bg-purple-900/20 border border-purple-500/30 rounded-xl p-4 flex items-center justify-between">
                        <div>
                            <p className="text-sm font-semibold text-purple-300">Gerar Pedido de Teste</p>
                            <p className="text-xs text-purple-400/80">Gerar um pedido aleatório automaticamente</p>
                        </div>
                        <button
                            onClick={() => {
                                onSimulateOrder();
                                onClose();
                            }}
                            className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm font-bold transition-all active:scale-95 shadow-lg shadow-purple-900/40"
                        >
                            <Zap size={16} />
                            Gerar Teste
                        </button>
                    </div>

                    <div className="relative">
                        <div className="absolute inset-0 flex items-center" aria-hidden="true">
                            <div className="w-full border-t border-slate-800"></div>
                        </div>
                        <div className="relative flex justify-center text-xs uppercase">
                            <span className="bg-slate-900 px-2 text-slate-500 font-bold tracking-widest">Ou Entrada Manual</span>
                        </div>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="col-span-2">
                                <label className="block text-xs font-bold text-slate-500 uppercase mb-1.5 ml-1">Cliente</label>
                                <input
                                    type="text"
                                    value={customerName}
                                    onChange={(e) => setCustomerName(e.target.value)}
                                    placeholder="Nome do cliente"
                                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-slate-500 uppercase mb-1.5 ml-1">Origem</label>
                                <select
                                    value={source}
                                    onChange={(e) => setSource(e.target.value as OrderSource)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all appearance-none"
                                >
                                    <option value={OrderSource.WHATSAPP}>WhatsApp</option>
                                    <option value={OrderSource.IFOOD}>iFood</option>
                                    <option value={OrderSource.FOOD99}>99Food</option>
                                    <option value={OrderSource.UBER}>Uber Eats</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-slate-500 uppercase mb-1.5 ml-1">Taxa Entrega (R$)</label>
                                <input
                                    type="number"
                                    step="0.50"
                                    value={deliveryFee}
                                    onChange={(e) => setDeliveryFee(e.target.value)}
                                    className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500 transition-all"
                                />
                            </div>
                        </div>

                        <div className="space-y-3">
                            <div className="flex items-center justify-between ml-1">
                                <label className="text-xs font-bold text-slate-500 uppercase">Itens do Pedido</label>
                                <button
                                    type="button"
                                    onClick={handleAddItem}
                                    className="text-xs font-bold text-purple-400 hover:text-purple-300 flex items-center gap-1 transition-colors"
                                >
                                    <Plus size={14} /> Adicionar Item
                                </button>
                            </div>

                            {items.map((item, index) => (
                                <div key={index} className="flex gap-2 items-start animate-in fade-in slide-in-from-top-2 duration-200">
                                    <div className="flex-1">
                                        <input
                                            type="text"
                                            value={item.name}
                                            onChange={(e) => handleItemChange(index, 'name', e.target.value)}
                                            placeholder="Nome do item (ex: Açaí 500ml)"
                                            className="w-full bg-slate-800 border border-slate-700 rounded-xl px-4 py-2 text-sm text-white focus:outline-none focus:border-purple-500 transition-all"
                                            required
                                        />
                                    </div>
                                    <div className="w-20">
                                        <input
                                            type="number"
                                            min="1"
                                            value={item.quantity}
                                            onChange={(e) => handleItemChange(index, 'quantity', parseInt(e.target.value) || 1)}
                                            className="w-full bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white text-center focus:outline-none focus:border-purple-500 transition-all"
                                        />
                                    </div>
                                    {items.length > 1 && (
                                        <button
                                            type="button"
                                            onClick={() => handleRemoveItem(index)}
                                            className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-all"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>

                        <div className="pt-4">
                            <button
                                type="submit"
                                className="w-full bg-purple-600 hover:bg-purple-700 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-purple-900/20 active:scale-[0.98]"
                            >
                                Criar Pedido Manual
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default NewOrderModal;
