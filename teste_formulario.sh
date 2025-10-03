#!/bin/bash

echo "🧪 TESTE DO FORMULÁRIO DE BUSCA"
echo "================================"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}📋 Testando diferentes cenários de busca...${NC}"
echo ""

# Teste 1: Busca simples (só ida)
echo -e "${YELLOW}1. Busca Simples - GRU → REC (só ida)${NC}"
echo "   Parâmetros: origem=GRU, destino=REC, data=2025-12-15, 1 adulto"
echo ""

response=$(curl -s -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "GRU",
    "destination": "REC", 
    "out_date": "2025-12-15",
    "pax": {"adults": 1},
    "cabin": "ECONOMY"
  }')

if [[ $response == *"ranked"* ]]; then
    echo -e "   ${GREEN}✓ SUCESSO${NC}"
    count=$(echo $response | grep -o '"id":' | wc -l)
    echo "   → Encontrou $count ofertas"
    
    # Extrair primeira oferta
    first_offer=$(echo $response | grep -o '"score":[0-9.]*' | head -1 | cut -d':' -f2)
    echo "   → Melhor score: $first_offer"
else
    echo -e "   ${RED}✗ FALHOU${NC}"
    echo "   Resposta: $response"
fi

echo ""

# Teste 2: Busca ida e volta
echo -e "${YELLOW}2. Busca Ida e Volta - CWB → GRU${NC}"
echo "   Parâmetros: origem=CWB, destino=GRU, ida=2025-12-10, volta=2025-12-15"
echo ""

response=$(curl -s -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "CWB",
    "destination": "GRU",
    "out_date": "2025-12-10", 
    "ret_date": "2025-12-15",
    "pax": {"adults": 1},
    "cabin": "ECONOMY"
  }')

if [[ $response == *"ranked"* ]]; then
    echo -e "   ${GREEN}✓ SUCESSO${NC}"
    count=$(echo $response | grep -o '"id":' | wc -l)
    echo "   → Encontrou $count ofertas"
else
    echo -e "   ${RED}✗ FALHOU${NC}"
fi

echo ""

# Teste 3: Múltiplos passageiros
echo -e "${YELLOW}3. Múltiplos Passageiros - BSB → FOR${NC}"
echo "   Parâmetros: 2 adultos + 1 criança, classe executiva"
echo ""

response=$(curl -s -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "BSB",
    "destination": "FOR",
    "out_date": "2025-12-20",
    "pax": {"adults": 2, "children": 1},
    "cabin": "BUSINESS"
  }')

if [[ $response == *"ranked"* ]]; then
    echo -e "   ${GREEN}✓ SUCESSO${NC}"
    count=$(echo $response | grep -o '"id":' | wc -l)
    echo "   → Encontrou $count ofertas"
else
    echo -e "   ${RED}✗ FALHOU${NC}"
fi

echo ""

# Teste 4: Teste com erro (formato inválido)
echo -e "${YELLOW}4. Teste de Validação - Formato Inválido${NC}"
echo "   Parâmetros: origem inválida (deve dar erro 422)"
echo ""

response=$(curl -s -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "INVALID",
    "destination": "GRU",
    "out_date": "2025-12-15",
    "passengers": 1
  }')

if [[ $response == *"422"* ]] || [[ $response == *"validation"* ]] || [[ $response == *"detail"* ]]; then
    echo -e "   ${GREEN}✓ ERRO ESPERADO (validação funcionando)${NC}"
else
    echo -e "   ${RED}✗ DEVERIA DAR ERRO${NC}"
fi

echo ""
echo "================================"
echo -e "${BLUE}📊 RESUMO DOS TESTES${NC}"
echo "================================"
echo ""
echo -e "${GREEN}✅ FORMATO CORRETO QUE FUNCIONA:${NC}"
echo ""
echo "curl -X POST http://localhost:8000/api/v1/search \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{"
echo "    \"origin\": \"GRU\","
echo "    \"destination\": \"REC\","
echo "    \"out_date\": \"2025-12-15\","
echo "    \"pax\": {\"adults\": 1},"
echo "    \"cabin\": \"ECONOMY\""
echo "  }'"
echo ""
echo -e "${YELLOW}⚠️ CAMPOS OBRIGATÓRIOS:${NC}"
echo "  • origin: Código IATA (3 letras maiúsculas)"
echo "  • destination: Código IATA (3 letras maiúsculas)" 
echo "  • out_date: Data no formato YYYY-MM-DD"
echo "  • pax: Objeto com adults (mínimo 1)"
echo ""
echo -e "${BLUE}🔧 CAMPOS OPCIONAIS:${NC}"
echo "  • ret_date: Data de volta (ida e volta)"
echo "  • cabin: ECONOMY, BUSINESS, FIRST"
echo "  • pax.children: Número de crianças"
echo "  • pax.infants: Número de bebês"
echo ""
echo -e "${GREEN}🌐 TESTE NO FRONTEND:${NC}"
echo "  → http://localhost:3000"
echo ""