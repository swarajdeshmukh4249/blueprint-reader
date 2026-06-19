import React, { useRef, useEffect, useState, useCallback } from 'react';
import { Stage, Layer, Line, Circle, Rect, Text as KonvaText, Arc } from 'react-konva';
import DxfParser from 'dxf-parser';

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

export default function DXFViewer({ file, width = 800, height = 600 }: DXFViewerProps) {
  const [entities, setEntities] = useState<DXFEntity[]>([]);
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [layers, setLayers] = useState<LayerInfo[]>([]);
  const [showLayerPanel, setShowLayerPanel] = useState(true);
  const stageRef = useRef<any>(null);
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
        setEntities(entityList);
        
        // Extract and categorize layers
        const layerMap = extractLayers(entityList);
        setLayers(layerMap);
        
        // Auto-fit to view
        if (stageRef.current) {
          const bounds = calculateBounds(entityList);
          const padding = 50;
          const contentWidth = bounds.maxX - bounds.minX || 1;
          const contentHeight = bounds.maxY - bounds.minY || 1;
          const scaleX = (width - padding * 2) / contentWidth;
          const scaleY = (height - padding * 2) / contentHeight;
          const newScale = Math.min(scaleX, scaleY);
          
          setScale(newScale);
          setOffset({
            x: padding - bounds.minX * newScale,
            y: padding - bounds.minY * newScale
          });
        }
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
    
    return Array.from(layerMap.entries()).map(([name, info]) => {
      const layerType = categorizeLayer(name, info.types);
      return {
        name,
        visible: true,
        type: layerType,
        ...getLayerStyle(layerType)
      };
    }).sort((a, b) => {
      const typeOrder = { wall: 0, furniture: 1, dimension: 2, text: 3, other: 4 };
      return typeOrder[a.type] - typeOrder[b.type];
    });
  };
  
  const categorizeLayer = (name: string, types: Set<string>): LayerInfo['type'] => {
    const upperName = name.toUpperCase();
    
    // Wall-related layers
    if (upperName.includes('WALL') || upperName.includes('WALLS') || 
        upperName.includes('STRUCT') || upperName.includes('COLUMN')) {
      return 'wall';
    }
    
    // Furniture-related layers
    if (upperName.includes('FURNITURE') || upperName.includes('FURN') ||
        upperName.includes('FIXTURE') || upperName.includes('EQUIP') ||
        upperName.includes('APPLIANCE')) {
      return 'furniture';
    }
    
    // Dimension-related layers
    if (upperName.includes('DIM') || upperName.includes('DIMENSION') ||
        upperName.includes('HATCH') || upperName.includes('PATTERN')) {
      return 'dimension';
    }
    
    // Text-related layers
    if (upperName.includes('TEXT') || upperName.includes('ANNOT') ||
        upperName.includes('LABEL') || upperName.includes('NOTE')) {
      return 'text';
    }
    
    // Check entity types for hints
    if (types.has('DIMENSION') || types.has('LEADER')) {
      return 'dimension';
    }
    if (types.has('TEXT') || types.has('MTEXT')) {
      return 'text';
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
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    
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

  const renderEntity = (entity: DXFEntity, index: number) => {
    const layerName = entity.layer || '0';
    const layer = layers.find(l => l.name === layerName);
    
    // Skip if layer is hidden
    if (!layer || !layer.visible) {
      return null;
    }
    
    const color = layer.color;
    const strokeWidth = layer.strokeWidth / scale;
    const commonProps = {
      key: index,
      stroke: color,
      strokeWidth,
      scaleX: scale,
      scaleY: scale,
      dash: layer.lineDash,
    };

    switch (entity.type) {
      case 'LINE':
        if (entity.vertices && entity.vertices.length >= 2) {
          return (
            <Line
              {...commonProps}
              points={[
                entity.vertices[0].x, entity.vertices[0].y,
                entity.vertices[1].x, entity.vertices[1].y
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
        if (entity.position && entity.radius && entity.startAngle !== undefined && entity.endAngle !== undefined) {
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
              scaleX={scale}
              scaleY={scale}
            />
          );
        }
        break;

      case 'TEXT':
      case 'MTEXT':
        if (entity.position && entity.text) {
          return (
            <KonvaText
              key={index}
              x={entity.position.x}
              y={entity.position.y}
              text={entity.text}
              fontSize={(entity.height || 1) * scale}
              fill={color}
              scaleX={1}
              scaleY={1}
            />
          );
        }
        break;

      default:
        return null;
    }
    return null;
  };


  const handleWheel = useCallback((e: any) => {
    e.evt.preventDefault();
    
    const stage = e.target.getStage();
    if (!stage) return;
    
    const oldScale = scale;
    const pointer = stage.getPointerPosition();
    if (!pointer) return;
    
    const scaleBy = 1.1;
    const newScale = e.evt.deltaY > 0 ? scale / scaleBy : scale * scaleBy;
    
    // Remove the hardcoded 10x limit - allow much higher zoom
    const clampedScale = Math.max(0.01, Math.min(newScale, 100));
    
    // Calculate new offset to zoom toward pointer
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
  }, [scale, offset]);
  
  const handleMouseDown = useCallback((e: any) => {
    setIsDragging(true);
    setLastPos({
      x: e.evt.clientX,
      y: e.evt.clientY,
    });
  }, []);
  
  const handleMouseMove = useCallback((e: any) => {
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
  }, [isDragging, lastPos]);
  
  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);
  
  const toggleLayer = (layerName: string) => {
    setLayers(prev => prev.map(l => 
      l.name === layerName ? { ...l, visible: !l.visible } : l
    ));
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
      y: padding - bounds.minY * newScale
    });
  }, [entities, width, height]);

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
                    border: layer.type === 'dimension' ? '1px dashed #0066cc' : 'none'
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
          </div>
          <div className="text-sm text-gray-600">
            <span className="mr-4">Scale: {scale.toFixed(2)}x</span>
            <span>Entities: {entities.length}</span>
          </div>
        </div>
        
        <Stage
          ref={stageRef}
          width={width}
          height={height}
          onWheel={handleWheel}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          draggable={false}
        >
          <Layer offsetX={offset.x} offsetY={offset.y}>
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
