'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { FileCode, Loader2, CheckCircle2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { getCurrentUser } from '@/lib/api/auth'
import type { User } from '@/lib/types'

export default function WelcomePage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const currentUser = await getCurrentUser()
        setUser(currentUser)
        
        // Auto-redirect to dashboard after 2 seconds
        setTimeout(() => {
          router.push('/dashboard')
        }, 2000)
      } catch (err) {
        console.error('Failed to fetch user:', err)
        // If user fetch fails, redirect to login
        router.push('/auth/login')
      } finally {
        setIsLoading(false)
      }
    }

    fetchUser()
  }, [router])

  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 text-primary animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
      {/* Logo */}
      <div className="mb-8 flex items-center gap-2">
        <FileCode className="h-8 w-8 text-primary" />
        <span className="text-2xl font-bold">CodeLens AI</span>
      </div>

      {/* Welcome Content */}
      <div className="text-center space-y-6 max-w-md animate-slideUp">
        {/* Success Icon */}
        <div className="flex justify-center">
          <div className="rounded-full bg-primary/10 p-4 border border-primary/20">
            <CheckCircle2 className="h-12 w-12 text-primary" />
          </div>
        </div>

        {/* User Avatar (if available) */}
        {user?.avatarUrl && (
          <div className="flex justify-center">
            <img
              src={user.avatarUrl}
              alt={user.name || user.username}
              className="w-20 h-20 rounded-full border-2 border-primary"
            />
          </div>
        )}

        {/* Welcome Message */}
        <div className="space-y-2">
          <h1 className="text-3xl font-bold">
            Welcome{user?.name ? `, ${user.name.split(' ')[0]}` : ' Back'}!
          </h1>
          <p className="text-muted-foreground">
            You're all set. Let's start exploring your codebases.
          </p>
        </div>

        {/* User Info */}
        {user && (
          <div className="bg-card border border-border/50 rounded-lg p-4 text-left space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Username:</span>
              <span className="font-medium">@{user.username}</span>
            </div>
            {user.email && (
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Email:</span>
                <span className="font-medium">{user.email}</span>
              </div>
            )}
          </div>
        )}

        {/* Action Button */}
        <Button
          onClick={() => router.push('/dashboard')}
          size="lg"
          className="w-full"
        >
          Go to Dashboard
        </Button>

        {/* Auto-redirect message */}
        <p className="text-xs text-muted-foreground">
          Redirecting automatically in a moment...
        </p>
      </div>
    </div>
  )
}
