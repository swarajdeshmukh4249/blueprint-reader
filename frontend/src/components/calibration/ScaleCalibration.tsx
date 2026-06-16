import React, { useState, useRef } from 'react'
import { Ruler, X } from 'lucide-react'

interface ScaleCalibrationProps {
  onScaleCalibrated: (scale: number, unit: string) => void
  imageSrc?: string
}

export default function ScaleCalibration({ onScaleCalibrated, imageSrc }: ScaleCalibrationProps) {
  const [points, setPoints] = useState<Array<{x: number, y: number}>>([])
  const [knownDistance, setKnownDistance] = useState('10.000')
  const [unit, setUnit] = useState('m')
  const [pixelDistance, setPixelDistance] = useState<number | null>(null)
  const [scaleFactor, setScaleFactor] = useState<number | null>(null)
  const [confidence, setConfidence] = useState<string>('')
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const imageRef = useRef<HTMLImageElement>(null)
  
  // Load image when src changes
  React.useEffect(() => {
    if (imageSrc && canvasRef.current) {
      const canvas = canvasRef.current
      const ctx = canvas.getContext('2d')
      const img = new Image()
      img.onload = () => {
        imageRef.current = img
        // Set canvas size to match image
        canvas.width = img.width
        canvas.height = img.height
        // Draw image
        ctx?.drawImage(img, 0, 0)
        // Redraw points if they exist
        if (points.length > 0) {
          redrawCanvas()
        }
      }
      img.src = imageSrc
    }
  }, [imageSrc])
  
  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (points.length >= 2) return
    
    const canvas = canvasRef.current
    if (!canvas) return
    
    const rect = canvas.getBoundingClientRect()
    const scaleX = canvas.width / rect.width
    const scaleY = canvas.height / rect.height
    const x = (e.clientX - rect.left) * scaleX
    const y = (e.clientY - rect.top) * scaleY
    
    setPoints([...points, { x, y }])
    redrawCanvas()
    
    // Calculate pixel distance if we have 2 points
    if (points.length === 1) {
      const dx = x - points[0].x
      const dy = y - points[0].y
      const distance = Math.sqrt(dx * dx + dy * dy)
      setPixelDistance(distance)
      
      // Calculate confidence based on pixel distance
      if (distance > 500) {
        setConfidence('High')
      } else if (distance > 200) {
        setConfidence('Medium')
      } else {
        setConfidence('Low')
      }
    }
  }
  
  const redrawCanvas = () => {
    const canvas = canvasRef.current
    if (!canvas) return
    
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    
    // Clear and redraw image
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    if (imageRef.current) {
      ctx.drawImage(imageRef.current, 0, 0)
    }
    
    // Draw dashed line between points
    if (points.length === 2) {
      ctx.beginPath()
      ctx.setLineDash([10, 10])
      ctx.strokeStyle = '#3b82f6'
      ctx.lineWidth = 3
      ctx.moveTo(points[0].x, points[0].y)
      ctx.lineTo(points[1].x, points[1].y)
      ctx.stroke()
      ctx.setLineDash([])
    }
    
    // Draw points
    points.forEach((point, index) => {
      ctx.beginPath()
      ctx.arc(point.x, point.y, 8, 0, 2 * Math.PI)
      ctx.fillStyle = index === 0 ? '#22c55e' : '#3b82f6'
      ctx.fill()
      ctx.strokeStyle = '#ffffff'
      ctx.lineWidth = 3
      ctx.stroke()
      
      // Draw label
      ctx.font = 'bold 16px Arial'
      ctx.fillStyle = '#1e293b'
      ctx.fillText(index === 0 ? 'A' : 'B', point.x + 15, point.y - 15)
    })
  }
  
  const calculateScale = () => {
    if (points.length !== 2 || !knownDistance || !pixelDistance) return
    
    const distance = parseFloat(knownDistance)
    const calculatedScale = distance / pixelDistance // m/px format
    
    setScaleFactor(calculatedScale)
    onScaleCalibrated(calculatedScale, unit)
  }
  
  const reset = () => {
    setPoints([])
    setKnownDistance('10.000')
    setPixelDistance(null)
    setScaleFactor(null)
    setConfidence('')
    redrawCanvas()
  }
  
  const removePoint = (index: number) => {
    const newPoints = points.filter((_, i) => i !== index)
    setPoints(newPoints)
    setPixelDistance(null)
    setScaleFactor(null)
    setConfidence('')
    redrawCanvas()
  }
  
  return (
    <div className="flex flex-col h-full">
      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <h3 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
          <Ruler className="w-5 h-5" />
          Scale Calibration
        </h3>
        <ol className="text-sm text-blue-700 space-y-1 list-decimal list-inside">
          <li>Select two reference points on the drawing</li>
          <li>Enter the real-world distance between them</li>
        </ol>
      </div>
      
      {/* Canvas */}
      <div className="flex-1 border border-gray-300 rounded-lg overflow-hidden bg-gray-50 mb-4">
        <canvas
          ref={canvasRef}
          onClick={handleCanvasClick}
          className="w-full h-full cursor-crosshair"
          style={{ maxHeight: '500px', objectFit: 'contain' }}
        />
      </div>
      
      {/* Calibration Panel */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-6">
        {/* Real-world Distance Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Real-world Distance
          </label>
          <div className="flex gap-2">
            <input
              type="number"
              step="0.001"
              value={knownDistance}
              onChange={(e) => setKnownDistance(e.target.value)}
              className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter distance"
            />
            <select
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
              className="border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="m">Meters</option>
              <option value="ft">Feet</option>
              <option value="mm">Millimeters</option>
              <option value="in">Inches</option>
            </select>
          </div>
        </div>
        
        {/* Pixel Distance Display */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Pixel Distance
          </label>
          <div className="bg-gray-50 border border-gray-200 rounded-lg px-4 py-3">
            <span className="text-lg font-semibold text-gray-900">
              {pixelDistance ? pixelDistance.toFixed(2) : '—'} px
            </span>
          </div>
        </div>
        
        {/* Scale Factor Display */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Scale Factor
          </label>
          <div className="bg-gray-50 border border-gray-200 rounded-lg px-4 py-3">
            <span className="text-lg font-semibold text-gray-900">
              {scaleFactor ? scaleFactor.toFixed(5) : '—'} {unit}/px
            </span>
          </div>
        </div>
        
        {/* Confidence Display */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Confidence
          </label>
          <div className={`border rounded-lg px-4 py-3 ${
            confidence === 'High' ? 'bg-green-50 border-green-200 text-green-800' :
            confidence === 'Medium' ? 'bg-yellow-50 border-yellow-200 text-yellow-800' :
            confidence === 'Low' ? 'bg-red-50 border-red-200 text-red-800' :
            'bg-gray-50 border-gray-200 text-gray-800'
          }`}>
            <span className="font-semibold">
              {confidence ? `${confidence} (${pixelDistance?.toFixed(2)} px)` : '—'}
            </span>
          </div>
        </div>
        
        {/* Selected Points */}
        {points.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Selected Points
            </label>
            <div className="space-y-2">
              {points.map((point, index) => (
                <div key={index} className="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-lg px-4 py-2">
                  <span className="font-medium">
                    Point {index === 0 ? 'A' : 'B'}: ({point.x.toFixed(0)}, {point.y.toFixed(0)})
                  </span>
                  <button
                    onClick={() => removePoint(index)}
                    className="text-red-500 hover:text-red-700"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {/* Action Buttons */}
        <div className="flex gap-3">
          <button
            onClick={calculateScale}
            disabled={points.length !== 2 || !knownDistance}
            className="flex-1 bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            Apply Scale
          </button>
          <button
            onClick={reset}
            className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 font-medium"
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  )
}
