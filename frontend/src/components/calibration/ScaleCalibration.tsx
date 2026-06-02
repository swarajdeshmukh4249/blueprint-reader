import React, { useState, useRef } from 'react'

interface ScaleCalibrationProps {
  onScaleCalibrated: (scale: number, unit: string) => void
}

export default function ScaleCalibration({ onScaleCalibrated }: ScaleCalibrationProps) {
  const [points, setPoints] = useState<Array<{x: number, y: number}>>([])
  const [knownDistance, setKnownDistance] = useState('')
  const [unit, setUnit] = useState('ft')
  const [scale, setScale] = useState<number | null>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (points.length >= 2) return
    
    const canvas = canvasRef.current
    if (!canvas) return
    
    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top
    
    setPoints([...points, { x, y }])
    
    // Draw point on canvas
    const ctx = canvas.getContext('2d')
    if (ctx) {
      ctx.beginPath()
      ctx.arc(x, y, 5, 0, 2 * Math.PI)
      ctx.fillStyle = points.length === 0 ? '#22c55e' : '#3b82f6'
      ctx.fill()
      ctx.stroke()
    }
  }
  
  const calculateScale = () => {
    if (points.length !== 2 || !knownDistance) return
    
    const dx = points[1].x - points[0].x
    const dy = points[1].y - points[0].y
    const pixelDistance = Math.sqrt(dx * dx + dy * dy)
    
    const distance = parseFloat(knownDistance)
    const calculatedScale = pixelDistance / distance
    
    setScale(calculatedScale)
    onScaleCalibrated(calculatedScale, unit)
  }
  
  const reset = () => {
    setPoints([])
    setKnownDistance('')
    setScale(null)
    
    // Clear canvas
    const canvas = canvasRef.current
    if (canvas) {
      const ctx = canvas.getContext('2d')
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height)
      }
    }
  }
  
  const commonReferences = [
    { name: 'Standard Door', distance: 3, unit: 'ft' },
    { name: 'Standard Window', distance: 4, unit: 'ft' },
    { name: 'Stair Width', distance: 4, unit: 'ft' },
    { name: 'A4 Paper Width', distance: 297, unit: 'mm' }
  ]
  
  return (
    <div className="space-y-4">
      <div className="bg-blue-50 border border-blue-200 rounded p-4">
        <h3 className="font-semibold text-blue-900 mb-2">Scale Calibration</h3>
        <p className="text-sm text-blue-700">
          Click two points on the blueprint, then enter the known distance between them.
        </p>
      </div>
      
      <div className="border rounded p-4">
        <canvas
          ref={canvasRef}
          width={800}
          height={600}
          onClick={handleCanvasClick}
          className="border bg-gray-50 cursor-crosshair"
        />
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1">Known Distance</label>
          <input
            type="number"
            value={knownDistance}
            onChange={(e) => setKnownDistance(e.target.value)}
            className="w-full border rounded px-3 py-2"
            placeholder="Enter distance"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Unit</label>
          <select
            value={unit}
            onChange={(e) => setUnit(e.target.value)}
            className="w-full border rounded px-3 py-2"
          >
            <option value="ft">Feet (ft)</option>
            <option value="m">Meters (m)</option>
            <option value="mm">Millimeters (mm)</option>
            <option value="in">Inches (in)</option>
          </select>
        </div>
      </div>
      
      <div>
        <label className="block text-sm font-medium mb-2">Common References</label>
        <div className="flex flex-wrap gap-2">
          {commonReferences.map(ref => (
            <button
              key={ref.name}
              onClick={() => {
                setKnownDistance(ref.distance.toString())
                setUnit(ref.unit)
              }}
              className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
            >
              {ref.name} ({ref.distance} {ref.unit})
            </button>
          ))}
        </div>
      </div>
      
      <div className="flex gap-2">
        <button
          onClick={calculateScale}
          disabled={points.length !== 2 || !knownDistance}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
        >
          Calculate Scale
        </button>
        <button
          onClick={reset}
          className="px-4 py-2 border rounded hover:bg-gray-50"
        >
          Reset
        </button>
      </div>
      
      {scale && (
        <div className="bg-green-50 border border-green-200 rounded p-4">
          <p className="text-green-900">
            <strong>Scale calculated:</strong> {scale.toFixed(2)} pixels per {unit}
          </p>
          <p className="text-sm text-green-700 mt-1">
            All measurements will be recalculated using this scale.
          </p>
        </div>
      )}
    </div>
  )
}
