import React from 'react';
import DXFViewer from './DXFViewer';
import PDFViewer from './PDFViewer';
import IFCViewer from './IFCViewer';

interface FileViewerProps {
  file?: File;
  width?: number;
  height?: number;
}

type SupportedKind = 'dxf' | 'pdf' | 'ifc' | 'unsupported';

function detectFileKind(file?: File): SupportedKind {
  if (!file) return 'unsupported';

  const name = file.name.toLowerCase();
  const ext = name.slice(name.lastIndexOf('.') + 1);

  // Prefer extension over MIME type — DXF/IFC files frequently arrive
  // with an empty or generic MIME type (application/octet-stream)
  // depending on OS/browser, so extension is the more reliable signal.
  if (ext === 'dxf') return 'dxf';
  if (ext === 'pdf') return 'pdf';
  if (ext === 'ifc') return 'ifc';

  // Fall back to MIME type in case extension is missing/unusual
  if (file.type === 'application/pdf') return 'pdf';

  return 'unsupported';
}

/**
 * FileViewer — single entry point that detects the uploaded file's type
 * and renders the matching specialized viewer (DXF / PDF / IFC).
 *
 * Usage:
 *   <FileViewer file={uploadedFile} width={900} height={650} />
 *
 * PNG/DWG/other types currently handled elsewhere in your pipeline
 * (e.g. rendered server-side as images) should be routed before this
 * component, or extend `detectFileKind` below to cover them.
 */
export default function FileViewer({ file, width = 800, height = 600 }: FileViewerProps) {
  const kind = detectFileKind(file);

  if (!file) {
    return (
      <div
        className="flex items-center justify-center bg-gray-50 text-gray-400 text-sm rounded-lg border border-gray-200"
        style={{ width, height }}
      >
        No file selected
      </div>
    );
  }

  switch (kind) {
    case 'dxf':
      return <DXFViewer file={file} width={width} height={height} />;
    case 'pdf':
      return <PDFViewer file={file} width={width} height={height} />;
    case 'ifc':
      return <IFCViewer file={file} width={width} height={height} />;
    default:
      return (
        <div
          className="flex flex-col items-center justify-center gap-2 bg-gray-50 text-gray-500 text-sm rounded-lg border border-gray-200 px-6 text-center"
          style={{ width, height }}
        >
          <span className="font-medium">Unsupported file type</span>
          <span className="text-xs text-gray-400">
            "{file.name}" — supported formats: .dxf, .pdf, .ifc
          </span>
        </div>
      );
  }
}