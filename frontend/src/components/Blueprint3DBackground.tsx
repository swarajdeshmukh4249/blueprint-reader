import { useEffect, useRef } from 'react'
import * as THREE from 'three'

export default function Blueprint3DBackground() {
  const hostRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const host = hostRef.current
    if (!host) return

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100)
    camera.position.set(0, 0, 8)

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5))
    renderer.setClearColor(0x000000, 0)
    host.appendChild(renderer.domElement)

    const group = new THREE.Group()
    scene.add(group)

    const material = new THREE.LineBasicMaterial({
      color: 0x31a8d8,
      transparent: true,
      opacity: 0.22,
    })

    const wireframes = [
      new THREE.EdgesGeometry(new THREE.BoxGeometry(2.3, 1.45, 1.2)),
      new THREE.EdgesGeometry(new THREE.OctahedronGeometry(1.1, 1)),
      new THREE.EdgesGeometry(new THREE.TorusGeometry(1.15, 0.035, 8, 48)),
    ].map((geometry, index) => {
      const mesh = new THREE.LineSegments(geometry, material.clone())
      mesh.material.opacity = index === 2 ? 0.16 : 0.2
      mesh.position.set(index === 0 ? -2.5 : index === 1 ? 2.3 : 0.5, index === 0 ? 1.1 : index === 1 ? -0.8 : 2.1, index * -0.6)
      mesh.rotation.set(index * 0.45, index * 0.65, index * 0.25)
      mesh.scale.setScalar(index === 2 ? 0.9 : 1)
      group.add(mesh)
      return mesh
    })

    const grid = new THREE.GridHelper(18, 18, 0x31a8d8, 0x31a8d8)
    const gridMaterial = Array.isArray(grid.material) ? grid.material[0] : grid.material
    gridMaterial.transparent = true
    gridMaterial.opacity = 0.06
    grid.rotation.x = Math.PI / 2.55
    grid.position.set(0, -2.3, -2)
    group.add(grid)

    const pointer = { x: 0, y: 0 }
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)')
    let frame = 0

    const resize = () => {
      const { width, height } = host.getBoundingClientRect()
      renderer.setSize(width, height, false)
      camera.aspect = width / Math.max(height, 1)
      camera.updateProjectionMatrix()
    }

    const handlePointerMove = (event: PointerEvent) => {
      pointer.x = (event.clientX / window.innerWidth - 0.5) * 2
      pointer.y = (event.clientY / window.innerHeight - 0.5) * 2
    }

    const animate = (time: number) => {
      if (!reducedMotion.matches) {
        group.rotation.y += 0.0008
        group.rotation.x = THREE.MathUtils.lerp(group.rotation.x, pointer.y * 0.08, 0.025)
        group.rotation.z = THREE.MathUtils.lerp(group.rotation.z, pointer.x * -0.05, 0.025)
        wireframes[0].rotation.y += 0.0015
        wireframes[1].rotation.x -= 0.0012
        wireframes[2].rotation.z += 0.001
        wireframes[2].position.y = 2.1 + Math.sin(time * 0.00035) * 0.12
      }
      renderer.render(scene, camera)
      frame = requestAnimationFrame(animate)
    }

    resize()
    window.addEventListener('resize', resize)
    window.addEventListener('pointermove', handlePointerMove, { passive: true })
    frame = requestAnimationFrame(animate)

    return () => {
      cancelAnimationFrame(frame)
      window.removeEventListener('resize', resize)
      window.removeEventListener('pointermove', handlePointerMove)
      wireframes.forEach((mesh) => {
        mesh.geometry.dispose()
        mesh.material.dispose()
      })
      grid.geometry.dispose()
      gridMaterial.dispose()
      renderer.dispose()
      renderer.domElement.remove()
    }
  }, [])

  return <div ref={hostRef} aria-hidden="true" className="pointer-events-none fixed inset-0 z-0 overflow-hidden opacity-90" />
}
