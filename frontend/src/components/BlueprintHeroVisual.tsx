import { cn } from '@/lib/utils'

type Props = {
  className?: string
}

export default function BlueprintHeroVisual({ className }: Props) {
  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-3xl border border-ink/10 bg-paper-2/60 shadow-soft',
        className,
      )}
    >
      <div className="absolute inset-0 bg-[radial-gradient(900px_420px_at_70%_25%,hsl(var(--accent)/0.10),transparent_60%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(135deg,hsl(var(--ink)/0.05),transparent_60%)]" />
      <div className="absolute inset-0 opacity-50 [mask-image:radial-gradient(closest-side_at_55%_40%,black,transparent_80%)]">
        <div className="absolute inset-0 bg-[linear-gradient(hsl(var(--ink)/0.09)_1px,transparent_1px),linear-gradient(90deg,hsl(var(--ink)/0.09)_1px,transparent_1px)] bg-[length:36px_36px]" />
      </div>

      <div className="relative aspect-[4/3] w-full">
        <div className="pointer-events-none absolute inset-y-0 left-0 w-1/3 animate-scan bg-[linear-gradient(90deg,transparent,hsla(191,92%,48%,0.22),transparent)] blur-sm" />
        <div className="absolute inset-0 p-8">
          <svg
            viewBox="0 0 780 560"
            className="h-full w-full"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <g
              className="animate-dash"
              stroke="hsl(var(--ink) / 0.62)"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeDasharray="900"
              strokeDashoffset="900"
            >
              <path d="M94 88H686V472H94V88Z" />
              <path d="M94 188H686" />
              <path d="M94 332H686" />
              <path d="M252 88V472" />
              <path d="M528 88V472" />
              <path d="M252 188H528V332H252V188Z" />
              <path d="M112 120H236V172H112V120Z" />
              <path d="M544 120H668V172H544V120Z" />
              <path d="M112 360H236V440H112V360Z" />
              <path d="M544 360H668V440H544V360Z" />
              <path d="M312 234H468V286H312V234Z" />
              <path d="M390 234V286" />
              <path d="M252 332L94 472" />
              <path d="M528 332L686 472" />
            </g>
            <g stroke="hsl(var(--accent) / 0.72)" strokeWidth="2">
              <path d="M252 188H528" />
              <path d="M252 332H528" />
              <path d="M252 188V332" />
              <path d="M528 188V332" />
            </g>
            <g fill="hsl(var(--ink) / 0.5)">
              <circle cx="174" cy="146" r="4" />
              <circle cx="606" cy="146" r="4" />
              <circle cx="174" cy="400" r="4" />
              <circle cx="606" cy="400" r="4" />
              <circle cx="390" cy="260" r="4" />
            </g>
          </svg>
        </div>
      </div>
    </div>
  )
}

