import React, { useEffect, useRef, useState } from 'react';
import { CalibrationManager } from '../../calibration/CalibrationManager.ts';

export default function ScaleCalibrationPanel({
  imageUrl,
  onClose,
  onScaleApplied,
  hidePreview = false,
  calibrationStatus = 'manual_required',
  autoCalibration,
}) {
  const [state, setState] = useState(CalibrationManager.getState());
  const [inputValue, setInputValue] = useState('');
  const [imageSize, setImageSize] = useState(null);
  const [appliedCalibration, setAppliedCalibration] = useState(null);
  const imageRef = useRef(null);

  useEffect(() => {
    CalibrationManager.reset();
    setState({ ...CalibrationManager.getState() });
    setInputValue('');
    setImageSize(null);
    setAppliedCalibration(null);

    const interval = setInterval(() => {
      setState({ ...CalibrationManager.getState() });
    }, 100);
    return () => clearInterval(interval);
  }, [imageUrl]);

  const handleImageClick = (event) => {
    if (!state.scaleMode || !imageRef.current) return;

    const rect = imageRef.current.getBoundingClientRect();
    if (!rect.width || !rect.height) return;

    const scaleX = imageRef.current.naturalWidth / rect.width;
    const scaleY = imageRef.current.naturalHeight / rect.height;
    const x = (event.clientX - rect.left) * scaleX;
    const y = (event.clientY - rect.top) * scaleY;

    CalibrationManager.addPoint({
      x,
      y,
      space: 'image',
    });
    setState({ ...CalibrationManager.getState() });
  };

  const apply = async () => {
    const value = parseFloat(inputValue);
    if (!value || value <= 0) return;

    CalibrationManager.setRealWorldDistance(value, state.unit);
    const currentState = CalibrationManager.getState();

    if (
      !currentState.pointA ||
      !currentState.pointB ||
      !currentState.scaleFactor
    ) {
      return;
    }

    const calibration = {
      point_a: currentState.pointA,
      point_b: currentState.pointB,
      real_world_distance: value,
      unit: currentState.unit,
      pixel_distance: Math.sqrt(
        Math.pow(currentState.pointB.x - currentState.pointA.x, 2) +
        Math.pow(currentState.pointB.y - currentState.pointA.y, 2) +
        Math.pow((currentState.pointB.z || 0) - (currentState.pointA.z || 0), 2)
      ),
      scale_factor: currentState.scaleFactor,
    };

    await onScaleApplied?.(calibration);
    setAppliedCalibration(calibration);
  };

  const reset = () => {
    CalibrationManager.reset();
    setInputValue('');
    setImageSize(null);
    setState({ ...CalibrationManager.getState() });
  };

  const pixelDistance = state.pointA && state.pointB
    ? Math.sqrt(
        Math.pow(state.pointB.x - state.pointA.x, 2) +
        Math.pow(state.pointB.y - state.pointA.y, 2) +
        Math.pow((state.pointB.z || 0) - (state.pointA.z || 0), 2)
      )
    : null;

  return (
    <div className="p-4 border bg-white w-[32rem] max-w-full rounded-lg shadow-lg">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-bold">Scale Calibration</h3>
        {onClose && (
          <button onClick={onClose} className="text-gray-500 hover:text-gray-800">
            Close
          </button>
        )}
      </div>

      {calibrationStatus === 'auto_calibrated' ? (
        <div className="mb-4 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-900">
          <div className="font-medium">Automatic scale detected and applied</div>
          <div className="mt-1 text-xs">
            {autoCalibration?.scale_ratio || 'Detected scale'}
            {autoCalibration?.mm_per_pixel ? ` · ${autoCalibration.mm_per_pixel.toFixed(3)} mm/px` : ''}
          </div>
        </div>
      ) : (
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-950">
          <div className="font-medium">No reliable scale detected — manual calibration required</div>
          <p className="mt-1 text-xs text-amber-800">
            Enable calibration, select two points on a known dimension, then enter that real-world distance.
          </p>
        </div>
      )}

      {!hidePreview && <div className="mb-4 rounded-lg border border-gray-200 bg-gray-50">
        {imageUrl ? (
          <div className="relative">
            <img
              ref={imageRef}
              src={imageUrl}
              alt="Blueprint"
              onLoad={() => {
                setImageSize({
                  width: imageRef.current?.naturalWidth || 0,
                  height: imageRef.current?.naturalHeight || 0,
                });
              }}
              onClick={handleImageClick}
              className="block w-full h-auto cursor-crosshair"
            />
            {imageSize && (
              <div className="absolute inset-0 pointer-events-none">
                {state.pointA && state.pointB && (
                  <svg
                    className="absolute inset-0 h-full w-full"
                    viewBox={`0 0 ${imageSize.width} ${imageSize.height}`}
                    preserveAspectRatio="none"
                    aria-label="Selected calibration distance"
                  >
                    <line
                      x1={state.pointA.x}
                      y1={state.pointA.y}
                      x2={state.pointB.x}
                      y2={state.pointB.y}
                      stroke="#2563eb"
                      strokeWidth={Math.max(imageSize.width, imageSize.height) / 500}
                      strokeDasharray="8 5"
                    />
                  </svg>
                )}
                {[state.pointA, state.pointB].filter(Boolean).map((point, index) => (
                  <div
                    key={`${point.x}-${point.y}-${index}`}
                    className="absolute"
                    style={{
                      left: `${(point.x / imageSize.width) * 100}%`,
                      top: `${(point.y / imageSize.height) * 100}%`,
                      transform: 'translate(-50%, -50%)',
                    }}
                  >
                    <div className={`h-4 w-4 rounded-full border-2 border-white ${index === 0 ? 'bg-green-500' : 'bg-blue-500'}`} />
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="p-6 text-sm text-gray-500">
            No blueprint preview available.
          </div>
        )}
      </div>}

      <div className="text-sm">
        <div>Point A: {state.pointA ? 'Set' : '-'}</div>
        <div>Point B: {state.pointB ? 'Set' : '-'}</div>
        <div>Pixel Distance: {pixelDistance ? pixelDistance.toFixed(2) : '-'}</div>
        <div>Scale Factor: {state.scaleFactor ? state.scaleFactor.toFixed(4) : '-'}</div>
        <div>Calibration Mode: {state.scaleMode ? 'ON' : 'OFF'}</div>
      </div>

      {appliedCalibration && (
        <div className="mt-3 rounded-lg border border-green-200 bg-green-50 p-3 text-sm text-green-900">
          <div className="font-medium">Scale calibration applied</div>
          <div className="mt-1 text-xs">
            {appliedCalibration.real_world_distance} {appliedCalibration.unit} across {appliedCalibration.pixel_distance.toFixed(2)} px
            {' · '}{appliedCalibration.scale_factor.toFixed(6)} {appliedCalibration.unit}/px
          </div>
        </div>
      )}

      <div className="mt-3 space-y-2">
        <div className="flex gap-2">
          <input
            type="number"
            min="0"
            step="any"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Enter real distance"
            className="border p-2 w-full rounded"
          />
          <select
            value={state.unit}
            onChange={(e) => {
              CalibrationManager.setRealWorldDistance(Number(inputValue) || 0, e.target.value);
              setState({ ...CalibrationManager.getState() });
            }}
            className="border p-2 rounded"
            aria-label="Distance unit"
          >
            <option value="m">m</option>
            <option value="ft">ft</option>
            <option value="mm">mm</option>
            <option value="in">in</option>
          </select>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => {
              CalibrationManager.enable();
              setState({ ...CalibrationManager.getState() });
            }}
            className="bg-green-600 text-white px-2 py-2 w-full rounded"
          >
            Enable Calibration
          </button>
          <button
            onClick={() => {
              CalibrationManager.reselectPoints();
              setAppliedCalibration(null);
              setState({ ...CalibrationManager.getState() });
            }}
            disabled={!state.pointA && !state.pointB}
            className="bg-blue-100 text-blue-900 px-2 py-2 w-full rounded disabled:opacity-50"
          >
            Reselect Points
          </button>
          <button
            onClick={reset}
            className="bg-gray-200 px-2 py-2 w-full rounded"
          >
            Reset
          </button>
        </div>
        <button
          onClick={apply}
          disabled={!state.pointA || !state.pointB || !inputValue}
          className="bg-blue-500 text-white px-2 py-2 w-full rounded disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Apply Scale
        </button>
      </div>
    </div>
  );
}
