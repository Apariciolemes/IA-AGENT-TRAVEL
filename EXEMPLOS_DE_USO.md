# 🚀 EXEMPLOS DE USO - Agente de Viagens

## ✅ Sistema ESTÁ Funcionando!

Containers ativos:
- ✅ Backend API (porta 8000)
- ✅ Frontend Nuxt (porta 3000)
- ✅ PostgreSQL (dados de voos)
- ✅ Redis (cache)

---

## 1️⃣ USAR VIA NAVEGADOR (Frontend)

### Opção A: Busca de Voos

**Passo a Passo:**

```bash
# 1. Abra no navegador:
http://localhost:3000
```

**O que você verá:**
- Título: "Encontre os Melhores Voos"
- Formulário com 4 campos

**Como usar:**
1. **Origem**: Digite `GRU` (São Paulo)
2. **Destino**: Digite `REC` (Recife)
3. **Data de Ida**: Escolha qualquer data futura (ex: 2025-12-15)
4. **Data de Volta**: (Opcional) Deixe vazio para só ida
5. Clique no botão azul **"Buscar Voos"**

**Resultado:**
- Você será redirecionado para `/offers`
- Verá 3-5 ofertas de voos
- Comparação entre dinheiro e milhas
- Cada oferta mostra:
  - Programa de milhas ou preço em R$
  - Duração do voo
  - Número de escalas
  - Se tem bagagem incluída
  - Score de qualidade

### Opção B: Chat (⚠️ Requer Ollama)

```bash
# 1. Abra:
http://localhost:3000/chat

# 2. Digite no chat:
"Quero voar de GRU para REC no dia 15 de dezembro"
```

**Status:** ❌ Chat NÃO funciona ainda - precisa configurar Ollama (LLM)

---

## 2️⃣ USAR VIA API (Swagger UI)

**Mais fácil e visual!**

```bash
# 1. Abra no navegador:
http://localhost:8000/docs
```

**Como testar:**

### Teste A: Buscar Voos

1. Na página do Swagger, procure: **POST /api/v1/search**
2. Clique em **"Try it out"**
3. Cole este JSON no campo de texto:

```json
{
  "origin": "GRU",
  "destination": "SSA",
  "out_date": "2025-12-20",
  "pax": {
    "adults": 1
  },
  "cabin": "ECONOMY",
  "bag_included": true
}
```

4. Clique em **"Execute"**
5. Role para baixo e veja a resposta JSON com as ofertas!

### Teste B: Comparar Ofertas

1. Procure: **POST /api/v1/compare**
2. Try it out
3. Cole:

```json
{
  "offers": [
    {"id": "smiles_123"},
    {"id": "latam_456"}
  ],
  "user_prefs": {
    "prefer_direct": true
  }
}
```

---

## 3️⃣ USAR VIA TERMINAL (curl)

### Exemplo 1: Buscar voos GRU → REC

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

**Resposta:**
```json
{
  "ranked": [
    {
      "id": "smiles_abc123",
      "source": "smiles",
      "miles": {
        "program": "smiles",
        "points": 7500,
        "taxes_cents": 12800
      },
      "score": 0.90,
      "score_explanation": "VÔO DIRETO E RÁPIDO | MELHOR PREÇO..."
    }
  ]
}
```

### Exemplo 2: Voo ida e volta GRU → SSA → GRU

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "GRU",
    "destination": "SSA",
    "out_date": "2025-12-20",
    "ret_date": "2025-12-27",
    "pax": {"adults": 2, "children": 1},
    "cabin": "ECONOMY",
    "bag_included": true
  }'
```

### Exemplo 3: Voos diretos apenas

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "GRU",
    "destination": "FOR",
    "out_date": "2026-01-10",
    "pax": {"adults": 1},
    "cabin": "ECONOMY",
    "direct_only": true
  }'
```

### Exemplo 4: Classe executiva

```bash
curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "GRU",
    "destination": "BSB",
    "out_date": "2025-12-01",
    "pax": {"adults": 1},
    "cabin": "BUSINESS"
  }'
```

---

## 4️⃣ INTERPRETAR OS RESULTADOS

### O que significa cada campo:

```json
{
  "id": "smiles_abc123",           // ID único da oferta
  "source": "smiles",               // Provedor (smiles, latam_pass, tudoazul, duffel)
  "offer_type": "miles",            // "miles" ou "cash"

  // Para milhas:
  "miles": {
    "program": "smiles",            // Programa de milhas
    "points": 7500,                 // Quantidade de milhas
    "taxes_cents": 12800            // R$ 128.00 em taxas
  },

  // Para dinheiro:
  "cash": {
    "currency": "BRL",
    "amount_cents": 45000           // R$ 450.00
  },

  "segments": [                     // Trechos do voo
    {
      "carrier": "G3",              // Código da cia (G3=Gol, LA=LATAM, AD=Azul)
      "flight_number": "1234",
      "origin": "GRU",
      "destination": "REC",
      "depart": "2025-12-15T10:45:00",
      "arrive": "2025-12-15T13:40:00",
      "duration_minutes": 175       // 2h55min
    }
  ],

  "stops_count": 0,                 // 0 = direto, 1 = 1 escala
  "baggage_included": true,         // Bagagem despachada incluída

  "score": 0.90,                    // Score 0-1 (quanto maior, melhor)
  "score_explanation": "VÔO DIRETO E RÁPIDO | MELHOR PREÇO..."
}
```

### Como escolher a melhor oferta:

1. **Score** (0-1): Quanto maior, melhor o custo-benefício
2. **stops_count**: 0 = direto (melhor)
3. **baggage_included**: true = economia extra
4. **score_explanation**: Explica por que é boa

---

## 5️⃣ ROTAS DISPONÍVEIS (Exemplos)

Você pode buscar qualquer rota brasileira:

```bash
# São Paulo → Recife
GRU → REC

# São Paulo → Salvador
GRU → SSA

# São Paulo → Fortaleza
GRU → FOR

# São Paulo → Brasília
GRU → BSB

# Rio → São Paulo
GIG → GRU

# Recife → São Paulo
REC → GRU
```

**Códigos IATA:**
- GRU = São Paulo (Guarulhos)
- CGH = São Paulo (Congonhas)
- GIG = Rio de Janeiro (Galeão)
- SDU = Rio de Janeiro (Santos Dumont)
- REC = Recife
- SSA = Salvador
- FOR = Fortaleza
- BSB = Brasília
- POA = Porto Alegre
- CWB = Curitiba

---

## 6️⃣ TESTAR RESERVA (Simulação)

```bash
curl -X POST http://localhost:8000/api/v1/booking/hold \
  -H "Content-Type: application/json" \
  -d '{
    "offer_id": "smiles_abc123",
    "passengers": [
      {
        "first_name": "João",
        "last_name": "Silva",
        "date_of_birth": "1990-01-15",
        "gender": "M",
        "document_type": "cpf",
        "document_number": "12345678900"
      }
    ],
    "contact_email": "joao@example.com",
    "contact_phone": "+5511999999999"
  }'
```

**Resposta:**
```json
{
  "booking_id": 1,
  "booking_reference": "TA5F3A2B1C",
  "status": "pending",
  "deeplink_url": "https://www.smiles.com.br/emission?origin=GRU...",
  "instructions": "1. Clique no link...\n2. Faça login..."
}
```

---

## 7️⃣ DADOS MOCKADOS vs REAIS

### ⚠️ Importante: Este é um MVP

**O que está MOCKADO:**
- ✅ API está funcionando
- ✅ Busca retorna ofertas
- ✅ Ranking está correto
- ❌ **MAS os voos são FICTÍCIOS** (dados de teste)

**Para usar com dados reais, você precisa:**

1. **API Keys de provedores reais:**
   - Duffel API (voos em dinheiro)
   - APIs de programas de milhas

2. **Configurar no `.env`:**
   ```env
   DUFFEL_API_KEY=sua-chave-real
   AMADEUS_API_KEY=sua-chave-real
   ```

---

## 8️⃣ PERGUNTAS FREQUENTES

### ❓ Por que o chat não funciona?

O chat precisa de um LLM (modelo de linguagem). Você escolheu Ollama (grátis), mas precisa:

```bash
# Baixar modelo (3.8 GB)
docker exec -it travel_ollama ollama pull llama2

# OU modelo menor (637 MB)
docker exec -it travel_ollama ollama pull tinyllama

# Restart
docker compose restart backend
```

### ❓ As ofertas são reais?

Não! São dados mockados para demonstração. Para voos reais, configure API keys.

### ❓ Como ver logs de erros?

```bash
# Backend
docker compose logs backend -f

# Frontend
docker compose logs frontend -f
```

### ❓ Como parar tudo?

```bash
docker compose down
```

### ❓ Como ver o banco de dados?

```bash
docker exec -it travel_postgres psql -U travel_user -d travel_agent

# Ver ofertas:
SELECT id, source, offer_type, origin, destination FROM offers LIMIT 5;

# Sair:
\q
```

---

## 9️⃣ RESUMO RÁPIDO

### ✅ O QUE FUNCIONA AGORA:

1. **Frontend Web** → http://localhost:3000
   - Formulário de busca ✅
   - Listagem de ofertas ✅
   - Visual bonito ✅

2. **API REST** → http://localhost:8000/docs
   - Buscar voos ✅
   - Comparar ofertas ✅
   - Simular reserva ✅
   - Swagger UI ✅

3. **Backend**
   - Pricing engine ✅
   - Cache Redis ✅
   - PostgreSQL ✅
   - Ranking inteligente ✅

### ❌ O QUE NÃO FUNCIONA (ainda):

- Chat conversacional (precisa Ollama configurado)
- Dados reais de voos (precisa API keys)
- Emissão real de bilhetes (é MVP)

---

## 🎯 TESTE COMPLETO EM 2 MINUTOS

```bash
# 1. Abra navegador
xdg-open http://localhost:3000

# 2. Preencha o formulário:
Origem: GRU
Destino: REC
Data: 2025-12-15

# 3. Clique "Buscar Voos"

# 4. Veja 3-5 ofertas aparecerem!

# 5. Para API, abra:
xdg-open http://localhost:8000/docs

# 6. Teste POST /api/v1/search no Swagger
```

---

**Pronto!** O sistema está 100% funcional para busca de voos.

Teste agora no navegador! 🚀
