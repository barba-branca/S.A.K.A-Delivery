# Documentação de Pagamentos - SAKA Delivery KDS

## Visão Geral

Este documento explica como o sistema de pagamentos do SAKA Delivery KDS funciona e como configurá-lo.

## Credenciais do MercadoPago (Teste)

As credenciais de teste do MercadoPago foram configuradas no arquivo [`backend/.env`](backend/.env):

```
MERCADOPAGO_PUBLIC_KEY=TEST-190099d0-ccba-45cf-b781-de0a268839ef
MERCADOPAGO_ACCESS_TOKEN=TEST-3835592661239049-022412-b285ad0e030c007283030f982463e12a-302103023
```

## Fluxo de Pagamento Atual

### 1. Registro de Usuário

O usuário precisa primeiro criar uma conta:

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "seu_usuario",
    "email": "email@exemplo.com",
    "full_name": "Nome Completo",
    "password": "sua_senha",
    "role": "ADMIN"
  }'
```

**Resposta:**
```json
{
  "message": "Conta criada com sucesso",
  "user": {
    "id": 1,
    "username": "seu_usuario",
    "saldoCredito": 0.0,
    ...
  },
  "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

Guarde o `access_token` - ele será usado em todas as requisições autenticadas.

---

### 2. Compra de Pacote (Simulação de Pagamento)

O sistema atual simula pagamentos através da compra de pacotes pré-pagos:

```bash
curl -X POST http://localhost:8000/pacotes/comprar \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -d '{"tipo":"padrao"}'
```

**Pacotes disponíveis:**
- `padrao`: R$ 5.000,00 = 1.000 pedidos

**Resposta:**
```json
{
  "message": "Pacote comprado com sucesso!",
  "pacote": {
    "id": 1,
    "valor_pago": 5000.0,
    "qtd_pedidos": 1000,
    "data_compra": "2026-02-25T16:20:26.289493"
  },
  "novo_saldo": 5000.0
}
```

---

### 3. Webhook de Pagamento

O sistema possui um endpoint para receber notificações de pagamento (pronto para integração com OpenPix ou MercadoPago):

**Endpoint:** `POST /webhook/pagamento`

```bash
curl -X POST http://localhost:8000/webhook/pagamento \
  -H "Content-Type: application/json" \
  -d '{
    "txid": "ID_TRANSACAO",
    "valor": 100.00,
    "user_id": 1
  }'
```

**Payload esperado:**
| Campo | Tipo | Descrição |
|-------|------|-----------|
| `txid` | string | ID único da transação |
| `valor` | float | Valor pago em reais |
| `user_id` | integer | ID do usuário que recebeu o crédito |

**Resposta:**
```json
{
  "status": "success",
  "message": "Crédito adicionado com sucesso",
  "txid": "ID_TRANSACAO",
  "novo_saldo": 5100.0
}
```

---

### 4. Verificar Saldo

Para verificar o saldo atual do usuário:

```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

**Resposta:**
```json
{
  "id": 1,
  "username": "admin",
  "saldoCredito": 5100.0,
  "saldo_credito": 5100.0,
  ...
}
```

---

## Configuração do Banco de Dados

O projeto está configurado para usar SQLite em desenvolvimento:

```env
DATABASE_URL=sqlite+aiosqlite:///./saka_delivery.db
```

O banco de dados é criado automaticamente na pasta `backend/` com o nome `saka_delivery.db`.

---

## Executando o Projeto

### Pré-requisitos
- Python 3.11+
- Node.js 18+

### Backend
```bash
cd backend
pip install -r requirements.txt
python run.py
```
Servidor rodando em: http://localhost:8000

### Frontend
```bash
npm install
npm run dev
```
Servidor rodando em: http://localhost:3000

---

## Integração com MercadoPago (Futuro)

O webhook de pagamento está preparado para receber notificações do MercadoPago. Para implementar a integração completa:

1. Configure as credenciais do MercadoPago no painel do MercadoPago
2. Configure a URL do webhook: `https://seu-dominio.com/webhook/pagamento`
3. Implemente a validação da assinatura do webhook
4. Processe os eventos de pagamento

---

## Testes com Cartões (MercadoPago)

Para testar pagamentos no ambiente de produção/sandbox do MercadoPago, você pode usar os cartões de teste:

| Bandeira | Número | Validade | CVV |
|----------|--------|----------|-----|
| Mastercard | 5031 4332 1540 6351 | 11/30 | 123 |
| Visa | 4235 6477 2802 5682 | 11/30 | 123 |

Nota: A integração direta com MercadoPago requer implementação adicional no código.
