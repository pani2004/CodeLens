'use client'

import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { FileCode, Loader2, AlertCircle } from 'lucide-react'
import { handleGitHubCallback } from '@/lib/api/auth'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

function CallbackContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [error, setError] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(true)

  useEffect(() => {
    const processCallback = async () => {
      try {
        const code = searchParams.get('code')
        const error = searchParams.get('error')
        const errorDescription = searchParams.get('error_description')

        // Handle OAuth errors
        if (error) {
          setError(errorDescription || 'Authentication was cancelled or failed.')
          setIsProcessing(false)
          return
        }

        // Check for authorization code
        if (!code) {
          setError('No authorization code received. Please try again.')
          setIsProcessing(false)
          return
        }

        // Exchange code for tokens
        await handleGitHubCallback(code)
        
        // Success! Redirect to welcome page
        router.push('/auth/welcome')
      } catch (err) {
        console.error('OAuth callback error:', err)
        setError(
          err instanceof Error 
            ? err.message 
            : 'Failed to complete authentication. Please try again.'
        )
        setIsProcessing(false)
      }
    }

    processCallback()
  }, [searchParams, router])

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
      {/* Logo */}
      <div className="mb-8 flex items-center gap-2">
        <FileCode className="h-8 w-8 text-primary" />
        <span className="text-2xl font-bold">CodeLens AI</span>
      </div>

      {/* Processing State */}
      {isProcessing && (
        <div className="text-center space-y-4 max-w-md">
          <div className="flex justify-center">
            <Loader2 className="h-12 w-12 text-primary animate-spin" />
          </div>
          <h1 className="text-2xl font-semibold">Completing Sign In...</h1>
          <p className="text-muted-foreground">
            Please wait while we securely authenticate your account with GitHub.
          </p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="text-center space-y-6 max-w-md">
          <div className="flex justify-center">
            <div className="rounded-full bg-destructive/10 p-4">
              <AlertCircle className="h-12 w-12 text-destructive" />
            </div>
          </div>
          <div className="space-y-2">
            <h1 className="text-2xl font-semibold">Authentication Failed</h1>
            <p className="text-muted-foreground">{error}</p>
          </div>
          <div className="flex flex-col gap-3">
            <Link href="/auth/login">
              <Button className="w-full">
                Try Again
              </Button>
            </Link>
            <Link href="/">
              <Button variant="outline" className="w-full">
                Back to Home
              </Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

export default function CallbackPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
        <Loader2 className="h-12 w-12 text-primary animate-spin" />
      </div>
    }>
      <CallbackContent />
    </Suspense>
  )
}
