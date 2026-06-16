import React, { useState } from 'react';
import { Upload, FileText, Box, Circle } from 'lucide-react';
import DXFViewer from '@/components/viewers/DXFViewer';
import IFCViewer from '@/components/viewers/IFCViewer';
import PDFViewer from '@/components/viewers/PDFViewer';

type FileType = 'dxf' | 'ifc' | 'pdf' | null;

export default function Viewer() {
  const [file, setFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState<FileType>(null);
  const [dragActive, setDragActive] = useState(false);

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
    } else {
      alert('Unsupported file format. Please upload a DXF, IFC, or PDF file.');
    }
  };

  const handleReset = () => {
    setFile(null);
    setFileType(null);
  };

  const renderViewer = () => {
    if (!file || !fileType) return null;

    switch (fileType) {
      case 'dxf':
        return <DXFViewer file={file} width={1000} height={700} />;
      case 'ifc':
        return <IFCViewer file={file} width={1000} height={700} />;
      case 'pdf':
        return <PDFViewer file={file} width={1000} height={700} />;
      default:
        return null;
    }
  };

  if (file && fileType) {
    return (
      <div className="min-h-screen bg-gray-100 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-6">
            <button
              onClick={handleReset}
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              ← Upload Different File
            </button>
            <h1 className="text-2xl font-bold mt-4">{file.name}</h1>
            <p className="text-gray-600">File type: {fileType.toUpperCase()}</p>
          </div>
          {renderViewer()}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">File Viewer</h1>
          <p className="text-gray-600">Upload DXF, IFC, or PDF files to view them</p>
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
            accept=".dxf,.ifc,.pdf"
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
            Supported formats: DXF, IFC, PDF
          </p>
        </div>

        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex items-center mb-4">
              <div className="p-3 bg-blue-100 rounded-lg mr-4">
                <FileText className="h-8 w-8 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">DXF Viewer</h3>
                <p className="text-sm text-gray-600">CAD drawings</p>
              </div>
            </div>
            <p className="text-sm text-gray-600">
              View and interact with DXF (Drawing Exchange Format) files. 
              Supports zoom, pan, and layer visualization.
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex items-center mb-4">
              <div className="p-3 bg-green-100 rounded-lg mr-4">
                <Box className="h-8 w-8 text-green-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">IFC Viewer</h3>
                <p className="text-sm text-gray-600">BIM models</p>
              </div>
            </div>
            <p className="text-sm text-gray-600">
              Explore IFC (Industry Foundation Classes) BIM models in 3D. 
              Rotate, zoom, and inspect building information models.
            </p>
          </div>

          <div className="bg-white rounded-lg p-6 shadow-sm">
            <div className="flex items-center mb-4">
              <div className="p-3 bg-red-100 rounded-lg mr-4">
                <Circle className="h-8 w-8 text-red-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">PDF Viewer</h3>
                <p className="text-sm text-gray-600">Documents</p>
              </div>
            </div>
            <p className="text-sm text-gray-600">
              View PDF documents with page navigation and zoom controls. 
              Perfect for specifications and documentation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
