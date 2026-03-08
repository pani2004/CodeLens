import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { ChatMessage } from '@/lib/types'

interface ChatStore {
  // Store messages by repo ID
  chatHistory: Record<string, ChatMessage[]>
  
  // Actions
  setMessages: (repoId: string, messages: ChatMessage[]) => void
  addMessage: (repoId: string, message: ChatMessage) => void
  updateLastMessage: (repoId: string, content: string) => void
  clearMessages: (repoId: string) => void
  getMessages: (repoId: string) => ChatMessage[]
}

export const useChatStore = create<ChatStore>()(
  persist(
    (set, get) => ({
      chatHistory: {},

      setMessages: (repoId, messages) =>
        set((state) => ({
          chatHistory: {
            ...state.chatHistory,
            [repoId]: messages,
          },
        })),

      addMessage: (repoId, message) =>
        set((state) => ({
          chatHistory: {
            ...state.chatHistory,
            [repoId]: [...(state.chatHistory[repoId] || []), message],
          },
        })),

      updateLastMessage: (repoId, content) =>
        set((state) => {
          const messages = state.chatHistory[repoId] || []
          if (messages.length === 0) return state

          const updatedMessages = [...messages]
          const lastMessage = updatedMessages[messages.length - 1]

          if (lastMessage.id === 'streaming') {
            updatedMessages[messages.length - 1] = { ...lastMessage, content }
          } else {
            updatedMessages.push({
              id: 'streaming',
              role: 'assistant',
              content,
              timestamp: new Date().toISOString(),
            })
          }

          return {
            chatHistory: {
              ...state.chatHistory,
              [repoId]: updatedMessages,
            },
          }
        }),

      clearMessages: (repoId) =>
        set((state) => ({
          chatHistory: {
            ...state.chatHistory,
            [repoId]: [],
          },
        })),

      getMessages: (repoId) => get().chatHistory[repoId] || [],
    }),
    {
      name: 'codelens-chat-storage',
      storage: createJSONStorage(() => sessionStorage),
    }
  )
)
