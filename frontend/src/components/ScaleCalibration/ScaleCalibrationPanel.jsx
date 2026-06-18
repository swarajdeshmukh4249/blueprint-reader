import React, { useState } from 'react';
import { X } from 'lucide-react';
import { useScaleCalibration } from '../../hooks/useScaleCalibration';
import BlueprintCanvas from './BlueprintCanvas';
import CalibrationSidebar from './CalibrationSidebar';

const ScaleCalibrationPanel = ({ imageUrl, onClose, onScaleApplied }) => {
  const [zoom, setZoom] = useState(1);
  
  const {
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
  } = useScaleCalibration();

  const handleApply = async () => {
    const calibrationData = applyScale();
    if (calibrationData) {
      // Call the parent callback with the calibration data
      if (onScaleApplied) {
        await onScaleApplied(calibrationData);
      }
      // Close the panel
      if (onClose) {
        onClose();
      }
    }
  };

  const handleReset = () => {
    reset();
    setZoom(1);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-8">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-7xl h-[800px] flex flex-col overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700 bg-gray-800/50">
          <div>
            <h1 className="text-2xl font-bold text-white">Scale Calibration</h1>
            <p className="text-sm text-gray-400 mt-1">Calibrate the blueprint to real-world measurements</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-6 h-6 text-gray-400" />
          </button>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Canvas Area */}
          <div className="flex-1 p-6">
            <BlueprintCanvas
              imageUrl={imageUrl}
              pointA={pointA}
              pointB={pointB}
              onPointPlace={handleCanvasClick}
              zoom={zoom}
              onZoomChange={setZoom}
            />
          </div>

          {/* Sidebar */}
          <div className="p-6 bg-gray-800/30">
            <CalibrationSidebar
              pointA={pointA}
              pointB={pointB}
              pixelDistance={pixelDistance}
              scaleFactor={scaleFactor}
              confidence={confidence}
              unit={unit}
              realWorldDistance={realWorldDistance}
              onUnitChange={setUnit}
              onDistanceChange={setRealWorldDistance}
              onApply={handleApply}
              onReset={handleReset}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScaleCalibrationPanel;
