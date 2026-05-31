import { useEffect, useMemo, useState } from 'react'

type Props = {
  className?: string
}

function getVideoUrl() {
  return (import.meta.env.VITE_HERO_VIDEO_URL as string | undefined) ?? ''
}

function getPosterUrl() {
  return (import.meta.env.VITE_HERO_VIDEO_POSTER_URL as string | undefined) ?? ''
}

export default function HeroBackgroundVideo({ className }: Props) {
  const src = useMemo(() => getVideoUrl().trim(), [])
  const poster = useMemo(() => getPosterUrl().trim(), [])
  const [reducedMotion, setReducedMotion] = useState(false)

  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    const apply = () => setReducedMotion(mq.matches)
    apply()
    mq.addEventListener?.('change', apply)
    return () => mq.removeEventListener?.('change', apply)
  }, [])

  if (!src || reducedMotion) return null

  return (
    <div className={className}>
      <video
        className="absolute inset-0 h-full w-full object-cover opacity-30"
        autoPlay
        muted
        loop
        playsInline
        preload="metadata"
        poster={poster || undefined}
      >
        <source src={src} />
      </video>
      <div className="absolute inset-0 bg-[radial-gradient(900px_520px_at_18%_18%,hsl(var(--accent)/0.18),transparent_55%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(180deg,hsl(var(--paper)/0.88),transparent_40%,hsl(var(--paper)/0.88))]" />
    </div>
  )
}
