import React, { useEffect, useState } from 'react'

interface BOQItem {
  category: string
  description: string
  unit: string
  quantity: number
  rate: number
  amount: number
}

interface BOQResult {
  items: BOQItem[]
  subtotal: number
  gst_amount: number
  gst_rate: number
  grand_total: number
}

interface BOQPreviewProps {
  analysisVersionId: string
  rooms: any[]
}

export default function BOQPreview({ analysisVersionId, rooms }: BOQPreviewProps) {
  const [boq, setBOQ] = useState<BOQResult | null>(null)
  const [loading, setLoading] = useState(false)
  
  useEffect(() => {
    const debouncedUpdate = debounce(async () => {
      setLoading(true)
      try {
        // This would call the API to calculate BOQ preview
        // For now, we'll simulate it
        const totalArea = rooms.reduce((sum, r) => sum + (r.area_sqft || 0), 0)
        
        // Simple BOQ calculation
        const items: BOQItem[] = [
          {
            category: 'Construction',
            description: 'Basic construction work',
            unit: 'sq ft',
            quantity: totalArea,
            rate: 150,
            amount: totalArea * 150
          },
          {
            category: 'Finishing',
            description: 'Internal finishing',
            unit: 'sq ft',
            quantity: totalArea,
            rate: 75,
            amount: totalArea * 75
          }
        ]
        
        const subtotal = items.reduce((sum, item) => sum + item.amount, 0)
        const gst_rate = 0.18
        const gst_amount = subtotal * gst_rate
        
        setBOQ({
          items,
          subtotal,
          gst_amount,
          gst_rate,
          grand_total: subtotal + gst_amount
        })
      } catch (error) {
        console.error('Failed to calculate BOQ preview', error)
      } finally {
        setLoading(false)
      }
    }, 500)
    
    debouncedUpdate()
  }, [rooms, analysisVersionId])
  
  if (loading) {
    return <div className="p-4 text-gray-500">Calculating BOQ...</div>
  }
  
  if (!boq) {
    return null
  }
  
  return (
    <div className="space-y-4">
      <h3 className="font-semibold">BOQ Preview</h3>
      
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-gray-500">Subtotal:</span>
          <span className="ml-2 font-medium">₹{boq.subtotal.toFixed(2)}</span>
        </div>
        <div>
          <span className="text-gray-500">GST (18%):</span>
          <span className="ml-2 font-medium">₹{boq.gst_amount.toFixed(2)}</span>
        </div>
        <div className="col-span-2">
          <span className="text-gray-500">Grand Total:</span>
          <span className="ml-2 font-bold text-lg">₹{boq.grand_total.toFixed(2)}</span>
        </div>
      </div>
      
      <div className="border-t pt-4">
        <h4 className="text-sm font-medium mb-2">Impact Analysis</h4>
        <div className="text-sm text-gray-600">
          Total Area: {rooms.reduce((sum, r) => sum + (r.area_sqft || 0), 0).toFixed(2)} sq ft
        </div>
      </div>
    </div>
  )
}

function debounce(func: Function, wait: number) {
  let timeout: NodeJS.Timeout
  return function executedFunction(...args: any[]) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}
