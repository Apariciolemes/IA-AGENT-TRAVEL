<template>
  <div class="min-h-screen bg-gray-50">
    <div class="container mx-auto px-4 py-8 max-w-4xl">
      <!-- Header -->
      <div class="mb-6 flex justify-between items-center">
        <div>
          <h1 class="text-3xl font-bold text-gray-900">Chat com Agente</h1>
          <p class="text-gray-600">Converse naturalmente para encontrar voos</p>
        </div>
        <NuxtLink to="/" class="btn-secondary">
          Voltar
        </NuxtLink>
      </div>

      <!-- Chat Container -->
      <div class="card min-h-[600px] flex flex-col">
        <!-- Messages -->
        <div ref="messagesContainer" class="flex-1 overflow-y-auto mb-4 space-y-4">
          <!-- Welcome Message -->
          <div v-if="chatStore.messages.length === 0" class="text-center py-12">
            <div class="text-6xl mb-4">✈️</div>
            <h2 class="text-2xl font-semibold text-gray-800 mb-2">
              Olá! Como posso ajudar?
            </h2>
            <p class="text-gray-600 mb-6">
              Me diga para onde você quer viajar e eu vou encontrar as melhores opções!
            </p>

            <!-- Quick Suggestions -->
            <div class="flex flex-wrap gap-2 justify-center">
              <button
                v-for="suggestion in quickSuggestions"
                :key="suggestion"
                @click="sendSuggestion(suggestion)"
                class="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm transition-colors"
              >
                {{ suggestion }}
              </button>
            </div>
          </div>

          <!-- Chat Messages -->
          <div
            v-for="(message, index) in chatStore.messages"
            :key="index"
            :class="[
              'flex',
              message.role === 'user' ? 'justify-end' : 'justify-start'
            ]"
          >
            <div
              :class="[
                'max-w-[80%] rounded-lg px-4 py-3',
                message.role === 'user'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-200 text-gray-900'
              ]"
            >
              <div class="whitespace-pre-wrap">{{ message.content }}</div>
            </div>
          </div>

          <!-- Loading Indicator -->
          <div v-if="chatStore.isLoading" class="flex justify-start">
            <div class="bg-gray-200 rounded-lg px-4 py-3">
              <div class="flex space-x-2">
                <div class="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                <div class="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                <div class="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Offers Display -->
        <div v-if="chatStore.offers.length > 0" class="mb-4 border-t pt-4">
          <h3 class="font-semibold text-lg mb-3">Ofertas Encontradas:</h3>
          <div class="space-y-2 max-h-48 overflow-y-auto">
            <div
              v-for="offer in chatStore.offers"
              :key="offer.id"
              class="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer"
              @click="viewOffer(offer)"
            >
              <div class="flex justify-between items-start">
                <div class="flex-1">
                  <div class="font-medium">
                    {{ offer.segments[0].from }} → {{ offer.segments[offer.segments.length - 1].to }}
                  </div>
                  <div class="text-sm text-gray-600">
                    {{ formatDuration(offer.duration_minutes) }} |
                    {{ offer.stops === 0 ? 'Direto' : `${offer.stops} escala(s)` }}
                  </div>
                  <div v-if="offer.explanation" class="text-xs text-gray-500 mt-1">
                    {{ offer.explanation }}
                  </div>
                </div>
                <div class="text-right">
                  <div v-if="offer.type === 'cash'" class="font-semibold text-primary-600">
                    R$ {{ offer.price.cash.amount.toFixed(2) }}
                  </div>
                  <div v-else class="font-semibold text-purple-600">
                    {{ offer.price.miles.points.toLocaleString() }} milhas
                    <div class="text-xs text-gray-600">+ R$ {{ offer.price.miles.taxes.toFixed(2) }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Input Area -->
        <div class="border-t pt-4">
          <form @submit.prevent="sendMessage" class="flex gap-2">
            <input
              v-model="messageInput"
              type="text"
              placeholder="Digite sua mensagem..."
              class="input-field flex-1"
              :disabled="chatStore.isLoading"
            />
            <button
              type="submit"
              class="btn-primary"
              :disabled="!messageInput.trim() || chatStore.isLoading"
            >
              Enviar
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useChatStore } from '~/stores/chat'

const chatStore = useChatStore()
const messageInput = ref('')
const messagesContainer = ref<HTMLElement | null>(null)

const quickSuggestions = [
  'Quero voar de GRU para REC em 15 de dezembro',
  'Buscar voos em milhas',
  'Mostrar só voos diretos'
]

const sendMessage = async () => {
  if (!messageInput.value.trim()) return

  const message = messageInput.value
  messageInput.value = ''

  await chatStore.sendMessage(message)

  // Scroll to bottom
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const sendSuggestion = async (suggestion: string) => {
  messageInput.value = suggestion
  await sendMessage()
}

const formatDuration = (minutes: number) => {
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return `${hours}h${mins.toString().padStart(2, '0')}m`
}

const viewOffer = (offer: any) => {
  // Navigate to offer details
  navigateTo(`/offer/${offer.id}`)
}
</script>
