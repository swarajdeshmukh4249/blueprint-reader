import React, { useEffect, useRef, useState } from 'react'

interface DXFViewerProps {
  fileUrl: string
  onLayerToggle?: (layerName: string, visible: boolean) => void
}

export default function DXFViewer({ fileUrl, onLayerToggle }: DXFViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [layers, setLayers] = useState<Array<{name: string, visible: boolean}>>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  useEffect(() => {
    loadDXF()
  }, [fileUrl])
  
  const loadDXF = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // This would use a DXF parsing library like dxf-parser
      // For now, we'll simulate the loading
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Simulate layers
      setLayers([
        { name: 'Walls', visible: true },
        { name: 'Doors', visible: true },
        { name: 'Windows', visible: true },
        { name: 'Furniture', visible: false },
        { name: 'Dimensions', visible: true }
      ])
      
      // Draw on canvas
      drawDXF()
      
    } catch (err) {
      setError('Failed to load DXF file')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }
  
  const drawDXF = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    
    // Draw grid
    ctx.strokeStyle = '#e5e7eb'
    ctx.lineWidth = 0.5
    for (let i = 0; i < canvas.width; i += 50) {
      ctx.beginPath()
      ctx.moveTo(i, 0)
      ctx.lineTo(i, canvas.height)
      ctx.stroke()
    }
    for (let i = 0; i < canvas.height; i += 50) {
      ctx.beginPath()
      ctx.moveTo(0, i)
      ctx.lineTo(canvas.width, i)
      ctx.stroke()
    }
    
    // Draw sample DXF content (would be parsed from actual file)
    ctx.strokeStyle = '#374151'
    ctx.lineWidth = 2
    
    // Draw walls
    ctx.strokeRect(100, 100, 400, 300)
    ctx.strokeRect(120, 120, 150, 100)
    ctx.strokeRect(300, 120, 150, 100)
    ctx.strokeRect(120, 250, 330, 130)
    
    // Draw door
    ctx.strokeStyle = '#3b82f6'
    ctx.beginPath()
    ctx.moveTo(270, 220)
    ctx.lineTo(270, 250)
    ctx.stroke()
    
    ctx.beginPath()
    ctx.arc(270, 220, 30, 0, Math.PI / 2)
    ctx.stroke()
  }
  
  const toggleLayer = (layerName: string) => {
    const newLayers = layers.map(l => 
      l.name === layerName ? { ...l, visible: !l.visible } : l
    )
    setLayers(newLayers)
    const layer = layers.find(l => l.name === layerName)
    onLayerToggle?.(layerName, !layer?.visible)
    drawDXF()
  }
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading DXF file...</div>
      </div>
    )
  }
  
  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-red-500">{error}</div>
      </div>
    )
  }
  
  return (
    <div className="flex h-screen">
      {/* Layer Panel */}
      <div className="w-64 border-r bg-gray-50 p-4">
        <h3 className="font-semibold mb-4">Layers</h3>
        <div className="space-y-2">
          {layers.map(layer => (
            <div key={layer.name} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={layer.visible}
                onChange={() => toggleLayer(layer.name)}
                className="rounded"
              />
              <span className="text-sm">{layer.name}</span>
            </div>
          ))}
        </div>
      </div>
      
      {/* Canvas */}
      <div className="flex-1 bg-white">
        <canvas
          ref={canvasRef}
          width={800}
          height={600}
          className="border"
        />
      </div>
      
      {/* Controls */}
      <div className="w-48 border-l bg-gray-50 p-4">
        <h3 className="font-semibold mb-4">Controls</h3>
        <div className="space-y-2">
          <button className="w-full px-3 py-2 bg-gray-200 rounded text-sm">
            Zoom In
          </button>
          <button className="w-full px-3 py-2 bg-gray-200 rounded text-sm">
            Zoom Out
          </button>
          <button className="w-full px-3 py-2 bg-gray-200 rounded text-sm">
            Pan
          </button>
          <button className="w-full px-3 py-2 bg-gray-200 rounded text-sm">
            Reset View
          </button>
        </div>
      </div>
    </div>
  )
}
