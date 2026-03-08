'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { LogOut, Settings, Search, SlidersHorizontal, FolderGit2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Logo } from '@/components/shared/Logo'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { ErrorState } from '@/components/shared/ErrorState'
import { EmptyState } from '@/components/shared/EmptyState'
import { RepoCard } from '@/components/features/repo/RepoCard'
import { AddRepoDialog } from '@/components/features/repo/AddRepoDialog'
import { getCurrentUser, logout } from '@/lib/api/auth'
import { getRepositories } from '@/lib/api/repos'
import type { User, Repository } from '@/lib/types'

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [repositories, setRepositories] = useState<Repository[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [languageFilter, setLanguageFilter] = useState<string>('all')

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true)
        const [currentUser, reposData] = await Promise.all([
          getCurrentUser(),
          getRepositories(),
        ])
        setUser(currentUser)
        setRepositories(reposData.items || reposData.data || [])
      } catch (err) {
        console.error('Failed to fetch data:', err)
        setError(err instanceof Error ? err.message : 'Failed to load dashboard')
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [])

  // Auto-refresh repositories that are processing
  useEffect(() => {
    const hasProcessingRepos = repositories.some(
      repo => repo.status === 'processing' || repo.status === 'pending'
    )

    if (!hasProcessingRepos) return

    const intervalId = setInterval(async () => {
      try {
        const reposData = await getRepositories()
        setRepositories(reposData.items || reposData.data || [])
      } catch (err) {
        console.error('Failed to refresh repositories:', err)
      }
    }, 5000) // Poll every 5 seconds

    return () => clearInterval(intervalId)
  }, [repositories])

  const handleLogout = async () => {
    await logout()
    router.push('/')
  }

  const handleRefresh = async () => {
    try {
      setIsLoading(true)
      const reposData = await getRepositories()
      setRepositories(reposData.items || reposData.data || [])
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh repositories')
    } finally {
      setIsLoading(false)
    }
  }

  // Filter repositories
  const filteredRepos = repositories.filter((repo) => {
    const matchesSearch = repo.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      repo.description?.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === 'all' || repo.status === statusFilter
    const matchesLanguage = languageFilter === 'all' || repo.primaryLanguage === languageFilter
    return matchesSearch && matchesStatus && matchesLanguage
  })

  // Get unique languages
  const languages = Array.from(new Set(repositories.map(r => r.primaryLanguage).filter(Boolean)))

  if (isLoading && !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner size="lg" text="Loading dashboard..." />
      </div>
    )
  }

  if (error && !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <ErrorState
          title="Failed to load dashboard"
          message={error}
          onRetry={handleRefresh}
        />
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="border-b border-border/40 backdrop-blur-sm sticky top-0 z-50 bg-background/80">
        <div className="container flex h-16 items-center justify-between px-4 mx-auto">
          <Logo />

          <div className="flex items-center gap-4">
            <AddRepoDialog onSuccess={handleRefresh} />
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="rounded-full">
                  {user?.avatarUrl ? (
                    <img
                      src={user.avatarUrl}
                      alt={user.name || user.username}
                      className="w-8 h-8 rounded-full"
                    />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-medium">
                      {user?.username?.[0]?.toUpperCase() || 'U'}
                    </div>
                  )}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium">{user?.name || user?.username}</p>
                    {user?.email && (
                      <p className="text-xs text-muted-foreground">{user.email}</p>
                    )}
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => router.push('/settings')}>
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-destructive">
                  <LogOut className="mr-2 h-4 w-4" />
                  Log Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="space-y-6">
          {/* Page Header */}
          <div>
            <h1 className="text-3xl font-bold mb-2">Your Repositories</h1>
            <p className="text-muted-foreground">
              Manage and explore your analyzed codebases
            </p>
          </div>

          {/* Filters */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search repositories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <div className="flex gap-2">
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]">
                  <SlidersHorizontal className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="completed">Ready</SelectItem>
                  <SelectItem value="processing">Processing</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                </SelectContent>
              </Select>

              {languages.length > 0 && (
                <Select value={languageFilter} onValueChange={setLanguageFilter}>
                  <SelectTrigger className="w-[150px]">
                    <SelectValue placeholder="Language" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Languages</SelectItem>
                    {languages.map((lang) => (
                      <SelectItem key={lang} value={lang || ''}>
                        {lang}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>
          </div>

          {/* Repository Grid */}
          {isLoading ? (
            <div className="flex justify-center py-12">
              <LoadingSpinner size="lg" text="Loading repositories..." />
            </div>
          ) : filteredRepos.length === 0 ? (
            repositories.length === 0 ? (
              <EmptyState
                icon={FolderGit2}
                title="No repositories yet"
                description="Get started by adding your first repository to analyze"
                action={{
                  label: 'Add Repository',
                  onClick: () => {}, // Dialog trigger handles this
                }}
              />
            ) : (
              <EmptyState
                icon={Search}
                title="No repositories found"
                description="Try adjusting your search or filters"
              />
            )
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {filteredRepos.map((repo) => (
                <RepoCard key={repo.id} repository={repo} />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
