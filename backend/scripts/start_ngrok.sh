#!/bin/bash
# Script para iniciar ngrok e configurar webhook do Mercado Pago
# Este script inicia o ngrok na porta 8000 (porta do servidor backend)

echo "=========================================="
echo "  Configuração do ngrok para Webhook"
echo "=========================================="
echo ""

# Verifica se o ngrok está instalado
if ! command -v ngrok &> /dev/null; then
    echo "ERRO: ngrok não está instalado!"
    echo "Para instalar, visite: https://ngrok.com/download"
    echo ""
    echo "Ou use o Chocolatey no Windows:"
    echo "  choco install ngrok"
    exit 1
fi

# Verifica se o servidor está rodando
echo "Verificando se o servidor está rodando na porta 8000..."
curl -s http://localhost:8000/health > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERRO: Servidor não está rodando na porta 8000!"
    echo "Inicie o servidor primeiro com: python run.py"
    exit 1
fi

echo "Servidor OK!"
echo ""

# Para qualquer instância anterior do ngrok
echo "Encerrando instâncias anteriores do ngrok..."
pkill -f "ngrok http" 2>/dev/null

# Aguarda um momento
sleep 2

# Inicia o ngrok na porta 8000
echo "Iniciando ngrok na porta 8000..."
ngrok http 8000 --log=stdout > ngrok_url.txt 2>&1 &

# Aguarda o ngrok iniciar
echo "Aguardando ngrok inicializar..."
sleep 5

# Obtém a URL do ngrok
NGROK_URL=$(curl -s localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | cut -d'"' -f4)

if [ -z "$NGROK_URL" ]; then
    # Tenta alternativo - lê do arquivo de log
    NGROK_URL=$(grep -o 'https://[^ ]*\.ngrok-free\.app' ngrok_url.txt | head -1)
fi

if [ -z "$NGROK_URL" ]; then
    echo "ERRO: Não foi possível obter a URL do ngrok!"
    echo "Verifique o painel do ngrok em: http://localhost:4040"
    exit 1
fi

echo ""
echo "=========================================="
echo "  URL do ngrok obtida com sucesso!"
echo "=========================================="
echo ""
echo "URL pública: $NGROK_URL"
echo ""
echo "Agora configure o webhook no painel do Mercado Pago:"
echo ""
echo "1. Acesse: https://www.mercadopago.com.br/developers/panel"
echo "2. Vá em 'Credenciais' > 'Webhooks'"
echo "3. Adicione a seguinte URL:"
echo ""
echo "   ${NGROK_URL}/webhook/mercadopago"
echo ""
echo "4. Marque os eventos:"
echo "   - Payments (Pagamentos)"
echo "   - Order (Mercado Pago)"
echo ""
echo "5. Salve as configurações"
echo ""
echo "=========================================="
echo "  URLs úteis"
echo "=========================================="
echo "Painel do ngrok: http://localhost:4040"
echo "Logs do ngrok:   http://localhost:4040/inspect/http"
echo "API Health:      ${NGROK_URL}/health"
echo ""

# Salva a URL em um arquivo para uso posterior
echo "$NGROK_URL" > .ngrok_url
echo "URL salva em: .ngrok_url"

echo ""
echo "Pressione Ctrl+C para encerrar o ngrok"
