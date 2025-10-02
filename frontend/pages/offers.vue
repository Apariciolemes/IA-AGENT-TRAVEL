<template>
  <div class="min-h-screen bg-gray-50">
    <div class="container mx-auto px-4 py-8">
      <!-- Header -->
      <div class="mb-6 flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Ofertas Disponíveis</h1>
          <p v-if="searchParams" class="text-gray-600">
            {{ searchParams.origin }} → {{ searchParams.destination }}
            | {{ formatDate(searchParams.outDate) }}
            <span v-if="searchParams.retDate">- {{ formatDate(searchParams.retDate) }}</span>
          </p>
        </div>
        <NuxtLink to="/" class="btn-secondary">
          Nova Busca
        </NuxtLink>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        <p class="mt-4 text-gray-600">Buscando melhores ofertas...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="card text-center py-12">
        <div class="text-4xl mb-4">⚠️</div>
        <p class="text-red-600 mb-4">{{ error }}</p>
        <button @click="searchOffers" class="btn-primary">
          Tentar Novamente
        </button>
      </div>

      <!-- Results -->
      <div v-else-if="offers.length > 0" class="space-y-4">
        <!-- Filters -->
        <div class="card flex gap-4 items-center">
          <label class="flex items-center gap-2">
            <input v-model="filters.cashOnly" type="checkbox" class="rounded" />
            <span>Somente Dinheiro</span>
          </label>
          <label class="flex items-center gap-2">
            <input v-model="filters.milesOnly" type="checkbox" class="rounded" />
            <span>Somente Milhas</span>
          </label>
          <label class="flex items-center gap-2">
            <input v-model="filters.directOnly" type="checkbox" class="rounded" />
            <span>Voos Diretos</span>
          </label>
        </div>

        <!-- Offer Cards -->
        <div
          v-for="offer in filteredOffers"
          :key="offer.id"
          class="card hover:shadow-lg transition-shadow cursor-pointer"
          @click="selectOffer(offer)"
        >
          <div class="flex justify-between items-start">
            <!-- Flight Info -->
            <div class="flex-1">
              <div class="flex items-center gap-4 mb-3">
                <div class="text-sm text-gray-600">{{ offer.source.toUpperCase() }}</div>
                <div
                  :class="[
                    'px-2 py-1 rounded text-xs font-medium',
                    offer.type === 'cash' ? 'bg-green-100 text-green-800' : 'bg-purple-100 text-purple-800'
                  ]"
                >
                  {{ offer.type === 'cash' ? 'Dinheiro' : 'Milhas' }}
                </div>
              </div>

              <!-- Segments -->
              <div class="space-y-2 mb-3">
                <div v-for="(segment, idx) in offer.segments" :key="idx" class="flex items-center gap-4">
                  <div class="font-semibold">
                    {{ segment.from }} → {{ segment.to }}
                  </div>
                  <div class="text-sm text-gray-600">
                    {{ segment.carrier }}{{ segment.flight_number }}
                  </div>
                  <div class="text-sm text-gray-600">
                    {{ formatTime(segment.depart) }} - {{ formatTime(segment.arrive) }}
                  </div>
                </div>
              </div>

              <!-- Details -->
              <div class="flex gap-4 text-sm text-gray-600">
                <span>⏱️ {{ formatDuration(offer.duration_minutes) }}</span>
                <span>{{ offer.stops === 0 ? '✈️ Direto' : `🔄 ${offer.stops} escala(s)` }}</span>
                <span>{{ offer.baggage_included ? '🧳 Bagagem incluída' : '🚫 Bagagem não incluída' }}</span>
              </div>

              <!-- Explanation -->
              <div v-if="offer.explanation" class="mt-3 text-sm text-gray-500 italic">
                {{ offer.explanation }}
              </div>
            </div>

            <!-- Price -->
            <div class="text-right ml-6">
              <div v-if="offer.type === 'cash'" class="text-3xl font-bold text-primary-600">
                R$ {{ offer.price.cash.amount.toFixed(2) }}
              </div>
              <div v-else>
                <div class="text-3xl font-bold text-purple-600">
                  {{ offer.price.miles.points.toLocaleString() }}
                </div>
                <div class="text-sm text-gray-600">
                  milhas + R$ {{ offer.price.miles.taxes.toFixed(2) }}
                </div>
                <div class="text-xs text-gray-500 mt-1">
                  {{ offer.price.miles.program }}
                </div>
              </div>

              <button class="btn-primary mt-4 w-full">
                Selecionar
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- No Results -->
      <div v-else class="card text-center py-12">
        <div class="text-4xl mb-4">🔍</div>
        <p class="text-gray-600">Nenhuma oferta encontrada para esta busca.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const config = useRuntimeConfig()

const searchParams = ref<any>(null)
const offers = ref<any[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const filters = ref({
  cashOnly: false,
  milesOnly: false,
  directOnly: false
})

// Parse search params from URL
onMounted(() => {
  searchParams.value = {
    origin: route.query.origin,
    destination: route.query.destination,
    outDate: route.query.outDate,
    retDate: route.query.retDate
  }

  if (searchParams.value.origin && searchParams.value.destination && searchParams.value.outDate) {
    searchOffers()
  }
})

const searchOffers = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await $fetch(`${config.public.apiBase}/api/v1/search`, {
      method: 'POST',
      body: {
        origin: searchParams.value.origin,
        destination: searchParams.value.destination,
        out_date: searchParams.value.outDate,
        ret_date: searchParams.value.retDate,
        pax: { adults: 1 },
        cabin: 'ECONOMY',
        bag_included: true
      }
    })

    offers.value = response.ranked || []
  } catch (err: any) {
    error.value = err.message || 'Erro ao buscar ofertas'
  } finally {
    loading.value = false
  }
}

const filteredOffers = computed(() => {
  let filtered = offers.value

  if (filters.value.cashOnly) {
    filtered = filtered.filter(o => o.type === 'cash')
  }
  if (filters.value.milesOnly) {
    filtered = filtered.filter(o => o.type === 'miles')
  }
  if (filters.value.directOnly) {
    filtered = filtered.filter(o => o.stops === 0)
  }

  return filtered
})

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('pt-BR')
}

const formatTime = (dateTimeStr: string) => {
  return new Date(dateTimeStr).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatDuration = (minutes: number) => {
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return `${hours}h${mins.toString().padStart(2, '0')}m`
}

const selectOffer = (offer: any) => {
  navigateTo(`/offer/${offer.id}`)
}
</script>
