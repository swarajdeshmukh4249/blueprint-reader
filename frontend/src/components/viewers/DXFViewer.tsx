import React, { useRef, useEffect, useState } from 'react';
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

export default function DXFViewer({ file, width = 800, height = 600 }: DXFViewerProps) {
  const [entities, setEntities] = useState<DXFEntity[]>([]);
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const stageRef = useRef<any>(null);

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

        setEntities(dxf.entities as DXFEntity[]);
        
        // Auto-fit to view
        if (stageRef.current) {
          const bounds = calculateBounds(dxf.entities as DXFEntity[]);
          const scaleX = width / (bounds.maxX - bounds.minX + 100);
          const scaleY = height / (bounds.maxY - bounds.minY + 100);
          const newScale = Math.min(scaleX, scaleY, 2);
          
          setScale(newScale);
          setOffset({
            x: (width - (bounds.maxX - bounds.minX) * newScale) / 2 - bounds.minX * newScale,
            y: (height - (bounds.maxY - bounds.minY) * newScale) / 2 - bounds.minY * newScale
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
    
    return { minX, minY, maxX, maxY };
  };

  const renderEntity = (entity: DXFEntity, index: number) => {
    const color = getColor(entity.color);
    const commonProps = {
      key: index,
      stroke: color,
      strokeWidth: 1 / scale,
      scaleX: scale,
      scaleY: scale,
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

  const getColor = (colorNumber?: number): string => {
    if (!colorNumber) return '#000000';
    
    // AutoCAD color index mapping
    const colors: Record<number, string> = {
      1: '#ff0000', 2: '#ffff00', 3: '#00ff00', 4: '#00ffff',
      5: '#0000ff', 6: '#ff00ff', 7: '#ffffff', 8: '#808080',
      9: '#404040',
    };
    
    return colors[colorNumber] || '#000000';
  };

  const handleWheel = (e: any) => {
    e.evt.preventDefault();
    const scaleBy = 1.1;
    const newScale = e.evt.deltaY > 0 ? scale / scaleBy : scale * scaleBy;
    setScale(Math.max(0.1, Math.min(newScale, 10)));
  };

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
    <div className="border border-gray-300 rounded-lg overflow-hidden bg-white">
      <Stage
        ref={stageRef}
        width={width}
        height={height}
        onWheel={handleWheel}
        draggable
      >
        <Layer offsetX={offset.x} offsetY={offset.y}>
          {entities.map((entity, index) => renderEntity(entity, index))}
        </Layer>
      </Stage>
      <div className="p-2 bg-gray-50 border-t text-sm text-gray-600">
        <span className="mr-4">Scale: {scale.toFixed(2)}x</span>
        <span>Entities: {entities.length}</span>
        <span className="ml-4 text-gray-400">Use mouse wheel to zoom, drag to pan</span>
      </div>
    </div>
  );
}
