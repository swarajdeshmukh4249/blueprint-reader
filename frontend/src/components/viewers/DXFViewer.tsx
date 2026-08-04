import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Stage, Layer, Line, Circle, Rect, Text as KonvaText, Arc } from 'react-konva';
import DxfParser from 'dxf-parser';
import { CalibrationManager } from '../../calibration/CalibrationManager';

interface DXFViewerProps {
  file: File;
  width?: number;
  height?: number;
}

interface DXFEntity {
  type: string;
  layer?: string;
  color?: number;
  vertices?: { x: number; y: number }[];
  position?: { x: number; y: number };
  radius?: number;
  startAngle?: number;
  endAngle?: number;
  text?: string;
  height?: number;
  width?: number;
}

interface LayerInfo {
  name: string;
  visible: boolean;
  type: 'wall' | 'furniture' | 'dimension' | 'text' | 'other';
  color: string;
  strokeWidth: number;
  lineDash?: number[];
}

// MTEXT entities carry inline formatting codes like
// {\fArial|b0|i0|c0|p34;\C7;Actual text} rather than plain text.
// This strips the formatting codes down to readable content.
function cleanMTextContent(raw: string | undefined): string {
  if (!raw) return '';
  let text = raw;

  // Remove font/format group codes: {\fArial|b0|i0|c0|p34;...}
  text = text.replace(/\{\\f[^;]*;/g, '');
  // Remove color override codes: \C7; \C255;
  text = text.replace(/\\C\d+;/g, '');
  // Remove width/height/align/tracking codes: \W1.5; \H2; \A1; \T1;
  text = text.replace(/\\[WHAT]\d*\.?\d*;/g, '');
  // Remove stacking/fraction codes \S...;
  text = text.replace(/\\S[^;]*;/g, '');
  // Paragraph/newline markers
  text = text.replace(/\\P/g, '\n');
  // Non-breaking space marker
  text = text.replace(/\\~/g, ' ');
  // Remove any leftover brace grouping
  text = text.replace(/[{}]/g, '');
  // Remove any remaining "\X;" style control sequences (single-letter code + args + semicolon)
  text = text.replace(/\\[A-Za-z][^;\\]*;/g, '');
  // Unescape literal backslash-escaped braces/backslashes
  text = text.replace(/\\([{}\\])/g, '$1');

  return text.trim();
}

export default function DXFViewer({ file, width = 800, height = 600 }: DXFViewerProps) {
  const [entities, setEntities] = useState<DXFEntity[]>([]);
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [layers, setLayers] = useState<LayerInfo[]>([]);
  const [showLayerPanel, setShowLayerPanel] = useState(true);
  const stageRef = useRef<any>(null);
  const handleCalibrationClick = useCallback((e: any) => {
    const state = CalibrationManager.getState();

    if (!state.scaleMode) return;

    const stage = e.target.getStage();
    if (!stage) return;

    const pointer = stage.getPointerPosition();
    if (!pointer) return;

    // convert screen coords -> DXF world coords using current transform
    const point = {
      x: (pointer.x - offset.x) / scale,
      y: (pointer.y - offset.y) / scale,
    };

    CalibrationManager.addPoint({
      x: point.x,
      y: point.y,
      space: 'dxf',
    });

    e.cancelBubble = true;
  }, [offset, scale]);
  const [isDragging, setIsDragging] = useState(false);
  const [lastPos, setLastPos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const loadDXF = async () => {
      try {
        setLoading(true);
        setError(null);

        const text = await file.text();
        const parser = new DxfParser();
        const dxf = parser.parseSync(text);

        if (!dxf || !dxf.entities) {
          throw new Error('Invalid DXF file or no entities found');
        }

        const entityList = dxf.entities as DXFEntity[];

        // Clean MTEXT/TEXT content of formatting codes up front so
        // every downstream consumer (render, search, export) sees
        // plain text instead of raw control sequences.
        const cleanedEntities = entityList.map(entity => {
          if ((entity.type === 'MTEXT' || entity.type === 'TEXT') && entity.text) {
            return { ...entity, text: cleanMTextContent(entity.text) };
          }
          return entity;
        });

        setEntities(cleanedEntities);

        // Extract and categorize layers
        const layerMap = extractLayers(cleanedEntities);
        setLayers(layerMap);

        // Auto-fit to view
        const bounds = calculateBounds(cleanedEntities);
        const padding = 50;
        const contentWidth = bounds.maxX - bounds.minX || 1;
        const contentHeight = bounds.maxY - bounds.minY || 1;
        const scaleX = (width - padding * 2) / contentWidth;
        const scaleY = (height - padding * 2) / contentHeight;
        const newScale = Math.min(scaleX, scaleY);

        setScale(newScale);
        setOffset({
          x: padding - bounds.minX * newScale,
          y: padding - bounds.minY * newScale,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load DXF file');
      } finally {
        setLoading(false);
      }
    };

    loadDXF();
  }, [file, width, height]);

  const extractLayers = (entities: DXFEntity[]): LayerInfo[] => {
    const layerMap = new Map<string, { count: number; types: Set<string> }>();

    entities.forEach(entity => {
      const layerName = entity.layer || '0';
      if (!layerMap.has(layerName)) {
        layerMap.set(layerName, { count: 0, types: new Set() });
      }
      const info = layerMap.get(layerName)!;
      info.count++;
      info.types.add(entity.type);
    });

    return Array.from(layerMap.entries())
      .map(([name, info]) => {
        const layerType = categorizeLayer(name, info.types);
        return {
          name,
          visible: true,
          type: layerType,
          ...getLayerStyle(layerType),
        };
      })
      .sort((a, b) => {
        const typeOrder = { wall: 0, furniture: 1, dimension: 2, text: 3, other: 4 };
        return typeOrder[a.type] - typeOrder[b.type];
      });
  };

  const categorizeLayer = (name: string, types: Set<string>): LayerInfo['type'] => {
    const upperName = name.toUpperCase();

    // Wall-related layers — checked first since structural geometry
    // should never be dashed regardless of name overlaps below.
    if (
      upperName.includes('WALL') ||
      upperName.includes('WALLS') ||
      upperName.includes('STRUCT') ||
      upperName.includes('COLUMN') ||
      upperName.includes('GRID') ||
      upperName.includes('OUTLINE')
    ) {
      return 'wall';
    }

    // Furniture-related layers
    if (
      upperName.includes('FURNITURE') ||
      upperName.includes('FURN') ||
      upperName.includes('FIXTURE') ||
      upperName.includes('EQUIP') ||
      upperName.includes('APPLIANCE')
    ) {
      return 'furniture';
    }

    // Text-related layers — checked before "dimension" because layer
    // names like "DIMENSION_TEXT" or "NOTES" should render as solid
    // text, not get swept into the dashed dimension-line bucket.
    if (
      upperName.includes('TEXT') ||
      upperName.includes('ANNOT') ||
      upperName.includes('LABEL') ||
      upperName.includes('NOTE') ||
      upperName.includes('TITLE')
    ) {
      return 'text';
    }

    // Dimension-related layers (actual dimension/leader lines + hatching)
    if (
      upperName.includes('DIM') ||
      upperName.includes('DIMENSION') ||
      upperName.includes('HATCH') ||
      upperName.includes('PATTERN') ||
      upperName.includes('CENTERLINE') ||
      upperName.includes('CENTER_LINE')
    ) {
      return 'dimension';
    }

    // Check entity types for hints (only when name gives no clue)
    if (types.has('TEXT') || types.has('MTEXT')) {
      return 'text';
    }
    if (types.has('DIMENSION') || types.has('LEADER')) {
      return 'dimension';
    }

    return 'other';
  };

  const getLayerStyle = (type: LayerInfo['type']) => {
    switch (type) {
      case 'wall':
        return { color: '#000000', strokeWidth: 2.5, lineDash: undefined };
      case 'furniture':
        return { color: '#666666', strokeWidth: 1, lineDash: undefined };
      case 'dimension':
        return { color: '#0066cc', strokeWidth: 0.5, lineDash: [5, 3] };
      case 'text':
        return { color: '#333333', strokeWidth: 0.5, lineDash: undefined };
      default:
        return { color: '#444444', strokeWidth: 1, lineDash: undefined };
    }
  };

  const calculateBounds = (entities: DXFEntity[]) => {
    let minX = Infinity,
      minY = Infinity,
      maxX = -Infinity,
      maxY = -Infinity;

    entities.forEach(entity => {
      if (entity.vertices && entity.vertices.length > 0) {
        entity.vertices.forEach(v => {
          minX = Math.min(minX, v.x);
          minY = Math.min(minY, v.y);
          maxX = Math.max(maxX, v.x);
          maxY = Math.max(maxY, v.y);
        });
      }
      if (entity.position) {
        minX = Math.min(minX, entity.position.x);
        minY = Math.min(minY, entity.position.y);
        maxX = Math.max(maxX, entity.position.x);
        maxY = Math.max(maxY, entity.position.y);
      }
      if (entity.radius && entity.position) {
        minX = Math.min(minX, entity.position.x - entity.radius);
        minY = Math.min(minY, entity.position.y - entity.radius);
        maxX = Math.max(maxX, entity.position.x + entity.radius);
        maxY = Math.max(maxY, entity.position.y + entity.radius);
      }
    });

    // Handle case where no bounds found
    if (minX === Infinity) {
      return { minX: 0, minY: 0, maxX: 100, maxY: 100 };
    }

    return { minX, minY, maxX, maxY };
  };

  // NOTE: scale/offset are no longer applied per-shape. The Layer itself
  // carries x, y, scaleX, scaleY — every shape below is drawn in raw DXF
  // coordinate space and the Layer transform handles zoom + pan for the
  // entire drawing in one shared matrix. Only stroke widths and dash
  // patterns are divided by `scale` so they stay visually constant in
  // screen pixels regardless of zoom level.
  const renderEntity = (entity: DXFEntity, index: number) => {
    const layerName = entity.layer || '0';
    const layer = layers.find(l => l.name === layerName);

    // Skip if layer is hidden
    if (!layer || !layer.visible) {
      return null;
    }

    const color = layer.color;
    const strokeWidth = layer.strokeWidth / scale;
    const dash = layer.lineDash ? layer.lineDash.map(d => d / scale) : undefined;
    const commonProps = {
      key: index,
      stroke: color,
      strokeWidth,
      dash,
    };

    switch (entity.type) {
      case 'LINE':
        if (entity.vertices && entity.vertices.length >= 2) {
          return (
            <Line
              {...commonProps}
              points={[
                entity.vertices[0].x,
                entity.vertices[0].y,
                entity.vertices[1].x,
                entity.vertices[1].y,
              ]}
            />
          );
        }
        break;

      case 'LWPOLYLINE':
      case 'POLYLINE':
        if (entity.vertices && entity.vertices.length > 0) {
          const points = entity.vertices.flatMap(v => [v.x, v.y]);
          return (
            <Line
              {...commonProps}
              points={points}
              closed={entity.type === 'LWPOLYLINE'}
            />
          );
        }
        break;

      case 'CIRCLE':
        if (entity.position && entity.radius) {
          return (
            <Circle
              {...commonProps}
              x={entity.position.x}
              y={entity.position.y}
              radius={entity.radius}
            />
          );
        }
        break;

      case 'ARC':
        if (
          entity.position &&
          entity.radius &&
          entity.startAngle !== undefined &&
          entity.endAngle !== undefined
        ) {
          return (
            <Arc
              key={index}
              x={entity.position.x}
              y={entity.position.y}
              innerRadius={entity.radius}
              outerRadius={entity.radius}
              angle={entity.endAngle - entity.startAngle}
              rotation={entity.startAngle}
              stroke={color}
              strokeWidth={1 / scale}
            />
          );
        }
        break;

      case 'TEXT':
      case 'MTEXT':
        // entity.text was already cleaned of formatting codes on load.
        // Skip rendering empty strings (codes that stripped to nothing).
        if (entity.position && entity.text && entity.text.trim().length > 0) {
          return (
            <KonvaText
              key={index}
              x={entity.position.x}
              y={entity.position.y}
              text={entity.text}
              fontSize={entity.height || 1}
              fill={color}
            />
          );
        }
        break;

      default:
        return null;
    }
    return null;
  };

  const handleWheel = useCallback(
    (e: any) => {
      e.evt.preventDefault();

      const stage = e.target.getStage();
      if (!stage) return;

      const oldScale = scale;
      const pointer = stage.getPointerPosition();
      if (!pointer) return;

      const scaleBy = 1.1;
      const newScale = e.evt.deltaY > 0 ? scale / scaleBy : scale * scaleBy;

      // Allow a wide zoom range
      const clampedScale = Math.max(0.01, Math.min(newScale, 100));

      // Zoom toward the pointer position (keeps the point under the
      // cursor visually fixed while scale changes)
      const mousePointTo = {
        x: (pointer.x - offset.x) / oldScale,
        y: (pointer.y - offset.y) / oldScale,
      };

      const newOffset = {
        x: pointer.x - mousePointTo.x * clampedScale,
        y: pointer.y - mousePointTo.y * clampedScale,
      };

      setScale(clampedScale);
      setOffset(newOffset);
    },
    [scale, offset]
  );

  const handleMouseDown = useCallback((e: any) => {
    setIsDragging(true);
    setLastPos({
      x: e.evt.clientX,
      y: e.evt.clientY,
    });
  }, []);

  const handleMouseMove = useCallback(
    (e: any) => {
      if (!isDragging) return;

      const dx = e.evt.clientX - lastPos.x;
      const dy = e.evt.clientY - lastPos.y;

      setOffset(prev => ({
        x: prev.x + dx,
        y: prev.y + dy,
      }));

      setLastPos({
        x: e.evt.clientX,
        y: e.evt.clientY,
      });
    },
    [isDragging, lastPos]
  );

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const toggleLayer = (layerName: string) => {
    setLayers(prev =>
      prev.map(l => (l.name === layerName ? { ...l, visible: !l.visible } : l))
    );
  };

  const resetView = useCallback(() => {
    if (entities.length === 0) return;

    const bounds = calculateBounds(entities);
    const padding = 50;
    const contentWidth = bounds.maxX - bounds.minX || 1;
    const contentHeight = bounds.maxY - bounds.minY || 1;
    const scaleX = (width - padding * 2) / contentWidth;
    const scaleY = (height - padding * 2) / contentHeight;
    const newScale = Math.min(scaleX, scaleY);

    setScale(newScale);
    setOffset({
      x: padding - bounds.minX * newScale,
      y: padding - bounds.minY * newScale,
    });
  }, [entities, width, height]);

  const zoomBy = useCallback(
    (factor: number) => {
      // Zoom centered on the middle of the canvas (used by +/- buttons)
      const centerX = width / 2;
      const centerY = height / 2;
      const oldScale = scale;
      const newScale = Math.max(0.01, Math.min(scale * factor, 100));

      const mousePointTo = {
        x: (centerX - offset.x) / oldScale,
        y: (centerY - offset.y) / oldScale,
      };

      const newOffset = {
        x: centerX - mousePointTo.x * newScale,
        y: centerY - mousePointTo.y * newScale,
      };

      setScale(newScale);
      setOffset(newOffset);
    },
    [scale, offset, width, height]
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full" style={{ width, height }}>
        <div className="text-gray-500">Loading DXF file...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full" style={{ width, height }}>
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="border border-gray-300 rounded-lg overflow-hidden bg-white flex">
      {/* Layer Panel */}
      {showLayerPanel && (
        <div className="w-64 border-r bg-gray-50 p-4 flex flex-col">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-800">Layers</h3>
            <button
              onClick={() => setShowLayerPanel(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              ×
            </button>
          </div>
          <div className="space-y-2 flex-1 overflow-y-auto">
            {layers.map(layer => (
              <div key={layer.name} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={layer.visible}
                  onChange={() => toggleLayer(layer.name)}
                  className="rounded border-gray-300"
                />
                <div
                  className="w-4 h-4 rounded"
                  style={{
                    backgroundColor: layer.color,
                    border: layer.type === 'dimension' ? '1px dashed #0066cc' : 'none',
                  }}
                />
                <span className="text-sm text-gray-700 flex-1 truncate">{layer.name}</span>
                <span className="text-xs text-gray-400 capitalize">{layer.type}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 pt-4 border-t">
            <button
              onClick={() => setLayers(prev => prev.map(l => ({ ...l, visible: true })))}
              className="w-full px-3 py-2 text-sm bg-gray-200 rounded hover:bg-gray-300 mb-2"
            >
              Show All
            </button>
            <button
              onClick={() => setLayers(prev => prev.map(l => ({ ...l, visible: false })))}
              className="w-full px-3 py-2 text-sm bg-gray-200 rounded hover:bg-gray-300"
            >
              Hide All
            </button>
          </div>
        </div>
      )}

      {/* Main Viewer */}
      <div className="flex-1 flex flex-col">
        <div className="flex items-center justify-between p-2 bg-gray-100 border-b">
          <div className="flex items-center gap-2">
            {!showLayerPanel && (
              <button
                onClick={() => setShowLayerPanel(true)}
                className="px-3 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
              >
                Layers
              </button>
            )}
            <button
              onClick={resetView}
              className="px-3 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
            >
              Reset View
            </button>
            <button
              onClick={() => zoomBy(1.25)}
              className="px-3 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
              aria-label="Zoom in"
            >
              +
            </button>
            <button
              onClick={() => zoomBy(1 / 1.25)}
              className="px-3 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
              aria-label="Zoom out"
            >
              −
            </button>
          </div>
          <div className="text-sm text-gray-600">
            <span className="mr-4">Scale: {(scale * 100).toFixed(0)}%</span>
            <span>Entities: {entities.length}</span>
          </div>
        </div>

        <Stage
          ref={stageRef}
          width={width}
          height={height}
          onWheel={handleWheel}
          onMouseDown={(e) => {
            const state = CalibrationManager.getState();
            // If calibration mode is active, intercept clicks
            if (state.scaleMode) {
              handleCalibrationClick(e);
              return;
            }
            handleMouseDown(e);
          }}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          draggable={false}
        >
          <Layer x={offset.x} y={offset.y} scaleX={scale} scaleY={scale}>
            {entities.map((entity, index) => renderEntity(entity, index))}
          </Layer>
        </Stage>

        <div className="p-2 bg-gray-50 border-t text-sm text-gray-500">
          Mouse wheel: zoom | Drag: pan | Layers: toggle visibility
        </div>
      </div>
    </div>
  );
}