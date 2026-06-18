import { useState, useCallback } from 'react';

export const useScaleCalibration = () => {
  const [pointA, setPointA] = useState(null);
  const [pointB, setPointB] = useState(null);
  const [realWorldDistance, setRealWorldDistance] = useState('');
  const [unit, setUnit] = useState('meters');
  const [scaleFactor, setScaleFactor] = useState(null);
  const [confidence, setConfidence] = useState(null);

  // Calculate pixel distance between two points
  const pixelDistance = pointA && pointB
    ? Math.sqrt(Math.pow(pointB.x - pointA.x, 2) + Math.pow(pointB.y - pointA.y, 2))
    : 0;

  // Calculate scale factor
  const calculateScaleFactor = useCallback(() => {
    if (pixelDistance > 0 && realWorldDistance) {
      const distance = parseFloat(realWorldDistance);
      if (!isNaN(distance) && distance > 0) {
        const factor = distance / pixelDistance;
        setScaleFactor(factor.toFixed(5));
        return factor.toFixed(5);
      }
    }
    return null;
  }, [pixelDistance, realWorldDistance]);

  // Calculate confidence based on pixel distance
  const calculateConfidence = useCallback(() => {
    if (pixelDistance > 500) {
      setConfidence('High');
    } else if (pixelDistance > 200) {
      setConfidence('Medium');
    } else if (pixelDistance > 0) {
      setConfidence('Low');
    } else {
      setConfidence(null);
    }
  }, [pixelDistance]);

  // Handle canvas click to place points
  const handleCanvasClick = useCallback((x, y) => {
    if (!pointA) {
      setPointA({ x, y });
    } else if (!pointB) {
      setPointB({ x, y });
      calculateConfidence();
    }
  }, [pointA, pointB, calculateConfidence]);

  // Reset calibration
  const reset = useCallback(() => {
    setPointA(null);
    setPointB(null);
    setRealWorldDistance('');
    setScaleFactor(null);
    setConfidence(null);
  }, []);

  // Apply scale and return calibration data
  const applyScale = useCallback(() => {
    const calculatedScale = calculateScaleFactor();
    if (calculatedScale) {
      return {
        point_a: pointA,
        point_b: pointB,
        real_world_distance: parseFloat(realWorldDistance),
        unit,
        pixel_distance: pixelDistance.toFixed(2),
        scale_factor: parseFloat(calculatedScale),
        calibrated_at: new Date().toISOString()
      };
    }
    return null;
  }, [pointA, pointB, realWorldDistance, unit, pixelDistance, calculateScaleFactor]);

  return {
    pointA,
    pointB,
    pixelDistance,
    scaleFactor,
    confidence,
    realWorldDistance,
    unit,
    handleCanvasClick,
    setRealWorldDistance,
    setUnit,
    calculateScaleFactor,
    reset,
    applyScale
  };
};
