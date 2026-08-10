import React from 'react'
import { motion, type Easing, useMotionValue, useSpring, useTransform } from 'framer-motion'

const ease: Easing = [0.42, 0, 0.58, 1] // easeInOut cubic bezier

// SVG path data for a realistic floor plan
const wallSegments = [
    // Outer walls
    { d: 'M 40 40 L 360 40', delay: 0, label: 'top-outer' },
    { d: 'M 360 40 L 360 300', delay: 0.15, label: 'right-outer' },
    { d: 'M 360 300 L 40 300', delay: 0.3, label: 'bottom-outer' },
    { d: 'M 40 300 L 40 40', delay: 0.45, label: 'left-outer' },

    // Interior walls
    { d: 'M 200 40 L 200 180', delay: 0.7, label: 'center-vert' },
    { d: 'M 40 180 L 200 180', delay: 0.85, label: 'left-horiz' },
    { d: 'M 200 180 L 200 300', delay: 1.0, label: 'center-vert-2' },
    { d: 'M 200 200 L 360 200', delay: 1.1, label: 'right-horiz' },

    // Extra detail walls
    { d: 'M 120 180 L 120 300', delay: 1.25, label: 'bath-wall' },
    { d: 'M 280 40 L 280 120', delay: 1.35, label: 'closet-wall' },
    { d: 'M 280 120 L 360 120', delay: 1.45, label: 'closet-wall-h' },
]

// Dimension lines
const dimensions = [
    { x1: 40, y1: 30, x2: 360, y2: 30, text: '8.0 m', textX: 200, textY: 25, delay: 1.6 },
    { x1: 370, y1: 40, x2: 370, y2: 300, text: '6.5 m', textX: 385, textY: 170, delay: 1.7 },
]

// Room labels
const roomLabels = [
    { text: 'LIVING ROOM', x: 120, y: 110, size: 10, delay: 1.8 },
    { text: '24.5 m²', x: 120, y: 125, size: 8, delay: 1.9 },
    { text: 'BEDROOM', x: 280, y: 80, size: 10, delay: 2.0 },
    { text: '16.8 m²', x: 280, y: 95, size: 8, delay: 2.1 },
    { text: 'KITCHEN', x: 120, y: 230, size: 10, delay: 2.2 },
    { text: '12.0 m²', x: 120, y: 245, size: 8, delay: 2.3 },
    { text: 'BATH', x: 75, y: 240, size: 8, delay: 2.35 },
    { text: 'OFFICE', x: 280, y: 250, size: 10, delay: 2.4 },
    { text: '10.2 m²', x: 280, y: 265, size: 8, delay: 2.5 },
]

// Door arcs
const doorArcs = [
    { d: 'M 200 60 A 30 30 0 0 1 225 40', delay: 2.6 },
    { d: 'M 155 180 A 25 25 0 0 0 180 205', delay: 2.7 },
    { d: 'M 200 220 A 25 25 0 0 1 225 200', delay: 2.8 },
    { d: 'M 310 200 A 25 25 0 0 1 335 225', delay: 2.85 },
]

// Window markers (small dashes on outer walls)
const windows = [
    { x1: 90, y1: 40, x2: 150, y2: 40, delay: 2.9 },
    { x1: 310, y1: 40, x2: 350, y2: 40, delay: 2.95 },
    { x1: 360, y1: 140, x2: 360, y2: 190, delay: 3.0 },
    { x1: 40, y1: 80, x2: 40, y2: 140, delay: 3.05 },
]

const pathDraw = {
    hidden: { pathLength: 0, opacity: 0 },
    visible: (delay: number) => ({
        pathLength: 1,
        opacity: 1,
        transition: {
            pathLength: { duration: 0.8, ease, delay },
            opacity: { duration: 0.1, delay },
        },
    }),
} as any // eslint-disable-line @typescript-eslint/no-explicit-any

const fadeIn = {
    hidden: { opacity: 0 },
    visible: (delay: number) => ({
        opacity: 1,
        transition: { duration: 0.5, delay },
    }),
}

export default function BlueprintDraftingCard() {
    const x = useMotionValue(0.5)
    const y = useMotionValue(0.5)

    const mouseXSpring = useSpring(x, { stiffness: 300, damping: 20 })
    const mouseYSpring = useSpring(y, { stiffness: 300, damping: 20 })

    const rotateX = useTransform(mouseYSpring, [0, 1], ['15deg', '-15deg'])
    const rotateY = useTransform(mouseXSpring, [0, 1], ['-15deg', '15deg'])

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
        const rect = e.currentTarget.getBoundingClientRect()
        const width = rect.width
        const height = rect.height
        const mouseX = e.clientX - rect.left
        const mouseY = e.clientY - rect.top
        x.set(mouseX / width)
        y.set(mouseY / height)
    }

    const handleMouseLeave = () => {
        x.set(0.5)
        y.set(0.5)
    }

    return (
        <motion.div
            style={{ rotateX, rotateY, perspective: 1000 }}
            onMouseMove={handleMouseMove}
            onMouseLeave={handleMouseLeave}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="blueprint-drafting-card"
        >
            {/* Card label */}
            <div className="drafting-card-header">
                <div className="drafting-card-dot" />
                <span className="drafting-card-label">FLOOR PLAN — UNIT A.102</span>
                <span className="drafting-card-scale">SCALE 1:100</span>
            </div>

            <div className="drafting-card-body">
                <svg
                    viewBox="0 0 420 340"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    className="drafting-svg"
                >
                    <rect width="420" height="340" fill="transparent" />

                    {/* Wall segments with draw animation */}
                    {wallSegments.map((seg, i) => (
                        <motion.path
                            key={i}
                            d={seg.d}
                            stroke="hsl(var(--arch-cyan))"
                            strokeWidth="2.5"
                            strokeLinecap="round"
                            fill="none"
                            style={{ filter: 'drop-shadow(0px 0px 4px hsl(var(--arch-cyan) / 0.5))' }}
                            variants={pathDraw}
                            initial="hidden"
                            animate="visible"
                            custom={seg.delay}
                        />
                    ))}

                    {/* Door arcs */}
                    {doorArcs.map((arc, i) => (
                        <motion.path
                            key={`door-${i}`}
                            d={arc.d}
                            stroke="hsl(var(--arch-cyan) / 0.6)"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeDasharray="4 3"
                            fill="none"
                            variants={pathDraw}
                            initial="hidden"
                            animate="visible"
                            custom={arc.delay}
                        />
                    ))}

                    {/* Window markers (double lines) */}
                    {windows.map((win, i) => (
                        <g key={`win-${i}`}>
                            <motion.line
                                x1={win.x1}
                                y1={win.y1}
                                x2={win.x2}
                                y2={win.y2}
                                stroke="hsl(var(--accent))"
                                strokeWidth="4"
                                variants={pathDraw}
                                initial="hidden"
                                animate="visible"
                                custom={win.delay}
                            />
                            <motion.line
                                x1={win.x1}
                                y1={win.y1 === win.y2 ? win.y1 - 2 : win.y1}
                                x2={win.x2}
                                y2={win.y2 === win.y1 ? win.y2 + 2 : win.y2}
                                stroke="hsl(var(--paper))"
                                strokeWidth="2"
                                variants={pathDraw}
                                initial="hidden"
                                animate="visible"
                                custom={win.delay + 0.05}
                            />
                        </g>
                    ))}

                    {/* Dimension lines */}
                    {dimensions.map((dim, i) => (
                        <g key={`dim-${i}`}>
                            <motion.line
                                x1={dim.x1}
                                y1={dim.y1}
                                x2={dim.x2}
                                y2={dim.y2}
                                stroke="hsl(var(--arch-cyan) / 0.35)"
                                strokeWidth="0.8"
                                strokeDasharray="6 3"
                                variants={pathDraw}
                                initial="hidden"
                                animate="visible"
                                custom={dim.delay}
                            />
                            {/* Dimension tick marks */}
                            <motion.line
                                x1={dim.x1}
                                y1={dim.y1 - 4}
                                x2={dim.x1}
                                y2={dim.y1 + 4}
                                stroke="hsl(var(--arch-cyan) / 0.35)"
                                strokeWidth="0.8"
                                variants={fadeIn}
                                initial="hidden"
                                animate="visible"
                                custom={dim.delay}
                            />
                            <motion.line
                                x1={dim.x2}
                                y1={dim.y2 - 4}
                                x2={dim.x2}
                                y2={dim.y2 + 4}
                                stroke="hsl(var(--arch-cyan) / 0.35)"
                                strokeWidth="0.8"
                                variants={fadeIn}
                                initial="hidden"
                                animate="visible"
                                custom={dim.delay}
                            />
                            {/* Dimension text */}
                            <motion.text
                                x={dim.textX}
                                y={dim.textY}
                                textAnchor="middle"
                                fill="hsl(var(--arch-cyan) / 0.5)"
                                fontSize="9"
                                fontFamily="monospace"
                                variants={fadeIn}
                                initial="hidden"
                                animate="visible"
                                custom={dim.delay + 0.15}
                            >
                                {dim.text}
                            </motion.text>
                        </g>
                    ))}

                    {/* Room labels */}
                    {roomLabels.map((room, i) => (
                        <motion.text
                            key={`room-${i}`}
                            x={room.x}
                            y={room.y}
                            textAnchor="middle"
                            fill={room.size >= 10 ? 'hsl(var(--ink) / 0.7)' : 'hsl(var(--arch-cyan) / 0.6)'}
                            fontSize={room.size}
                            fontFamily={room.size >= 10 ? '"Inter", sans-serif' : 'monospace'}
                            fontWeight={room.size >= 10 ? 500 : 400}
                            letterSpacing={room.size >= 10 ? '0.1em' : '0.05em'}
                            variants={fadeIn}
                            initial="hidden"
                            animate="visible"
                            custom={room.delay}
                        >
                            {room.text}
                        </motion.text>
                    ))}

                    {/* Compass rose (top right) */}
                    <motion.g
                        variants={fadeIn}
                        initial="hidden"
                        animate="visible"
                        custom={3.1}
                    >
                        <circle cx="395" cy="25" r="12" fill="none" stroke="hsl(var(--arch-cyan) / 0.3)" strokeWidth="0.8" />
                        <line x1="395" y1="16" x2="395" y2="34" stroke="hsl(var(--arch-cyan) / 0.4)" strokeWidth="0.8" />
                        <line x1="386" y1="25" x2="404" y2="25" stroke="hsl(var(--arch-cyan) / 0.4)" strokeWidth="0.8" />
                        <text x="395" y="14" textAnchor="middle" fill="hsl(var(--arch-cyan) / 0.5)" fontSize="7" fontWeight="bold">N</text>
                    </motion.g>

                    {/* Drafting pen cursor animation — a small dot that follows the drawing */}
                    <motion.circle
                        cx="0"
                        cy="0"
                        r="3"
                        fill="hsl(var(--arch-cyan))"
                        style={{ filter: 'drop-shadow(0px 0px 6px hsl(var(--arch-cyan)))' }}
                        initial={{ opacity: 0 }}
                        animate={{
                            opacity: [0, 1, 1, 1, 1, 0],
                            cx: [40, 360, 360, 40, 40, 200],
                            cy: [40, 40, 300, 300, 40, 180],
                        }}
                        transition={{
                            duration: 2.5,
                            ease: 'easeInOut',
                            times: [0, 0.2, 0.4, 0.6, 0.8, 1],
                        }}
                    />
                </svg>
            </div>

            {/* Bottom status bar */}
            <div className="drafting-card-footer">
                <motion.div
                    className="drafting-progress"
                    initial={{ width: '0%' }}
                    animate={{ width: '100%' }}
                    transition={{ duration: 3.2, ease: 'easeInOut' }}
                />
                <motion.span
                    className="drafting-card-status"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 3.3, duration: 0.4 }}
                >
                    ✓ Blueprint analysis ready
                </motion.span>
            </div>
        </motion.div>
    )
}
