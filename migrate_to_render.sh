#!/bin/bash
# Script para migrar dados para Render

echo "🚀 Iniciando migração para Render..."

# 1. Instalar dependências
echo "📦 Instalando dependências..."
pip install -r requirements.txt

# 2. Executar migrações
echo "🗄️ Executando migrações..."
python manage.py migrate

# 3. Importar dados do backup
echo "📥 Importando dados do backup..."
python manage.py loaddata dashboard_backup.json

# 4. Coletar arquivos estáticos
echo "📂 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "✅ Migração concluída!"
echo "🎉 Seu dashboard está pronto no Render!"