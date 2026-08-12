import React, { useState, useEffect } from 'react';
import { Upload, FileText, Box, Circle } from 'lucide-react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import DXFViewer from '@/components/viewers/DXFViewer';
import IFCViewer from '@/components/viewers/IFCViewer';
import PDFViewer from '@/components/viewers/PDFViewer';
import { API_BASE_URL } from '@/lib/api';
import ThemeToggle from '@/components/ThemeToggle';
import SimpleCube from '@/components/SimpleCube';
import Glass3DCard from '@/components/Glass3DCard';
type FileType = 'dxf' | 'ifc' | 'pdf' | null;

export default function Viewer() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const jobId = searchParams.get('job_id');

  const [file, setFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState<FileType>(null);
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /* =====================================================
     DRAG & DROP
  ===================================================== */

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

  /* =====================================================
     FILE PROCESSING
  ===================================================== */

  const processFile = (uploadedFile: File) => {
    const extension = uploadedFile.name
      .split('.')
      .pop()
      ?.toLowerCase();

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
      alert(
        'Unsupported file format. Please upload a DXF, IFC, or PDF file.'
      );
    }
  };

  /* =====================================================
     RESET
  ===================================================== */

  const handleReset = () => {
    setFile(null);
    setFileType(null);
    setError(null);
  };

  /* =====================================================
     FETCH FILE USING JOB ID
  ===================================================== */

  useEffect(() => {
    const fetchFileByJobId = async () => {
      if (!jobId) return;

      setLoading(true);
      setError(null);

      try {
        const token =
          await (window as any).Clerk?.session?.getToken();

        const response = await fetch(
          `${API_BASE_URL}/blueprint-files/${jobId}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error('Failed to fetch file');
        }

        const fileData = await response.json();

        if (!fileData.file_path) {
          throw new Error('File path not found');
        }

        const fileResponse = await fetch(fileData.file_path);

        if (!fileResponse.ok) {
          throw new Error('Failed to download file');
        }

        const blob = await fileResponse.blob();

        const filename =
          fileData.filename || 'blueprint';

        const downloadedFile = new File(
          [blob],
          filename,
          {
            type: blob.type,
          }
        );

        processFile(downloadedFile);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load file'
        );
      } finally {
        setLoading(false);
      }
    };

    fetchFileByJobId();
  }, [jobId]);

  /* =====================================================
     VIEWER
  ===================================================== */

  const renderViewer = () => {
    if (!file || !fileType) return null;

    switch (fileType) {
      case 'dxf':
        return (
          <DXFViewer
            file={file}
            width={1000}
            height={700}
          />
        );

      case 'ifc':
        return (
          <IFCViewer
            file={file}
            width={1000}
            height={700}
          />
        );

      case 'pdf':
        return (
          <PDFViewer
            file={file}
            width={1000}
            height={700}
          />
        );

      default:
        return null;
    }
  };

  /* =====================================================
     LOADING STATE
  ===================================================== */

  if (loading) {
    return (
      <div className="relative min-h-screen overflow-hidden text-ink">

        {/* BACKGROUND DESIGN */}
        <div className="fixed inset-0 z-0 pointer-events-none">
          <SimpleCube />
        </div>

        <ThemeToggle />

        {/* TRANSPARENT FOREGROUND */}
        <main className="relative z-10 min-h-screen bg-transparent p-8">

          <div className="max-w-7xl mx-auto">

            <div className="
              flex
              items-center
              justify-center
              min-h-[70vh]
            ">
              <div className="
                rounded-2xl
                border border-white/10
                bg-white/[0.015]
                backdrop-blur-[2px]
                px-8
                py-5
              ">
                <div className="text-ink/60">
                  Loading file...
                </div>
              </div>
            </div>

          </div>

        </main>

      </div>
    );
  }

  /* =====================================================
     ERROR STATE
  ===================================================== */

  if (error && jobId) {
    return (
      <div className="relative min-h-screen overflow-hidden text-ink">

        {/* BACKGROUND */}
        <div className="fixed inset-0 z-0 pointer-events-none">
          <SimpleCube />
        </div>

        <ThemeToggle />

        {/* FOREGROUND */}
        <main className="relative z-10 min-h-screen bg-transparent p-8">

          <div className="max-w-7xl mx-auto">

            <div className="mb-8">

              <button
                onClick={() =>
                  navigate(`/results/${jobId}`)
                }
                className="
                  px-4
                  py-2
                  rounded-lg
                  bg-white/[0.025]
                  backdrop-blur-sm
                  border border-white/10
                  text-ink
                  hover:bg-white/[0.06]
                  transition-all
                "
              >
                ← Back to Analysis
              </button>

            </div>

            <div className="
              min-h-[50vh]
              flex
              items-center
              justify-center
            ">

              <div className="
                bg-red-500/[0.04]
                backdrop-blur-sm
                border border-red-500/10
                rounded-2xl
                px-8
                py-6
              ">

                <div className="text-red-500">
                  Error: {error}
                </div>

              </div>

            </div>

          </div>

        </main>

      </div>
    );
  }

  /* =====================================================
     FILE VIEWER
  ===================================================== */

  if (file && fileType) {
    return (
      <div className="relative min-h-screen overflow-hidden text-ink">

        {/* =================================================
            GLOBAL BACKGROUND
        ================================================= */}

        <div className="fixed inset-0 z-0 pointer-events-none">
          <SimpleCube />
        </div>

        <ThemeToggle />

        {/* =================================================
            TRANSPARENT PAGE
        ================================================= */}

        <main className="
          relative
          z-10
          min-h-screen
          bg-transparent
          p-8
        ">

          <div className="max-w-7xl mx-auto">

            {/* =================================================
                HEADER
            ================================================= */}

            <div className="mb-8">

              <button
                onClick={() =>
                  jobId
                    ? navigate(`/results/${jobId}`)
                    : handleReset()
                }
                className="
                  inline-flex
                  items-center
                  px-4
                  py-2
                  rounded-lg

                  bg-white/[0.025]
                  backdrop-blur-sm

                  border border-white/10

                  text-ink

                  hover:bg-white/[0.06]

                  transition-all
                "
              >
                ← {jobId ? 'Back to Analysis' : 'Upload Different File'}
              </button>

              <h1 className="
                text-2xl
                font-bold
                mt-5
              ">
                {file.name}
              </h1>

              <p className="
                text-ink/55
                mt-1
              ">
                File type: {fileType.toUpperCase()}
              </p>

            </div>

            {/* =================================================
                VIEWER
            ================================================= */}

            <div className="
              bg-white/[0.012]
              backdrop-blur-[2px]

              border border-white/10

              rounded-2xl

              p-5

              shadow-sm

              overflow-hidden
            ">

              {renderViewer()}

            </div>

          </div>

        </main>

      </div>
    );
  }

  /* =====================================================
     DEFAULT UPLOAD PAGE
  ===================================================== */

  return (
    <div className="
      relative
      min-h-screen
      overflow-hidden
      text-ink
    ">

      {/* =================================================
          GLOBAL BACKGROUND
      ================================================= */}

      <div className="
        fixed
        inset-0
        z-0
        pointer-events-none
      ">
        <SimpleCube />
      </div>

      <ThemeToggle />

      {/* =================================================
          ENTIRE PAGE TRANSPARENT
      ================================================= */}

      <main className="
        relative
        z-10
        min-h-screen
        bg-transparent
        p-8
      ">

        <div className="max-w-4xl mx-auto">

          {/* =================================================
              TITLE
          ================================================= */}

          <div className="
            text-center
            mb-10
          ">

            <h1 className="
              text-4xl
              font-bold
              mb-2
            ">
              File Viewer
            </h1>

            <p className="
              text-ink/55
            ">
              Upload DXF, IFC, or PDF files to view them
            </p>

          </div>

          {/* =================================================
              UPLOAD AREA
          ================================================= */}

          <div
            className={`
              rounded-2xl
              p-12
              text-center

              border-2
              border-dashed

              backdrop-blur-[2px]

              transition-all

              ${
                dragActive
                  ? `
                    border-accent
                    bg-accent/[0.06]
                  `
                  : `
                    border-white/15
                    bg-white/[0.012]
                    hover:bg-white/[0.025]
                  `
              }
            `}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >

            <Upload
              className="
                mx-auto
                h-16
                w-16
                text-ink/35
                mb-5
              "
            />

            <p className="
              text-lg
              text-ink/60
              mb-5
            ">
              Drag and drop a file here,
              or click to select
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
              className="
                inline-block
                px-6
                py-3
                rounded-lg

                bg-accent
                text-paper

                hover:opacity-80

                cursor-pointer

                transition-opacity
              "
            >
              Select File
            </label>

            <p className="
              text-sm
              text-ink/40
              mt-5
            ">
              Supported formats:
              DXF, IFC, PDF
            </p>

                    </div>
          {/* =================================================
              FEATURE CARDS
          ================================================= */}

          <div
            className="
              mt-12
              grid
              grid-cols-1
              md:grid-cols-3
              gap-6
              [perspective:1200px]
            "
          >

            {/* DXF */}
            <Glass3DCard>
              <div className="p-6">

                <div className="flex items-center mb-4">

                  <div
                    className="
                      p-3
                      bg-accent/[0.06]
                      rounded-xl
                      mr-4
                      border border-accent/10
                      transition-all
                      duration-300
                      group-hover:scale-110
                      group-hover:-translate-y-1
                      group-hover:shadow-[0_10px_25px_rgba(0,0,0,0.15)]
                    "
                    style={{
                      transform: 'translateZ(35px)',
                    }}
                  >
                    <FileText className="h-8 w-8 text-accent" />
                  </div>

                  <div>
                    <h3 className="font-semibold text-lg">
                      DXF Viewer
                    </h3>

                    <p className="text-sm text-ink/50">
                      CAD drawings
                    </p>
                  </div>

                </div>

                <p className="text-sm text-ink/55 leading-relaxed">
                  View and interact with DXF
                  (Drawing Exchange Format)
                  files. Supports zoom, pan,
                  and layer visualization.
                </p>

              </div>
            </Glass3DCard>


            {/* IFC */}
            <Glass3DCard>
              <div className="p-6">

                <div className="flex items-center mb-4">

                  <div
                    className="
                      p-3
                      bg-accent/[0.06]
                      rounded-xl
                      mr-4
                      border border-accent/10
                      transition-all
                      duration-300
                      group-hover:scale-110
                      group-hover:-translate-y-1
                      group-hover:shadow-[0_10px_25px_rgba(0,0,0,0.15)]
                    "
                    style={{
                      transform: 'translateZ(35px)',
                    }}
                  >
                    <Box className="h-8 w-8 text-accent" />
                  </div>

                  <div>
                    <h3 className="font-semibold text-lg">
                      IFC Viewer
                    </h3>

                    <p className="text-sm text-ink/50">
                      BIM models
                    </p>
                  </div>

                </div>

                <p className="text-sm text-ink/55 leading-relaxed">
                  Explore IFC (Industry Foundation
                  Classes) BIM models in 3D.
                  Rotate, zoom, and inspect
                  building information models.
                </p>

              </div>
            </Glass3DCard>


            {/* PDF */}
            <Glass3DCard>
              <div className="p-6">

                <div className="flex items-center mb-4">

                  <div
                    className="
                      p-3
                      bg-accent/[0.06]
                      rounded-xl
                      mr-4
                      border border-accent/10
                      transition-all
                      duration-300
                      group-hover:scale-110
                      group-hover:-translate-y-1
                      group-hover:shadow-[0_10px_25px_rgba(0,0,0,0.15)]
                    "
                    style={{
                      transform: 'translateZ(35px)',
                    }}
                  >
                    <Circle className="h-8 w-8 text-accent" />
                  </div>

                  <div>
                    <h3 className="font-semibold text-lg">
                      PDF Viewer
                    </h3>

                    <p className="text-sm text-ink/50">
                      Documents
                    </p>
                  </div>

                </div>

                <p className="text-sm text-ink/55 leading-relaxed">
                  View PDF documents with page
                  navigation and zoom controls.
                  Perfect for specifications
                  and documentation.
                </p>

              </div>
            </Glass3DCard>

          </div>

        </div>
      </main>
    </div>
  );
}