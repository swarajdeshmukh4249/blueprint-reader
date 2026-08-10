import { useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'

type Props = {
  className?: string
  density?: number
  connectionDistance?: number
}

type Node = {
  x: number
  y: number
  vx: number
  vy: number
  radius: number
}

const MAX_NODES = 85
const POINTER_RADIUS = 180

export default function PlexusBackground({
  className,
  density = 0.00011,
  connectionDistance = 150,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const context = canvas.getContext('2d')
    if (!context) return

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)')
    let frame = 0
    let width = 0
    let height = 0
    let nodes: Node[] = []
    const pointer = { x: -1000, y: -1000 }

    const createNodes = () => {
      const count = Math.min(MAX_NODES, Math.max(24, Math.round(width * height * density)))
      nodes = Array.from({ length: count }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.18,
        vy: (Math.random() - 0.5) * 0.18,
        radius: Math.random() * 1.5 + 1,
      }))
    }

    const resize = () => {
      const bounds = canvas.getBoundingClientRect()
      const ratio = Math.min(window.devicePixelRatio || 1, 2)
      width = bounds.width
      height = bounds.height
      canvas.width = Math.round(width * ratio)
      canvas.height = Math.round(height * ratio)
      canvas.style.width = `${width}px`
      canvas.style.height = `${height}px`
      context.setTransform(ratio, 0, 0, ratio, 0, 0)
      createNodes()
      draw()
    }

    const draw = () => {
      context.clearRect(0, 0, width, height)
      const distance = Math.min(connectionDistance, Math.max(110, width * 0.18))

      for (const node of nodes) {
        if (!reducedMotion.matches) {
          node.x += node.vx
          node.y += node.vy
          if (node.x < -10 || node.x > width + 10) node.vx *= -1
          if (node.y < -10 || node.y > height + 10) node.vy *= -1
        }

        const dx = pointer.x - node.x
        const dy = pointer.y - node.y
        const proximity = Math.max(0, 1 - Math.hypot(dx, dy) / POINTER_RADIUS)
        const radius = node.radius + proximity * 2
        context.beginPath()
        context.arc(node.x, node.y, radius, 0, Math.PI * 2)
        context.fillStyle = `hsl(var(--plexus-node) / ${0.34 + proximity * 0.5})`
        context.fill()
      }

      for (let index = 0; index < nodes.length; index += 1) {
        for (let next = index + 1; next < nodes.length; next += 1) {
          const first = nodes[index]
          const second = nodes[next]
          const dx = first.x - second.x
          const dy = first.y - second.y
          const length = Math.hypot(dx, dy)
          if (length > distance) continue

          const pointerBoost = Math.max(
            0,
            1 - Math.min(Math.hypot(pointer.x - (first.x + second.x) / 2, pointer.y - (first.y + second.y) / 2), POINTER_RADIUS) / POINTER_RADIUS,
          )
          context.beginPath()
          context.moveTo(first.x, first.y)
          context.lineTo(second.x, second.y)
          context.strokeStyle = `hsl(var(--plexus-line) / ${((1 - length / distance) * 0.24 + pointerBoost * 0.36).toFixed(3)})`
          context.lineWidth = pointerBoost > 0.2 ? 1.1 : 0.7
          context.stroke()
        }
      }
    }

    const animate = () => {
      draw()
      if (!reducedMotion.matches) frame = requestAnimationFrame(animate)
    }

    const handlePointerMove = (event: PointerEvent) => {
      const bounds = canvas.getBoundingClientRect()
      pointer.x = event.clientX - bounds.left
      pointer.y = event.clientY - bounds.top
      if (reducedMotion.matches) draw()
    }

    const handlePointerLeave = () => {
      pointer.x = -1000
      pointer.y = -1000
      if (reducedMotion.matches) draw()
    }

    resize()
    window.addEventListener('resize', resize)
    canvas.addEventListener('pointermove', handlePointerMove)
    canvas.addEventListener('pointerleave', handlePointerLeave)
    reducedMotion.addEventListener('change', resize)
    if (!reducedMotion.matches) frame = requestAnimationFrame(animate)

    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('resize', resize)
      canvas.removeEventListener('pointermove', handlePointerMove)
      canvas.removeEventListener('pointerleave', handlePointerLeave)
      reducedMotion.removeEventListener('change', resize)
    }
  }, [connectionDistance, density])

  return <canvas ref={canvasRef} aria-hidden="true" className={cn('h-full w-full', className)} />
}
