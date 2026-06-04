#!/bin/bash
# setup.sh - Instalação v3.0

echo "🤖 Agente Pessoal v3.0 - Instalação"
echo "===================================="

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale Python 3.11+"
    exit 1
fi

echo "✅ Python encontrado"

if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv venv
fi

echo "🔄 Ativando ambiente..."
source venv/bin/activate

echo "📥 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🗄️  Inicializando banco de dados..."
python -c "from database.models import init_db; init_db(); print('✅ Banco de dados pronto!')"

if [ ! -f ".env" ]; then
    echo "📝 Criando .env..."
    cp .env.example .env
    echo "⚠️  Edite .env com suas chaves!"
fi

echo ""
echo "✅ Instalação concluída!"
echo ""
echo "🚀 Para iniciar:"
echo "  API:        python api/main.py"
echo "  Web:        streamlit run ui/streamlit_app.py"
echo "  Dashboard:  streamlit run ui/dashboard.py"
echo "  Telegram:   python ui/bot_telegram.py"
echo "  WhatsApp:   python ui/bot_whatsapp.py"
echo "  Terminal:   python agents/coordenador.py"
echo ""
echo "🐳 Docker:"
echo "  docker-compose -f docker/docker-compose.yml up -d"
