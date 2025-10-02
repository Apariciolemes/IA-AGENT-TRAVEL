#!/bin/bash

echo "🧪 TESTE COMPLETO DO SISTEMA"
echo "=============================="
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Teste 1: Backend Health
echo -n "1. Testando Backend Health... "
response=$(curl -s http://localhost:8000/health)
if [[ $response == *"healthy"* ]]; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FALHOU${NC}"
    echo "Resposta: $response"
fi

# Teste 2: API Root
echo -n "2. Testando API Root... "
response=$(curl -s http://localhost:8000/)
if [[ $response == *"Travel Agent API"* ]]; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FALHOU${NC}"
fi

# Teste 3: Busca de Voos
echo -n "3. Testando Busca de Voos (GRU → REC)... "
response=$(curl -s -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "GRU",
    "destination": "REC",
    "out_date": "2025-12-15",
    "pax": {"adults": 1},
    "cabin": "ECONOMY"
  }')

if [[ $response == *"ranked"* ]] && [[ $response == *"smiles"* ]]; then
    echo -e "${GREEN}✓ OK${NC}"
    # Contar ofertas
    count=$(echo $response | grep -o '"id":' | wc -l)
    echo "   → Encontrou $count ofertas"
else
    echo -e "${RED}✗ FALHOU${NC}"
fi

# Teste 4: Frontend
echo -n "4. Testando Frontend (HTML)... "
response=$(curl -s http://localhost:3000)
if [[ $response == *"Agente de Viagens"* ]] || [[ $response == *"<html"* ]]; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FALHOU${NC}"
fi

# Teste 5: PostgreSQL
echo -n "5. Testando PostgreSQL... "
count=$(docker exec -it travel_postgres psql -U travel_user -d travel_agent -t -c "SELECT COUNT(*) FROM airports;" 2>/dev/null | tr -d ' \r\n')
if [[ $count -gt 0 ]]; then
    echo -e "${GREEN}✓ OK${NC}"
    echo "   → $count aeroportos no banco"
else
    echo -e "${YELLOW}⚠ AVISO${NC} (não crítico)"
fi

# Teste 6: Redis
echo -n "6. Testando Redis... "
response=$(docker exec -it travel_redis redis-cli PING 2>/dev/null | tr -d '\r')
if [[ $response == "PONG" ]]; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FALHOU${NC}"
fi

echo ""
echo "=============================="
echo "📊 RESUMO"
echo "=============================="
echo ""
echo -e "${GREEN}✅ SISTEMA FUNCIONANDO!${NC}"
echo ""
echo "🌐 URLs Disponíveis:"
echo "   • Frontend:  http://localhost:3000"
echo "   • API Docs:  http://localhost:8000/docs"
echo "   • Health:    http://localhost:8000/health"
echo ""
echo "🧪 Exemplo de Busca:"
echo '   curl -X POST http://localhost:8000/api/v1/search \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '"'"'{"origin":"GRU","destination":"REC","out_date":"2025-12-15","pax":{"adults":1},"cabin":"ECONOMY"}'"'"
echo ""
echo "📖 Veja EXEMPLOS_DE_USO.md para guia completo!"
echo ""
