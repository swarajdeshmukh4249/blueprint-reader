import { useEffect, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Text } from '@react-three/drei'
import * as THREE from 'three'

// Simple interpolator function
function lerp(start: number, end: number, t: number) {
    return start + (end - start) * Math.max(0, Math.min(1, t))
}

function mapRange(value: number, inMin: number, inMax: number, outMin: number, outMax: number) {
    const t = (value - inMin) / (inMax - inMin)
    return lerp(outMin, outMax, t)
}

function BlueprintModel({ scrollRef }: { scrollRef: { current: number } }) {
    const groupRef = useRef<THREE.Group>(null)

    useFrame(() => {
        if (!groupRef.current) return
        const s = scrollRef.current

        // Map scroll progress to extrusion/rotation
        const rotateX = mapRange(s, 0, 0.4, -Math.PI / 2, -Math.PI / 6)
        const rotateY = mapRange(s, 0.4, 0.7, 0, Math.PI / 4)
        const yPosition = mapRange(s, 0, 0.4, -2, -1)

        groupRef.current.rotation.x = rotateX
        groupRef.current.rotation.y = rotateY
        groupRef.current.position.y = yPosition
    })

    return (
        <group ref={groupRef} scale={1.5}>
            <gridHelper args={[10, 20]} position={[0, 0, 0]} />
            {/* Outer Walls */}
            <ExtrudingWall scrollRef={scrollRef} position={[-2.5, 0, 0]} args={[0.1, 1, 5]} />
            <ExtrudingWall scrollRef={scrollRef} position={[2.5, 0, 0]} args={[0.1, 1, 5]} />
            <ExtrudingWall scrollRef={scrollRef} position={[0, 0, -2.5]} args={[5, 1, 0.1]} />
            <ExtrudingWall scrollRef={scrollRef} position={[0, 0, 2.5]} args={[5, 1, 0.1]} />
            {/* Inner Walls */}
            <ExtrudingWall scrollRef={scrollRef} position={[0, 0, 0]} args={[0.1, 1, 2]} />
            <ExtrudingWall scrollRef={scrollRef} position={[1, 0, 1]} args={[2, 1, 0.1]} />
        </group>
    )
}

function ExtrudingWall({ scrollRef, position, args }: { scrollRef: { current: number }, position: [number, number, number], args: [number, number, number] }) {
    const meshRef = useRef<THREE.Mesh>(null)

    useFrame(() => {
        if (!meshRef.current) return
        const s = scrollRef.current
        const scaleY = mapRange(s, 0.2, 0.6, 0.01, args[1])
        meshRef.current.scale.y = scaleY
    })

    return (
        <mesh ref={meshRef} position={position}>
            <boxGeometry args={args} />
            <meshBasicMaterial color="#00D4FF" wireframe />
        </mesh>
    )
}

function DataPoints({ scrollRef }: { scrollRef: { current: number } }) {
    const groupRef = useRef<THREE.Group>(null)

    useFrame(() => {
        if (!groupRef.current) return
        const s = scrollRef.current
        const yOffset = mapRange(s, 0.5, 0.6, -2, 0)

        // Scale jumps from 0 to 1 between 0.5 and 0.6, stays 1 until 0.8, then goes to 0 by 0.9
        let sc = 0
        if (s >= 0.5 && s < 0.6) sc = mapRange(s, 0.5, 0.6, 0, 1)
        else if (s >= 0.6 && s < 0.8) sc = 1
        else if (s >= 0.8 && s <= 0.9) sc = mapRange(s, 0.8, 0.9, 1, 0)
        else if (s > 0.9) sc = 0

        groupRef.current.position.y = yOffset
        groupRef.current.scale.setScalar(sc)
    })

    return (
        <group ref={groupRef}>
            <Text position={[-2.5, 1.2, 0]} color="#00D4FF" fontSize={0.2} anchorX="center" anchorY="bottom">
                W-240
            </Text>
            <Text position={[2.5, 1.2, 0]} color="#0EA5C4" fontSize={0.2} anchorX="center" anchorY="bottom">
                W-241 (D)
            </Text>
            <Text position={[0, 0.5, 0]} color="#00D4FF" fontSize={0.3} anchorX="center" anchorY="middle" rotation={[-Math.PI / 2, 0, 0]}>
                LIVING AREA 42.5m²
            </Text>
        </group>
    )
}

export default function ArchVision3D({ scrollYProgress }: { scrollYProgress: any }) {
    const scrollRef = useRef(0)

    useEffect(() => {
        return scrollYProgress.on("change", (latest: number) => {
            scrollRef.current = latest
        })
    }, [scrollYProgress])

    return (
        <div className="pointer-events-none fixed inset-0 z-0 h-screen w-screen">
            <Canvas camera={{ position: [0, 0, 8] as [number, number, number], fov: 50 }}>
                <ambientLight intensity={0.5} />
                <pointLight position={[10, 10, 10]} intensity={1} color="#00D4FF" />
                <BlueprintModel scrollRef={scrollRef} />
                <DataPoints scrollRef={scrollRef} />
            </Canvas>
        </div>
    )
}
