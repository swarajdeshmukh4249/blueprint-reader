import React, { useState } from 'react'
import ThemeToggle from '@/components/ThemeToggle'
import SimpleCube from '@/components/SimpleCube'
import Glass3DCard from '@/components/Glass3DCard'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  ArrowLeft,
  Upload,
  FileText,
  Box,
  Circle,
  LayoutDashboard,
  BarChart3
} from 'lucide-react'
import DXFViewer from '@/components/viewers/DXFViewer'
import IFCViewer from '@/components/viewers/IFCViewer'
import PDFViewer from '@/components/viewers/PDFViewer'
import ScaleCalibrationPanel from '@/components/ScaleCalibration/ScaleCalibrationPanel'
import { useNavigationStore } from '@/stores/useNavigationStore'

type FileType = 'dxf' | 'ifc' | 'pdf' | 'image' | null

export default function ScaleCalibrationPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { currentAnalysis } = useNavigationStore()

  const [file, setFile] = useState<File | null>(null)
  const [fileType, setFileType] = useState<FileType>(null)
  const [dragActive, setDragActive] = useState(false)
  const [imageSrc, setImageSrc] = useState<string | null>(null)
  const [showCalibration, setShowCalibration] = useState(false)

  const contextFileId =
    searchParams.get('file') || currentAnalysis?.fileId

  const contextProjectId =
    searchParams.get('project') || currentAnalysis?.projectId

  const backToResults = contextFileId
    ? `/results/${contextFileId}`
    : currentAnalysis?.originPath || '/upload'

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()

    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()

    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0])
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault()

    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0])
    }
  }

  const processFile = (uploadedFile: File) => {
    const extension = uploadedFile.name
      .split('.')
      .pop()
      ?.toLowerCase()

    if (extension === 'dxf') {
      setFileType('dxf')
      setFile(uploadedFile)
    } else if (extension === 'ifc') {
      setFileType('ifc')
      setFile(uploadedFile)
    } else if (extension === 'pdf') {
      setFileType('pdf')
      setFile(uploadedFile)

      const url = URL.createObjectURL(uploadedFile)
      setImageSrc(url)
    } else if (
      extension === 'png' ||
      extension === 'jpg' ||
      extension === 'jpeg'
    ) {
      setFileType('image')
      setFile(uploadedFile)

      const url = URL.createObjectURL(uploadedFile)
      setImageSrc(url)

      setShowCalibration(true)
    } else {
      alert(
        'Unsupported file format. Please upload a DXF, IFC, PDF, or image file.'
      )
    }
  }

  const handleReset = () => {
    setFile(null)
    setFileType(null)
    setImageSrc(null)
    setShowCalibration(false)
  }

  const handleScaleCalibrated = (calibration: {
    scale_factor: number
    unit: string
  }) => {
    console.log('Scale calibrated:', calibration)
  }

  const renderViewer = () => {
    if (!file || !fileType) return null

    switch (fileType) {
      case 'dxf':
        return <DXFViewer file={file} width={800} height={600} />

      case 'ifc':
        return <IFCViewer file={file} width={800} height={600} />

      case 'pdf':
        return <PDFViewer file={file} width={800} height={600} />

      case 'image':
        return imageSrc ? (
          <img
            src={imageSrc}
            alt={file.name}
            className="max-h-[600px] max-w-full object-contain"
          />
        ) : null

      default:
        return null
    }
  }

  /*
  ============================================================
  CALIBRATION VIEW
  ============================================================
  */

  if (showCalibration && file && fileType) {
    const isImage = fileType === 'image'

    return (
      <div className="relative min-h-screen overflow-hidden bg-transparent">

        {/* BACKGROUND DESIGN */}
        <div className="fixed inset-0 z-0 pointer-events-none">
          <SimpleCube />
        </div>

        <ThemeToggle />

        {/* FOREGROUND */}
        <div className="relative z-10 min-h-screen flex flex-col">

          {/* TOP BAR */}
          <div className="border-b border-ink/10 bg-transparent backdrop-blur-[2px]">

            <div className="px-6 py-3">

              <div className="flex items-center justify-between">

                {/* Breadcrumb */}
                <div className="flex items-center gap-2 text-sm text-ink/55">

                  <button
                    onClick={() => navigate('/dashboard')}
                    className="flex items-center gap-1 hover:text-ink transition-colors"
                  >
                    <LayoutDashboard className="w-3.5 h-3.5" />
                    Dashboard
                  </button>

                  <span className="text-ink/25">/</span>

                  <button
                    onClick={() =>
                      navigate(
                        contextProjectId
                          ? `/upload?project=${contextProjectId}`
                          : '/upload'
                      )
                    }
                    className="flex items-center gap-1 hover:text-ink transition-colors"
                  >
                    <Upload className="w-3.5 h-3.5" />
                    Upload
                  </button>

                  <span className="text-ink/25">/</span>

                  {contextFileId && (
                    <>
                      <button
                        onClick={() => navigate(backToResults)}
                        className="hover:text-ink transition-colors"
                      >
                        Results
                      </button>

                      <span className="text-ink/25">/</span>
                    </>
                  )}

                  <span className="text-ink font-medium">
                    Scale Calibration
                  </span>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">

                  <button
                    onClick={() => navigate(backToResults)}
                    className="
                      flex items-center gap-1.5
                      text-xs text-ink/55
                      hover:text-ink
                      border border-ink/15
                      rounded-full
                      px-3 py-1.5
                      bg-transparent
                      backdrop-blur-sm
                      transition
                      hover:bg-ink/5
                    "
                  >
                    <ArrowLeft className="w-3 h-3" />
                    Back to Results
                  </button>

                  <button
                    onClick={() => navigate('/new-analytics')}
                    className="
                      flex items-center gap-1.5
                      text-xs text-ink/55
                      hover:text-ink
                      border border-ink/15
                      rounded-full
                      px-3 py-1.5
                      bg-transparent
                      backdrop-blur-sm
                      transition
                      hover:bg-ink/5
                    "
                  >
                    <BarChart3 className="w-3 h-3" />
                    Analytics
                  </button>

                </div>

              </div>
            </div>
          </div>

          {/* MAIN */}
          <div className="flex flex-1 min-h-0">

            {/* SIDEBAR */}
            <aside
              className="
                w-64
                shrink-0
                border-r border-ink/10
                bg-transparent
                backdrop-blur-[2px]
                p-4
              "
            >

              <div className="flex items-center gap-2 mb-6">

                <button
                  onClick={() => navigate(backToResults)}
                  className="text-ink/60 hover:text-ink"
                >
                  <ArrowLeft className="w-5 h-5" />
                </button>

                <h1 className="text-lg font-semibold text-ink">
                  Scale Calibration
                </h1>

              </div>

              <nav className="space-y-2">

                {/* Active */}
                <button
                  className="
                    w-full
                    text-left
                    px-3 py-2
                    rounded-lg
                    bg-accent/5
                    border border-accent/20
                    text-accent
                    font-medium
                    backdrop-blur-sm
                  "
                >
                  Scale Calibration
                </button>

                {contextFileId && (
                  <button
                    onClick={() => navigate(backToResults)}
                    className="
                      w-full text-left
                      px-3 py-2
                      rounded-lg
                      text-ink/75
                      hover:bg-ink/5
                      transition
                    "
                  >
                    ← Results
                  </button>
                )}

                <button
                  onClick={() =>
                    navigate(
                      contextProjectId
                        ? `/upload?project=${contextProjectId}`
                        : '/upload'
                    )
                  }
                  className="
                    w-full text-left
                    px-3 py-2
                    rounded-lg
                    text-ink/75
                    hover:bg-ink/5
                    transition
                  "
                >
                  Upload
                </button>

                <button
                  onClick={() => navigate('/dashboard')}
                  className="
                    w-full text-left
                    px-3 py-2
                    rounded-lg
                    text-ink/75
                    hover:bg-ink/5
                    transition
                  "
                >
                  Dashboard
                </button>

                <button
                  onClick={() => navigate('/viewer')}
                  className="
                    w-full text-left
                    px-3 py-2
                    rounded-lg
                    text-ink/75
                    hover:bg-ink/5
                    transition
                  "
                >
                  File Viewer
                </button>

              </nav>
            </aside>

            {/* CONTENT */}
            <div className="flex-1 flex min-w-0 min-h-0">

              {/* BLUEPRINT */}
              {!isImage && (
                <div className="flex-1 min-w-0 p-6 overflow-auto">

                  <div
                    className="
                      h-full
                      rounded-2xl
                      border border-ink/10
                      bg-transparent
                      backdrop-blur-[1px]
                      p-4
                    "
                  >

                    <h2 className="text-lg font-semibold mb-4 text-ink">
                      {file.name}
                    </h2>

                    <div
                      className="
                        border border-ink/15
                        rounded-xl
                        overflow-hidden
                        inline-block
                        max-w-full
                        bg-transparent
                      "
                    >
                      {renderViewer()}
                    </div>

                  </div>
                </div>
              )}

              {/* CALIBRATION PANEL */}
              <div
                className={`
                  ${
                    isImage
                      ? 'flex-1 flex items-start justify-center'
                      : 'w-96 shrink-0'
                  }

                  border-l border-ink/10
                  bg-transparent
                  backdrop-blur-[2px]
                  p-6
                  overflow-y-auto
                `}
              >

                <ScaleCalibrationPanel
                  imageUrl={
                    isImage
                      ? imageSrc ?? undefined
                      : undefined
                  }
                  hidePreview={!isImage}
                  onClose={() => setShowCalibration(false)}
                  onScaleApplied={handleScaleCalibrated}
                />

              </div>

            </div>
          </div>
        </div>
      </div>
    )
  }

  /*
  ============================================================
  FILE PREVIEW VIEW
  ============================================================
  */

  if (file && fileType) {

    return (
      <div className="relative min-h-screen overflow-hidden bg-transparent">

        {/* BACKGROUND */}
        <div className="fixed inset-0 z-0 pointer-events-none">
          <SimpleCube />
        </div>

        <ThemeToggle />

        <div className="relative z-10 min-h-screen p-8">

          <div className="max-w-7xl mx-auto">

            {/* Breadcrumb */}
            <div className="flex items-center gap-2 text-sm text-ink/55 mb-6">

              <button
                onClick={() => navigate('/dashboard')}
                className="hover:text-ink"
              >
                Dashboard
              </button>

              <span>/</span>

              <button
                onClick={() =>
                  navigate(
                    contextProjectId
                      ? `/upload?project=${contextProjectId}`
                      : '/upload'
                  )
                }
                className="hover:text-ink"
              >
                Upload
              </button>

              {contextFileId && (
                <>
                  <span>/</span>

                  <button
                    onClick={() => navigate(backToResults)}
                    className="hover:text-ink"
                  >
                    Results
                  </button>
                </>
              )}

              <span>/</span>

              <span className="text-ink font-medium">
                Scale Calibration
              </span>

            </div>

            {/* HEADER */}
            <div
              className="
                mb-6
                rounded-2xl
                border border-ink/10
                bg-transparent
                backdrop-blur-[2px]
                p-6
              "
            >

              <div className="flex flex-wrap gap-2">

                <button
                  onClick={() => navigate(backToResults)}
                  className="
                    px-4 py-2
                    bg-transparent
                    border border-ink/20
                    text-ink
                    rounded-lg
                    hover:bg-ink/5
                    transition
                  "
                >
                  ← Back
                </button>

                <button
                  onClick={handleReset}
                  className="
                    px-4 py-2
                    bg-transparent
                    border border-ink/20
                    text-ink
                    rounded-lg
                    hover:bg-ink/5
                    transition
                  "
                >
                  Upload Different File
                </button>

              </div>

              <h1 className="text-2xl font-bold mt-5 text-ink">
                {file.name}
              </h1>

              <p className="text-ink/60 mt-1">
                File type: {fileType.toUpperCase()}
              </p>

              <button
                onClick={() => setShowCalibration(true)}
                className="
                  mt-4
                  px-4 py-2
                  bg-accent/90
                  text-paper
                  rounded-lg
                  hover:bg-accent
                  transition
                "
              >
                Enable Scale Calibration
              </button>

            </div>

            {/* VIEWER */}
            <div
              className="
                rounded-2xl
                border border-ink/10
                bg-transparent
                backdrop-blur-[1px]
                p-5
                overflow-auto
              "
            >
              {renderViewer()}
            </div>

          </div>
        </div>
      </div>
    )
  }

  /*
  ============================================================
  UPLOAD / EMPTY STATE
  ============================================================
  */

  return (
    <div className="relative min-h-screen overflow-hidden bg-transparent">

      {/* BACKGROUND DESIGN */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <SimpleCube />
      </div>

      <ThemeToggle />

      {/* FOREGROUND */}
      <div className="relative z-10 min-h-screen p-8">

        <div className="max-w-4xl mx-auto">

          {/* BREADCRUMB */}
          <div
            className="
              flex items-center gap-2
              text-sm text-ink/55
              mb-6
            "
          >

            <button
              onClick={() => navigate('/dashboard')}
              className="hover:text-ink transition"
            >
              Dashboard
            </button>

            <span>/</span>

            <button
              onClick={() =>
                navigate(
                  contextProjectId
                    ? `/upload?project=${contextProjectId}`
                    : '/upload'
                )
              }
              className="hover:text-ink transition"
            >
              Upload
            </button>

            {contextFileId && (
              <>
                <span>/</span>

                <button
                  onClick={() => navigate(backToResults)}
                  className="hover:text-ink transition"
                >
                  Results
                </button>
              </>
            )}

            <span>/</span>

            <span className="text-ink font-medium">
              Scale Calibration
            </span>

          </div>

          {/* BACK BUTTON */}
          <div className="mb-6">

            <button
              onClick={() => navigate(backToResults)}
              className="
                px-4 py-2
                bg-transparent
                border border-ink/20
                text-ink
                rounded-lg
                hover:bg-ink/5
                transition
              "
            >
              ← Back
            </button>

          </div>

          {/* HEADING */}
          <div className="text-center mb-8">

            <h1 className="text-4xl font-bold text-ink mb-2">
              Scale Calibration
            </h1>

            <p className="text-ink/60">
              Upload a blueprint or image to calibrate its scale
            </p>

          </div>

          {/* UPLOAD BOX */}
          <div
            className={`
              border-2
              border-dashed
              rounded-2xl
              p-12
              text-center
              transition-all
              backdrop-blur-[1px]

              ${
                dragActive
                  ? 'border-accent bg-accent/5'
                  : 'border-ink/20 bg-transparent hover:bg-ink/5'
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
                text-ink/40
                mb-4
              "
            />

            <p className="text-lg text-ink/65 mb-4">
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
              className="
                inline-block
                px-6 py-3
                bg-accent
                text-paper
                rounded-lg
                hover:opacity-80
                cursor-pointer
                transition
              "
            >
              Select File
            </label>

            <p className="text-sm text-ink/50 mt-4">
              Supported formats: DXF, IFC, PDF, PNG, JPG, JPEG
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

  {/* =================================================
      PDF CALIBRATION
  ================================================= */}

  <Glass3DCard>

    <div className="p-6">

      <div className="flex items-center mb-4">

        {/* 3D ICON */}
        <div
          className="
            p-3
            bg-blue-500/[0.04]
            border border-blue-500/20
            rounded-xl
            mr-4

            transition-all
            duration-500
            ease-out

            group-hover:scale-110
            group-hover:-translate-y-1
            group-hover:rotate-3

            group-hover:shadow-[0_12px_30px_rgba(37,99,235,0.15)]
          "
          style={{
            transform: 'translateZ(35px)',
          }}
        >
          <FileText
            className="
              h-8
              w-8
              text-blue-600
              transition-transform
              duration-500
              group-hover:scale-110
            "
          />
        </div>

        <div>

          <h3 className="font-semibold text-lg text-ink">
            PDF Calibration
          </h3>

          <p className="text-sm text-ink/55">
            Documents
          </p>

        </div>

      </div>

      <p className="
        text-sm
        text-ink/55
        leading-relaxed
      ">
        Calibrate scale from PDF blueprints
        with point selection and distance
        measurement.
      </p>

    </div>

  </Glass3DCard>


  {/* =================================================
      IMAGE CALIBRATION
  ================================================= */}

  <Glass3DCard>

    <div className="p-6">

      <div className="flex items-center mb-4">

        {/* 3D ICON */}
        <div
          className="
            p-3
            bg-green-500/[0.04]
            border border-green-500/20
            rounded-xl
            mr-4

            transition-all
            duration-500
            ease-out

            group-hover:scale-110
            group-hover:-translate-y-1
            group-hover:rotate-3

            group-hover:shadow-[0_12px_30px_rgba(34,197,94,0.15)]
          "
          style={{
            transform: 'translateZ(35px)',
          }}
        >
          <Circle
            className="
              h-8
              w-8
              text-green-600

              transition-transform
              duration-500

              group-hover:scale-110
            "
          />
        </div>

        <div>

          <h3 className="font-semibold text-lg text-ink">
            Image Calibration
          </h3>

          <p className="text-sm text-ink/55">
            Blueprints
          </p>

        </div>

      </div>

      <p className="
        text-sm
        text-ink/55
        leading-relaxed
      ">
        Upload blueprint images (PNG, JPG)
        for precise scale calibration and
        measurement.
      </p>

    </div>

  </Glass3DCard>


  {/* =================================================
      CAD SUPPORT
  ================================================= */}

  <Glass3DCard>

    <div className="p-6">

      <div className="flex items-center mb-4">

        {/* 3D ICON */}
        <div
          className="
            p-3
            bg-purple-500/[0.04]
            border border-purple-500/20
            rounded-xl
            mr-4

            transition-all
            duration-500
            ease-out

            group-hover:scale-110
            group-hover:-translate-y-1
            group-hover:rotate-3

            group-hover:shadow-[0_12px_30px_rgba(168,85,247,0.15)]
          "
          style={{
            transform: 'translateZ(35px)',
          }}
        >
          <Box
            className="
              h-8
              w-8
              text-purple-600

              transition-transform
              duration-500

              group-hover:scale-110
            "
          />
        </div>

        <div>

          <h3 className="font-semibold text-lg text-ink">
            CAD Support
          </h3>

          <p className="text-sm text-ink/55">
            DXF/IFC
          </p>

        </div>

      </div>

      <p className="
        text-sm
        text-ink/55
        leading-relaxed
      ">
        View DXF and IFC files. Calibration
        coming soon for CAD formats.
      </p>

    </div>

  </Glass3DCard>

</div>
      </div>
    </div>
    </div>
  )
}