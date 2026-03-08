import { apiClient, handleApiError } from './client'
import type { ChatMessage, ChatRequest, ChatResponse } from '../types'

/**
 * Send a chat message (streaming)
 */
export async function* sendChatMessage(
  repoId: string,
  message: string,
  filePath?: string
): AsyncGenerator<string> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  
  const request: ChatRequest = {
    repo_id: repoId,
    message,
    ...(filePath && { file_path: filePath }),
  }
  
  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` }),
    },
    body: JSON.stringify(request),
  })

  if (!response.ok) {
    throw new Error('Failed to send message')
  }

  const reader = response.body?.getReader()
  const decoder = new TextDecoder()

  if (!reader) {
    throw new Error('No response body')
  }

  try {
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) break
      
      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') {
            return
          }
          try {
            const parsed = JSON.parse(data)
            if (parsed.content) {
              yield parsed.content
            }
          } catch (e) {
            // Skip invalid JSON
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}

/**
 * Send a non-streaming chat message
 */
export async function sendChatMessageSync(request: ChatRequest): Promise<ChatResponse> {
  try {
    const response = await apiClient.post<ChatResponse>('/chat/sync', request)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * Get chat history for a repository
 */
export async function getChatHistory(repoId: string): Promise<ChatMessage[]> {
  try {
    const response = await apiClient.get<{ messages: ChatMessage[] }>(`/chat/history/${repoId}`)
    return response.data.messages
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * Clear chat history for a repository
 */
export async function clearChatHistory(repoId: string): Promise<void> {
  try {
    await apiClient.delete(`/chat/history/${repoId}`)
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * Get suggested prompts for a repository
 */
export async function getSuggestedPrompts(repoId: string): Promise<string[]> {
  try {
    const response = await apiClient.get<{ prompts: string[] }>(`/chat/prompts/${repoId}`)
    return response.data.prompts
  } catch (error) {
    return [
      "What does this project do?",
      "Explain the main architecture",
      "Show me the entry points",
      "What are the key dependencies?",
      "How does authentication work?",
    ]
  }
}
