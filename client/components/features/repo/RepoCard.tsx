import Link from 'next/link'
import { MessageSquare, Loader2, CheckCircle2, XCircle, Clock } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { Repository } from '@/lib/types'
import { formatRelativeTime, getLanguageColor } from '@/lib/utils/format'
import { cn } from '@/lib/utils/cn'

interface RepoCardProps {
  repository: Repository
}

const statusConfig = {
  pending: {
    icon: Clock,
    label: 'Pending',
    color: 'text-yellow-500',
    bg: 'bg-yellow-500/10',
    animate: false,
  },
  processing: {
    icon: Loader2,
    label: 'Processing',
    color: 'text-blue-500',
    bg: 'bg-blue-500/10',
    animate: true,
  },
  completed: {
    icon: CheckCircle2,
    label: 'Ready',
    color: 'text-green-500',
    bg: 'bg-green-500/10',
    animate: false,
  },
  failed: {
    icon: XCircle,
    label: 'Failed',
    color: 'text-red-500',
    bg: 'bg-red-500/10',
    animate: false,
  },
}

export function RepoCard({ repository }: RepoCardProps) {
  const status = statusConfig[repository.status]
  const StatusIcon = status.icon
  const isReady = repository.status === 'completed'

  return (
    <Card className="border-border/50 hover:border-primary/50 transition-all duration-300 card-hover group">
      <CardHeader className="space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg truncate group-hover:text-primary transition-colors">
              {repository.name}
            </CardTitle>
            {repository.description && (
              <CardDescription className="line-clamp-2 mt-1">
                {repository.description}
              </CardDescription>
            )}
          </div>
          <div className={cn('rounded-full p-2', status.bg)}>
            <StatusIcon 
              className={cn('h-4 w-4', status.color, status.animate && 'animate-spin')} 
            />
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap text-xs">
          {repository.primaryLanguage && (
            <Badge variant="secondary" className="gap-1.5">
              <span 
                className="w-2 h-2 rounded-full" 
                style={{ backgroundColor: getLanguageColor(repository.primaryLanguage) }}
              />
              {repository.primaryLanguage}
            </Badge>
          )}
          <Badge variant="outline">{status.label}</Badge>
          <span className="text-muted-foreground">
            {formatRelativeTime(new Date(repository.analyzedAt || repository.createdAt || repository.created_at))}
          </span>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {/* Progress indicator for processing */}
        {repository.status === 'processing' && (
          <div className="space-y-2">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{repository.error_message || repository.errorMessage || 'Analyzing codebase...'}</span>
              <span>{repository.analysisProgress || repository.processing_progress || 0}%</span>
            </div>
            <div className="h-1.5 bg-muted rounded-full overflow-hidden">
              <div 
                className="h-full bg-primary transition-all duration-300 rounded-full"
                style={{ width: `${repository.analysisProgress || repository.processing_progress || 0}%` }}
              />
            </div>
          </div>
        )}

        {/* Error message for failed */}
        {repository.status === 'failed' && (repository.error_message || repository.errorMessage) && (
          <div className="text-xs text-destructive bg-destructive/10 border border-destructive/30 rounded-md p-2">
            {repository.error_message || repository.errorMessage}
          </div>
        )}

        {/* Stats for completed repos */}
        {isReady && repository.stats && (
          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="bg-muted/50 rounded-md p-2">
              <div className="text-lg font-semibold">{repository.stats.totalFiles}</div>
              <div className="text-xs text-muted-foreground">Files</div>
            </div>
            <div className="bg-muted/50 rounded-md p-2">
              <div className="text-lg font-semibold">{repository.stats.totalLines}</div>
              <div className="text-xs text-muted-foreground">Lines</div>
            </div>
            <div className="bg-muted/50 rounded-md p-2">
              <div className="text-lg font-semibold">{repository.stats.complexity}</div>
              <div className="text-xs text-muted-foreground">Complexity</div>
            </div>
          </div>
        )}

        {/* Action button */}
        <Link href={isReady ? `/chat/${repository.id}` : '#'}>
          <Button 
            className="w-full gap-2" 
            disabled={!isReady}
            variant={isReady ? 'default' : 'outline'}
          >
            <MessageSquare className="h-4 w-4" />
            {isReady ? 'Chat Now' : 'Waiting for Analysis'}
          </Button>
        </Link>
      </CardContent>
    </Card>
  )
}
