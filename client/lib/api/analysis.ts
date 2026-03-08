import { apiClient, handleApiError } from './client'
import type { DependencyGraph, ExecutionFlow } from '../types'

/**
 * Get dependency graph for a repository
 */
export async function getDependencyGraph(
  repoId: string,
  language?: string,
  depth?: number
): Promise<DependencyGraph> {
  try {
    const response = await apiClient.get<DependencyGraph>(`/analysis/${repoId}/graph`, {
      params: {
        ...(language && { language }),
        ...(depth && { depth }),
      },
      timeout: 60000, // 60 seconds for graph generation
    })
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * Get execution flows for a repository
 */
export async function getExecutionFlows(repoId: string): Promise<ExecutionFlow[]> {
  try {
    const response = await apiClient.get<{ flows: ExecutionFlow[] }>(`/analysis/${repoId}/flows`)
    return response.data.flows
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}

/**
 * Get a specific execution flow detail
 */
export async function getFlowDetail(repoId: string, flowId: string): Promise<ExecutionFlow> {
  try {
    const response = await apiClient.get<ExecutionFlow>(`/analysis/${repoId}/flows/${flowId}`)
    return response.data
  } catch (error) {
    throw new Error(handleApiError(error))
  }
}
