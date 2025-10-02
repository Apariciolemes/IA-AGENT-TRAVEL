# 📁 Estrutura do Projeto

```
monorepo-agent/
│
├── 📄 README.md                    # Documentação principal
├── 📄 CLAUDE.md                    # Referência técnica para IA
├── 📄 QUICKSTART.md                # Guia de início rápido
├── 📄 ESTRUTURA.md                 # Este arquivo
├── 📄 .env.example                 # Template de variáveis
├── 📄 .env                         # Variáveis (não commitar)
├── 📄 .gitignore                   # Ignorar arquivos
├── 📄 docker-compose.yml           # Orquestração de containers
│
├── 📂 backend/                     # Backend Python/FastAPI
│   ├── 📄 Dockerfile              # Container backend
│   ├── 📄 requirements.txt        # Dependências Python
│   ├── 📄 config.py               # Configurações (Pydantic)
│   │
│   ├── 📂 api/                    # Camada HTTP
│   │   ├── main.py               # App FastAPI
│   │   └── routes/               # Endpoints
│   │       ├── search.py         # POST /search, /compare
│   │       ├── chat.py           # POST /chat
│   │       └── booking.py        # POST /booking/*
│   │
│   ├── 📂 agents/                 # Agente IA
│   │   ├── travel_agent.py       # Orquestrador principal
│   │   ├── llm_client.py         # Cliente LLM unificado
│   │   └── tools.py              # Funções expostas ao LLM
│   │
│   ├── 📂 services/               # Lógica de negócio
│   │   ├── search_service.py     # Busca e cache
│   │   ├── pricing_engine.py    # Ranking de ofertas
│   │   └── booking_service.py   # Reservas
│   │
│   ├── 📂 providers/              # Integrações externas
│   │   ├── base_provider.py     # Interface abstrata
│   │   ├── duffel_provider.py   # Duffel API (stub)
│   │   ├── amadeus_provider.py  # Amadeus API (stub)
│   │   ├── kiwi_provider.py     # Kiwi API (stub)
│   │   ├── smiles_provider.py   # Smiles (mock)
│   │   ├── latam_provider.py    # LATAM Pass (mock)
│   │   └── tudoazul_provider.py # TudoAzul (mock)
│   │
│   ├── 📂 schemas/                # Modelos Pydantic
│   │   ├── flight.py             # SearchParams, Offer, etc
│   │   └── chat.py               # ChatMessage, ChatResponse
│   │
│   ├── 📂 workers/                # Background jobs
│   │   ├── celery_app.py         # Config Celery
│   │   └── tasks.py              # Tarefas (scraping, cache)
│   │
│   ├── 📂 database/               # Persistência
│   │   └── db.py                 # SQLAlchemy + Redis
│   │
│   └── 📂 models/                 # (Futuro: ORM models)
│
├── 📂 frontend/                    # Frontend Nuxt 3
│   ├── 📄 Dockerfile              # Container frontend
│   ├── 📄 package.json            # Dependências Node
│   ├── 📄 nuxt.config.ts          # Config Nuxt
│   ├── 📄 tailwind.config.js     # Config Tailwind
│   ├── 📄 app.vue                 # Root component
│   │
│   ├── 📂 pages/                  # Páginas (rotas)
│   │   ├── index.vue             # Home com formulário
│   │   ├── chat.vue              # Interface do chat
│   │   └── offers.vue            # Listagem de ofertas
│   │
│   ├── 📂 components/             # Componentes Vue
│   │   └── (a ser criado)
│   │
│   ├── 📂 stores/                 # Pinia state
│   │   └── chat.ts               # Estado do chat
│   │
│   ├── 📂 composables/            # Lógica reutilizável
│   │   └── (a ser criado)
│   │
│   └── 📂 assets/                 # Assets estáticos
│       └── css/
│           └── main.css          # Estilos Tailwind
│
├── 📂 infra/                       # Infraestrutura
│   └── init.sql                   # Schema PostgreSQL
│
└── 📂 scripts/                     # Scripts úteis
    └── start.sh                   # Script de inicialização
```

## 🔑 Arquivos Principais

### Backend

| Arquivo | Função |
|---------|--------|
| `api/main.py` | Inicializa FastAPI, middleware, rotas |
| `agents/travel_agent.py` | Agente conversacional (processa mensagens) |
| `agents/llm_client.py` | Abstração para OpenAI/Anthropic/Azure |
| `agents/tools.py` | Ferramentas (search_flights, hold_booking) |
| `services/search_service.py` | Busca + cache (Redis/Postgres) |
| `services/pricing_engine.py` | Ranking por custo efetivo |
| `providers/duffel_provider.py` | Exemplo de integração com API |
| `schemas/flight.py` | Validação com Pydantic |

### Frontend

| Arquivo | Função |
|---------|--------|
| `pages/index.vue` | Landing page + formulário de busca |
| `pages/chat.vue` | Interface do chat conversacional |
| `pages/offers.vue` | Lista de ofertas encontradas |
| `stores/chat.ts` | Estado global do chat (Pinia) |
| `nuxt.config.ts` | Configuração do Nuxt (modules, runtime) |

### Infraestrutura

| Arquivo | Função |
|---------|--------|
| `docker-compose.yml` | Orquestra 5 containers (postgres, redis, backend, celery, frontend) |
| `infra/init.sql` | Cria tabelas ao inicializar Postgres |
| `.env.example` | Template de variáveis de ambiente |

## 🔄 Fluxo de Dados Típico

### 1. Busca via Chat

```
User → Frontend (chat.vue)
    → POST /api/v1/chat {"message": "GRU → REC, 15/12"}
    → TravelAgent.process_message()
    → LLMClient (OpenAI/Anthropic)
    → Function call: search_flights(origin, destination, date)
    → SearchService.search_cash_offers() + search_miles_offers()
    → [Duffel, Smiles, LATAM, TudoAzul providers em paralelo]
    → PricingEngine.rank_offers()
    → PostgreSQL (armazena) + Redis (cache)
    → LLM formata resposta
    → Frontend recebe {message: "...", offers: [...]}
    → Exibe na UI
```

### 2. Busca Direta

```
User → Frontend (offers.vue)
    → POST /api/v1/search {origin, destination, out_date}
    → SearchService (checa cache primeiro)
    → Se stale: busca live em todos providers
    → PricingEngine.rank_offers()
    → Retorna {ranked: [...], cached: bool}
    → Frontend exibe ofertas
```

### 3. Reserva

```
User clica "Selecionar" → Frontend
    → POST /api/v1/booking/hold {offer_id, passengers, contact}
    → BookingService.hold_or_create_booking()
    → Gera booking_reference + deeplink
    → Armazena no Postgres
    → Retorna {booking_reference, deeplink_url, instructions}
    → Frontend exibe link e instruções
```

## 🗃️ Banco de Dados

### PostgreSQL

| Tabela | Propósito |
|--------|-----------|
| `airports` | IATA codes (GRU, REC, etc) |
| `carriers` | Companhias aéreas (LA, G3, AD) |
| `offers` | Ofertas normalizadas (cash + miles) |
| `queries_cache` | Cache de buscas (metadata) |
| `bookings` | Reservas criadas |
| `users` | Usuários (v1) |
| `price_alerts` | Alertas de preço (v1) |
| `knowledge_base` | Embeddings para FAQ (v1) |

### Redis

| Key Pattern | Uso |
|-------------|-----|
| `search:{hash}` | Cache de ofertas (TTL 30 min) |
| `celery:*` | Fila de tarefas Celery |

## 🚦 Fluxo de Startup

```bash
docker compose up
    ↓
1. postgres + redis iniciam
2. Backend aguarda DBs (healthcheck)
3. Backend roda migrations (init.sql)
4. Backend inicia FastAPI (porta 8000)
5. Celery worker + beat iniciam
6. Frontend npm install + build
7. Frontend inicia Nuxt dev (porta 3000)
    ↓
✅ Sistema pronto!
```

## 🔌 Endpoints da API

| Método | Endpoint | Função |
|--------|----------|--------|
| GET | `/` | Info da API |
| GET | `/health` | Health check |
| POST | `/api/v1/search` | Buscar voos |
| POST | `/api/v1/compare` | Comparar ofertas |
| GET | `/api/v1/offers/{id}` | Detalhes de oferta |
| POST | `/api/v1/chat` | Chat conversacional |
| POST | `/api/v1/booking/hold` | Criar reserva/deeplink |
| POST | `/api/v1/booking/confirm` | Confirmar reserva (v1) |
| POST | `/api/v1/booking/ancillaries` | Add assentos/bagagem |
| GET | `/api/v1/booking/{id}` | Status da reserva |

Docs interativos: http://localhost:8000/docs

## 📦 Containers Docker

| Container | Imagem | Porta | Função |
|-----------|--------|-------|--------|
| `travel_postgres` | pgvector/pgvector:pg16 | 5432 | Banco principal |
| `travel_redis` | redis:7-alpine | 6379 | Cache + fila |
| `travel_backend` | Custom (Python 3.11) | 8000 | API FastAPI |
| `travel_celery_worker` | Same as backend | - | Background tasks |
| `travel_celery_beat` | Same as backend | - | Scheduler |
| `travel_frontend` | Custom (Node 20) | 3000 | Nuxt 3 SSR |

## 🎨 Stack Tecnológico

### Backend
- **Framework**: FastAPI 0.109
- **Async**: asyncio, httpx
- **ORM**: SQLAlchemy 2.0 + Alembic
- **Cache**: Redis + hiredis
- **Queue**: Celery + Flower
- **LLM**: LangChain + OpenAI/Anthropic
- **Scraping**: Playwright (para v1)
- **Logs**: structlog
- **Validação**: Pydantic 2.5

### Frontend
- **Framework**: Nuxt 3.9
- **UI**: Tailwind CSS 3.4
- **State**: Pinia 2.1
- **Utils**: VueUse
- **HTTP**: $fetch (ofetch)

### Infra
- **DB**: PostgreSQL 16 + pgvector
- **Cache**: Redis 7
- **Orchestration**: Docker Compose
- **Deploy**: Fly.io / Render / Railway (sugestão)

## 📊 Métricas e Observabilidade

### Logs Estruturados

Todos os eventos usam `structlog`:
```python
logger.info("event_name", key=value, trace_id=trace_id)
```

### Eventos Principais

- `agent_processing` → Chat iniciou processamento
- `tool_search_flights` → Busca de voos chamada
- `duffel_search_complete` → Provider retornou resultados
- `offers_ranked` → Ranking concluído
- `booking_created` → Reserva criada
- `llm_error` → Erro no LLM
- `search_error` → Erro na busca

### Trace ID

Cada request tem `X-Trace-ID` para correlação:
```bash
curl -H "X-Trace-ID: test123" http://localhost:8000/api/v1/search
# Buscar logs: docker compose logs | grep test123
```

## 🔒 Segurança

### Secrets Management

- ✅ `.env` para dev local
- ✅ `.env` no `.gitignore`
- 🔜 Vault/AWS Secrets em prod

### Compliance

- **LGPD**: Dados pessoais criptografados, TTL curto
- **Scraping**: Rate limit, respeitar robots.txt, preferir APIs
- **API Keys**: Rotação periódica

## 📈 Roadmap

- [x] MVP: Chat + busca + deeplinks
- [ ] v1: Emissão real, scraping, login
- [ ] v2: Alertas, mobile app, pacotes

---

**Última atualização**: 2025-01-15
**Versão**: MVP 1.0
