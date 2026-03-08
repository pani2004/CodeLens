import { apiClient, handleApiError } from './client'
import type { Repository, RepositorySummary, PaginatedResponse, UsageQuota } from '../types'

/**
 * Get all repositories for current user
 */
export async function getRepositories(page = 1, pageSize = 20): Promise<PaginatedResponse<Repository>> {
  try {
    const response = await apiClient.get<PaginatedResponse<Repository>>('/repos', {
      params: { page, page_size: pageSize },
    })
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * Get repository by ID
 */
export async function getRepository(repoId: string): Promise<Repository> {
  try {
    const response = await apiClient.get<Repository>(`/repos/${repoId}`)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * Analyze a new repository
 */
export async function analyzeRepository(githubUrl: string): Promise<{ repo_id: string; task_id: string }> {
  try {
    const response = await apiClient.post<{ repo_id: string; task_id: string }>('/repos/analyze', {
      github_url: githubUrl,
    })
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * Get repository analysis status
 */
export async function getRepositoryStatus(repoId: string): Promise<{
  status: string
  progress: number
  message?: string
}> {
  try {
    const response = await apiClient.get<{
      status: string
      progress: number
      message?: string
    }>(`/repos/${repoId}/status`)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * Get repository summary
 */
export async function getRepositorySummary(repoId: string): Promise<RepositorySummary> {
  try {
    const response = await apiClient.get<RepositorySummary>(`/repos/${repoId}/summary`)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * Regenerate repository summary
 */
export async function regenerateSummary(repoId: string): Promise<RepositorySummary> {
  try {
    const response = await apiClient.post<RepositorySummary>(`/repos/${repoId}/summary/regenerate`)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * Delete repository
 */
export async function deleteRepository(repoId: string): Promise<void> {
  try {
    await apiClient.delete(`/repos/${repoId}`)
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * Get user's GitHub repositories
 */
export async function getGitHubRepositories(): Promise<Array<{
  name: string
  full_name: string
  url: string
  description: string
  language: string
  stars: number
}>> {
  try {
    const response = await apiClient.get('/repos/github/list')
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * Get usage quota
 */
export async function getUsageQuota(): Promise<UsageQuota> {
  try {
    const response = await apiClient.get<UsageQuota>('/repos/quota')
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}
