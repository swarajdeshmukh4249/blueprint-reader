import { Check, Layers, Scan, Shapes } from 'lucide-react'
import type { ReactNode } from 'react'
import BlueprintHeroVisual from '@/components/BlueprintHeroVisual'
import Container from '@/components/Container'

function Step({
  title,
  description,
  icon,
}: {
  title: string
  description: string
  icon: ReactNode
}) {
  return (
    <div className="rounded-2xl border border-ink/10 bg-paper/60 p-6 shadow-[0_12px_36px_hsl(var(--shadow)/0.08)]">
      <div className="flex items-start gap-4">
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

export default function About() {
  return (
    <div className="pb-16">
      <Container className="pt-10 md:pt-14">
        <div className="grid gap-10 md:grid-cols-12 md:items-start">
          <div className="space-y-5 md:col-span-6">
            <div className="text-xs tracking-[0.22em] text-ink/55">ABOUT</div>
            <h1 className="font-display text-4xl leading-[0.95] tracking-tight md:text-5xl">
              From drawing to takeoff,
              <span className="block text-ink/80">without the noise.</span>
            </h1>
            <p className="max-w-xl text-sm leading-relaxed text-ink/70">
              ArchVision turns common construction and architectural formats into structured
              outputs. The UI stays calm, but the pipeline is built for messy real-world files.
            </p>

            <div className="grid gap-4">
              <Step
                icon={<Scan className="h-5 w-5" />}
                title="Ingest and normalize"
                description="PDFs, images, and CAD/BIM files are converted into analyzable representations."
              />
              <Step
                icon={<Shapes className="h-5 w-5" />}
                title="Extract geometry + text"
                description="OCR and vector parsing work together to isolate rooms, boundaries, and labels."
              />
              <Step
                icon={<Layers className="h-5 w-5" />}
                title="Structure the result"
                description="Rooms, areas, totals, and BOQ-oriented items are organized into exportable data."
              />
              <Step
                icon={<Check className="h-5 w-5" />}
                title="Present with clarity"
                description="A results view designed like a schedule: readable first, detailed when needed."
              />
            </div>
          </div>

          <div className="md:col-span-6 md:pt-2">
            <BlueprintHeroVisual className="animate-drift" />
            <div className="mt-4 rounded-2xl border border-ink/10 bg-paper/50 p-5 text-sm text-ink/70">
              You can connect this UI to your deployed FastAPI endpoint using{' '}
              <span className="font-medium text-ink">VITE_API_BASE_URL</span>.
            </div>
          </div>
        </div>
      </Container>
    </div>
  )
}
