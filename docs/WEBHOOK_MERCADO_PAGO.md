# Configuração Completa do Webhook do Mercado Pago

Este documento descreve como configurar, implementar e fazer deploy do webhook do Mercado Pago para receber notificações de pagamentos no SAKA Delivery KDS.

## Índice

1. [Pré-requisitos](#pré-requisitos)
2. [Configuração do Ambiente de Desenvolvimento](#configuração-do-ambiente-de-desenvolvimento)
3. [Configuração de Eventos no Painel do Mercado Pago](#configuração-de-eventos-no-painel-do-mercado-pago)
4. [Variáveis de Ambiente](#variáveis-de-ambiente)
5. [Arquitetura do Sistema](#arquitetura-do-sistema)
6. [Endpoints Disponíveis](#endpoints-disponíveis)
7. [Segurança e Autenticação](#segurança-e-autenticação)
8. [Idempotência](#idempotência)
9. [Logging e Auditoria](#logging-e-auditoria)
10. [Testes Unitários](#testes-unitários)
11. [Deployment em Produção](#deployment-em-produção)
12. [Troubleshooting](#troubleshooting)

---

## Pré-requisitos

1. **Servidor rodando**: O servidor backend deve estar rodando na porta 8000
2. **ngrok instalado**: Para expor o servidor local para a internet durante desenvolvimento
3. **Credenciais do Mercado Pago**: Access Token configurado no arquivo `.env`
4. **Python 3.9+** com as dependências instaladas

---

## Configuração do Ambiente de Desenvolvimento

### 1.1 Iniciar o ngrok

O ngrok cria um tunnel seguro que expõe seu servidor local para a internet.

#### Usando PowerShell (Windows)

```powershell
cd backend
.\scripts\start_ngrok.ps1
```

#### Usando Bash (Linux/Mac)

```bash
cd backend
choco install ngrok  # Se não tiver instalado
chmod +x scripts/start_ngrok.sh
./scripts/start_ngrok.sh
```

#### Manual

```bash
ngrok http 8000 --log=stdout > ngrok_url.txt 2>&1 &
sleep 5
# Obter URL
curl -s localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*'
```

O ngrok fornecerá uma URL pública (ex: `https://abc123.ngrok-free.app`).

**Importante**: O ngrok é apenas para desenvolvimento. Em produção, use HTTPS com certificado SSL válido.

---

### 1.2 Configurar a URL do Webhook

1. Acesse: https://www.mercadopago.com.br/developers/panel
2. Selecione seu aplicativo
3. Vá em **Credenciais** > **Webhooks**
4. Adicione a URL do webhook:

```
https://SUA_URL_NGROK/webhook/mercadopago
```

---

## Configuração de Eventos no Painel do Mercado Pago

No painel do Mercado Pago Developers, marque os seguintes eventos:

| Evento | Descrição |
|--------|-----------|
| `payment.created` | Novo pagamento criado |
| `payment.updated` | Pagamento atualizado |
| `payment.approved` | Pagamento aprovado |
| `payment.rejected` | Pagamento rejeitado |
| `order.created` | Ordem criada |
| `order.updated` | Ordem atualizada |

### Configuração para Produção

Quando finalizar os testes:

1. Substitua a URL de teste pela URL de produção (com HTTPS)
2. Use o **Access Token de Produção** (não o de teste)
3. Mantenha o webhook_secret configurado
4. Configure retry no painel do MP para garantir entrega

---

## Variáveis de Ambiente

Adicione as seguintes variáveis ao seu arquivo `.env`:

```env
# =============================================
# Mercado Pago - Credenciais
# =============================================

# Chave Pública (para o frontend)
MERCADOPAGO_PUBLIC_KEY=TEST-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Access Token (para API - MANTENHA SECRETO)
MERCADOPAGO_ACCESS_TOKEN=TEST-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxx

# Segredo do Webhook (gere com: openssl rand -hex 32)
MERCADOPAGO_WEBHOOK_SECRET=sua_chave_secreta_minimo_32_caracteres

# =============================================
# Configurações de Retry do Webhook
# =============================================
WEBHOOK_MAX_RETRIES=3
WEBHOOK_RETRY_DELAY=5
```

### Geração de Segredo Seguro

```bash
# Linux/Mac
openssl rand -hex 32

# PowerShell
[System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32) | ForEach-Object { $_.ToString("x2") }
```

---

## Arquitetura do Sistema

### Fluxo de Processamento

```
1. Cliente faz pagamento no Mercado Pago (Checkout Transparente)
         ↓
2. Mercado Pago envia notificação POST para /webhook/mercadopago
         ↓
3. Servidor valida a assinatura HMAC-SHA256 (se configurada)
         ↓
4. Servidor verifica idempotência (evita duplicatas)
         ↓
5. Servidor consulta API do Mercado Pago para validar o pagamento
         ↓
6. Servidor extrai o user_id do pagamento
         ↓
7. Servidor adiciona crédito ao saldo do usuário
         ↓
8. Servidor registra log de auditoria
         ↓
9. Retorna HTTP 200 para confirmar recebimento
```

### Identificação do Usuário

O `user_id` do usuário pode ser enviado de várias formas:

1. **external_reference** (recomendado): No momento de criar o pagamento
2. **description**: No formato `user_id:123`
3. **payer.identification.number**: Número do documento

---

## Endpoints Disponíveis

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/webhook/mercadopago` | Recebe notificações do Mercado Pago |
| GET | `/webhook/health` | Verifica saúde do webhook |
| GET | `/webhook/logs` | Lista logs de webhooks |
| GET | `/webhook/logs/{log_id}` | Detalha um log específico |

---

## Segurança e Autenticação

### Validação de Assinatura HMAC-SHA256

O Mercado Pago envia um cabeçalho `x-signature` que contém:

- `id`: ID da notificação
- `timestamp`: Timestamp da geração
- `signature`: HMAC-SHA256 dos dados

O servidor valida essa assinatura para garantir que a requisição veio do Mercado Pago.

**Para habilitar**:

1. Gere um segredo seguro
2. Adicione no painel do Mercado Pago
3. Configure `MERCADOPAGO_WEBHOOK_SECRET` no `.env`

### Respostas HTTP

| Código | Descrição |
|--------|-----------|
| 200 | Sucesso - notificação recebida e processada |
| 200 | Ignorado - tipo de evento não processado |
| 400 | Erro - payload inválido ou dados inconsistentes |
| 401 | Erro - assinatura de webhook inválida |
| 500 | Erro interno do servidor |

---

## Idempotência

O sistema implementa idempotência para evitar que webhooks sejam processados múltiplas vezes:

1. Cada webhook tem um `webhook_id` único
2. O sistema verifica se o `webhook_id` já foi processado anteriormente
3. Se duplicado, retorna sucesso sem reprocessar
4. Mantém registro de todos os pagamentos processados

**Benefícios**:
- Evita créditos duplicados
- Mantém integridade dos dados
- Permite reenvio seguro pelo Mercado Pago

---

## Logging e Auditoria

O sistema mantém logs detalhados de todas as operações:

### Logs de Arquivo

Os logs são salvos em: `backend/logs/webhook_mercadopago.log`

Formato:
```
2024-01-15 10:30:45 | INFO     | webhook_mercado_pago | webhook_mercadopago:328 |Webhook processado com sucesso
```

### Logs no Banco de Dados

A API `/webhook/logs` retorna:

```json
{
  "logs": [
    {
      "id": 1,
      "webhook_id": "webhook_123",
      "payment_id": 123456,
      "user_id": 1,
      "action": "payment.created",
      "status": "success",
      "transaction_amount": 100.00,
      "payment_status": "approved",
      "credit_added": 100.00,
      "new_balance": 150.00,
      "error_message": null,
      "created_at": "2024-01-15T10:30:45",
      "processed_at": "2024-01-15T10:30:46"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

---

## Testes Unitários

Execute os testes com:

```bash
cd backend
pytest tests/test_webhook.py -v
```

Os testes cobrem:

- Extração de user_id de várias fontes
- Validação de assinatura HMAC-SHA256
- Verificação de idempotência
- Adição de crédito ao usuário
- Processamento de webhooks

---

## Deployment em Produção

### 1. Configure o Ambiente

```env
DEBUG=false
HOST=0.0.0.0
PORT=8000
```

### 2. Use HTTPS

Configure um proxy reverso com HTTPS:

- **NGINX** com Let's Encrypt
- **Cloudflare** (recomendado)
- **AWS ALB** com ACM

### 3. Atualize a URL do Webhook

No painel do Mercado Pago, altere a URL para:

```
https://seudominio.com/webhook/mercadopago
```

### 4. Use Credenciais de Produção

```env
MERCADOPAGO_ACCESS_TOKEN=PROD-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxx
```

### 5. Monitoramento

- Configure alertas para erros no webhook
- Monitore os logs regularmente
- Use `/webhook/health` para health checks

---

## Troubleshooting

### Webhook não está chegando

1. Verifique se o ngrok está rodando: http://localhost:4040
2. Verifique os logs do ngrok na aba "Inspect"
3. Verifique se a URL está correta no painel do Mercado Pago
4. Confirme que o servidor está acessível

### Erro de assinatura inválida (401)

1. Verifique se o `MERCADOPAGO_WEBHOOK_SECRET` está configurado corretamente
2. Para testes, você pode deixar em branco para desabilitar a validação
3. Verifique se o segredo no painel do MP é igual ao do .env

### Pagamento não encontrado

1. Verifique se o `MERCADOPAGO_ACCESS_TOKEN` está correto
2. Confirme que o payment_id existe no Mercado Pago
3. Verifique os logs em `/webhook/logs`

### Crédito não adicionado

1. Verifique os logs de webhook: `GET /webhook/logs`
2. Confirme que o user_id está sendo extraído corretamente
3. Verifique se o usuário existe no banco de dados
4. Verifique se o status do pagamento é "approved"

### Múltiplos créditos aplicados

1. O sistema de idempotência deve evitar isso
2. Verifique os logs para ver se háwebhooks duplicados
3. Entre em contato com o suporte do Mercado Pago

---

## Suporte

Em caso de problemas, verifique:

1. Logs do servidor (terminal)
2. Logs do ngrok (http://localhost:4040/inspect/http)
3. Logs de webhook via API (`GET /webhook/logs`)
4. Painel do Mercado Pago para ver tentativas de entrega

---

## Referências

- [Documentação do Mercado Pago - Webhooks](https://www.mercadopago.com.br/developers/pt/docs/notifications/webhooks)
- [API de Pagamentos do Mercado Pago](https://www.mercadopago.com.br/developers/pt/reference/payments/_payments_id/get)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
