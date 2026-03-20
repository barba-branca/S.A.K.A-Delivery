#!/bin/bash
set -e

echo "=========================================="
echo "🚀 Booting S.A.K.A Delivery on Replit VPS"
echo "=========================================="

echo "🔧 [1/4] Instalando dependências do Backend (FastAPI)..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "🗄️ [2/4] Sincronizando Banco de Dados Automático..."
alembic upgrade head || echo "⚠️ Aviso: Conexão com o banco falhou. Verifique se o Add-on do PostgreSQL está ativo no Replit!"

echo "🟢 [3/4] Iniciando Servidor Backend (Plano de Fundo)..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

echo "📦 [4/4] Instalando dependências do Frontend (React Vite)..."
cd ..
npm install

echo "🌐 Boot Completo! Servindo Frontend..."
npm run dev -- --host 0.0.0.0 --port 5173
