import { apiClient, handleApiError } from './client'
import type { User, AuthTokens } from '../types'

/**
 * Initiate GitHub OAuth flow
 */
export async function initiateGitHubLogin(): Promise<string> {
  try {
    const response = await apiClient.get<{ authorization_url: string }>('/auth/github/login')
    return response.data.authorization_url
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * Handle GitHub OAuth callback
 */
export async function handleGitHubCallback(code: string): Promise<{ user: User; tokens: AuthTokens }> {
  try {
    const response = await apiClient.post<{ user: User; tokens: AuthTokens }>('/auth/github/callback', {
      code,
    })
    
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', response.data.tokens.access_token)
      localStorage.setItem('refresh_token', response.data.tokens.refresh_token)
    }
    
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * Get current user
 */
export async function getCurrentUser(): Promise<User> {
  try {
    const response = await apiClient.get<User>('/auth/me')
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * Refresh access token
 */
export async function refreshAccessToken(refreshToken: string): Promise<AuthTokens> {
  try {
    const response = await apiClient.post<AuthTokens>('/auth/refresh', {
      refresh_token: refreshToken,
    })
    
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', response.data.access_token)
    }
    
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * Logout user
 */
export async function logout(): Promise<void> {
  try {
    await apiClient.post('/auth/logout')
  } catch (error) {
    console.error('Logout error:', error)
  } finally {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  }
}
