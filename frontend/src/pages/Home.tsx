import { ArrowRight, FileText, LayoutGrid, Ruler, Sparkles } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import type { ReactNode } from 'react'
import BlueprintHeroVisual from '@/components/BlueprintHeroVisual'
import HeroBackgroundVideo from '@/components/HeroBackgroundVideo'
import Container from '@/components/Container'
import { cn } from '@/lib/utils'

function Chip({ children }: { children: string }) {
  return (
    <span className="inline-flex items-center rounded-full border border-ink/10 bg-paper/60 px-3 py-1 text-xs tracking-wide text-ink/70">
      {children}
    </span>
  )
}

function Card({
  icon,
  title,
  description,
}: {
  icon: ReactNode
  title: string
  description: string
}) {
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-ink/10 bg-paper/60 p-6 shadow-[0_10px_30px_hsl(var(--shadow)/0.08)] transition hover:-translate-y-1 hover:bg-paper">
      <div className="absolute inset-0 opacity-0 transition-opacity group-hover:opacity-100">
        <div className="absolute -left-24 -top-24 h-72 w-72 rounded-full bg-accent/10 blur-2xl" />
      </div>
      <div className="relative flex items-start gap-4">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl border border-ink/10 bg-paper-2/60 text-ink">
          {icon}
        </div>
        <div className="space-y-1">
          <div className="text-sm font-semibold tracking-tight">{title}</div>
          <div className="text-sm leading-relaxed text-ink/70">{description}</div>
        </div>
      </div>
    </div>
  )
}

export default function Home() {
  return (
    <div className="pb-16">
      <section>
        <div className="relative">
          <HeroBackgroundVideo className="pointer-events-none absolute inset-0 -z-10 overflow-hidden" />
          <Container className="grid items-start gap-10 pt-12 md:grid-cols-12 md:gap-12 md:pt-16">
          <div className="md:col-span-6">
            <div className="animate-reveal space-y-6">
              <div className="flex flex-wrap items-center gap-2">
                <Chip>PDF</Chip>
                <Chip>JPG / PNG</Chip>
                <Chip>DXF</Chip>
                <Chip>DWG</Chip>
                <Chip>IFC</Chip>
              </div>

              <h1 className="font-display text-[44px] leading-[0.92] tracking-tight text-ink md:text-[74px]">
                Blueprint
                <span className="block text-ink/85">Intelligence,</span>
                <span className="block">Delivered.</span>
              </h1>

              <p className="max-w-xl text-base leading-relaxed text-ink/70 md:text-lg">
                Upload a drawing1. Get room areas, totals, and a BOQ-ready structure—presented with the
                clarity of an architectural studio and the speed of automation.
              </p>

              <div className="flex flex-wrap items-center gap-3">
                <NavLink
                  to="/upload"
                  className="inline-flex items-center gap-2 rounded-full bg-ink px-5 py-3 text-sm font-medium text-paper transition hover:-translate-y-px hover:bg-ink/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50"
                >
                  Analyze a blueprint <ArrowRight className="h-4 w-4" />
                </NavLink>
                <NavLink
                  to="/about"
                  className={cn(
                    'inline-flex items-center gap-2 rounded-full border border-ink/15 bg-paper/50 px-5 py-3 text-sm font-medium text-ink/80 transition',
                    'hover:-translate-y-px hover:bg-paper hover:text-ink focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50',
                  )}
                >
                  How it works
                </NavLink>
              </div>

              <div className="grid max-w-xl grid-cols-3 gap-4 pt-2 text-sm">
                <div className="rounded-2xl border border-ink/10 bg-paper/50 p-4">
                  <div className="font-display text-2xl tracking-tight">Rooms</div>
                  <div className="mt-1 text-ink/65">Structured detection</div>
                </div>
                <div className="rounded-2xl border border-ink/10 bg-paper/50 p-4">
                  <div className="font-display text-2xl tracking-tight">Areas</div>
                  <div className="mt-1 text-ink/65">Totals + schedules</div>
                </div>
                <div className="rounded-2xl border border-ink/10 bg-paper/50 p-4">
                  <div className="font-display text-2xl tracking-tight">BOQ</div>
                  <div className="mt-1 text-ink/65">Export-ready outputs</div>
                </div>
              </div>
            </div>
          </div>

          <div className="md:col-span-6 md:pt-3">
            <BlueprintHeroVisual className="animate-reveal [animation-delay:140ms]" />
          </div>
          </Container>
        </div>
      </section>

      <section className="mt-16">
        <Container>
          <div className="grid gap-6 md:grid-cols-12">
            <div className="md:col-span-4">
              <div className="space-y-4">
                <div className="inline-flex items-center gap-2 rounded-full border border-ink/10 bg-paper/60 px-3 py-1 text-xs tracking-[0.2em] text-ink/60">
                  <Sparkles className="h-3.5 w-3.5 text-accent" />
                  CAPABILITIES
                </div>
                <h2 className="font-display text-3xl leading-tight tracking-tight md:text-4xl">
                  Built for real drawings.
                </h2>
                <p className="text-sm leading-relaxed text-ink/70">
                  The interface is designed to feel like a premium tool—fast, calm, and precise—while
                  the pipeline behind it converts plans into readable quantities.
                </p>
              </div>
            </div>

            <div className="md:col-span-8">
              <div className="grid gap-4 md:grid-cols-2">
                <Card
                  icon={<LayoutGrid className="h-5 w-5" />}
                  title="Room schedule output"
                  description="A clean list of rooms with areas and totals, ready to review or share."
                />
                <Card
                  icon={<Ruler className="h-5 w-5" />}
                  title="Area totals and rollups"
                  description="Summaries that surface the key numbers first—then let you drill into details."
                />
                <Card
                  icon={<FileText className="h-5 w-5" />}
                  title="Export formats"
                  description="Download JSON or CSV, or copy the raw output to plug into your workflow."
                />
                <Card
                  icon={<Sparkles className="h-5 w-5" />}
                  title="Blueprint-themed motion"
                  description="Subtle scanning, linework reveals, and micro-interactions—innovative, not loud."
                />
              </div>
            </div>
          </div>
        </Container>
      </section>

      <section className="mt-16">
        <Container>
          <div className="grid gap-6 rounded-3xl border border-ink/10 bg-paper/60 p-8 md:grid-cols-12 md:items-center">
            <div className="md:col-span-7">
              <h3 className="font-display text-3xl leading-tight tracking-tight md:text-4xl">
                See what the output looks like.
              </h3>
              <p className="mt-3 max-w-xl text-sm leading-relaxed text-ink/70">
                A results view that prioritizes the essentials—rooms, areas, totals—plus an export
                layer for whatever comes next.
              </p>
            </div>
            <div className="md:col-span-5">
              <div className="rounded-2xl border border-ink/10 bg-paper-2/60 p-5 text-sm shadow-[0_16px_40px_hsl(var(--shadow)/0.12)]">
                <div className="flex items-center justify-between text-xs tracking-wide text-ink/60">
                  <span>Rooms</span>
                  <span>Total Area</span>
                </div>
                <div className="mt-4 space-y-3">
                  {[
                    ['Living', '18.4 m²'],
                    ['Kitchen', '12.1 m²'],
                    ['Bedroom', '14.0 m²'],
                    ['Bath', '4.8 m²'],
                  ].map(([name, value]) => (
                    <div
                      key={name}
                      className="flex items-center justify-between rounded-xl border border-ink/10 bg-paper/60 px-4 py-3"
                    >
                      <div className="font-medium">{name}</div>
                      <div className="text-ink/70">{value}</div>
                    </div>
                  ))}
                </div>
                <div className="mt-5 flex items-center justify-between rounded-xl border border-ink/10 bg-paper/60 px-4 py-3">
                  <div className="text-xs tracking-wide text-ink/60">Total</div>
                  <div className="font-semibold">49.3 m²</div>
                </div>
              </div>
            </div>
          </div>
        </Container>
      </section>
    </div>
  )
}
