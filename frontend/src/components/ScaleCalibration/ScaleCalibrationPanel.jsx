import React, { useState, useEffect } from 'react';
import { CalibrationManager } from '../calibration/CalibrationManager';

export default function ScaleCalibrationPanel() {
  const [state, setState] = useState(CalibrationManager.getState());
  const [inputValue, setInputValue] = useState('');

  useEffect(() => {
    const interval = setInterval(() => {
      setState({ ...CalibrationManager.getState() });
    }, 100);
    return () => clearInterval(interval);
  }, []);

  const apply = () => {
    const value = parseFloat(inputValue);
    if (!value) return;

    CalibrationManager.setRealWorldDistance(value, state.unit);
  };

  return (
    <div className="p-3 border bg-white w-80">
      <h3 className="font-bold mb-2">Scale Calibration</h3>

      <div className="text-sm">
        <div>Point A: {state.pointA ? 'Set' : '-'}</div>
        <div>Point B: {state.pointB ? 'Set' : '-'}</div>
        <div>
          Pixel Distance:{' '}
          {state.pointA && state.pointB
            ? Math.sqrt(
                Math.pow(state.pointB.x - state.pointA.x, 2) +
                Math.pow(state.pointB.y - state.pointA.y, 2)
              ).toFixed(2)
            : '-'}
        </div>
        <div>
          Scale Factor:{' '}
          {state.scaleFactor ? state.scaleFactor.toFixed(4) : '-'}
        </div>
      </div>

      <div className="mt-3">
        <input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Enter real distance"
          className="border p-1 w-full"
        />
        <button
          onClick={apply}
          className="mt-2 bg-blue-500 text-white px-2 py-1 w-full"
        >
          Apply
        </button>

        <button
          onClick={() => CalibrationManager.reset()}
          className="mt-2 bg-gray-300 px-2 py-1 w-full"
        >
          Reset
        </button>
      </div>
    </div>
  );
}