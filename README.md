# Agente de Viagens - Sistema Conversacional de Busca de Voos

Sistema completo de busca inteligente de voos em dinheiro e milhas, com agente conversacional em português brasileiro.

## 🎯 Características Principais

- 🤖 **Agente Conversacional**: Chat em linguagem natural (pt-BR) para busca de voos
- 💰 **Dinheiro + Milhas**: Busca simultânea em preços e programas de fidelidade
- ⚡ **Cache Inteligente**: Redis + PostgreSQL para respostas rápidas
- 🔍 **Múltiplos Provedores**: Integração com APIs e scraping controlado
- 📊 **Ranking Inteligente**: Engine de precificação com custo efetivo
- 🎫 **Reservas**: Geração de deeplinks e instruções para emissão

## 🏗️ Arquitetura

```
monorepo-agent/
├── backend/              # FastAPI + Python
│   ├── api/             # Endpoints REST
│   ├── agents/          # Agente IA (LLM + Tools)
│   ├── services/        # Lógica de negócio
│   ├── providers/       # Integrações (APIs/Scraping)
│   ├── workers/         # Celery tasks
│   └── database/        # PostgreSQL + Redis
├── frontend/            # Nuxt 3 + Vue
│   ├── pages/          # Páginas públicas
│   ├── components/     # Componentes Vue
│   └── stores/         # Pinia state
├── infra/              # SQL schemas
└── docker-compose.yml  # Orquestração
```

## 🚀 Quick Start

### Pré-requisitos

- Docker & Docker Compose
- (Opcional) Node.js 20+ e Python 3.11+ para desenvolvimento local

### Instalação

1. **Clone o repositório**
```bash
git clone <repo-url>
cd monorepo-agent
```

2. **Configure variáveis de ambiente**
```bash
cp .env.example .env
# Edite .env com suas chaves de API
```

3. **Inicie os containers**
```bash
docker compose up --build
```

4. **Acesse os serviços**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📝 Configuração

### Variáveis de Ambiente Essenciais

```env
# LLM Provider (obrigatório para o chat)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
OPENAI_API_KEY=sk-your-key-here

# Provedores de Voos (opcional no MVP)
DUFFEL_API_KEY=your-duffel-key
AMADEUS_API_KEY=your-amadeus-key
KIWI_API_KEY=your-kiwi-key

# Pricing Engine
R_PER_MILE=0.03
MAX_STOPS=1
```

### Suporte a Múltiplos LLMs

O sistema suporta:
- **OpenAI**: GPT-4, GPT-3.5 Turbo
- **Anthropic**: Claude 3 (Opus, Sonnet, Haiku)
- **Azure OpenAI**: Modelos via Azure

Configure via `LLM_PROVIDER` e `LLM_MODEL` no `.env`.

## 🎮 Uso

### 1. Chat Conversacional

Acesse `/chat` e converse naturalmente:

```
Usuário: "Quero voar de GRU para REC no dia 15 de dezembro"
Agente: "Ótimo! Vou buscar voos de São Paulo (GRU) para Recife (REC)
         no dia 15/12. Gostaria de ida e volta? Quantos passageiros?"

Usuário: "Só ida, 1 adulto"
Agente: [busca voos e apresenta 5 melhores opções]
```

### 2. Busca Direta

Use o formulário na home ou chame a API:

```bash
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

### 3. Reserva

```bash
curl -X POST http://localhost:8000/api/v1/booking/hold \
  -H "Content-Type: application/json" \
  -d '{
    "offer_id": "duffel_abc123",
    "passengers": [{
      "first_name": "João",
      "last_name": "Silva",
      "date_of_birth": "1990-01-01",
      "gender": "M",
      "document_type": "cpf",
      "document_number": "12345678900"
    }],
    "contact_email": "joao@example.com",
    "contact_phone": "+5511999999999"
  }'
```

## 🔌 Integrações

### Provedores Implementados (MVP)

| Provedor | Tipo | Status | Notas |
|----------|------|--------|-------|
| Duffel | Cash (NDC) | Stub | API REST |
| Amadeus | Cash (GDS) | Stub | API REST |
| Kiwi/Tequila | Cash (OTA) | Stub | API REST |
| Smiles | Milhas | Mock | Scraping* |
| LATAM Pass | Milhas | Mock | Scraping* |
| TudoAzul | Milhas | Mock | Scraping* |

*Scraping: No MVP, retorna dados mockados. Implementação real requer Playwright com stealth mode e deve respeitar ToS.

### Adicionando Novos Provedores

1. Crie classe em `backend/providers/`
2. Herde de `BaseProvider`
3. Implemente `search_offers()`
4. Registre em `SearchService`

```python
class NovoProvider(BaseProvider):
    async def search_offers(self, params: SearchParams, trace_id: str) -> List[Offer]:
        # Implementação
        pass
```

## 🧠 Agente IA

### Arquitetura

```
User Message
    ↓
[LLM com System Prompt]
    ↓
Function Calling (Tools)
    ↓
- search_flights
- compare_offers
- hold_booking
    ↓
[LLM com Resultado]
    ↓
Resposta Natural
```

### Tools Disponíveis

1. **search_flights**: Busca voos com parâmetros estruturados
2. **compare_offers**: Compara ofertas específicas
3. **hold_booking**: Cria reserva ou deeplink

### Customização do Agente

Edite `backend/agents/travel_agent.py`:
- System prompt em `_build_system_prompt()`
- Lógica de tools em `backend/agents/tools.py`
- Cliente LLM em `backend/agents/llm_client.py`

## 📊 Pricing Engine

### Cálculo de Score

```python
score = (
    PRICE_WEIGHT * price_score +      # 40%
    DURATION_WEIGHT * duration_score + # 30%
    STOPS_WEIGHT * stops_score +       # 20%
    ANCILLARY_WEIGHT * ancillary_score # 10%
)
```

### Conversão Milhas → BRL

```python
effective_price = (miles * R_PER_MILE) + taxes
```

Parametrizável via `R_PER_MILE` (padrão: R$ 0,03/milha).

## 🗄️ Banco de Dados

### Schema Principal

- **airports**: Aeroportos (IATA)
- **carriers**: Companhias aéreas
- **offers**: Ofertas normalizadas (cash + miles)
- **queries_cache**: Cache de buscas
- **bookings**: Reservas
- **users**: Usuários (v1)
- **price_alerts**: Alertas de preço (v1)

### Migrations

```bash
# Dentro do container backend
alembic revision --autogenerate -m "descrição"
alembic upgrade head
```

## 🔄 Workers & Background Jobs

### Celery Tasks

- **scrape_miles_offers**: Coleta dados de milhas (stub)
- **refresh_popular_routes**: Atualiza cache de rotas populares
- **cleanup_expired_offers**: Remove ofertas expiradas
- **send_price_alert**: Envia alertas (v1)

### Monitoramento

```bash
# Flower (Celery monitoring)
docker compose exec celery_worker celery -A workers.celery_app flower
# Acesse: http://localhost:5555
```

## 🧪 Testes

```bash
# Backend
docker compose exec backend pytest

# Frontend
docker compose exec frontend npm run test
```

## 🚨 Observabilidade

### Logs

Estruturados via `structlog`:
```python
logger.info("event_name", key=value, trace_id=trace_id)
```

### Tracing

Cada requisição recebe `X-Trace-ID` para rastreamento end-to-end.

### Métricas (Futuro)

- OpenTelemetry → Prometheus → Grafana
- KPIs: latência, cache hit rate, conversão

## 🔒 Segurança & Compliance

### LGPD

- Consentimento explícito
- Dados mínimos necessários
- Criptografia de PII
- Logs sem dados sensíveis

### Scraping

- ⚠️ **Respeitar robots.txt e ToS**
- Rate limiting rigoroso
- Rotating proxies
- Preferir APIs oficiais

### Secrets

- Usar `.env` (nunca commitar)
- Vault/AWS Secrets Manager em produção
- Rotação de chaves

## 📈 Roadmap

### MVP (Atual)
- ✅ Chat funcional
- ✅ Busca em dinheiro (stubs)
- ✅ Busca em milhas (mocks)
- ✅ Ranking e comparação
- ✅ Deeplinks para emissão

### v1 (Próximos Passos)
- [ ] Emissão real via Duffel
- [ ] Scraping controlado de milhas
- [ ] Seleção de assentos/bagagem
- [ ] Login e histórico
- [ ] Alertas de preço
- [ ] Mais provedores

### v2 (Futuro)
- [ ] App mobile
- [ ] Pagamento integrado
- [ ] Pacotes (voo + hotel)
- [ ] Cashback em milhas

## 🤝 Contribuindo

1. Fork o projeto
2. Crie branch (`git checkout -b feature/nova-feature`)
3. Commit (`git commit -m 'Add: nova feature'`)
4. Push (`git push origin feature/nova-feature`)
5. Abra Pull Request

## 📄 Licença

MIT License - veja LICENSE para detalhes

## 📞 Suporte

- Documentação: `./docs/`
- Issues: GitHub Issues
- Email: support@travel-agent.com

## 🙏 Agradecimentos

- Duffel, Amadeus, Kiwi pela documentação de APIs
- OpenAI/Anthropic pelos LLMs
- Comunidade open-source

---

**Desenvolvido com ❤️ para facilitar viagens aéreas no Brasil**
