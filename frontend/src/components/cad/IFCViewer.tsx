import React, { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'

interface IFCViewerProps {
  fileUrl: string
  onElementSelect?: (elementId: string) => void
}

export default function IFCViewer({ fileUrl, onElementSelect }: IFCViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [floors, setFloors] = useState<Array<{name: string, visible: boolean}>>([])
  const [elements, setElements] = useState<Array<{id: string, type: string, visible: boolean}>>([])
  const [selectedFloor, setSelectedFloor] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  
  useEffect(() => {
    initThreeJS()
    loadIFC()
  }, [fileUrl])
  
  const initThreeJS = () => {
    const container = containerRef.current
    if (!container) return
    
    // Scene setup
    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0xf0f0f0)
    
    // Camera
    const camera = new THREE.PerspectiveCamera(
      75,
      container.clientWidth / container.clientHeight,
      0.1,
      1000
    )
    camera.position.set(10, 10, 10)
    camera.lookAt(0, 0, 0)
    
    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setSize(container.clientWidth, container.clientHeight)
    container.appendChild(renderer.domElement)
    
    // Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
    scene.add(ambientLight)
    
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
    directionalLight.position.set(10, 20, 10)
    scene.add(directionalLight)
    
    // Grid helper
    const gridHelper = new THREE.GridHelper(20, 20)
    scene.add(gridHelper)
    
    // Axes helper
    const axesHelper = new THREE.AxesHelper(5)
    scene.add(axesHelper)
    
    // Sample IFC geometry (would be parsed from actual IFC file)
    const geometry = new THREE.BoxGeometry(4, 3, 4)
    const material = new THREE.MeshLambertMaterial({ color: 0x3b82f6 })
    const cube = new THREE.Mesh(geometry, material)
    cube.position.y = 1.5
    scene.add(cube)
    
    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate)
      renderer.render(scene, camera)
    }
    animate()
    
    // Cleanup
    return () => {
      container.removeChild(renderer.domElement)
    }
  }
  
  const loadIFC = async () => {
    try {
      setLoading(true)
      
      // This would use an IFC parsing library like web-ifc
      // For now, we'll simulate the loading
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Simulate floors
      setFloors([
        { name: 'Ground Floor', visible: true },
        { name: 'First Floor', visible: true },
        { name: 'Second Floor', visible: false }
      ])
      
      // Simulate elements
      setElements([
        { id: '1', type: 'IfcWall', visible: true },
        { id: '2', type: 'IfcSlab', visible: true },
        { id: '3', type: 'IfcWindow', visible: true },
        { id: '4', type: 'IfcDoor', visible: true }
      ])
      
    } catch (err) {
      console.error('Failed to load IFC file', err)
    } finally {
      setLoading(false)
    }
  }
  
  const toggleFloor = (floorName: string) => {
    setFloors(floors.map(f => 
      f.name === floorName ? { ...f, visible: !f.visible } : f
    ))
  }
  
  const toggleElement = (elementId: string) => {
    setElements(elements.map(e => 
      e.id === elementId ? { ...e, visible: !e.visible } : e
    ))
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading IFC file...</div>
      </div>
    )
  }
  
  return (
    <div className="flex h-screen">
      {/* Floor Panel */}
      <div className="w-64 border-r bg-gray-50 p-4">
        <h3 className="font-semibold mb-4">Floors</h3>
        <div className="space-y-2">
          {floors.map(floor => (
            <div key={floor.name} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={floor.visible}
                onChange={() => toggleFloor(floor.name)}
                className="rounded"
              />
              <span className="text-sm">{floor.name}</span>
            </div>
          ))}
        </div>
        
        <h3 className="font-semibold mt-6 mb-4">Elements</h3>
        <div className="space-y-2">
          {elements.map(element => (
            <div key={element.id} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={element.visible}
                onChange={() => toggleElement(element.id)}
                className="rounded"
              />
              <span className="text-sm">{element.type}</span>
            </div>
          ))}
        </div>
      </div>
      
      {/* 3D Viewport */}
      <div className="flex-1" ref={containerRef} />
      
      {/* Controls */}
      <div className="w-48 border-l bg-gray-50 p-4">
        <h3 className="font-semibold mb-4">View Controls</h3>
        <div className="space-y-2">
          <button className="w-full px-3 py-2 bg-gray-200 rounded text-sm">
            Rotate
          </button>
          <button className="w-full px-3 py-2 bg-gray-200 rounded text-sm">
            Pan
          </button>
          <button className="w-full px-3 py-2 bg-gray-200 rounded text-sm">
            Zoom
          </button>
          <button className="w-full px-3 py-2 bg-gray-200 rounded text-sm">
            Reset View
          </button>
        </div>
        
        <h3 className="font-semibold mt-6 mb-4">Display</h3>
        <div className="space-y-2">
          <button className="w-full px-3 py-2 bg-blue-500 text-white rounded text-sm">
            Wireframe
          </button>
          <button className="w-full px-3 py-2 bg-gray-200 rounded text-sm">
            Solid
          </button>
          <button className="w-full px-3 py-2 bg-gray-200 rounded text-sm">
            Transparent
          </button>
        </div>
      </div>
    </div>
  )
}
