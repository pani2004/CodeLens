'use client'

import { useState } from 'react'
import { 
  ChevronDown, 
  ChevronRight, 
  File, 
  Folder, 
  FileCode,
  FileJson,
  FileText,
  Settings,
  Image as ImageIcon
} from 'lucide-react'
import { cn } from '@/lib/utils/cn'
import type { FileNode } from '@/lib/types'

interface FileExplorerProps {
  files: FileNode[]
  onFileSelect?: (file: FileNode) => void
  selectedFileId?: string
}

interface FileTreeItemProps {
  node: FileNode
  level: number
  onFileSelect?: (file: FileNode) => void
  selectedFileId?: string
}

// Get icon based on file extension
function getFileIcon(fileName: string, language?: string) {
  const ext = fileName.split('.').pop()?.toLowerCase()
  
  // Code files
  if (['js', 'jsx', 'ts', 'tsx', 'py', 'java', 'cpp', 'c', 'h', 'go', 'rs', 'rb', 'php', 'swift', 'kt'].includes(ext || '')) {
    return <FileCode className="h-4 w-4 text-blue-500 flex-shrink-0" />
  }
  
  // Config files
  if (['json', 'yaml', 'yml', 'toml', 'ini', 'env'].includes(ext || '')) {
    return <FileJson className="h-4 w-4 text-yellow-500 flex-shrink-0" />
  }
  
  // Markdown/Text
  if (['md', 'txt', 'log'].includes(ext || '')) {
    return <FileText className="h-4 w-4 text-gray-500 flex-shrink-0" />
  }
  
  // Config/Settings
  if (ext === 'config' || fileName.includes('config')) {
    return <Settings className="h-4 w-4 text-purple-500 flex-shrink-0" />
  }
  
  // HTML/CSS
  if (['html', 'css', 'scss', 'less'].includes(ext || '')) {
    return <FileCode className="h-4 w-4 text-orange-500 flex-shrink-0" />
  }
  
  // Images
  if (['png', 'jpg', 'jpeg', 'gif', 'svg', 'ico'].includes(ext || '')) {
    return <ImageIcon className="h-4 w-4 text-green-500 flex-shrink-0" />
  }
  
  // Default
  return <File className="h-4 w-4 text-muted-foreground flex-shrink-0" />
}

// VS Code-like sorting: src first, config files last
function sortFileTree(nodes: FileNode[]): FileNode[] {
  const configFiles = ['package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml']
  const configPatterns = ['.config.js', '.config.ts', '.config.mjs', 'tsconfig.json', '.gitignore', '.env', '.eslintrc', '.prettierrc']
  
  const isConfigFile = (name: string) => {
    if (configFiles.includes(name)) return true
    return configPatterns.some(pattern => name.includes(pattern))
  }
  
  return [...nodes].sort((a, b) => {
    // Directories come before files
    if (a.type === 'directory' && b.type === 'file') return -1
    if (a.type === 'file' && b.type === 'directory') return 1
    
    // Among directories: src comes first
    if (a.type === 'directory' && b.type === 'directory') {
      if (a.name === 'src') return -1
      if (b.name === 'src') return 1
      return a.name.localeCompare(b.name)
    }
    
    // Among files: config files go to bottom
    if (a.type === 'file' && b.type === 'file') {
      const aIsConfig = isConfigFile(a.name)
      const bIsConfig = isConfigFile(b.name)
      
      if (aIsConfig && !bIsConfig) return 1
      if (!aIsConfig && bIsConfig) return -1
      
      // Sort config files: package.json first among configs
      if (aIsConfig && bIsConfig) {
        if (a.name === 'package.json') return -1
        if (b.name === 'package.json') return 1
      }
      
      return a.name.localeCompare(b.name)
    }
    
    return 0
  })
}

function FileTreeItem({ node, level, onFileSelect, selectedFileId }: FileTreeItemProps) {
  const [isExpanded, setIsExpanded] = useState(level === 0)
  const isSelected = node.id === selectedFileId
  const isFile = node.type === 'file'

  const handleClick = () => {
    if (isFile) {
      onFileSelect?.(node)
    } else {
      setIsExpanded(!isExpanded)
    }
  }
  
  // Sort children if this is a directory
  const sortedChildren = node.children ? sortFileTree(node.children) : []

  return (
    <div>
      <button
        onClick={handleClick}
        className={cn(
          'flex items-center gap-2 w-full px-2 py-1.5 text-sm hover:bg-accent rounded-md transition-colors',
          isSelected && 'bg-accent text-accent-foreground font-medium'
        )}
        style={{ paddingLeft: `${level * 12 + 8}px` }}
      >
        {!isFile && (
          <span className="flex-shrink-0">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            )}
          </span>
        )}
        {isFile ? (
          getFileIcon(node.name, node.language)
        ) : (
          <Folder className={cn(
            "h-4 w-4 flex-shrink-0",
            isExpanded ? "text-yellow-500" : "text-blue-500"
          )} />
        )}
        <span className="truncate">{node.name}</span>
      </button>
      {!isFile && isExpanded && sortedChildren.length > 0 && (
        <div>
          {sortedChildren.map((child) => (
            <FileTreeItem
              key={child.id}
              node={child}
              level={level + 1}
              onFileSelect={onFileSelect}
              selectedFileId={selectedFileId}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export function FileExplorer({ files, onFileSelect, selectedFileId }: FileExplorerProps) {
  if (!files || files.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-muted-foreground p-4">
        No files to display
      </div>
    )
  }
  
  // Sort root level files
  const sortedFiles = sortFileTree(files)

  return (
    <div className="h-full overflow-y-auto overflow-x-hidden scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent">
      <div className="px-2 py-2 space-y-0.5">
        {sortedFiles.map((node) => (
          <FileTreeItem
            key={node.id}
            node={node}
            level={0}
            onFileSelect={onFileSelect}
            selectedFileId={selectedFileId}
          />
        ))}
      </div>
    </div>
  )
}
