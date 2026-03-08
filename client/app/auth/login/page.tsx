'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Github, FileCode, ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { initiateGitHubLogin } from '@/lib/api/auth'

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleGitHubLogin = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const authUrl = await initiateGitHubLogin()
      window.location.href = authUrl
    } catch (err) {
      setError('Failed to initiate GitHub login. Please try again.')
      setIsLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
      {/* Back to home link */}
      <Link 
        href="/" 
        className="absolute top-8 left-8 flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Home
      </Link>

      {/* Logo */}
      <div className="mb-10 flex items-center gap-3">
        <FileCode className="h-9 w-9 text-primary" />
        <span className="text-3xl font-bold tracking-tight">CodeLens AI</span>
      </div>

      {/* Login Card */}
      <Card className="w-full max-w-md border-border/50">
        <CardHeader className="space-y-2 text-center pb-2">
          <CardTitle className="text-3xl font-bold">Welcome Back</CardTitle>
          <CardDescription className="text-base text-muted-foreground">
            Sign in to your account to continue exploring codebases
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6 pt-6">
          {/* GitHub Login Button */}
          <Button
            onClick={handleGitHubLogin}
            disabled={isLoading}
            className="w-full gap-3 h-12 text-base font-medium"
            size="lg"
          >
            <Github className="h-5 w-5" />
            {isLoading ? 'Connecting...' : 'Continue with GitHub'}
          </Button>

          {/* Error Message */}
          {error && (
            <div className="text-sm text-destructive bg-destructive/10 border border-destructive/50 rounded-md p-3">
              {error}
            </div>
          )}

          {/* Sign Up Link */}
          <div className="text-center text-sm text-muted-foreground">
            Don&apos;t have an account?{' '}
            <Link href="#" className="text-primary hover:underline font-medium">
              Sign up
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Footer */}
      <p className="mt-8 text-xs text-muted-foreground text-center max-w-md">
        By continuing, you agree to our{' '}
        <Link href="#" className="underline hover:text-foreground">
          Terms of Service
        </Link>{' '}
        and{' '}
        <Link href="#" className="underline hover:text-foreground">
          Privacy Policy
        </Link>
      </p>
    </div>
  )
}
