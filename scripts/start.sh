#!/bin/bash

echo "🚀 Iniciando Agente de Viagens..."
echo ""

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "⚠️  Arquivo .env não encontrado. Criando a partir do .env.example..."
    cp .env.example .env
    echo ""
    echo "📝 IMPORTANTE: Edite o arquivo .env e configure:"
    echo "   - LLM_PROVIDER (openai ou anthropic)"
    echo "   - OPENAI_API_KEY ou ANTHROPIC_API_KEY"
    echo ""
    echo "Depois execute novamente: ./scripts/start.sh"
    exit 1
fi

# Verificar se Docker está rodando
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker não está rodando. Por favor, inicie o Docker Desktop."
    exit 1
fi

echo "✅ Docker detectado"
echo ""

# Build e start
echo "🔨 Building containers (pode levar alguns minutos na primeira vez)..."
docker compose up --build -d

echo ""
echo "⏳ Aguardando serviços ficarem prontos..."
sleep 10

# Health check
echo ""
echo "🔍 Verificando saúde dos serviços..."

for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend: OK"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend não respondeu após 30 segundos"
        echo "Execute 'docker compose logs backend' para ver os logs"
        exit 1
    fi
    sleep 1
done

echo ""
echo "🎉 Sistema iniciado com sucesso!"
echo ""
echo "📍 Acesse os serviços:"
echo "   Frontend:  http://localhost:3000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   Health:    http://localhost:8000/health"
echo ""
echo "💬 Teste o chat:"
echo "   curl -X POST http://localhost:8000/api/v1/chat \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"message\": \"Oi\"}'"
echo ""
echo "📊 Ver logs:"
echo "   docker compose logs -f backend"
echo "   docker compose logs -f frontend"
echo ""
echo "🛑 Para parar:"
echo "   docker compose down"
echo ""
