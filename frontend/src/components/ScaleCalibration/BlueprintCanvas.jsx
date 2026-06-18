import React, { useRef, useState, useEffect } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Move } from 'lucide-react';

const BlueprintCanvas = ({ imageUrl, pointA, pointB, onPointPlace, zoom = 1, onZoomChange }) => {
  const canvasRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageDimensions, setImageDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const img = new Image();
    img.onload = () => {
      setImageDimensions({ width: img.width, height: img.height });
      setImageLoaded(true);
    };
    img.src = imageUrl;
  }, [imageUrl]);

  const handleCanvasClick = (e) => {
    if (isDragging) return;
    
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - pan.x) / zoom;
    const y = (e.clientY - rect.top - pan.y) / zoom;

    onPointPlace(x, y);
  };

  const handleMouseDown = (e) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleZoomIn = () => {
    onZoomChange(Math.min(zoom * 1.2, 5));
  };

  const handleZoomOut = () => {
    onZoomChange(Math.max(zoom / 1.2, 0.2));
  };

  const handleReset = () => {
    onZoomChange(1);
    setPan({ x: 0, y: 0 });
  };

  return (
    <div className="relative bg-gray-900 rounded-lg overflow-hidden border border-gray-700">
      {/* Toolbar */}
      <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-10 flex items-center gap-2 bg-gray-800/90 backdrop-blur-sm rounded-lg px-4 py-2 border border-gray-700">
        <button
          onClick={handleZoomOut}
          className="p-2 hover:bg-gray-700 rounded-md transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="w-4 h-4 text-gray-300" />
        </button>
        <span className="text-sm text-gray-300 min-w-[60px] text-center">
          {Math.round(zoom * 100)}%
        </span>
        <button
          onClick={handleZoomIn}
          className="p-2 hover:bg-gray-700 rounded-md transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="w-4 h-4 text-gray-300" />
        </button>
        <div className="w-px h-6 bg-gray-600 mx-2" />
        <button
          onClick={handleReset}
          className="p-2 hover:bg-gray-700 rounded-md transition-colors"
          title="Reset View"
        >
          <RotateCcw className="w-4 h-4 text-gray-300" />
        </button>
        <div className="w-px h-6 bg-gray-600 mx-2" />
        <Move className="w-4 h-4 text-gray-400" />
      </div>

      {/* Canvas */}
      <div
        ref={canvasRef}
        className="w-full h-[600px] cursor-crosshair relative"
        onClick={handleCanvasClick}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{ cursor: isDragging ? 'grabbing' : 'crosshair' }}
      >
        {imageLoaded && (
          <div
            style={{
              transform: `scale(${zoom}) translate(${pan.x / zoom}px, ${pan.y / zoom}px)`,
              transformOrigin: 'top left',
              transition: isDragging ? 'none' : 'transform 0.1s ease-out'
            }}
          >
            <img
              src={imageUrl}
              alt="Blueprint"
              className="max-w-none"
              style={{ width: imageDimensions.width, height: imageDimensions.height }}
            />
            
            {/* SVG Overlay */}
            <svg
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: imageDimensions.width,
                height: imageDimensions.height,
                pointerEvents: 'none'
              }}
            >
              {/* Dashed line between points */}
              {pointA && pointB && (
                <line
                  x1={pointA.x}
                  y1={pointA.y}
                  x2={pointB.x}
                  y2={pointB.y}
                  stroke="#2563EB"
                  strokeWidth={3}
                  strokeDasharray="8 4"
                />
              )}

              {/* Point A marker */}
              {pointA && (
                <>
                  <circle
                    cx={pointA.x}
                    cy={pointA.y}
                    r={10}
                    fill="#2563EB"
                    stroke="#ffffff"
                    strokeWidth={3}
                    filter="drop-shadow(0 2px 4px rgba(0,0,0,0.3))"
                  />
                  <text
                    x={pointA.x + 15}
                    y={pointA.y - 15}
                    fill="#ffffff"
                    fontSize={14}
                    fontWeight="bold"
                    stroke="#000000"
                    strokeWidth={3}
                    paintOrder="stroke"
                  >
                    Point A
                  </text>
                </>
              )}

              {/* Point B marker */}
              {pointB && (
                <>
                  <circle
                    cx={pointB.x}
                    cy={pointB.y}
                    r={10}
                    fill="#2563EB"
                    stroke="#ffffff"
                    strokeWidth={3}
                    filter="drop-shadow(0 2px 4px rgba(0,0,0,0.3))"
                  />
                  <text
                    x={pointB.x + 15}
                    y={pointB.y - 15}
                    fill="#ffffff"
                    fontSize={14}
                    fontWeight="bold"
                    stroke="#000000"
                    strokeWidth={3}
                    paintOrder="stroke"
                  >
                    Point B
                  </text>
                </>
              )}
            </svg>
          </div>
        )}
        
        {!imageLoaded && (
          <div className="flex items-center justify-center h-full text-gray-500">
            Loading blueprint...
          </div>
        )}
      </div>
    </div>
  );
};

export default BlueprintCanvas;
