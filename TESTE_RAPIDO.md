# 🧪 Teste Rápido do Sistema

## 1️⃣ Antes de Iniciar

### Verificar Pré-requisitos

```bash
# Docker instalado?
docker --version

# Docker Compose instalado?
docker compose version

# Docker está rodando?
docker info
```

### Configurar LLM API Key

**OBRIGATÓRIO**: Edite `.env` e adicione sua chave:

```bash
# OpenAI (recomendado)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
OPENAI_API_KEY=sk-proj-sua-chave-aqui

# OU Anthropic
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-sonnet-20240229
ANTHROPIC_API_KEY=sk-ant-sua-chave-aqui
```

## 2️⃣ Iniciar Sistema

### Opção A: Script Automático

```bash
./scripts/start.sh
```

### Opção B: Manual

```bash
docker compose up --build
```

Aguarde até ver:
```
travel_backend     | INFO: Application startup complete
travel_frontend    | ✔ Vite server built
```

## 3️⃣ Verificar Saúde

```bash
# Health check do backend
curl http://localhost:8000/health

# Deve retornar: {"status": "healthy"}
```

```bash
# Frontend carregou?
curl -I http://localhost:3000

# Deve retornar: HTTP/1.1 200 OK
```

## 4️⃣ Testar Funcionalidades

### A) Testar Chat

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Oi, me ajude a encontrar um voo"
  }'
```

**Resultado Esperado**:
```json
{
  "message": "Olá! Claro, vou ajudar você a encontrar o melhor voo...",
  "conversation_id": "uuid-aqui",
  "needs_clarification": true,
  "missing_fields": ["origin", "destination", "date"]
}
```

### B) Buscar Voos

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "GRU",
    "destination": "REC",
    "out_date": "2025-12-15",
    "pax": {"adults": 1},
    "cabin": "ECONOMY",
    "bag_included": true
  }'
```

**Resultado Esperado**: JSON com ~5 ofertas ranqueadas

```json
{
  "ranked": [
    {
      "id": "duffel_...",
      "type": "cash",
      "price": {"cash": {"amount": 450.00}},
      "segments": [...],
      "duration_minutes": 180,
      "stops": 0,
      "explanation": "MELHOR PREÇO | voo direto..."
    },
    ...
  ],
  "cached": false
}
```

### C) Chat com Busca Completa

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quero voar de GRU para REC no dia 15 de dezembro, 1 adulto"
  }'
```

**Resultado Esperado**:
- LLM entende os parâmetros
- Chama `search_flights` automaticamente
- Retorna ofertas + explicação

### D) Teste no Frontend

1. Abra: http://localhost:3000
2. Clique em **"Iniciar Chat"**
3. Digite: `Quero voar de São Paulo para Recife dia 15 de dezembro`
4. Aguarde resposta do agente
5. Veja as ofertas aparecerem

## 5️⃣ Verificar Logs

### Backend

```bash
docker compose logs -f backend
```

**Procure por**:
- `llm_client_initialized` → LLM configurado
- `agent_processing` → Chat processando
- `tool_search_flights` → Busca executada
- `offers_ranked` → Ranking completo

### Frontend

```bash
docker compose logs -f frontend
```

### Redis (cache)

```bash
docker compose exec redis redis-cli

# Verificar chaves de cache
KEYS search:*

# Ver conteúdo de uma chave
GET search:abc123...
```

### PostgreSQL

```bash
docker compose exec postgres psql -U travel_user -d travel_agent

# Ver ofertas armazenadas
SELECT id, source, offer_type, origin, destination, out_date FROM offers LIMIT 5;

# Sair
\q
```

## 6️⃣ Testar API Docs Interativa

1. Acesse: http://localhost:8000/docs
2. Expanda **POST /api/v1/search**
3. Clique em "Try it out"
4. Preencha:
```json
{
  "origin": "GRU",
  "destination": "REC",
  "out_date": "2025-12-15",
  "pax": {"adults": 1},
  "cabin": "ECONOMY"
}
```
5. Clique "Execute"
6. Veja resposta abaixo

## 7️⃣ Checklist de Validação

- [ ] Backend respondeu no health check
- [ ] Frontend carrega página inicial
- [ ] Chat retorna resposta do LLM
- [ ] Busca direta retorna ofertas
- [ ] Chat com busca completa funciona
- [ ] Ofertas têm score e explanation
- [ ] Logs mostram eventos estruturados
- [ ] API Docs interativa funciona

## 🐛 Troubleshooting

### Erro: "llm_error: authentication failed"

**Causa**: API key inválida

**Solução**:
1. Verifique `.env` → `OPENAI_API_KEY` ou `ANTHROPIC_API_KEY`
2. Teste a key:
```bash
# OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer sk-sua-key"

# Anthropic
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: sk-ant-sua-key"
```

### Erro: "Connection refused"

**Causa**: Containers não iniciaram

**Solução**:
```bash
docker compose ps  # Ver status
docker compose logs backend  # Ver erros
docker compose restart  # Reiniciar
```

### Chat não chama `search_flights`

**Causa**: LLM não entendeu ou function calling não configurado

**Solução**:
1. Verifique logs: `docker compose logs backend | grep tool`
2. Teste com mensagem mais explícita: "Buscar voos GRU para REC dia 15/12"
3. Verifique temperature no `.env` (padrão: 0.7)

### Ofertas todas iguais

**Causa**: Mock data (esperado no MVP)

**Solução**: Normal! Provedores retornam dados fictícios. Para dados reais:
- Configure `DUFFEL_API_KEY` no `.env`
- Implemente integração real em `providers/duffel_provider.py`

## 8️⃣ Próximos Testes (v1)

Quando tiver APIs reais:

```bash
# Testar Duffel
DUFFEL_API_KEY=test_123 docker compose up

# Testar scraping (v1)
SCRAPING_ENABLED=true docker compose up celery_worker
```

## 9️⃣ Parar Sistema

```bash
# Parar mas manter dados
docker compose down

# Parar e remover volumes (limpa banco)
docker compose down -v
```

## 🎯 Métricas de Sucesso

✅ **Backend**: Responde em < 500ms (health check)
✅ **Chat**: Responde em < 5s (com LLM)
✅ **Busca**: Retorna em < 3s (com cache) ou < 10s (live)
✅ **Ofertas**: Mínimo 2-3 ofertas por busca
✅ **Ranking**: Score entre 0-1, explicação presente

---

**Tempo estimado de teste**: 10 minutos
**Dificuldade**: Fácil 🟢

**Dúvidas?** Consulte:
- `README.md` → Visão geral
- `CLAUDE.md` → Referência técnica
- `STATUS.md` → Status do projeto
