# CLAUDE.md - Referência para IA Assistente

> **Propósito**: Este arquivo deve ser consultado sempre que você (Claude ou outra IA) precisar entender, modificar ou debugar este projeto.

## 🎯 Visão Geral do Projeto

**Nome**: Agente de Viagens (Travel Agent)
**Tipo**: Sistema conversacional de busca de voos em dinheiro e milhas
**Stack Principal**: FastAPI (backend) + Nuxt 3 (frontend) + PostgreSQL + Redis
**Idioma**: Português Brasileiro (pt-BR)

### Objetivo

Criar um agente conversacional que:
1. Entende perguntas em linguagem natural sobre voos
2. Busca ofertas em dinheiro (via APIs de OTAs/NDC) e milhas (via APIs ou scraping)
3. Compara e rankeia ofertas por custo efetivo
4. Ajuda na reserva/emissão

## 🏗️ Arquitetura Detalhada

### Fluxo de Dados

```
Frontend (Nuxt 3)
    ↓ HTTP
Backend FastAPI (/api/v1/chat)
    ↓
TravelAgent (agents/travel_agent.py)
    ↓
LLMClient (OpenAI/Anthropic/Azure)
    ↓ Function Calling
Tools (agents/tools.py)
    ↓ search_flights
SearchService (services/search_service.py)
    ↓ Parallel
├─ DuffelProvider (cash)
├─ AmadeusProvider (cash)
├─ SmilesProvider (miles)
├─ LatamPassProvider (miles)
└─ TudoAzulProvider (miles)
    ↓
PricingEngine (ranking)
    ↓
PostgreSQL (storage) + Redis (cache)
```

### Componentes Críticos

#### 1. Agente IA (`backend/agents/travel_agent.py`)

**Responsabilidade**: Orquestração da conversa e chamadas de ferramentas

**Fluxo**:
1. Recebe mensagem do usuário
2. Envia para LLM com system prompt + histórico
3. LLM decide se chama função ou responde direto
4. Se chamar função → executa via `TravelTools`
5. Retorna resultado ao LLM para formatação
6. Envia resposta ao usuário

**Prompt de Sistema** (modificável em `_build_system_prompt()`):
```
Você é um agente de viagens sênior...
- Sempre peça origem, destino, datas
- Consulte dinheiro E milhas
- Apresente no máximo 5 opções
- Seja transparente sobre limitações
```

#### 2. Tools (`backend/agents/tools.py`)

**Funções expostas ao LLM**:

```python
search_flights(origin, destination, out_date, ret_date?, adults?, cabin?, ...)
  → Busca voos e retorna ofertas ranqueadas

hold_booking(offer_id, passenger_data, contact_email, ...)
  → Cria reserva ou gera deeplink

compare_offers(offer_ids, prefer_miles?, prefer_direct?)
  → Compara ofertas específicas
```

**Formato de retorno** (JSON):
```json
{
  "success": true,
  "offers": [
    {
      "id": "duffel_abc123",
      "type": "cash",
      "price": {"cash": {"amount": 450.00, "currency": "BRL"}},
      "segments": [...],
      "duration_minutes": 180,
      "stops": 0,
      "explanation": "MELHOR PREÇO | voo direto | bagagem incluída"
    }
  ]
}
```

#### 3. Pricing Engine (`backend/services/pricing_engine.py`)

**Algoritmo de Ranking**:
```python
score = (
    0.4 * price_score +      # Custo efetivo (R$)
    0.3 * duration_score +   # Duração total
    0.2 * stops_score +      # Número de escalas
    0.1 * ancillary_score    # Bagagem, etc
)
```

**Conversão Milhas → BRL**:
```python
effective_price = (miles * R_PER_MILE) + taxes_brl
# R_PER_MILE padrão: 0.03 (configurável)
```

**Normalização**:
- Preço: R$ 200–2000 → score 1.0–0.1
- Duração: 60–600 min → score 1.0–0.1
- Escalas: 0 = 1.0, 1 = 0.5, 2+ = 0.2

#### 4. Provedores (`backend/providers/`)

**Interface Base** (`base_provider.py`):
```python
class BaseProvider(ABC):
    @abstractmethod
    async def search_offers(self, params: SearchParams, trace_id: str) -> List[Offer]:
        pass
```

**Implementações**:
- `duffel_provider.py`: NDC aggregator (stub retorna mock data)
- `smiles_provider.py`: Gol Smiles (mock)
- `latam_provider.py`: LATAM Pass (mock)
- `tudoazul_provider.py`: TudoAzul Azul (mock)

**⚠️ Importante**: No MVP, todos retornam dados mockados. Implementação real requer:
- Duffel: Chamar `POST /air/offer_requests`
- Milhas: Scraping com Playwright (respeitar ToS!)

#### 5. Search Service (`backend/services/search_service.py`)

**Cache Strategy**:
1. Checa Redis (`search:{hash}`)
2. Se hit e age < 30 min → retorna
3. Caso contrário → busca live
4. Armazena em Redis (TTL 30 min) + PostgreSQL (6h)

**Hash de Busca**:
```python
f"{origin}:{destination}:{out_date}:{ret_date}:{pax}:{cabin}"
→ MD5 → cache key
```

## 🗄️ Schema do Banco

### Tabelas Principais

```sql
offers (
  id VARCHAR(100) PK,
  source VARCHAR(50),           -- 'duffel', 'smiles', etc
  offer_type VARCHAR(20),       -- 'cash' ou 'miles'
  cabin VARCHAR(20),

  -- Cash
  currency VARCHAR(3),
  price_cents BIGINT,

  -- Miles
  miles BIGINT,
  miles_program VARCHAR(50),
  taxes_cents BIGINT,

  segments JSONB,               -- Array de voos
  out_date DATE,
  ret_date DATE,

  hash VARCHAR(64) UNIQUE,      -- Para deduplicação
  expires_at TIMESTAMP
)
```

**Segments JSON**:
```json
[
  {
    "carrier": "LA",
    "flightNumber": "3261",
    "from": "GRU", "to": "REC",
    "depart": "2025-11-12T08:20:00-03:00",
    "arrive": "2025-11-12T11:15:00-03:00",
    "durationMinutes": 175,
    "fareClass": "Y",
    "equipment": "A321"
  }
]
```

## 🔧 Configuração e Parametrização

### Variáveis de Ambiente Críticas

```env
# LLM (obrigatório para chat funcionar)
LLM_PROVIDER=openai               # ou 'anthropic', 'azure'
LLM_MODEL=gpt-4-turbo-preview
OPENAI_API_KEY=sk-...

# Pricing
R_PER_MILE=0.03                   # R$ por milha
PRICE_WEIGHT=0.4
DURATION_WEIGHT=0.3
STOPS_WEIGHT=0.2

# Cache
CACHE_TTL_MINUTES=30
LIVE_SEARCH_THRESHOLD_MINUTES=30
```

### Trocar LLM Provider

**OpenAI → Anthropic**:
```env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-opus-20240229
ANTHROPIC_API_KEY=sk-ant-...
```

**Código** (`agents/llm_client.py`):
- `_openai_completion()`: usa `client.chat.completions.create()`
- `_anthropic_completion()`: usa `client.messages.create()`
- Tools convertidos automaticamente

## 🐛 Debugging

### Problema: Chat não responde

**1. Verificar LLM**:
```bash
docker compose logs backend | grep llm
```
Procurar por:
- `llm_client_initialized` → provider correto?
- `llm_error` → API key válida?

**2. Testar diretamente**:
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Oi"}'
```

**3. Verificar function calling**:
```python
# backend/agents/tools.py
logger.info("tool_search_flights", params=params)
```
Se não aparecer no log → LLM não está chamando tools

### Problema: Busca não retorna ofertas

**1. Verificar provedores**:
```bash
docker compose logs backend | grep provider
```

**2. Forçar refresh**:
```bash
curl -X POST http://localhost:8000/api/v1/search?force_live=true \
  -d '{"origin": "GRU", "destination": "REC", ...}'
```

**3. Checar cache**:
```bash
docker compose exec redis redis-cli
> KEYS search:*
> GET search:<hash>
```

### Problema: Ofertas não rankeadas corretamente

**Ajustar pesos**:
```env
PRICE_WEIGHT=0.5     # Priorizar preço
STOPS_WEIGHT=0.3     # Priorizar voos diretos
```

**Ou modificar código** (`services/pricing_engine.py`):
```python
def _calculate_score(self, offer, params):
    # Custom logic here
    if offer.stops_count == 0:
        stops_score = 1.5  # Boost diretos
```

## 🔄 Adicionando Features

### 1. Novo Provedor de Voos

```python
# backend/providers/novo_provider.py
from providers.base_provider import BaseProvider

class NovoProvider(BaseProvider):
    def is_available(self) -> bool:
        return bool(settings.NOVO_API_KEY)

    async def search_offers(self, params: SearchParams, trace_id: str) -> List[Offer]:
        # 1. Chamar API
        response = await httpx.post(
            "https://api.novo.com/search",
            json={"from": params.origin, ...}
        )

        # 2. Normalizar resposta
        offers = []
        for item in response.json()["results"]:
            offers.append(Offer(
                id=f"novo_{item['id']}",
                source="novo",
                offer_type=OfferType.CASH,
                cash=CashPrice(...),
                segments=[...],
                ...
            ))

        return offers
```

**Registrar**:
```python
# services/search_service.py
async def search_cash_offers(self, params, trace_id):
    # ...
    if settings.NOVO_API_KEY:
        novo = NovoProvider()
        offers = await novo.search_offers(params, trace_id)
        all_offers.extend(offers)
```

### 2. Nova Tool para o Agente

```python
# agents/tools.py
def get_tool_definitions(self):
    return [
        # ... tools existentes
        {
            "type": "function",
            "function": {
                "name": "get_seat_map",
                "description": "Obter mapa de assentos de um voo",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "offer_id": {"type": "string"},
                        "segment_index": {"type": "integer"}
                    }
                }
            }
        }
    ]

async def get_seat_map(self, params):
    # Implementação
    pass
```

### 3. Modificar System Prompt

```python
# agents/travel_agent.py
def _build_system_prompt(self):
    return """
    Você é um agente de viagens...

    NOVO: Sempre pergunte se o usuário tem preferência de assento.
    """
```

## 📊 Monitoramento

### Logs Importantes

```python
# Eventos que DEVEM estar nos logs
logger.info("agent_processing", conversation_id, trace_id)
logger.info("tool_search_flights", params, trace_id)
logger.info("duffel_search_complete", count, trace_id)
logger.info("offers_ranked", total_offers, top_score)
logger.error("search_error", error, trace_id)
```

### Rastreamento com Trace ID

Toda request tem `X-Trace-ID`:
```bash
curl -H "X-Trace-ID: test123" http://localhost:8000/api/v1/search
```

Buscar logs:
```bash
docker compose logs backend | grep test123
```

## 🚀 Deploy

### Produção (Docker Compose)

```bash
# Build
docker compose -f docker-compose.prod.yml build

# Deploy
docker compose -f docker-compose.prod.yml up -d

# Migrations
docker compose exec backend alembic upgrade head

# Health check
curl http://your-domain.com/health
```

### Variáveis Essenciais em Prod

```env
ENVIRONMENT=production
LOG_LEVEL=warning
POSTGRES_PASSWORD=<strong-password>
JWT_SECRET=<random-256-bit-key>
OPENAI_API_KEY=<prod-key>
```

## 🔐 Segurança

### Scraping Responsável

Se implementar scraping real:

```python
# workers/scraper.py
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def scrape_miles(program, params):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0...",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        await stealth_async(page)

        # Rate limiting
        await asyncio.sleep(random.uniform(2, 5))

        # Scrape...
```

**⚠️ IMPORTANTE**:
- Respeitar `robots.txt`
- Rate limit < 5 req/min
- Usar rotating proxies
- Não burlar CAPTCHA de forma maliciosa
- Preferir APIs oficiais

### LGPD Compliance

```python
# Ao armazenar dados de passageiros
- Criptografar CPF/passaporte
- Não logar PII
- TTL curto (24h)
- Consentimento explícito no frontend
```

## 🧪 Testes

### Testar Agente

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quero voar de GRU para REC no dia 15/12"
  }'
```

**Esperado**:
1. LLM entende origem/destino/data
2. Chama `search_flights`
3. Retorna ofertas + explicação

### Testar Pricing

```python
# pytest backend/tests/test_pricing.py
def test_ranking():
    offers = [
        # Oferta cara mas direta
        Offer(price_cents=80000, stops=0, duration=180),
        # Oferta barata com escala
        Offer(price_cents=40000, stops=1, duration=360)
    ]

    engine = PricingEngine()
    ranked = engine.rank_offers(offers)

    # Deve priorizar baseado em pesos
    assert ranked[0].score > ranked[1].score
```

## 📚 Recursos Externos

- **Duffel API**: https://duffel.com/docs/api
- **Amadeus Self-Service**: https://developers.amadeus.com
- **Kiwi Tequila**: https://tequila.kiwi.com/portal/docs
- **LangChain**: https://python.langchain.com/docs
- **FastAPI**: https://fastapi.tiangolo.com
- **Nuxt 3**: https://nuxt.com

## 🤝 Convenções de Código

### Python

```python
# Imports
from typing import List, Optional
import structlog

# Logging
logger = structlog.get_logger()
logger.info("event_name", key=value, trace_id=trace_id)

# Async
async def search_offers(self, params: SearchParams) -> List[Offer]:
    pass

# Error handling
try:
    result = await service.do_something()
except Exception as e:
    logger.error("error_event", error=str(e))
    raise
```

### TypeScript/Vue

```typescript
// Composables
const config = useRuntimeConfig()
const router = useRouter()

// API calls
const { data, error } = await $fetch('/api/endpoint')

// Store
const chatStore = useChatStore()
await chatStore.sendMessage(message)
```

## 🎯 Próximos Passos (Roadmap)

### MVP → v1

1. **Integrar API real** (Duffel):
   - Substituir mock em `duffel_provider.py`
   - Testar com sandbox

2. **Scraping controlado** (Smiles):
   - Implementar em `workers/scraper.py`
   - Circuit breaker + rate limit

3. **Emissão real**:
   - `booking_service.py` → chamar Duffel Orders API
   - PNR retrieval

4. **Assentos/Bagagem**:
   - Ancillaries via Duffel
   - UI para seleção

### v1 → v2

- Login OAuth (Google, Apple)
- Histórico de buscas
- Alertas de preço (Celery + email)
- Mobile app (React Native)

---

## 📞 Dúvidas Frequentes (para IA)

**Q: Como adiciono suporte a um novo LLM?**
A: Edite `agents/llm_client.py`, adicione método `_novo_provider_completion()` e registre em `__init__()`.

**Q: Ofertas não aparecem no frontend**
A: Verifique:
1. CORS habilitado no backend
2. `NUXT_PUBLIC_API_BASE` aponta para `http://localhost:8000`
3. Backend retorna `{"ranked": [...]}` no endpoint `/search`

**Q: Como forço busca em tempo real?**
A: `POST /api/v1/search?force_live=true` ou limpe cache Redis.

**Q: Scraping é legal?**
A: Depende do ToS do site. Neste projeto:
- ✅ Usar APIs oficiais
- ⚠️ Scraping apenas se não houver alternativa e dentro dos limites legais
- 🚫 Nunca burlar proteções de forma maliciosa

---

**Última atualização**: 2025-01-15
**Versão do projeto**: MVP 1.0
