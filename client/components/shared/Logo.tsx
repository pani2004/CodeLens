import { FileCode } from 'lucide-react'
import Link from 'next/link'
import { cn } from '@/lib/utils/cn'

interface LogoProps {
  size?: 'sm' | 'md' | 'lg'
  showText?: boolean
  href?: string
  className?: string
}

const sizeConfig = {
  sm: { icon: 'h-4 w-4', text: 'text-sm' },
  md: { icon: 'h-6 w-6', text: 'text-xl' },
  lg: { icon: 'h-8 w-8', text: 'text-2xl' },
}

export function Logo({ size = 'md', showText = true, href = '/', className }: LogoProps) {
  const content = (
    <div className={cn('flex items-center gap-2', className)}>
      <FileCode className={cn('text-primary', sizeConfig[size].icon)} />
      {showText && (
        <span className={cn('font-bold', sizeConfig[size].text)}>
          CodeLens AI
        </span>
      )}
    </div>
  )

  if (href) {
    return (
      <Link href={href} className="hover:opacity-80 transition-opacity">
        {content}
      </Link>
    )
  }

  return content
}
