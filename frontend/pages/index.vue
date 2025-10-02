<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
    <!-- Hero Section -->
    <div class="container mx-auto px-4 py-16">
      <div class="text-center mb-12">
        <h1 class="text-5xl font-bold text-gray-900 mb-4">
          Encontre os Melhores Voos
        </h1>
        <p class="text-xl text-gray-600 mb-8">
          Compare preços em dinheiro e milhas com nosso agente inteligente
        </p>
      </div>

      <!-- Quick Search Form -->
      <div class="max-w-4xl mx-auto card mb-12">
        <form @submit.prevent="handleQuickSearch" class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Origem
              </label>
              <input
                v-model="searchForm.origin"
                type="text"
                placeholder="GRU"
                class="input-field uppercase"
                maxlength="3"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Destino
              </label>
              <input
                v-model="searchForm.destination"
                type="text"
                placeholder="REC"
                class="input-field uppercase"
                maxlength="3"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Data de Ida
              </label>
              <input
                v-model="searchForm.outDate"
                type="date"
                class="input-field"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Data de Volta (opcional)
              </label>
              <input
                v-model="searchForm.retDate"
                type="date"
                class="input-field"
              />
            </div>
          </div>

          <button type="submit" class="btn-primary w-full text-lg">
            Buscar Voos
          </button>
        </form>

        <div class="mt-6 text-center">
          <p class="text-gray-600 mb-4">Ou converse com nosso agente</p>
          <NuxtLink to="/chat" class="btn-secondary inline-block">
            Iniciar Chat
          </NuxtLink>
        </div>
      </div>

      <!-- Features -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
        <div class="card text-center">
          <div class="text-4xl mb-4">💰</div>
          <h3 class="text-xl font-semibold mb-2">Dinheiro e Milhas</h3>
          <p class="text-gray-600">
            Compare preços em reais e pontos de todos os programas
          </p>
        </div>

        <div class="card text-center">
          <div class="text-4xl mb-4">🤖</div>
          <h3 class="text-xl font-semibold mb-2">Agente Inteligente</h3>
          <p class="text-gray-600">
            Converse naturalmente para encontrar sua viagem ideal
          </p>
        </div>

        <div class="card text-center">
          <div class="text-4xl mb-4">⚡</div>
          <h3 class="text-xl font-semibold mb-2">Resultados Rápidos</h3>
          <p class="text-gray-600">
            Cache inteligente e busca em tempo real quando necessário
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const router = useRouter()

const searchForm = ref({
  origin: '',
  destination: '',
  outDate: '',
  retDate: ''
})

const handleQuickSearch = () => {
  // Navigate to results page with search params
  const query: any = {
    origin: searchForm.value.origin,
    destination: searchForm.value.destination,
    outDate: searchForm.value.outDate
  }

  if (searchForm.value.retDate) {
    query.retDate = searchForm.value.retDate
  }

  router.push({
    path: '/offers',
    query
  })
}
</script>
