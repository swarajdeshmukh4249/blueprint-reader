import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as pdfjsLib from 'pdfjs-dist';


// pdfjs-dist needs its worker script available at a URL the browser can
// fetch. Importing it with Vite's `?url` suffix bundles the worker file
// and gives back a hashed, content-addressed URL — no manual /public
// copying needed (unlike web-ifc's wasm file).
import pdfWorkerSrc from 'pdfjs-dist/build/pdf.worker.mjs?url';

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorkerSrc;

interface PDFViewerProps {
  file?: File;
  width?: number;
  height?: number;
}

interface TextMatch {
  pageNumber: number;
  snippet: string;
}

export default function PDFViewer({ file, width = 800, height = 600 }: PDFViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const renderTaskRef = useRef<any>(null);
  const pdfDocRef = useRef<pdfjsLib.PDFDocumentProxy | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [numPages, setNumPages] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [scale, setScale] = useState(1);
  const [fitMode, setFitMode] = useState<'width' | 'page' | 'custom'>('width');
  const [rotation, setRotation] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<TextMatch[]>([]);
  const [searching, setSearching] = useState(false);

  // --- Load document when file changes ---
  useEffect(() => {
    if (!file) {
      setLoading(false);
      return;
    }

    let cancelled = false;

    const loadPDF = async () => {
      try {
        setLoading(true);
        setError(null);
        setSearchResults([]);
        setSearchQuery('');

        const buffer = await file.arrayBuffer();
        const pdf = await pdfjsLib.getDocument({ data: buffer }).promise;
        if (cancelled) return;

        pdfDocRef.current = pdf;
        setNumPages(pdf.numPages);
        setCurrentPage(1);
        setLoading(false);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load PDF file');
          setLoading(false);
        }
      }
    };

    loadPDF();

    return () => {
      cancelled = true;

      if (pdfDocRef.current) {
        (pdfDocRef.current as any)?.destroy?.();
        pdfDocRef.current?.cleanup?.();
      }

      pdfDocRef.current = null;
    };
  }, [file]);

  // --- Render current page whenever page/scale/rotation/fitMode changes ---
  const renderPage = useCallback(async () => {
    const pdf = pdfDocRef.current;
    const canvas = canvasRef.current;
    if (!pdf || !canvas) return;

    // Cancel any in-flight render before starting a new one — rapid
    // page/zoom changes otherwise queue up redundant renders that
    // fight over the same canvas.
    if (renderTaskRef.current) {
      renderTaskRef.current.cancel();
    }

    try {
      const page = await pdf.getPage(currentPage);
      const baseViewport = page.getViewport({ scale: 1, rotation });

      let effectiveScale = scale;
      if (fitMode === 'width') {
        effectiveScale = (width - 32) / baseViewport.width;
      } else if (fitMode === 'page') {
        effectiveScale = Math.min(
          (width - 32) / baseViewport.width,
          (height - 32) / baseViewport.height
        );
      }

      const viewport = page.getViewport({ scale: effectiveScale, rotation });
      canvas.width = viewport.width;
      canvas.height = viewport.height;

      const context = canvas.getContext('2d');
      if (!context) return;

      const renderTask = page.render({
        canvas,
        canvasContext: context,
        viewport,
      } as any);
      renderTaskRef.current = renderTask;
      await renderTask.promise;
      renderTaskRef.current = null;

      if (fitMode !== 'custom') {
        setScale(effectiveScale);
      }
    } catch (err: any) {
      // RenderingCancelledException is expected when we cancel an
      // in-flight render on rapid navigation — not a real error.
      if (err?.name !== 'RenderingCancelledException') {
        setError(err instanceof Error ? err.message : 'Failed to render page');
      }
    }
  }, [currentPage, scale, rotation, fitMode, width, height]);

  useEffect(() => {
    if (!loading && pdfDocRef.current) {
      renderPage();
    }
  }, [loading, renderPage]);

  const goToPage = useCallback(
    (page: number) => {
      const clamped = Math.max(1, Math.min(page, numPages));
      setCurrentPage(clamped);
    },
    [numPages]
  );

  const zoomIn = useCallback(() => {
    setFitMode('custom');
    setScale(prev => Math.min(prev * 1.25, 8));
  }, []);

  const zoomOut = useCallback(() => {
    setFitMode('custom');
    setScale(prev => Math.max(prev / 1.25, 0.1));
  }, []);

  const fitToWidth = useCallback(() => setFitMode('width'), []);
  const fitToPage = useCallback(() => setFitMode('page'), []);

  const rotate = useCallback(() => {
    setRotation(prev => (prev + 90) % 360);
  }, []);

  // --- Text search across all pages ---
  const runSearch = useCallback(async () => {
    const pdf = pdfDocRef.current;
    if (!pdf || !searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    const query = searchQuery.toLowerCase();
    const matches: TextMatch[] = [];

    try {
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();
        const pageText = textContent.items
          .map((item: any) => ('str' in item ? item.str : ''))
          .join(' ');

        const lowerText = pageText.toLowerCase();
        let idx = lowerText.indexOf(query);
        if (idx !== -1) {
          const start = Math.max(0, idx - 30);
          const end = Math.min(pageText.length, idx + query.length + 30);
          const snippet = (start > 0 ? '…' : '') + pageText.slice(start, end).trim() + '…';
          matches.push({ pageNumber: i, snippet });
        }
      }
    } catch (err) {
      // Search failure shouldn't block the viewer — surface nothing
      // found rather than throwing.
    }

    setSearchResults(matches);
    setSearching(false);
  }, [searchQuery]);

  const handleSearchKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === 'Enter') runSearch();
    },
    [runSearch]
  );

  if (!file) {
    return (
      <div
        className="flex items-center justify-center bg-gray-50 text-gray-400 text-sm"
        style={{ width, height }}
      >
        No PDF file loaded
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="flex items-center justify-center bg-white text-red-500 text-sm px-4 text-center"
        style={{ width, height }}
      >
        Error: {error}
      </div>
    );
  }

  return (
    <div className="border border-gray-300 rounded-lg overflow-hidden bg-white flex" style={{ width }}>
      {/* Search sidebar */}
      <div className="w-56 border-r bg-gray-50 p-3 flex flex-col" style={{ height }}>
        <div className="flex gap-1 mb-3">
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            onKeyDown={handleSearchKeyDown}
            placeholder="Search text…"
            className="flex-1 px-2 py-1 text-sm border border-gray-300 rounded"
          />
          <button
            onClick={runSearch}
            className="px-2 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
          >
            Go
          </button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-1">
          {searching && <div className="text-xs text-gray-400">Searching…</div>}
          {!searching && searchQuery && searchResults.length === 0 && (
            <div className="text-xs text-gray-400">No matches found</div>
          )}
          {searchResults.map((result, i) => (
            <button
              key={i}
              onClick={() => goToPage(result.pageNumber)}
              className="w-full text-left p-2 text-xs rounded hover:bg-gray-200 border border-gray-200"
            >
              <div className="font-medium text-gray-700 mb-0.5">Page {result.pageNumber}</div>
              <div className="text-gray-500 line-clamp-2">{result.snippet}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Main viewer */}
      <div className="flex-1 flex flex-col">
        <div className="flex items-center justify-between p-2 bg-gray-100 border-b flex-wrap gap-2">
          <div className="flex items-center gap-1">
            <button
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage <= 1}
              className="px-2 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300 disabled:opacity-40"
            >
              ‹
            </button>
            <span className="text-sm text-gray-600 px-2">
              Page{' '}
              <input
                type="number"
                value={currentPage}
                min={1}
                max={numPages}
                onChange={e => goToPage(parseInt(e.target.value) || 1)}
                className="w-12 text-center border border-gray-300 rounded px-1"
              />{' '}
              of {numPages}
            </span>
            <button
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage >= numPages}
              className="px-2 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300 disabled:opacity-40"
            >
              ›
            </button>
          </div>

          <div className="flex items-center gap-1">
            <button onClick={zoomOut} className="px-2 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300">
              −
            </button>
            <span className="text-sm text-gray-600 w-14 text-center">
              {(scale * 100).toFixed(0)}%
            </span>
            <button onClick={zoomIn} className="px-2 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300">
              +
            </button>
            <button
              onClick={fitToWidth}
              className={`px-2 py-1 text-sm rounded hover:bg-gray-300 ${
                fitMode === 'width' ? 'bg-gray-400 text-white' : 'bg-gray-200'
              }`}
            >
              Fit Width
            </button>
            <button
              onClick={fitToPage}
              className={`px-2 py-1 text-sm rounded hover:bg-gray-300 ${
                fitMode === 'page' ? 'bg-gray-400 text-white' : 'bg-gray-200'
              }`}
            >
              Fit Page
            </button>
            <button onClick={rotate} className="px-2 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300">
              ⟳
            </button>
          </div>
        </div>

        <div
          className="flex-1 overflow-auto bg-gray-200 flex items-center justify-center p-4"
          style={{ height: height - 50 }}
        >
          {loading ? (
            <div className="text-gray-500 text-sm">Loading PDF…</div>
          ) : (
            <canvas ref={canvasRef} className="shadow-md bg-white" />
          )}
        </div>
      </div>
    </div>
  );
}