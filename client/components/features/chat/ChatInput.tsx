'use client'

import { useState } from 'react'
import { Send, Loader2, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils/cn'

interface ChatInputProps {
  onSend: (message: string) => void
  isLoading?: boolean
  disabled?: boolean
  suggestedPrompts?: string[]
}

export function ChatInput({ onSend, isLoading, disabled, suggestedPrompts = [] }: ChatInputProps) {
  const [message, setMessage] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim() && !isLoading) {
      onSend(message.trim())
      setMessage('')
    }
  }

  const handleSuggestedPrompt = (prompt: string) => {
    onSend(prompt)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="space-y-3">
      {/* Suggested Prompts */}
      {suggestedPrompts.length > 0 && (
        <div className="flex flex-wrap gap-2">
          <div className="flex items-center gap-1 text-sm text-muted-foreground">
            <Sparkles className="h-4 w-4" />
            <span>Try asking:</span>
          </div>
          {suggestedPrompts.map((prompt, index) => (
            <Badge
              key={index}
              variant="secondary"
              className={cn(
                "text-sm px-3 py-1 transition-colors",
                !isLoading && !disabled && "cursor-pointer hover:bg-primary hover:text-primary-foreground",
                (isLoading || disabled) && "opacity-50 cursor-not-allowed"
              )}
              onClick={() => !isLoading && !disabled && handleSuggestedPrompt(prompt)}
            >
              {prompt}
            </Badge>
          ))}
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="relative">
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything about this codebase... (Shift+Enter for new line)"
          disabled={disabled || isLoading}
          className="min-h-[80px] pr-12 resize-none text-base"
          rows={3}
        />
        <Button
          type="submit"
          size="icon"
          disabled={!message.trim() || isLoading || disabled}
          className={cn(
            'absolute bottom-2 right-2 h-8 w-8',
            isLoading && 'opacity-50'
          )}
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </form>

      <p className="text-xs text-muted-foreground text-center">
        AI can make mistakes. Verify important information.
      </p>
    </div>
  )
}
