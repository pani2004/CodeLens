'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, FolderGit2, Network, GitBranch, Workflow, Trash2, RefreshCw } from 'lucide-react'
import Link from 'next/link'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Logo } from '@/components/shared/Logo'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { ErrorState } from '@/components/shared/ErrorState'
import { FileExplorer } from '@/components/features/file-explorer/FileExplorer'
import { ChatMessages } from '@/components/features/chat/ChatMessages'
import { ChatInput } from '@/components/features/chat/ChatInput'
import { FileViewerModal } from '@/components/features/file-viewer/FileViewerModal'
import { getRepository, deleteRepository } from '@/lib/api/repos'
import { getChatHistory, sendChatMessage, getSuggestedPrompts } from '@/lib/api/chat'
import { useChatStore } from '@/lib/store/chat-store'
import type { Repository, ChatMessage, FileNode } from '@/lib/types'

export default function ChatPage() {
  const params = useParams()
  const router = useRouter()
  const repoId = params.repoId as string
  const { getMessages, setMessages, addMessage, updateLastMessage } = useChatStore()
  const messages = getMessages(repoId)

  const [repository, setRepository] = useState<Repository | null>(null)
  const [fileTree, setFileTree] = useState<FileNode[]>([])
  const [selectedFile, setSelectedFile] = useState<FileNode | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [suggestedPrompts, setSuggestedPrompts] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true)
        const [repo, history, prompts] = await Promise.all([
          getRepository(repoId),
          getChatHistory(repoId),
          getSuggestedPrompts(repoId),
        ])
        setRepository(repo)
        setFileTree(repo.metadata?.file_tree || [])
        
        // Only update if backend has newer history or store is empty
        if (history.length > 0 && messages.length === 0) {
          setMessages(repoId, history)
        }
        
        setSuggestedPrompts(prompts)
      } catch (err) {
        console.error('Failed to fetch data:', err)
        setError(err instanceof Error ? err.message : 'Failed to load chat')
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [repoId])

  const handleSendMessage = async (content: string) => {
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }

    addMessage(repoId, userMessage)
    setIsSending(true)

    try {
      let assistantContent = ''
      
      // Stream the response
      for await (const chunk of sendChatMessage(repoId, content, selectedFile?.path)) {
        assistantContent += chunk  
        updateLastMessage(repoId, assistantContent)
      }
      const finalMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: assistantContent,
        timestamp: new Date().toISOString(),
      }
      
      // Replace streaming message with final message
      const currentMessages = getMessages(repoId)
      const withoutStreaming = currentMessages.filter((m) => m.id !== 'streaming')
      setMessages(repoId, [...withoutStreaming, finalMessage])
      
    } catch (err) {
      console.error('Failed to send message:', err)
      addMessage(repoId, {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
      })
    } finally {
      setIsSending(false)
    }
  }

  const handleDeleteRepository = async () => {
    try {
      await deleteRepository(repoId)
      toast.success('Repository deleted successfully')
      router.push('/dashboard')
    } catch (err) {
      console.error('Failed to delete repository:', err)
      toast.error('Failed to delete repository', {
        description: err instanceof Error ? err.message : 'Please try again',
      })
    }
  }

  const handleFileSelect = (file: FileNode) => {
    if (file.type === 'file') {
      setSelectedFile(file)
      setIsModalOpen(true)
    }
  }

  const handleExplainFile = (content: string, fileName: string) => {
    const explainPrompt = `Please explain this file (${fileName}):\n\n\`\`\`\n${content}\n\`\`\``
    handleSendMessage(explainPrompt)
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner size="lg" text="Loading chat..." />
      </div>
    )
  }

  if (error || !repository) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <ErrorState
          title="Failed to load chat"
          message={error || 'Repository not found'}
          onRetry={() => window.location.reload()}
        />
      </div>
    )
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      {/* Header */}
      <header className="border-b border-border/40 backdrop-blur-sm z-50 bg-background/80 flex-shrink-0">
        <div className="container flex h-14 items-center justify-between px-4 mx-auto">
          <div className="flex items-center gap-4">
            <Link href="/dashboard">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <Separator orientation="vertical" className="h-6" />
            <Logo showText={false} href="/" />
            <div className="flex flex-col">
              <h1 className="text-sm font-semibold">{repository.name}</h1>
              <p className="text-xs text-muted-foreground">{repository.primaryLanguage}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link href={`/graph/${repoId}`}>
              <Button variant="ghost" size="sm" className="gap-2">
                <Network className="h-4 w-4" />
                Graph View
              </Button>
            </Link>
            <Link href={`/flows/${repoId}`}>
              <Button variant="ghost" size="sm" className="gap-2">
                <Workflow className="h-4 w-4" />
                Flow View
              </Button>
            </Link>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="ghost" size="icon">
                  <Trash2 className="h-4 w-4" />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Repository?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will permanently delete the analysis for "{repository.name}". 
                    This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={handleDeleteRepository} className="bg-destructive text-destructive-foreground">
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>
      </header>

      {/* 3-Panel Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel: File Explorer */}
        <div className="w-80 border-r border-border/40 flex flex-col bg-background-secondary overflow-hidden">
          <div className="border-b border-border/40 px-4 py-3 flex-shrink-0">
            <h2 className="text-sm font-semibold flex items-center gap-2">
              <FolderGit2 className="h-4 w-4" />
              File Explorer
            </h2>
          </div>
          <div className="flex-1 overflow-hidden">
            <FileExplorer
              files={fileTree}
              onFileSelect={handleFileSelect}
              selectedFileId={selectedFile?.id}
            />
          </div>
        </div>

        {/* Center Panel: Chat */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <ChatMessages messages={messages} isLoading={isSending} />
          <div className="border-t border-border/40 p-4 flex-shrink-0">
            <ChatInput
              onSend={handleSendMessage}
              isLoading={isSending}
              suggestedPrompts={messages.length === 0 ? suggestedPrompts : []}
            />
          </div>
        </div>
      </div>

      {/* File Viewer Modal */}
      <FileViewerModal
        file={selectedFile}
        repoId={repoId}
        open={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onExplain={handleExplainFile}
      />
    </div>
  )
}
