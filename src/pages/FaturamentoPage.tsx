import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { QrCode, CreditCard, Wallet, Copy, Check, AlertCircle, RefreshCw, DollarSign, Activity, Zap } from 'lucide-react';
import QRCodeLib from 'qrcode';
import PaymentModal from '../components/PaymentModal';

interface FaturamentoData {
    saldoAtual: number;
    valorCredito: number;
    chavePix: string;
    codigoPix: string;
    txid: string;
    status: string;
}

const FaturamentoPage: React.FC = () => {
    const { user, token } = useAuth();
    const [loading, setLoading] = useState(false);
    const [valor, setValor] = useState<string>('100.00');
    const [faturamento, setFaturamento] = useState<FaturamentoData | null>(null);
    const [copied, setCopied] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [historico, setHistorico] = useState<any[]>([]);
    const [consumo, setConsumo] = useState<any[]>([]);
    const [qrCodeUrl, setQrCodeUrl] = useState<string>('');
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [showPaymentModal, setShowPaymentModal] = useState(false);

    // Valores pré-definidos
    const valoresPredefinidos = [
        { valor: 50, label: 'R$ 50' },
        { valor: 100, label: 'R$ 100' },
        { valor: 200, label: 'R$ 200' },
        { valor: 500, label: 'R$ 500' },
        { valor: 1000, label: 'R$ 1.000' },
    ];

    const gerarQRCode = async () => {
        if (!token || !user) return;

        const valorNum = parseFloat(valor);
        if (isNaN(valorNum) || valorNum <= 0) {
            setError('Valor inválido');
            return;
        }

        setShowPaymentModal(true);
    };

    const copiarCodigo = () => {
        if (faturamento?.codigoPix) {
            navigator.clipboard.writeText(faturamento.codigoPix);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    const carregarHistorico = async () => {
        if (!token || !user) return;

        try {
            const response = await fetch(`http://localhost:8000/faturamento/historico/${user.id}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                setHistorico(data.historico || []);
            }

            // Buscar histórico de consumo de créditos (pedidos)
            const responsePedidos = await fetch(`http://localhost:8000/pedidos?limit=10`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (responsePedidos.ok) {
                const pedidosData = await responsePedidos.json();
                setConsumo(pedidosData || []);
            }
        } catch (err) {
            console.error('Erro ao carregar histórico:', err);
        }
    };

    useEffect(() => {
        carregarHistorico();
    }, [token, user]);

    if (!user) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center text-slate-400">
                    <AlertCircle className="w-12 h-12 mx-auto mb-4" />
                    <p>Faça login para acessar o faturamento</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full bg-slate-950 text-slate-100 overflow-hidden relative">
            {/* Background Effects */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-lg h-64 bg-purple-600/20 blur-[100px] pointer-events-none rounded-full"></div>

            {/* Header */}
            <header className="h-20 bg-slate-900/80 backdrop-blur-xl border-b border-white/5 flex items-center justify-center shrink-0 z-10 px-6">
                <div className="w-full max-w-4xl flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl shadow-lg shadow-purple-500/20 text-white">
                            <Wallet className="w-5 h-5" />
                        </div>
                        <h1 className="font-bold text-lg bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">Minha Carteira</h1>
                    </div>

                    <div className="text-right flex flex-col items-end justify-center">
                        <p className="text-[10px] text-slate-400 uppercase tracking-widest font-semibold flex items-center gap-1 mb-1"><Zap size={10} className="text-emerald-400" /> Saldo Disponível</p>
                        <p className="text-base font-semibold text-emerald-400 drop-shadow-[0_0_8px_rgba(52,211,153,0.3)] leading-none">
                            R$ {(user.saldoCredito || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </p>
                        <p className="text-[10px] text-purple-400/80 font-medium uppercase tracking-wide mt-1">
                            Equivale a {Math.floor((user.saldoCredito || 0) / 5)} entregas
                        </p>
                    </div>
                </div>
            </header>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6 z-10 relative">
                <div className="max-w-4xl mx-auto space-y-6">

                    {/* Card Principal - Gerar QR Code */}
                    <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-3xl p-8 relative overflow-hidden group hover:border-purple-500/50 transition-colors">
                        <div className="absolute -top-24 -right-24 w-48 h-48 bg-purple-600/20 blur-3xl rounded-full group-hover:bg-purple-600/30 transition-all"></div>
                        <h2 className="text-lg font-bold mb-6 flex items-center gap-2 text-white">
                            <QrCode className="w-5 h-5 text-purple-400" />
                            Adicionar Créditos
                        </h2>

                        {/* Valores Pré-definidos */}
                        <div className="mb-6">
                            <label className="block text-sm text-slate-400 mb-2">Valores Rápidos</label>
                            <div className="flex flex-wrap gap-2">
                                {valoresPredefinidos.map((v) => (
                                    <button
                                        key={v.valor}
                                        onClick={() => setValor(v.valor.toString())}
                                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${valor === v.valor.toString()
                                            ? 'bg-gradient-to-r from-purple-500 to-indigo-600 text-white shadow-lg shadow-purple-500/25 border border-purple-400/50'
                                            : 'bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10'
                                            }`}
                                    >
                                        {v.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Input de Valor */}
                        <div className="mb-4">
                            <label className="block text-sm text-slate-400 mb-2">Valor Personalizado (R$)</label>
                            <div className="relative">
                                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                                <input
                                    type="number"
                                    value={valor}
                                    onChange={(e) => setValor(e.target.value)}
                                    step="0.01"
                                    min="1"
                                    max="10000"
                                    className="w-full bg-black/40 border border-white/10 rounded-xl py-4 pl-12 pr-4 text-white text-xl font-medium focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50 transition-all"
                                    placeholder="0,00"
                                />
                            </div>
                        </div>

                        {error && (
                            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
                                {error}
                            </div>
                        )}

                        {/* Botão Gerar */}
                        <button
                            onClick={gerarQRCode}
                            disabled={loading}
                            className="w-full bg-white text-black hover:bg-slate-200 disabled:bg-slate-700 disabled:text-slate-400 font-bold py-4 rounded-xl transition-all flex items-center justify-center gap-2 mt-6 shadow-[0_0_20px_rgba(255,255,255,0.1)]"
                        >
                            {loading ? (
                                <>
                                    <RefreshCw className="w-5 h-5 animate-spin" />
                                    Processando Transação...
                                </>
                            ) : (
                                <>
                                    <QrCode className="w-5 h-5" />
                                    Gerar Pagamento Seguro
                                </>
                            )}
                        </button>
                    </div>

                    {/* QR Code e Informações de Pagamento */}
                    {faturamento && (
                        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                            <div className="flex flex-col md:flex-row gap-6">

                                {/* QR Code Visual */}
                                <div className="flex flex-col items-center justify-center p-4 bg-white rounded-xl">
                                    {qrCodeUrl ? (
                                        <img
                                            src={qrCodeUrl}
                                            alt="QR Code PIX"
                                            className="w-48 h-48"
                                        />
                                    ) : (
                                        <div className="w-48 h-48 bg-slate-900 flex items-center justify-center rounded-lg">
                                            <QrCode className="w-32 h-32 text-slate-900" />
                                        </div>
                                    )}
                                    <p className="mt-2 text-xs text-slate-600 text-center">
                                        Escaneie com seu banco
                                    </p>
                                </div>

                                {/* Informações do Pagamento */}
                                <div className="flex-1 space-y-4">
                                    <div className="flex items-center justify-between">
                                        <span className="text-slate-400">Status</span>
                                        <span className={`px-3 py-1 rounded-full text-xs font-bold ${faturamento.status === 'PAGO'
                                            ? 'bg-emerald-500/20 text-emerald-400'
                                            : 'bg-amber-500/20 text-amber-400'
                                            }`}>
                                            {faturamento.status === 'PAGO' ? '✓ Pago' : '⏳ Pendente'}
                                        </span>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <span className="text-slate-400">Valor</span>
                                        <span className="text-2xl font-bold text-emerald-400">
                                            R$ {faturamento.valorCredito.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                        </span>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <span className="text-slate-400">Chave PIX</span>
                                        <span className="text-sm font-mono">{faturamento.chavePix}</span>
                                    </div>

                                    <div className="flex items-center justify-between">
                                        <span className="text-slate-400">Transaction ID</span>
                                        <span className="text-sm font-mono text-slate-500">{faturamento.txid}</span>
                                    </div>

                                    {/* Código PIX Copiável */}
                                    <div className="mt-4">
                                        <label className="block text-sm text-slate-400 mb-2">Código PIX (Copia e Cola)</label>
                                        <div className="flex gap-2">
                                            <input
                                                type="text"
                                                value={faturamento.codigoPix}
                                                readOnly
                                                className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs font-mono text-slate-400"
                                            />
                                            <button
                                                onClick={copiarCodigo}
                                                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
                                            >
                                                {copied ? <Check className="w-5 h-5 text-emerald-400" /> : <Copy className="w-5 h-5 text-slate-400" />}
                                            </button>
                                        </div>
                                    </div>

                                    {/* Instruções */}
                                    <div className="mt-4 p-4 bg-purple-900/20 border border-purple-500/30 rounded-xl">
                                        <h4 className="font-bold text-purple-300 mb-2">Como pagar:</h4>
                                        <ol className="text-sm text-purple-400/80 space-y-1 list-decimal list-inside">
                                            <li>Abra o aplicativo do seu banco</li>
                                            <li>Escolha a opção PIX Copia e Cola</li>
                                            <li>Cole o código acima ou escaneie o QR Code</li>
                                            <li>Confirme o pagamento de R$ {faturamento.valorCredito.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</li>
                                            <li>Seu crédito será adicionado automaticamente</li>
                                        </ol>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="grid md:grid-cols-2 gap-6">
                        {/* Histórico de Consumo */}
                        <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-3xl p-6">
                            <h2 className="text-lg font-bold mb-4 flex items-center gap-2 text-white">
                                <Activity className="w-5 h-5 text-emerald-400" />
                                Histórico de Consumo
                            </h2>

                            {consumo.length === 0 ? (
                                <div className="text-center py-8 text-slate-500">
                                    <Activity className="w-12 h-12 mx-auto mb-2 opacity-20" />
                                    <p>Nenhum consumo registrado</p>
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {consumo.map((item: any, index: number) => (
                                        <div key={index} className="flex flex-col p-4 bg-white/5 border border-white/5 rounded-2xl hover:bg-white/10 transition-colors">
                                            <div className="flex justify-between items-start mb-2">
                                                <span className="font-bold text-white">Pedido #{item.id}</span>
                                                <span className="text-rose-400 font-medium">-{item.valor_consumido?.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</span>
                                            </div>
                                            <div className="flex justify-between items-center text-xs text-slate-400">
                                                <span>{new Date(item.data).toLocaleString('pt-BR')}</span>
                                                <span className="bg-purple-500/20 text-purple-300 px-2 py-1 rounded-md">Logística S.A.K.A.</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Histórico de Recargas e Informações */}
                        <div className="space-y-6">
                            <div className="bg-slate-900/50 backdrop-blur-md border border-white/10 rounded-3xl p-6">
                                <h2 className="text-lg font-bold mb-4 flex items-center gap-2 text-white">
                                    <CreditCard className="w-5 h-5 text-purple-400" />
                                    Últimas Recargas
                                </h2>

                                {historico.length === 0 ? (
                                    <div className="text-center py-8 text-slate-500">
                                        <Wallet className="w-12 h-12 mx-auto mb-2 opacity-20" />
                                        <p>Nenhuma recarga realizada ainda</p>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {historico.slice(0, 5).map((item: any, index: number) => (
                                            <div key={index} className="flex items-center justify-between p-4 bg-white/5 border border-white/5 rounded-2xl">
                                                <div>
                                                    <p className="font-bold text-white text-lg">R$ {item.valor?.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>
                                                    <p className="text-xs text-slate-400">{item.data}</p>
                                                </div>
                                                <span className={`px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-wider ${item.status === 'PAGO' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                                                    }`}>
                                                    {item.status}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Informações do Plano */}
                    <div className="bg-gradient-to-r from-purple-900/40 to-indigo-900/40 border border-purple-500/20 rounded-3xl p-8 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-8 w-64 h-64 bg-white/5 rounded-full blur-3xl mix-blend-overlay pointer-events-none"></div>
                        <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-white">
                            <Zap className="w-6 h-6 text-emerald-400" />
                            Status do Sistema
                        </h2>

                        <div className="grid md:grid-cols-2 gap-6 relative z-10">
                            <div className="p-5 bg-black/20 rounded-2xl border border-white/5">
                                <p className="text-emerald-400 text-xs font-bold uppercase tracking-widest mb-1">Modulo Ativo</p>
                                <p className="text-2xl font-black text-white">SaaS Integrado</p>
                            </div>
                            <div className="p-5 bg-black/20 rounded-2xl border border-white/5">
                                <p className="text-purple-400 text-xs font-bold uppercase tracking-widest mb-1">Custo Operacional</p>
                                <p className="text-2xl font-black text-white">5 Créditos / Pedido</p>
                            </div>
                        </div>

                        <p className="mt-6 text-sm text-slate-300 font-medium leading-relaxed">
                            O sistema de logística inteligente da S.A.K.A garante entregas eficientes de ponta a ponta.
                            Seus créditos são deduzidos automaticamente otimizando seu fluxo de caixa na nuvem.
                        </p>
                    </div>
                </div>
            </div>

            {/* Payment Modal */}
            <PaymentModal
                isOpen={showPaymentModal}
                onClose={() => setShowPaymentModal(false)}
                valor={parseFloat(valor) || 0}
            />
        </div>
    );
};
export default FaturamentoPage;
