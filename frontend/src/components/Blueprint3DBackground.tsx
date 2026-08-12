import { useEffect, useRef } from 'react'
import * as THREE from 'three'

export default function Blueprint3DBackground() {
  const hostRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const host = hostRef.current
    if (!host) return

    const scene = new THREE.Scene()

    const camera = new THREE.PerspectiveCamera(
      45,
      1,
      0.1,
      100
    )

    camera.position.set(0, 0, 8)

    const renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true,
    })

    renderer.setPixelRatio(
      Math.min(window.devicePixelRatio, 1.5)
    )

    renderer.setClearColor(0x000000, 0)

    host.appendChild(renderer.domElement)

    const group = new THREE.Group()
    scene.add(group)

    // -----------------------------
    // BLUEPRINT MATERIAL
    // -----------------------------

    const material = new THREE.LineBasicMaterial({
      color: 0x31a8d8,
      transparent: true,
      opacity: 0.35,
    })

    // -----------------------------
    // 3D OBJECTS
    // -----------------------------

    const box = new THREE.LineSegments(
      new THREE.EdgesGeometry(
        new THREE.BoxGeometry(2.3, 1.45, 1.2)
      ),
      material.clone()
    )

    box.position.set(-2.5, 1.1, -1)
    box.rotation.set(0.2, 0.5, 0.1)

    group.add(box)

    const octahedron = new THREE.LineSegments(
      new THREE.EdgesGeometry(
        new THREE.OctahedronGeometry(1.1, 1)
      ),
      material.clone()
    )

    octahedron.position.set(2.3, -0.8, -1.5)
    octahedron.rotation.set(0.4, 0.8, 0.2)

    group.add(octahedron)

    const torus = new THREE.LineSegments(
      new THREE.EdgesGeometry(
        new THREE.TorusGeometry(
          1.15,
          0.035,
          8,
          48
        )
      ),
      material.clone()
    )

    torus.position.set(0.5, 2.1, -2)
    torus.rotation.set(0.5, 0.6, 0.2)

    group.add(torus)

    // -----------------------------
    // BLUEPRINT GRID
    // -----------------------------

    const grid = new THREE.GridHelper(
      18,
      18,
      0x31a8d8,
      0x31a8d8
    )

    const gridMaterial = Array.isArray(grid.material)
      ? grid.material[0]
      : grid.material

    gridMaterial.transparent = true
    gridMaterial.opacity = 0.08

    grid.rotation.x = Math.PI / 2.55
    grid.position.set(0, -2.3, -2)

    group.add(grid)

    // -----------------------------
    // MOUSE PARALLAX
    // -----------------------------

    const pointer = {
      x: 0,
      y: 0,
    }

    const handlePointerMove = (event: PointerEvent) => {
      pointer.x =
        (event.clientX / window.innerWidth - 0.5) * 2

      pointer.y =
        (event.clientY / window.innerHeight - 0.5) * 2
    }

    // -----------------------------
    // RESIZE
    // -----------------------------

    const resize = () => {
      const {
        width,
        height,
      } = host.getBoundingClientRect()

      renderer.setSize(width, height, false)

      camera.aspect =
        width / Math.max(height, 1)

      camera.updateProjectionMatrix()
    }

    // -----------------------------
    // ANIMATION
    // -----------------------------

    let frame = 0

    const animate = (time: number) => {

      group.rotation.y += 0.0007

      group.rotation.x = THREE.MathUtils.lerp(
        group.rotation.x,
        pointer.y * 0.06,
        0.025
      )

      group.rotation.z = THREE.MathUtils.lerp(
        group.rotation.z,
        pointer.x * -0.04,
        0.025
      )

      box.rotation.y += 0.0012

      octahedron.rotation.x -= 0.001

      torus.rotation.z += 0.001

      torus.position.y =
        2.1 +
        Math.sin(time * 0.00035) * 0.12

      renderer.render(scene, camera)

      frame = requestAnimationFrame(animate)
    }

    resize()

    window.addEventListener(
      'resize',
      resize
    )

    window.addEventListener(
      'pointermove',
      handlePointerMove,
      { passive: true }
    )

    frame = requestAnimationFrame(animate)

    return () => {
      cancelAnimationFrame(frame)

      window.removeEventListener(
        'resize',
        resize
      )

      window.removeEventListener(
        'pointermove',
        handlePointerMove
      )

      box.geometry.dispose()
      box.material.dispose()

      octahedron.geometry.dispose()
      octahedron.material.dispose()

      torus.geometry.dispose()
      torus.material.dispose()

      grid.geometry.dispose()
      gridMaterial.dispose()

      renderer.dispose()

      if (renderer.domElement.parentNode) {
        renderer.domElement.parentNode.removeChild(
          renderer.domElement
        )
      }
    }
  }, [])

  return (
    <div
      ref={hostRef}
      aria-hidden="true"
      className="
        pointer-events-none
        fixed
        inset-0
        z-0
        overflow-hidden
      "
    />
  )
}