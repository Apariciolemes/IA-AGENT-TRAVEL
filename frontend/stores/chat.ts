import { defineStore } from 'pinia'

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: string
}

export interface Offer {
  id: string
  source: string
  type: 'cash' | 'miles'
  price: {
    cash?: {
      amount: number
      currency: string
    }
    miles?: {
      program: string
      points: number
      taxes: number
    }
  }
  segments: any[]
  duration_minutes: number
  stops: number
  baggage_included: boolean
  score?: number
  explanation?: string
}

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [] as ChatMessage[],
    conversationId: null as string | null,
    offers: [] as Offer[],
    isLoading: false,
    error: null as string | null
  }),

  actions: {
    addMessage(message: ChatMessage) {
      this.messages.push(message)
    },

    async sendMessage(content: string) {
      // Add user message
      this.addMessage({
        role: 'user',
        content,
        timestamp: new Date().toISOString()
      })

      this.isLoading = true
      this.error = null

      try {
        const config = useRuntimeConfig()
        const response = await $fetch(`${config.public.apiBase}/api/v1/chat`, {
          method: 'POST',
          body: {
            message: content,
            conversation_id: this.conversationId,
            history: this.messages.slice(-6, -1) // Last 5 messages before current
          }
        })

        // Add assistant response
        this.addMessage({
          role: 'assistant',
          content: response.message,
          timestamp: new Date().toISOString()
        })

        // Update conversation ID
        if (response.conversation_id) {
          this.conversationId = response.conversation_id
        }

        // Update offers if provided
        if (response.offers) {
          this.offers = response.offers
        }

      } catch (error: any) {
        this.error = error.message || 'Erro ao enviar mensagem'
        this.addMessage({
          role: 'assistant',
          content: 'Desculpe, ocorreu um erro. Por favor, tente novamente.',
          timestamp: new Date().toISOString()
        })
      } finally {
        this.isLoading = false
      }
    },

    clearChat() {
      this.messages = []
      this.conversationId = null
      this.offers = []
      this.error = null
    }
  }
})
