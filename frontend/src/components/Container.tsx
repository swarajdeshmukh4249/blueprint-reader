import { cn } from '@/lib/utils'
import type { ReactNode } from 'react'

type Props = {
  className?: string
  children: ReactNode
}

export default function Container({ className, children }: Props) {
  return (
    <div className={cn('mx-auto w-full max-w-6xl px-6', className)}>
      {children}
    </div>
  )
}
