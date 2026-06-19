import React, { useRef, useState } from 'react';
import { CalibrationManager } from '../calibration/CalibrationManager';

export default function BlueprintCanvas({
  imageUrl,
  width,
  height,
}) {
  const canvasRef = useRef(null);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom] = useState(1);
  const [isDragging, setIsDragging] = useState(false);

  const handleClick = (e) => {
    const calib = CalibrationManager.getState();

    const rect = canvasRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left - pan.x) / zoom;
    const y = (e.clientY - rect.top - pan.y) / zoom;

    if (calib.scaleMode) {
      CalibrationManager.addPoint({
        x,
        y,
        space: 'image',
      });
      return;
    }

    // normal image click behavior (if needed)
  };

  return (
    <div
      ref={canvasRef}
      style={{ width, height, position: 'relative', overflow: 'hidden' }}
      onClick={handleClick}
    >
      <img
        src={imageUrl}
        style={{
          transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
          transformOrigin: 'top left',
          width: '100%',
          height: '100%',
        }}
      />
    </div>
  );
}