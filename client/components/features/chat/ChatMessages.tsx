'use client'

import { useEffect, useRef } from 'react'
import { Bot, User as UserIcon } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { CodeBlock } from './CodeBlock'
import { cn } from '@/lib/utils/cn'
import type { ChatMessage } from '@/lib/types'
import { formatRelativeTime } from '@/lib/utils/format'

interface ChatMessagesProps {
  messages: ChatMessage[]
  isLoading?: boolean
}

interface MessageItemProps {
  message: ChatMessage
}

function MessageItem({ message }: MessageItemProps) {
  const isUser = message.role === 'user'
  const isStreaming = !isUser && message.id === 'streaming'

  return (
    <div className={cn('flex gap-3 group', isUser && 'flex-row-reverse')}>
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser ? 'bg-primary' : 'bg-muted'
        )}
      >
        {isUser ? (
          <UserIcon className="h-4 w-4 text-primary-foreground" />
        ) : (
          <Bot className="h-4 w-4 text-foreground" />
        )}
      </div>

      {/* Message Content */}
      <div className={cn('flex-1 space-y-2 max-w-[85%]', isUser && 'flex flex-col items-end')}>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span className="font-medium">{isUser ? 'You' : 'AI Assistant'}</span>
          <span>{formatRelativeTime(new Date(message.timestamp))}</span>
        </div>

        <div
          className={cn(
            'rounded-lg break-words text-base',
            isUser
              ? 'bg-primary text-primary-foreground p-4'
              : 'bg-transparent text-foreground'
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : isStreaming && !message.content ? (
        
            <div className="bg-muted rounded-lg p-4">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-foreground/60 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-foreground/60 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-foreground/60 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          ) : (
            <div className="prose prose-invert max-w-none prose-pre:p-0 prose-pre:m-0 prose-pre:bg-transparent">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                 
                  code({ node, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || '')
                    const language = match ? match[1] : ''
                    const value = String(children).replace(/\n$/, '')
                    const isInline = !match && !String(children).includes('\n')

                    return (
                      <CodeBlock
                        language={language}
                        value={value}
                        inline={isInline}
                        className={className}
                      />
                    )
                  },
                  pre: ({ children }) => <div className="not-prose">{children}</div>,
                  p: ({ children }) => <p className="mb-3 leading-7 last:mb-0">{children}</p>,
                  h1: ({ children }) => <h1 className="text-2xl font-bold mb-4 mt-6 first:mt-0">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-xl font-semibold mb-3 mt-5 first:mt-0">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-lg font-semibold mb-2 mt-4 first:mt-0">{children}</h3>,
                  ul: ({ children }) => <ul className="list-disc list-outside ml-4 mb-3 space-y-1">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-outside ml-4 mb-3 space-y-1">{children}</ol>,
                  li: ({ children }) => <li className="leading-7">{children}</li>,
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-primary/50 pl-4 italic my-3 text-muted-foreground">
                      {children}
                    </blockquote>
                  ),
                  a: ({ children, href }) => (
                    <a
                      href={href}
                      className="text-primary hover:text-primary/80 underline underline-offset-2 transition-colors"
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {children}
                    </a>
                  ),
                  table: ({ children }) => (
                    <div className="my-4 overflow-x-auto">
                      <table className="min-w-full border-collapse border border-border/40">
                        {children}
                      </table>
                    </div>
                  ),
                  th: ({ children }) => (
                    <th className="border border-border/40 px-4 py-2 bg-muted/50 font-semibold text-left">
                      {children}
                    </th>
                  ),
                  td: ({ children }) => (
                    <td className="border border-border/40 px-4 py-2">
                      {children}
                    </td>
                  ),
                  hr: () => <hr className="my-6 border-border/40" />,
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export function ChatMessages({ messages, isLoading }: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const hasStreamingMessage = messages.some((m) => m.id === 'streaming')

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
      {messages.length === 0 && !isLoading ? (
        <div className="flex flex-col items-center justify-center h-full text-center space-y-4 select-none">
          <div className="rounded-full bg-primary/10 p-4 pointer-events-none">
            <Bot className="h-12 w-12 text-primary" />
          </div>
          <div className="pointer-events-none">
            <h3 className="text-lg font-semibold mb-2">Start a conversation</h3>
            <p className="text-muted-foreground text-sm max-w-md">
              Ask me anything about this codebase. I can explain functions, trace execution flows,
              identify dependencies, and more.
            </p>
          </div>
        </div>
      ) : (
        <>
          {messages.map((message) => (
            <MessageItem key={message.id} message={message} />
          ))}
         
          {isLoading && !hasStreamingMessage && (
            <div className="flex gap-3">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                <Bot className="h-4 w-4" />
              </div>
              <div className="flex-1 space-y-2">
                <div className="text-xs text-muted-foreground">
                  <span className="font-medium">AI Assistant</span>
                </div>
                <div className="bg-muted rounded-lg p-4">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-foreground/60 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-foreground/60 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-foreground/60 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </>
      )}
    </div>
  )
}
