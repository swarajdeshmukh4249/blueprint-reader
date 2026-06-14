import { cn } from '@/lib/utils'

export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('animate-pulse rounded-md bg-ink/10', className)}
      {...props}
    />
  )
}

export function CardSkeleton() {
  return (
    <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-6">
      <Skeleton className="h-4 w-3/4 mb-4" />
      <Skeleton className="h-3 w-1/2 mb-2" />
      <Skeleton className="h-3 w-1/3" />
    </div>
  )
}

export function StatsSkeleton() {
  return (
    <div className="rounded-lg border border-ink/10 bg-paper-2/50 p-6">
      <div className="flex items-center justify-between">
        <div>
          <Skeleton className="h-4 w-24 mb-2" />
          <Skeleton className="h-8 w-16" />
        </div>
        <Skeleton className="h-8 w-8 rounded-full" />
      </div>
    </div>
  )
}

export function TableSkeleton({ rows = 5 }: { rows?: number }) {
  return (
    <div className="rounded-lg border border-ink/10 bg-paper-2/50 overflow-hidden">
      <div className="px-6 py-4 border-b border-ink/10">
        <Skeleton className="h-5 w-32" />
      </div>
      <div className="divide-y divide-ink/5">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="px-6 py-4">
            <div className="flex items-center gap-4">
              <Skeleton className="h-5 w-5 rounded" />
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-16" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export function ListSkeleton({ items = 5 }: { items?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="rounded-lg border border-ink/10 bg-paper-2/50 p-4">
          <div className="flex items-start gap-3">
            <Skeleton className="h-10 w-10 rounded-full" />
            <div className="flex-1">
              <Skeleton className="h-4 w-3/4 mb-2" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export function PageSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-10 w-32" />
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <StatsSkeleton key={i} />
        ))}
      </div>
      
      <TableSkeleton rows={5} />
    </div>
  )
}

export function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12'
  }
  
  return (
    <div className={`animate-spin rounded-full border-2 border-ink/10 border-t-accent ${sizeClasses[size]}`} />
  )
}

export function LoadingOverlay({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-paper/80 backdrop-blur-sm">
      <div className="text-center">
        <LoadingSpinner size="lg" />
        <p className="mt-4 text-sm text-ink/70">{message}</p>
      </div>
    </div>
  )
}
