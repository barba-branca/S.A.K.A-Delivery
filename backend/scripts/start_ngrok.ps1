# Script PowerShell para iniciar ngrok e configurar webhook do Mercado Pago
# Este script inicia o ngrok na porta 8000 (porta do servidor backend)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Configuracao do ngrok para Webhook" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verifica se o ngrok está instalado
$ngrokPath = Get-Command ngrok -ErrorAction SilentlyContinue
if (-not $ngrokPath) {
    Write-Host "ERRO: ngrok nao esta instalado!" -ForegroundColor Red
    Write-Host "Para instalar, visite: https://ngrok.com/download" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Ou use o Chocolatey no Windows:" -ForegroundColor Yellow
    Write-Host "  choco install ngrok" -ForegroundColor Yellow
    exit 1
}

# Verifica se o servidor está rodando
Write-Host "Verificando se o servidor esta rodando na porta 8000..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -ne 200) {
        throw "Servidor retornou status diferente de 200"
    }
} catch {
    Write-Host "ERRO: Servidor nao esta rodando na porta 8000!" -ForegroundColor Red
    Write-Host "Inicie o servidor primeiro com: python run.py" -ForegroundColor Yellow
    exit 1
}

Write-Host "Servidor OK!" -ForegroundColor Green
Write-Host ""

# Para qualquer instância anterior do ngrok
Write-Host "Encerrando instancias anteriores do ngrok..." -ForegroundColor Yellow
Get-Process -Name "ngrok" -ErrorAction SilentlyContinue | Stop-Process -Force

# Aguarda um momento
Start-Sleep -Seconds 2

# Inicia o ngrok na porta 8000
Write-Host "Iniciando ngrok na porta 8000..." -ForegroundColor Yellow
Start-Process -FilePath "ngrok" -ArgumentList "http 8000" -NoNewWindow -PassThru

# Aguarda o ngrok iniciar
Write-Host "Aguardando ngrok inicializar..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Obtém a URL do ngrok
try {
    $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -TimeoutSec 10
    $NGROK_URL = $tunnels.tunnels[0].public_url
} catch {
    Write-Host "Aviso: Nao foi possivel obter URL via API. Tentando metodo alternativo..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    try {
        $tunnels = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -TimeoutSec 10
        $NGROK_URL = $tunnels.tunnels[0].public_url
    } catch {
        $NGROK_URL = $null
    }
}

if ([string]::IsNullOrEmpty($NGROK_URL)) {
    Write-Host "ERRO: Nao foi possivel obter a URL do ngrok!" -ForegroundColor Red
    Write-Host "Verifique o painel do ngrok em: http://localhost:4040" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  URL do ngrok obtida com sucesso!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "URL publica: $NGROK_URL" -ForegroundColor Cyan
Write-Host ""
Write-Host "Agora configure o webhook no painel do Mercado Pago:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Acesse: https://www.mercadopago.com.br/developers/panel" -ForegroundColor White
Write-Host "2. Va em 'Credenciais' > 'Webhooks'" -ForegroundColor White
Write-Host "3. Adicione a seguinte URL:" -ForegroundColor White
Write-Host ""
Write-Host "   ${NGROK_URL}/webhook/mercadopago" -ForegroundColor Cyan
Write-Host ""
Write-Host "4. Marque os eventos:" -ForegroundColor White
Write-Host "   - Payments (Pagamentos)" -ForegroundColor White
Write-Host "   - Order (Mercado Pago)" -ForegroundColor White
Write-Host ""
Write-Host "5. Salve as configuracoes" -ForegroundColor White
Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "  Uteis" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Painel do ngrok: http://localhost:4040" -ForegroundColor White
Write-Host "Logs do ngrok:   http://localhost:4040/inspect/http" -ForegroundColor White
Write-Host "API Health:      ${NGROK_URL}/health" -ForegroundColor White
Write-Host ""

# Salva a URL em um arquivo para uso posterior
$NGROK_URL | Out-File -FilePath ".ngrok_url" -Encoding utf8
Write-Host "URL salva em: .ngrok_url" -ForegroundColor Green

Write-Host ""
Write-Host "Pressione Ctrl+C para encerrar o ngrok" -ForegroundColor Yellow
Write-Host ""

# Mantém o script aberto
Read-Host "Pressione Enter para sair"
