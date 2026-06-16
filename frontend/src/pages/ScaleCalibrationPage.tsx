import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Upload, FileText, Box, Circle } from 'lucide-react';
import DXFViewer from '@/components/viewers/DXFViewer';
import IFCViewer from '@/components/viewers/IFCViewer';
import PDFViewer from '@/components/viewers/PDFViewer';
import ScaleCalibration from '@/components/calibration/ScaleCalibration';

type FileType = 'dxf' | 'ifc' | 'pdf' | null;

export default function ScaleCalibrationPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState<FileType>(null);
  const [dragActive, setDragActive] = useState(false);
  const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [showCalibration, setShowCalibration] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = (uploadedFile: File) => {
    const extension = uploadedFile.name.split('.').pop()?.toLowerCase();
    
    if (extension === 'dxf') {
      setFileType('dxf');
      setFile(uploadedFile);
    } else if (extension === 'ifc') {
      setFileType('ifc');
      setFile(uploadedFile);
    } else if (extension === 'pdf') {
      setFileType('pdf');
      setFile(uploadedFile);
      // For PDF, create a preview image
      const url = URL.createObjectURL(uploadedFile);
      setImageSrc(url);
    } else if (extension === 'png' || extension === 'jpg' || extension === 'jpeg') {
      // For image files, use directly for calibration
      setFileType(null);
      setFile(uploadedFile);
      const url = URL.createObjectURL(uploadedFile);
      setImageSrc(url);
      setShowCalibration(true);
    } else {
      alert('Unsupported file format. Please upload a DXF, IFC, PDF, or image file.');
    }
  };

  const handleReset = () => {
    setFile(null);
    setFileType(null);
    setImageSrc(null);
    setShowCalibration(false);
  };

  const handleScaleCalibrated = (scale: number, unit: string) => {
    console.log('Scale calibrated:', scale, unit);
    // Here you would save the scale to your backend or state
    alert(`Scale calibrated: ${scale.toFixed(5)} ${unit}/px`);
  };

  const renderViewer = () => {
    if (!file || !fileType) return null;

    switch (fileType) {
      case 'dxf':
        return <DXFViewer file={file} width={800} height={600} />;
      case 'ifc':
        return <IFCViewer file={file} width={800} height={600} />;
      case 'pdf':
        return <PDFViewer file={file} width={800} height={600} />;
      default:
        return null;
    }
  };

  if (showCalibration && imageSrc) {
    return (
      <div className="min-h-screen bg-gray-100 flex">
        {/* Sidebar */}
        <div className="w-64 bg-white border-r border-gray-200 p-4">
          <div className="flex items-center gap-2 mb-6">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <h1 className="text-lg font-semibold">Scale Calibration</h1>
          </div>
          
          <nav className="space-y-2">
            <button className="w-full text-left px-3 py-2 rounded-lg bg-blue-50 text-blue-700 font-medium">
              Scale Calibration
            </button>
            <button 
              onClick={() => navigate('/dashboard')}
              className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-100 text-gray-700"
            >
              Dashboard
            </button>
            <button 
              onClick={() => navigate('/viewer')}
              className="w-full text-left px-3 py-2 rounded-lg hover:bg-gray-100 text-gray-700"
            >
              File Viewer
            </button>
          </nav>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex">
          {/* Blueprint Area */}
          <div className="flex-1 p-6">
            <div className="bg-white rounded-lg shadow-sm p-4 h-full">
              <h2 className="text-lg font-semibold mb-4">{file?.name || 'Blueprint'}</h2>
              <div className="border border-gray-300 rounded-lg overflow-hidden">
                <img 
                  src={imageSrc} 
                  alt="Blueprint" 
                  className="w-full h-full object-contain"
                  style={{ maxHeight: '600px' }}
                />
              </div>
            </div>
          </div>

          {/* Calibration Panel */}
          <div className="w-96 bg-white border-l border-gray-200 p-6 overflow-y-auto">
            <ScaleCalibration 
              onScaleCalibrated={handleScaleCalibrated}
              imageSrc={imageSrc}
            />
          </div>
        </div>
      </div>
    );
  }

  if (file && fileType) {
    return (
      <div className="min-h-screen bg-gray-100 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-6">
            <button
              onClick={() => navigate('/dashboard')}
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 mb-4"
            >
              ← Back to Dashboard
            </button>
            <button
              onClick={handleReset}
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 ml-2"
            >
              Upload Different File
            </button>
            <h1 className="text-2xl font-bold mt-4">{file.name}</h1>
            <p className="text-gray-600">File type: {fileType.toUpperCase()}</p>
            <button
              onClick={() => {
                if (fileType === 'pdf') {
                  setShowCalibration(true);
                } else {
                  alert('Calibration is currently available for PDF and image files only.');
                }
              }}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Enable Scale Calibration
            </button>
          </div>
          {renderViewer()}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <button
            onClick={() => navigate('/dashboard')}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            ← Back to Dashboard
          </button>
        </div>
        
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">Scale Calibration</h1>
          <p className="text-gray-600">Upload a blueprint or image to calibrate its scale</p>
        </div>

        <div
          className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
            dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <Upload className="mx-auto h-16 w-16 text-gray-400 mb-4" />
          <p className="text-lg text-gray-600 mb-4">
            Drag and drop a file here, or click to select
          </p>
          <input
            type="file"
            onChange={handleChange}
            accept=".dxf,.ifc,.pdf,.png,.jpg,.jpeg"
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="inline-block px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 cursor-pointer"
          >
            Select File
          </label>
          <p className="text-sm text-gray-500 mt-4">
            Supported formats: DXF, IFC, PDF, PNG, JPG, JPEG
          </p>
        </div>

        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex items-center mb-4">
              <div className="p-3 bg-blue-100 rounded-lg mr-4">
                <FileText className="h-8 w-8 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">PDF Calibration</h3>
                <p className="text-sm text-gray-600">Documents</p>
              </div>
            </div>
            <p className="text-sm text-gray-600">
              Calibrate scale from PDF blueprints with point selection and distance measurement.
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex items-center mb-4">
              <div className="p-3 bg-green-100 rounded-lg mr-4">
                <Circle className="h-8 w-8 text-green-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">Image Calibration</h3>
                <p className="text-sm text-gray-600">Blueprints</p>
              </div>
            </div>
            <p className="text-sm text-gray-600">
              Upload blueprint images (PNG, JPG) for precise scale calibration and measurement.
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex items-center mb-4">
              <div className="p-3 bg-purple-100 rounded-lg mr-4">
                <Box className="h-8 w-8 text-purple-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">CAD Support</h3>
                <p className="text-sm text-gray-600">DXF/IFC</p>
              </div>
            </div>
            <p className="text-sm text-gray-600">
              View DXF and IFC files. Calibration coming soon for CAD formats.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
