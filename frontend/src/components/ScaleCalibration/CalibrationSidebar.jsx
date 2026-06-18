import React from 'react';
import { Ruler, CheckCircle, AlertCircle, XCircle } from 'lucide-react';

const CalibrationSidebar = ({
  pointA,
  pointB,
  pixelDistance,
  scaleFactor,
  confidence,
  unit,
  realWorldDistance,
  onUnitChange,
  onDistanceChange,
  onApply,
  onReset
}) => {
  const getConfidenceColor = () => {
    switch (confidence) {
      case 'High':
        return 'bg-green-500';
      case 'Medium':
        return 'bg-yellow-500';
      case 'Low':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getConfidenceIcon = () => {
    switch (confidence) {
      case 'High':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'Medium':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'Low':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return null;
    }
  };

  const canApply = pointA && pointB && realWorldDistance && parseFloat(realWorldDistance) > 0;

  return (
    <div className="w-96 bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-blue-500/20 rounded-lg">
          <Ruler className="w-6 h-6 text-blue-400" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-white">Scale Calibration</h2>
          <p className="text-sm text-gray-400">Set real-world measurements</p>
        </div>
      </div>

      {/* Instructions */}
      <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-300 mb-3">Instructions</h3>
        <ol className="space-y-2 text-sm text-gray-400">
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 w-5 h-5 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center text-xs font-medium">
              1
            </span>
            <span>Select two reference points on the drawing</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="flex-shrink-0 w-5 h-5 bg-blue-500/20 text-blue-400 rounded-full flex items-center justify-center text-xs font-medium">
              2
            </span>
            <span>Enter the real-world distance between them</span>
          </li>
        </ol>
      </div>

      {/* Real-world Distance Input */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Real-world Distance
        </label>
        <div className="flex gap-2">
          <input
            type="number"
            step="0.001"
            value={realWorldDistance}
            onChange={(e) => onDistanceChange(e.target.value)}
            className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-white placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
            placeholder="Enter distance"
          />
          <select
            value={unit}
            onChange={(e) => onUnitChange(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
          >
            <option value="meters">Meters</option>
            <option value="feet">Feet</option>
            <option value="inches">Inches</option>
            <option value="cm">Centimeters</option>
          </select>
        </div>
      </div>

      {/* Computed Values */}
      <div className="space-y-4">
        {/* Pixel Distance */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Pixel Distance
          </label>
          <div className="bg-gray-900/50 border border-gray-700 rounded-lg px-4 py-3">
            <span className="text-lg font-semibold text-white">
              {pixelDistance > 0 ? pixelDistance.toFixed(2) : '—'} px
            </span>
          </div>
        </div>

        {/* Scale Factor */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Scale Factor
          </label>
          <div className="bg-gray-900/50 border border-gray-700 rounded-lg px-4 py-3">
            <span className="text-lg font-semibold text-white">
              {scaleFactor ? `${scaleFactor} ${unit}/px` : '—'}
            </span>
          </div>
        </div>

        {/* Confidence */}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Confidence
          </label>
          <div className="bg-gray-900/50 border border-gray-700 rounded-lg px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              {confidence && (
                <>
                  <div className={`w-3 h-3 rounded-full ${getConfidenceColor()}`} />
                  <span className="font-semibold text-white">{confidence}</span>
                </>
              )}
              {!confidence && <span className="text-gray-500">—</span>}
            </div>
            {getConfidenceIcon()}
          </div>
          {confidence === 'Low' && (
            <p className="text-xs text-yellow-500 mt-1">
              Select points farther apart for better accuracy
            </p>
          )}
        </div>
      </div>

      {/* Selected Points Info */}
      {(pointA || pointB) && (
        <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-300 mb-3">Selected Points</h3>
          <div className="space-y-2">
            {pointA && (
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-400">Point A:</span>
                <span className="text-white font-mono">
                  ({pointA.x.toFixed(0)}, {pointA.y.toFixed(0)})
                </span>
              </div>
            )}
            {pointB && (
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-400">Point B:</span>
                <span className="text-white font-mono">
                  ({pointB.x.toFixed(0)}, {pointB.y.toFixed(0)})
                </span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="space-y-3 pt-4 border-t border-gray-700">
        <button
          onClick={onApply}
          disabled={!canApply}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:cursor-not-allowed text-white font-medium py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <Ruler className="w-5 h-5" />
          Apply Scale
        </button>
        <button
          onClick={onReset}
          className="w-full bg-gray-700 hover:bg-gray-600 text-white font-medium py-3 rounded-lg transition-colors"
        >
          Reset
        </button>
      </div>
    </div>
  );
};

export default CalibrationSidebar;
