import React, { useState, useEffect, useCallback, useRef } from 'react';
import { X, Copy, Check, QrCode, RefreshCw, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import QRCodeLib from 'qrcode';
import { createPixPaymentAPI, checkPaymentStatusAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

interface PaymentModalProps {
    isOpen: boolean;
    onClose: () => void;
    valor: number;
}

type ModalStep = 'generating' | 'awaiting' | 'approved' | 'error';

const PaymentModal: React.FC<PaymentModalProps> = ({ isOpen, onClose, valor }) => {
    const { refreshUser } = useAuth();
    const [step, setStep] = useState<ModalStep>('generating');
    const [qrCodeUrl, setQrCodeUrl] = useState('');
    const [copiaCola, setCopiaCola] = useState('');
    const [transactionId, setTransactionId] = useState<number | null>(null);
    const [copied, setCopied] = useState(false);
    const [errorMsg, setErrorMsg] = useState('');
    const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

    // Gerar pagamento ao abrir o modal
    useEffect(() => {
        if (!isOpen) return;

        setStep('generating');
        setQrCodeUrl('');
        setCopiaCola('');
        setTransactionId(null);
        setErrorMsg('');
        setCopied(false);

        const generatePayment = async () => {
            try {
                const data = await createPixPaymentAPI(valor);

                setTransactionId(data.transaction_id);
                setCopiaCola(data.copia_cola);

                // Gerar QR Code visual a partir do copia_cola
                if (data.qr_code_base64) {
                    setQrCodeUrl(`data:image/png;base64,${data.qr_code_base64}`);
                } else {
                    try {
                        const qrDataUrl = await QRCodeLib.toDataURL(data.qr_code, {
                            width: 280,
                            margin: 2,
                            color: { dark: '#000000', light: '#FFFFFF' },
                            errorCorrectionLevel: 'M',
                        });
                        setQrCodeUrl(qrDataUrl);
                    } catch {
                        setQrCodeUrl('');
                    }
                }

                setStep('awaiting');
            } catch (err: any) {
                setErrorMsg(
                    err.response?.data?.detail || err.message || 'Erro ao gerar pagamento'
                );
                setStep('error');
            }
        };

        generatePayment();
    }, [isOpen, valor]);

    // Polling de status
    useEffect(() => {
        if (step !== 'awaiting' || !transactionId) return;

        const poll = async () => {
            try {
                const data = await checkPaymentStatusAPI(transactionId);
                if (data.status === 'approved') {
                    setStep('approved');
                    await refreshUser();
                    if (pollingRef.current) {
                        clearInterval(pollingRef.current);
                        pollingRef.current = null;
                    }
                } else if (data.status === 'cancelled') {
                    setErrorMsg('Pagamento cancelado ou expirado');
                    setStep('error');
                    if (pollingRef.current) {
                        clearInterval(pollingRef.current);
                        pollingRef.current = null;
                    }
                }
            } catch {
                // Silently retry
            }
        };

        pollingRef.current = setInterval(poll, 3000);

        return () => {
            if (pollingRef.current) {
                clearInterval(pollingRef.current);
                pollingRef.current = null;
            }
        };
    }, [step, transactionId, refreshUser]);

    // Limpar polling ao fechar
    useEffect(() => {
        if (!isOpen && pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
        }
    }, [isOpen]);

    const handleCopy = useCallback(() => {
        if (copiaCola) {
            navigator.clipboard.writeText(copiaCola);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    }, [copiaCola]);

    const handleClose = useCallback(() => {
        if (pollingRef.current) {
            clearInterval(pollingRef.current);
            pollingRef.current = null;
        }
        onClose();
    }, [onClose]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/70 backdrop-blur-sm"
                onClick={handleClose}
            />

            {/* Modal */}
            <div className="relative w-full max-w-md mx-4 bg-slate-900 border border-white/10 rounded-3xl shadow-2xl shadow-purple-500/10 overflow-hidden animate-in fade-in zoom-in duration-300">
                {/* Header */}
                <div className="flex items-center justify-between p-6 pb-4 border-b border-white/5">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl text-white">
                            <QrCode className="w-5 h-5" />
                        </div>
                        <div>
                            <h2 className="font-bold text-white text-lg">Pagamento PIX</h2>
                            <p className="text-sm text-slate-400">
                                R$ {valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={handleClose}
                        className="p-2 rounded-xl hover:bg-white/10 transition-colors text-slate-400 hover:text-white"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-5">

                    {/* Step: Generating */}
                    {step === 'generating' && (
                        <div className="flex flex-col items-center justify-center py-12 space-y-4">
                            <div className="relative">
                                <div className="w-16 h-16 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin" />
                            </div>
                            <p className="text-slate-300 font-medium">Gerando pagamento PIX...</p>
                            <p className="text-xs text-slate-500">Conectando ao Mercado Pago</p>
                        </div>
                    )}

                    {/* Step: Awaiting Payment */}
                    {step === 'awaiting' && (
                        <>
                            {/* QR Code */}
                            <div className="flex justify-center">
                                <div className="bg-white rounded-2xl p-3 shadow-lg shadow-purple-500/10">
                                    {qrCodeUrl ? (
                                        <img
                                            src={qrCodeUrl}
                                            alt="QR Code PIX"
                                            className="w-56 h-56 rounded-lg"
                                        />
                                    ) : (
                                        <div className="w-56 h-56 flex items-center justify-center bg-gray-100 rounded-lg">
                                            <QrCode className="w-24 h-24 text-gray-300" />
                                        </div>
                                    )}
                                </div>
                            </div>

                            <p className="text-center text-xs text-slate-500">
                                Escaneie o QR Code com o app do seu banco
                            </p>

                            {/* Copy PIX Key */}
                            <button
                                onClick={handleCopy}
                                className={`w-full flex items-center justify-center gap-2 py-3.5 rounded-xl font-semibold text-sm transition-all ${copied
                                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                                        : 'bg-white/5 text-white border border-white/10 hover:bg-white/10 hover:border-purple-500/40'
                                    }`}
                            >
                                {copied ? (
                                    <>
                                        <Check className="w-4 h-4" />
                                        Chave PIX Copiada!
                                    </>
                                ) : (
                                    <>
                                        <Copy className="w-4 h-4" />
                                        Copiar Chave PIX
                                    </>
                                )}
                            </button>

                            {/* Processing status */}
                            <div className="flex items-center justify-center gap-2 py-3 px-4 bg-amber-500/10 border border-amber-500/20 rounded-xl">
                                <Loader2 className="w-4 h-4 text-amber-400 animate-spin" />
                                <span className="text-sm font-medium text-amber-400">
                                    Processando Pagamento...
                                </span>
                            </div>

                            <p className="text-center text-[11px] text-slate-500 leading-relaxed">
                                Após o pagamento, seus créditos serão adicionados automaticamente.
                                <br />
                                Verificamos o status a cada 3 segundos.
                            </p>
                        </>
                    )}

                    {/* Step: Approved */}
                    {step === 'approved' && (
                        <div className="flex flex-col items-center justify-center py-8 space-y-4">
                            <div className="p-4 bg-emerald-500/20 rounded-full border border-emerald-500/30">
                                <CheckCircle className="w-12 h-12 text-emerald-400" />
                            </div>
                            <h3 className="text-xl font-bold text-emerald-400">
                                Pagamento Confirmado!
                            </h3>
                            <p className="text-slate-400 text-sm text-center">
                                R$ {valor.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} adicionados
                                ao seu saldo de créditos.
                            </p>
                            <button
                                onClick={handleClose}
                                className="mt-4 w-full py-3.5 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white font-bold rounded-xl hover:from-emerald-600 hover:to-emerald-700 transition-all shadow-lg shadow-emerald-500/20"
                            >
                                Fechar
                            </button>
                        </div>
                    )}

                    {/* Step: Error */}
                    {step === 'error' && (
                        <div className="flex flex-col items-center justify-center py-8 space-y-4">
                            <div className="p-4 bg-red-500/20 rounded-full border border-red-500/30">
                                <AlertCircle className="w-12 h-12 text-red-400" />
                            </div>
                            <h3 className="text-xl font-bold text-red-400">
                                Erro no Pagamento
                            </h3>
                            <p className="text-slate-400 text-sm text-center">
                                {errorMsg}
                            </p>
                            <button
                                onClick={handleClose}
                                className="mt-4 w-full py-3.5 bg-white/5 border border-white/10 text-white font-bold rounded-xl hover:bg-white/10 transition-all"
                            >
                                Fechar
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default PaymentModal;
