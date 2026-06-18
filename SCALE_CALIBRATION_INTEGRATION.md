# Scale Calibration Integration Guide

This guide shows how to integrate the Manual Scale Calibration feature into your ArchVision project's analysis flow.

## Overview

The Scale Calibration feature allows users to:
1. Click two points on a blueprint image
2. Enter the real-world distance between them
3. Calculate a scale factor (meters per pixel)
4. Apply this scale to all subsequent area/distance calculations

## Files Created

### Frontend Components
- `frontend/src/hooks/useScaleCalibration.js` - Custom hook for calibration logic
- `frontend/src/components/ScaleCalibration/BlueprintCanvas.jsx` - Canvas with image and SVG overlay
- `frontend/src/components/ScaleCalibration/CalibrationSidebar.jsx` - Right panel with inputs and controls
- `frontend/src/components/ScaleCalibration/ScaleCalibrationPanel.jsx` - Main modal wrapper

### Backend
- Updated `backend/api/calibration.py` with new endpoint: `POST /api/v1/calibration/analysis-jobs/{job_id}/scale-calibration`

### Database
- The `analysis_jobs` table already has a `scale_calibration` JSONB column - no migration needed

## Integration Steps

### Step 1: Import the Component

In your analysis view component (e.g., `AnalysisView.jsx` or similar):

```jsx
import ScaleCalibrationPanel from '../components/ScaleCalibration/ScaleCalibrationPanel';
```

### Step 2: Add State for Calibration Modal

```jsx
const [showCalibration, setShowCalibration] = useState(false);
const [blueprintImageUrl, setBlueprintImageUrl] = useState(null);
const [jobId, setJobId] = useState(null);
```

### Step 3: Add "Calibrate Scale" Button

Add a button in your analysis UI to open the calibration panel:

```jsx
<button
  onClick={() => setShowCalibration(true)}
  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
>
  <Ruler className="w-4 h-4" />
  Calibrate Scale
</button>
```

### Step 4: Add the ScaleCalibrationPanel Modal

Add this to your component's JSX:

```jsx
{showCalibration && blueprintImageUrl && (
  <ScaleCalibrationPanel
    imageUrl={blueprintImageUrl}
    onClose={() => setShowCalibration(false)}
    onScaleApplied={handleScaleApplied}
  />
)}
```

### Step 5: Implement the Scale Applied Handler

```jsx
const handleScaleApplied = async (calibrationData) => {
  try {
    // Call the backend API to save calibration
    const response = await fetch(
      `${import.meta.env.VITE_API_URL}/api/v1/calibration/analysis-jobs/${jobId}/scale-calibration`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${yourAuthToken}`,
        },
        body: JSON.stringify(calibrationData),
      }
    );

    if (!response.ok) {
      throw new Error('Failed to save calibration');
    }

    const result = await response.json();
    console.log('Calibration saved:', result);

    // Update your local state with the new scale factor
    // This will be used for subsequent BOQ calculations
    setScaleFactor(result.scale_factor);
    
    // Optionally trigger a re-analysis with the new scale
    // await reanalyzeWithNewScale(result.scale_factor);

  } catch (error) {
    console.error('Error saving calibration:', error);
    // Show error toast/notification
  }
};
```

### Step 6: Use the Scale Factor in BOQ Calculations

When generating BOQ or calculating areas, use the scale factor:

```jsx
// Example: Convert pixel area to real-world area
const pixelArea = width * height; // in square pixels
const scaleFactor = job.scale_calibration?.scale_factor || 0.001; // default fallback
const realWorldArea = pixelArea * (scaleFactor * scaleFactor); // in square meters

// Or if using the unit from calibration
const unit = job.scale_calibration?.unit || 'meters';
```

## Complete Example Integration

Here's a complete example of how to integrate into an analysis view:

```jsx
import React, { useState, useEffect } from 'react';
import { Ruler } from 'lucide-react';
import ScaleCalibrationPanel from '../components/ScaleCalibration/ScaleCalibrationPanel';

const AnalysisView = ({ jobId, blueprintFile }) => {
  const [showCalibration, setShowCalibration] = useState(false);
  const [blueprintImageUrl, setBlueprintImageUrl] = useState(null);
  const [jobData, setJobData] = useState(null);

  useEffect(() => {
    // Load blueprint image URL
    if (blueprintFile) {
      setBlueprintImageUrl(blueprintFile.storage_path);
    }
    
    // Load job data to check if already calibrated
    loadJobData();
  }, [blueprintFile, jobId]);

  const loadJobData = async () => {
    // Fetch job data from API
    const response = await fetch(`/api/v1/analysis-jobs/${jobId}`);
    const data = await response.json();
    setJobData(data);
  };

  const handleScaleApplied = async (calibrationData) => {
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/calibration/analysis-jobs/${jobId}/scale-calibration`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${await getToken()}`,
          },
          body: JSON.stringify(calibrationData),
        }
      );

      if (!response.ok) throw new Error('Failed to save calibration');

      const result = await response.json();
      console.log('Calibration saved:', result);
      
      // Reload job data to get updated calibration
      await loadJobData();
      
      setShowCalibration(false);
    } catch (error) {
      console.error('Error saving calibration:', error);
      alert('Failed to save calibration. Please try again.');
    }
  };

  return (
    <div className="analysis-view">
      {/* Header with calibration button */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Blueprint Analysis</h1>
        <button
          onClick={() => setShowCalibration(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2"
        >
          <Ruler className="w-4 h-4" />
          {jobData?.scale_calibration ? 'Recalibrate Scale' : 'Calibrate Scale'}
        </button>
      </div>

      {/* Show calibration status if already calibrated */}
      {jobData?.scale_calibration && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
          <p className="text-green-800">
            Scale calibrated: {jobData.scale_calibration?.scale_factor} {jobData.scale_calibration?.unit}/px
          </p>
        </div>
      )}

      {/* Your existing analysis content */}
      <div className="analysis-content">
        {/* Blueprint viewer, room editor, etc. */}
      </div>

      {/* Calibration Modal */}
      {showCalibration && blueprintImageUrl && (
        <ScaleCalibrationPanel
          imageUrl={blueprintImageUrl}
          onClose={() => setShowCalibration(false)}
          onScaleApplied={handleScaleApplied}
        />
      )}
    </div>
  );
};

export default AnalysisView;
```

## API Endpoint Details

### POST /api/v1/calibration/analysis-jobs/{job_id}/scale-calibration

**Request Body:**
```json
{
  "point_a": { "x": 120, "y": 430 },
  "point_b": { "x": 820, "y": 140 },
  "real_world_distance": 10.0,
  "unit": "meters",
  "pixel_distance": 824.35,
  "scale_factor": 0.01213
}
```

**Response:**
```json
{
  "success": true,
  "scale_factor": 0.01213,
  "unit": "meters",
  "message": "Scale calibration applied successfully"
}
```

## Database Schema

The `analysis_jobs` table includes:

- `scale_calibration` (JSONB) - Stores complete calibration data
- Other columns: id, file_name, file_path, file_type, storage_bucket, status, result (jsonb), error, created_at, updated_at, user_id, org_id

The `scale_calibration` JSONB structure:
```json
{
  "scale_factor": 0.01213,
  "unit": "meters",
  "pixel_distance": 824.35,
  "real_world_distance": 10.0,
  "point_a": { "x": 120, "y": 430 },
  "point_b": { "x": 820, "y": 140 },
  "calibrated_at": "2026-06-18T10:00:00Z"
}
```

## Styling Notes

The components use:
- Dark theme matching your existing Autodesk-inspired design
- Blue accent color (#2563EB) for interactive elements
- Tailwind CSS for styling
- Lucide React icons

All components are designed to match your existing dark theme with:
- Gray-800/900 backgrounds
- Gray-700 borders
- White text
- Blue-500/600 for primary actions

## Testing

To test the integration:

1. Upload a blueprint to a project
2. Click "Calibrate Scale" button
3. Click two points on the blueprint
4. Enter the real-world distance (e.g., 10 meters)
5. Click "Apply Scale"
6. Verify the calibration is saved to the database
7. Verify the scale factor is used in subsequent calculations

## Troubleshooting

**Issue: Canvas not displaying image**
- Ensure `imageUrl` prop is a valid URL
- Check browser console for CORS errors
- Verify image is accessible

**Issue: Points not placing correctly**
- Ensure canvas click coordinates are being calculated correctly
- Check that image dimensions are loaded before placing points
- Verify zoom/pan transformations are applied correctly

**Issue: API call failing**
- Check authentication token is valid
- Verify project ID exists
- Check backend logs for errors
- Ensure CORS is configured correctly

**Issue: Scale factor not being used**
- Verify calibration data is saved to database
- Check that scale factor is being retrieved from project data
- Ensure BOQ calculation logic uses the scale factor
