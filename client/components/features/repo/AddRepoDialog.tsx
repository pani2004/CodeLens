'use client'

import { useState, useEffect } from 'react'
import { Plus, Github, Link as LinkIcon, X, Star, GitFork, Loader2, Search } from 'lucide-react'
import { toast } from 'sonner'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { analyzeRepository, getGitHubRepositories } from '@/lib/api/repos'
import { cn } from '@/lib/utils/cn'

interface AddRepoDialogProps {
  onSuccess?: () => void
}

interface GitHubRepo {
  name: string
  full_name: string
  url: string
  description: string
  language: string
  stars: number
}

export function AddRepoDialog({ onSuccess }: AddRepoDialogProps) {
  const [open, setOpen] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isFetchingRepos, setIsFetchingRepos] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [githubUrl, setGithubUrl] = useState('')
  const [githubRepos, setGithubRepos] = useState<GitHubRepo[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedRepo, setSelectedRepo] = useState<string | null>(null)

  // Fetch GitHub repos when dialog opens
  useEffect(() => {
    if (open) {
      fetchGitHubRepos()
    }
  }, [open])

  const fetchGitHubRepos = async () => {
    setIsFetchingRepos(true)
    setError(null)
    try {
      const repos = await getGitHubRepositories()
      setGithubRepos(repos)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch repositories'
      setError(errorMessage)
    } finally {
      setIsFetchingRepos(false)
    }
  }

  const handleAnalyzeRepo = async (repoUrl: string) => {
    setIsLoading(true)
    setError(null)
    setSelectedRepo(repoUrl)

    try {
      await analyzeRepository(repoUrl)
      setOpen(false)
      setGithubUrl('')
      setSearchQuery('')
      setSelectedRepo(null)
      toast.success('Repository added successfully!', {
        description: 'Analysis will begin shortly.',
      })
      onSuccess?.()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to add repository'
      setError(errorMessage)
      toast.error('Failed to add repository', {
        description: errorMessage,
      })
      setSelectedRepo(null)
    } finally {
      setIsLoading(false)
    }
  }

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    await handleAnalyzeRepo(githubUrl)
  }

  const filteredRepos = githubRepos.filter((repo) =>
    repo.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    repo.description?.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="gap-2">
          <Plus className="h-4 w-4" />
          Add Repository
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh]">
        <DialogHeader>
          <DialogTitle>Add New Repository</DialogTitle>
          <DialogDescription>
            Select a repository from your GitHub account or enter a URL manually
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="github" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="github">
              <Github className="h-4 w-4 mr-2" />
              Your Repositories
            </TabsTrigger>
            <TabsTrigger value="manual">
              <LinkIcon className="h-4 w-4 mr-2" />
              Manual URL
            </TabsTrigger>
          </TabsList>

          {/* GitHub Repos Tab */}
          <TabsContent value="github" className="space-y-4 mt-4">
            {/* Search bar */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search your repositories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
                disabled={isFetchingRepos}
              />
            </div>

            {/* Error message */}
            {error && (
              <div className="flex items-start gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/30 rounded-md p-3">
                <X className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Loading state */}
            {isFetchingRepos && (
              <div className="flex flex-col items-center justify-center py-12 gap-3">
                <Loader2 className="h-8 w-8 text-primary animate-spin" />
                <p className="text-sm text-muted-foreground">Loading your repositories...</p>
              </div>
            )}

            {/* Repos list */}
            {!isFetchingRepos && githubRepos.length > 0 && (
              <ScrollArea className="h-[400px] pr-4">
                <div className="space-y-2">
                  {filteredRepos.map((repo) => (
                    <button
                      key={repo.full_name}
                      onClick={() => handleAnalyzeRepo(repo.url)}
                      disabled={isLoading}
                      className={cn(
                        "w-full text-left p-4 rounded-lg border border-border/50 hover:border-primary/50 hover:bg-accent/50 transition-all group",
                        selectedRepo === repo.url && "border-primary bg-accent",
                        isLoading && selectedRepo !== repo.url && "opacity-50 cursor-not-allowed"
                      )}
                    >
                      <div className="space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1 min-w-0">
                            <h4 className="font-semibold text-sm group-hover:text-primary transition-colors truncate">
                              {repo.name}
                            </h4>
                            {repo.description && (
                              <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
                                {repo.description}
                              </p>
                            )}
                          </div>
                          {selectedRepo === repo.url && isLoading && (
                            <Loader2 className="h-4 w-4 text-primary animate-spin flex-shrink-0" />
                          )}
                        </div>

                        <div className="flex items-center gap-2 flex-wrap text-xs">
                          {repo.language && (
                            <Badge variant="secondary" className="text-xs">
                              {repo.language}
                            </Badge>
                          )}
                          <div className="flex items-center gap-1 text-muted-foreground">
                            <Star className="h-3 w-3" />
                            <span>{repo.stars}</span>
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}

                  {filteredRepos.length === 0 && (
                    <div className="text-center py-8 text-muted-foreground">
                      <p className="text-sm">No repositories found</p>
                      <p className="text-xs mt-1">Try adjusting your search</p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            )}

            {/* Empty state */}
            {!isFetchingRepos && githubRepos.length === 0 && !error && (
              <div className="text-center py-12 text-muted-foreground">
                <Github className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p className="text-sm font-medium">No repositories found</p>
                <p className="text-xs mt-1">Create a repository on GitHub first</p>
              </div>
            )}
          </TabsContent>

          {/* Manual URL Tab */}
          <TabsContent value="manual" className="space-y-4 mt-4">
            <form onSubmit={handleManualSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="github-url">Repository URL</Label>
                <Input
                  id="github-url"
                  type="url"
                  placeholder="https://github.com/username/repository"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  disabled={isLoading}
                  required
                />
                <p className="text-xs text-muted-foreground">
                  Enter the full GitHub repository URL
                </p>
              </div>

              {error && (
                <div className="flex items-start gap-2 text-sm text-destructive bg-destructive/10 border border-destructive/30 rounded-md p-3">
                  <X className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}

              <div className="flex justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setOpen(false)}
                  disabled={isLoading}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    'Analyze Repository'
                  )}
                </Button>
              </div>
            </form>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
