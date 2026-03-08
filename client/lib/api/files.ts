import { apiClient } from './client'

export interface FileContentResponse {
  content: string
  file_path: string
  language: string
  size: number
}

export async function getFileContent(repoId: string, filePath: string): Promise<FileContentResponse> {
  const response = await apiClient.get<FileContentResponse>(
    `/repos/${repoId}/files`,
    { params: { file_path: filePath } }
  )
  return response.data
}
