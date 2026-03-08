// User types
export interface User {
  id: string
  github_id: string
  username: string
  email: string
  avatar_url: string
  created_at: string
  // Helper properties for UI (derived from other fields)
  avatarUrl?: string
  name?: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
}

// Repository types
export interface Repository {
  id: string
  user_id: string
  github_url: string
  name: string
  description: string | null
  language: string
  star_count: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  processing_progress: number
  error_message?: string | null
  metadata: RepositoryMetadata
  created_at: string
  updated_at: string
  // Helper properties for UI
  primaryLanguage?: string
  analyzedAt?: string
  createdAt?: string
  analysisProgress?: number
  errorMessage?: string
  stats?: {
    totalFiles: number
    totalLines: number
    complexity: number
  }
}

export interface RepositoryMetadata {
  summary?: string
  tech_stack?: string[]
  key_files?: string[]
  entry_points?: string[]
  architecture?: string
  total_files?: number
  total_lines?: number
  file_tree?: FileNode[]
}

export interface RepositorySummary {
  repository: Repository
  purpose: string
  features: string[]
  tech_stack: string[]
  architecture: string
  key_files: string[]
  fileTree?: FileNode[]
  dependencyGraph?: DependencyGraph
  executionFlows?: ExecutionFlow[]
}

// Code chunk types
export interface CodeChunk {
  id: string
  repo_id: string
  file_path: string
  chunk_type: 'file' | 'class' | 'function' | 'block'
  content: string
  language: string
  start_line: number
  end_line: number
  metadata: {
    symbols?: string[]
    imports?: string[]
    exports?: string[]
  }
}

// Chat types
export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  sources?: CodeSource[]
}

export interface CodeSource {
  file_path: string
  start_line: number
  end_line: number
  content: string
  relevance_score?: number
}

export interface ChatRequest {
  repo_id: string
  message: string
  file_path?: string
  history?: ChatMessage[]
}

export interface ChatResponse {
  message: string
  sources: CodeSource[]
  model: string
}

// Graph types
export interface DependencyNode {
  id: string
  label: string
  type: 'file' | 'module' | 'package'
  language: string
  size: number
  complexity?: number
}

export interface DependencyEdge {
  source: string
  target: string
  type: 'import' | 'export' | 'call'
  weight: number
  label?: string
}

export interface DependencyGraph {
  nodes: DependencyNode[]
  edges: DependencyEdge[]
  entry_points: string[]
  metrics: {
    total_nodes: number
    total_edges: number
    circular_dependencies: string[][]
  }
}

// Flow types
export interface ExecutionFlow {
  id: string
  route: string
  method: string
  description: string
  steps: FlowStep[]
  complexity: number
  nodes: FlowNode[]
  edges: FlowEdge[]
}

export interface FlowNode {
  id: string
  type: 'start' | 'end' | 'process' | 'decision'
  label: string
  description?: string
}

export interface FlowEdge {
  source: string
  target: string
  label?: string
  type?: string
}

export interface FlowStep {
  order: number
  type: 'middleware' | 'handler' | 'database' | 'external_api' | 'response'
  file_path: string
  function_name: string
  line_number: number
  description: string
}

// File explorer types
export interface FileNode {
  id: string
  path: string
  name: string
  type: 'file' | 'directory'
  language?: string
  size?: number
  children?: FileNode[]
}

// API response types
export interface ApiResponse<T> {
  data: T
  message?: string
  error?: string
}

export interface PaginatedResponse<T> {
  items?: T[] // Alias for data
  data: T[]
  total: number
  page: number
  page_size: number
  has_next: boolean
}

// Error types
export interface ApiError {
  message: string
  code: string
  details?: Record<string, string[]>
}

// Usage quota types
export interface UsageQuota {
  chat_requests: {
    used: number
    limit: number
  }
  repos_analyzed: {
    used: number
    limit: number
  }
  storage: {
    used: number
    limit: number
  }
  tier: 'free' | 'pro'
}
