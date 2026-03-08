'use client'

import { useState, useEffect } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { FileCode, Lightbulb, Loader2, X } from 'lucide-react'
import { FileNode } from '@/lib/types'
import { getFileContent } from '@/lib/api/files'
import { toast } from 'sonner'

interface FileViewerModalProps {
  file: FileNode | null
  repoId: string
  open: boolean
  onClose: () => void
  onExplain: (content: string, fileName: string) => void
}

export function FileViewerModal({ file, repoId, open, onClose, onExplain }: FileViewerModalProps) {
  const [content, setContent] = useState<string>('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (open && file) {
      fetchFileContent()
    }
  }, [open, file])

  const fetchFileContent = async () => {
    if (!file) return

    setLoading(true)
    try {
      const data = await getFileContent(repoId, file.path)
      setContent(data.content)
    } catch (error) {
      console.error('Failed to fetch file content:', error)
      toast.error('Failed to load file content')
      setContent('// Error loading file content')
    } finally {
      setLoading(false)
    }
  }

  const handleExplain = () => {
    if (content && file) {
      onExplain(content, file.name)
      onClose()
    }
  }

  if (!file) return null

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl h-[85vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileCode className="h-5 w-5" />
            {file.name}
          </DialogTitle>
          <p className="text-sm text-muted-foreground">{file.path}</p>
        </DialogHeader>

        <div className="flex-1 overflow-hidden relative rounded-md border">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : (
            <div className="h-full overflow-auto scrollbar-thin">
              <SyntaxHighlighter
                language={file.language || 'text'}
                style={vscDarkPlus}
                showLineNumbers
                customStyle={{
                  margin: 0,
                  padding: '1rem',
                  fontSize: '0.875rem',
                  background: 'transparent',
                }}
                lineNumberStyle={{
                  minWidth: '3em',
                  paddingRight: '1em',
                  color: '#6B7280',
                  userSelect: 'none',
                }}
              >
                {content}
              </SyntaxHighlighter>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            <X className="h-4 w-4 mr-2" />
            Close
          </Button>
          <Button onClick={handleExplain} disabled={loading || !content}>
            <Lightbulb className="h-4 w-4 mr-2" />
            Explain this file
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
