# 🚀 Quick Start Guide

Guia rápido para rodar o projeto em **menos de 5 minutos**.

## Pré-requisitos

- ✅ Docker Desktop instalado
- ✅ 8GB RAM disponível
- ✅ Chave de API de LLM (OpenAI ou Anthropic)

## Passo a Passo

### 1. Clone e Entre no Diretório

```bash
cd monorepo-agent
```

### 2. Configure Variáveis de Ambiente

```bash
cp .env.example .env
```

Edite `.env` e adicione **no mínimo**:

```env
# OBRIGATÓRIO: Configure um LLM
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
OPENAI_API_KEY=sk-sua-chave-aqui

# Opcional: APIs de provedores de voos (no MVP funcionam sem)
DUFFEL_API_KEY=
AMADEUS_API_KEY=
```

### 3. Inicie os Containers

```bash
docker compose up --build
```

Aguarde ~2-3 minutos para build e inicialização.

### 4. Acesse os Serviços

Quando ver estas mensagens nos logs:
```
travel_backend     | INFO: Application startup complete
travel_frontend    | ✔ Vite server built
```

Abra:
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🎮 Teste o Sistema

### Opção 1: Interface Web

1. Acesse http://localhost:3000
2. Clique em "Iniciar Chat"
3. Digite: **"Quero voar de GRU para REC no dia 15 de dezembro"**
4. O agente deve responder e buscar voos

### Opção 2: API Direta

```bash
# Testar chat
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Oi, quero buscar voos"}'

# Testar busca
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "GRU",
    "destination": "REC",
    "out_date": "2025-12-15",
    "pax": {"adults": 1},
    "cabin": "ECONOMY"
  }'
```

## ✅ Checklist de Verificação

- [ ] Frontend carrega em http://localhost:3000
- [ ] API responde em http://localhost:8000/health
- [ ] Chat retorna resposta do agente
- [ ] Busca retorna ofertas mockadas
- [ ] Logs mostram `llm_client_initialized`

## 🐛 Problemas Comuns

### Backend não inicia

**Erro**: `ModuleNotFoundError: No module named 'fastapi'`

**Solução**:
```bash
docker compose down
docker compose build --no-cache backend
docker compose up
```

### Chat não responde

**Erro**: `llm_error: authentication failed`

**Solução**: Verifique `OPENAI_API_KEY` no `.env`

### Porta 8000 já em uso

**Solução**: Altere porta no `.env`:
```env
BACKEND_PORT=8001
```

E acesse http://localhost:8001

## 📖 Próximos Passos

1. **Leia o README.md** para entender a arquitetura
2. **Consulte CLAUDE.md** para referência técnica completa
3. **Explore a API** em http://localhost:8000/docs

## 🛑 Parar o Sistema

```bash
docker compose down
```

Para remover volumes (dados do banco):
```bash
docker compose down -v
```

## 📞 Precisa de Ajuda?

- **Documentação completa**: `README.md`
- **Referência técnica**: `CLAUDE.md`
- **Issues**: GitHub Issues

---

**Tempo estimado**: 5 minutos ⏱️
**Dificuldade**: Fácil 🟢
