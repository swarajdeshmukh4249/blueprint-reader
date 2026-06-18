import React, { useRef, useEffect, useState } from 'react';
import * as THREE from 'three';
import { IFCLoader } from 'web-ifc-three';

interface IFCViewerProps {
  file: File;
  width?: number;
  height?: number;
}

export default function IFCViewer({ file, width = 800, height = 600 }: IFCViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const loaderRef = useRef<IFCLoader | null>(null);

  useEffect(() => {
    let ifcLoader: IFCLoader | null = null;

    const initViewer = async () => {
      try {
        setLoading(true);
        setError(null);

        if (!containerRef.current) return;

        // Initialize Three.js scene
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xf0f0f0);

        // Initialize camera
        const camera = new THREE.PerspectiveCamera(
          45,
          width / height,
          0.1,
          1000
        );
        camera.position.set(10, 10, 10);
        camera.lookAt(0, 0, 0);

        // Initialize renderer
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(width, height);
        renderer.setPixelRatio(window.devicePixelRatio);
        containerRef.current.appendChild(renderer.domElement);

        // Add lights
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 20, 10);
        scene.add(directionalLight);

        // Initialize IFC loader
        ifcLoader = new IFCLoader();
        loaderRef.current = ifcLoader;

        // Load IFC file
        const arrayBuffer = await file.arrayBuffer();
        const model = await ifcLoader.parse(arrayBuffer);
        
        scene.add(model);

        // Add grid helper
        const gridHelper = new THREE.GridHelper(20, 20, 0x888888, 0xcccccc);
        scene.add(gridHelper);

        // Add orbit controls (manual implementation)
        let isDragging = false;
        let previousMousePosition = { x: 0, y: 0 };

        const onMouseDown = (e: MouseEvent) => {
          isDragging = true;
          previousMousePosition = { x: e.clientX, y: e.clientY };
        };

        const onMouseMove = (e: MouseEvent) => {
          if (!isDragging) return;

          const deltaMove = {
            x: e.clientX - previousMousePosition.x,
            y: e.clientY - previousMousePosition.y
          };

          const rotationSpeed = 0.005;
          camera.position.x = camera.position.x * Math.cos(deltaMove.x * rotationSpeed) - camera.position.z * Math.sin(deltaMove.x * rotationSpeed);
          camera.position.z = camera.position.x * Math.sin(deltaMove.x * rotationSpeed) + camera.position.z * Math.cos(deltaMove.x * rotationSpeed);
          camera.position.y += deltaMove.y * rotationSpeed;
          camera.lookAt(0, 0, 0);

          previousMousePosition = { x: e.clientX, y: e.clientY };
        };

        const onMouseUp = () => {
          isDragging = false;
        };

        const onWheel = (e: WheelEvent) => {
          e.preventDefault();
          const zoomSpeed = 0.001;
          const zoom = 1 + e.deltaY * zoomSpeed;
          camera.position.multiplyScalar(zoom);
        };

        renderer.domElement.addEventListener('mousedown', onMouseDown);
        renderer.domElement.addEventListener('mousemove', onMouseMove);
        renderer.domElement.addEventListener('mouseup', onMouseUp);
        renderer.domElement.addEventListener('wheel', onWheel);

        // Animation loop
        const animate = () => {
          requestAnimationFrame(animate);
          renderer.render(scene, camera);
        };
        animate();

        setLoading(false);

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load IFC file');
        setLoading(false);
      }
    };

    initViewer();

    return () => {
      if (containerRef.current && containerRef.current.firstChild) {
        containerRef.current.removeChild(containerRef.current.firstChild);
      }
    };
  }, [file, width, height]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full" style={{ width, height }}>
        <div className="text-gray-500">Loading IFC file...</div>
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
      <div ref={containerRef} style={{ width, height }} />
      <div className="p-2 bg-gray-50 border-t text-sm text-gray-600">
        <span className="text-gray-400">Drag to rotate, scroll to zoom</span>
      </div>
    </div>
  );
}
