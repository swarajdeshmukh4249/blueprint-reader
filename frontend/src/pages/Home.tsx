import { useRef, useState, useEffect } from 'react'
import { motion, useScroll, useTransform, useSpring } from 'framer-motion'
import { ArrowRight } from 'lucide-react'
import { NavLink } from 'react-router-dom'
import ArchVision3D from '@/components/ArchVision3D'
import InitialDraftingBackground from '@/components/InitialDraftingBackground'

export default function Home() {
  const containerRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({ target: containerRef })

  // State for the intro animation
  const [introDone, setIntroDone] = useState(false)
  useEffect(() => {
    const timer = setTimeout(() => {
      setIntroDone(true)
    }, 4500)
    return () => clearTimeout(timer)
  }, [])

  // Apply spring for smoother scrolling
  const smoothScroll = useSpring(scrollYProgress, { stiffness: 120, damping: 30 })

  // Text animations tied to scroll
  const headerOpacity = useTransform(smoothScroll, [0, 0.1], [1, 0])
  const headerY = useTransform(smoothScroll, [0, 0.1], [0, -50])

  const boqOpacity = useTransform(smoothScroll, [0.8, 0.9], [0, 1])
  const boqY = useTransform(smoothScroll, [0.8, 0.9], [50, 0])

  return (
    <div ref={containerRef} className="relative h-[400vh] bg-transparent text-ink">
      {/* Light/Dark mode toggle */}
      <button
        onClick={() => {
          const html = document.documentElement
          html.classList.toggle('dark')
        }}
        className="fixed top-4 right-4 z-30 rounded-full bg-ink px-4 py-2 text-paper shadow-lg hover:bg-accent transition-colors"
      >
        Toggle Light/Dark
      </button>
      {/* Intro Blueprint Animation */}
      <div className="pointer-events-none fixed inset-0 z-0 transition-opacity duration-1000" style={{ opacity: introDone ? 0 : 1 }}>
        <InitialDraftingBackground />
      </div>

      {/* 3D Model background fixed to viewport */}
      <div className="pointer-events-none fixed inset-0 z-0 transition-opacity duration-1000" style={{ opacity: introDone ? 1 : 0 }}>
        <ArchVision3D scrollYProgress={smoothScroll} />
      </div>

      {/* Hero Section */}
      <motion.section
        style={{ opacity: headerOpacity, y: headerY }}
        className="fixed inset-0 z-10 flex flex-col items-center justify-center text-center px-4"
      >
        <h1 className="font-sans text-[60px] leading-tight tracking-[0.02em] md:text-[100px] font-medium text-ink">
          Arch<span className="text-accent">Vision</span>
        </h1>
        <p className="mt-6 max-w-2xl text-lg md:text-2xl font-light text-ink/70">
          Turn architectural blueprints into 3D models and instant Bills of Quantities.
        </p>
        <div className="mt-10">
          <NavLink
            to="/upload"
            className="group relative inline-flex items-center gap-3 overflow-hidden rounded-full bg-ink px-8 py-4 text-base font-medium text-paper transition-all hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/50"
          >
            <span className="relative z-10">Start Analyzing</span>
            <ArrowRight className="relative z-10 h-5 w-5 transition-transform group-hover:translate-x-1" />
          </NavLink>
        </div>
      </motion.section>

      {/* The drawing card has been moved to be the fullscreen InitialDraftingBackground above */}

      {/* BOQ Final Section */}
      <motion.section
        style={{ opacity: boqOpacity, y: boqY }}
        className="pointer-events-none fixed inset-0 z-20 flex flex-col items-center justify-center px-4 pt-[40vh]"
      >
        <div className="pointer-events-auto mt-auto mb-20 w-full max-w-3xl overflow-hidden rounded-xl border border-accent/20 bg-paper-2/90 p-1 shadow-[0_0_40px_rgba(0,212,255,0.1)] backdrop-blur-md">
          <div className="flex items-center justify-between border-b border-accent/20 bg-accent/5 px-6 py-4">
            <h2 className="text-xl font-medium tracking-wide text-ink">Instant BOQ Generated</h2>
            <div className="text-sm font-mono text-accent">Confidence: 99.8%</div>
          </div>
          <div className="divide-y divide-accent/10">
            {[
              { item: 'Structural Walls (Concrete)', qty: '142 m³', cost: '$12,400' },
              { item: 'Interior Partitions (Drywall)', qty: '310 m²', cost: '$4,650' },
              { item: 'Standard Doors (Wooden)', qty: '14 units', cost: '$2,100' },
              { item: 'Window Glazing (Double-paned)', qty: '42 m²', cost: '$3,800' },
              { item: 'Flooring (Ceramic Tile)', qty: '185 m²', cost: '$5,550' },
            ].map((row, i) => (
              <div key={i} className="flex justify-between px-6 py-4 hover:bg-accent/5 transition-colors">
                <span className="font-light text-ink/90">{row.item}</span>
                <div className="flex gap-12 font-mono text-sm">
                  <span className="text-ink/60">{row.qty}</span>
                  <span className="w-16 text-right text-accent">{row.cost}</span>
                </div>
              </div>
            ))}
            <div className="flex justify-between bg-accent/10 px-6 py-5 font-mono text-base font-semibold text-accent">
              <span>Total Estimated Cost</span>
              <span>$28,500</span>
            </div>
          </div>
        </div>
      </motion.section>
    </div>
  )
}
