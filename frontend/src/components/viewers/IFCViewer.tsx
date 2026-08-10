import React, { useRef, useEffect, useState, useCallback } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { IfcAPI, IFCRELDEFINESBYTYPE } from 'web-ifc';
import { CalibrationManager } from '../../calibration/CalibrationManager';

interface IFCViewerProps {
  file?: File;
  width?: number;
  height?: number;
}

interface IFCMeshEntry {
  mesh: THREE.Mesh;
  expressID: number;
}

// web-ifc ships its wasm binary separately from the JS API. In a Vite
// project the .wasm file needs to be served as a static asset — copy
// node_modules/web-ifc/web-ifc.wasm (and web-ifc-mt.wasm if present)
// into your /public folder so this path resolves at runtime.
// If you'd rather not manage that manually, see the note at the
// bottom of this file for a Vite plugin alternative.
const WASM_PATH = '/wasm/';

export default function IFCViewer({ file, width = 800, height = 600 }: IFCViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const ifcApiRef = useRef<IfcAPI | null>(null);
  const modelIDRef = useRef<number | null>(null);
  const meshesRef = useRef<IFCMeshEntry[]>([]);
  const animationFrameRef = useRef<number | null>(null);
  const raycasterRef = useRef(new THREE.Raycaster());
  const mouseRef = useRef(new THREE.Vector2());
  const calibrationGuideRef = useRef<THREE.Group | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loadProgress, setLoadProgress] = useState(0);
  const [selectedElement, setSelectedElement] = useState<{
    expressID: number;
    properties: Record<string, any>;
  } | null>(null);
  const [showWireframe, setShowWireframe] = useState(false);
  const [elementCount, setElementCount] = useState(0);

  // --- Scene setup (once per mount) ---
  useEffect(() => {
    if (!containerRef.current) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf0f0f0);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 10000);
    camera.position.set(10, 10, 10);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    rendererRef.current = renderer;
    containerRef.current.innerHTML = '';
    containerRef.current.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controlsRef.current = controls;

    // Lighting — IFC models have no embedded lights, so add a basic
    // three-point setup so geometry isn't rendered flat black.
    const ambient = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambient);
    const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.8);
    dirLight1.position.set(50, 100, 50);
    scene.add(dirLight1);
    const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.4);
    dirLight2.position.set(-50, 50, -50);
    scene.add(dirLight2);

    const grid = new THREE.GridHelper(100, 100, 0xcccccc, 0xe5e5e5);
    scene.add(grid);

    const animate = () => {
      animationFrameRef.current = requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const updateCalibrationGuide = () => {
      if (calibrationGuideRef.current) {
        scene.remove(calibrationGuideRef.current);
        calibrationGuideRef.current.traverse((object: any) => {
          object.geometry?.dispose?.();
          object.material?.dispose?.();
        });
      }

      const calibration = CalibrationManager.getState();
      const points = [calibration.pointA, calibration.pointB].filter(
        (point): point is NonNullable<typeof point> => Boolean(point && point.space === 'ifc'),
      );
      if (!points.length) {
        calibrationGuideRef.current = null;
        return;
      }

      const guide = new THREE.Group();
      const bounds = new THREE.Box3();
      meshesRef.current.forEach(({ mesh }) => bounds.expandByObject(mesh));
      const markerRadius = Math.max(bounds.getSize(new THREE.Vector3()).length() / 250, 0.01);
      const markerGeometry = new THREE.SphereGeometry(markerRadius, 16, 12);
      points.forEach((point, index) => {
        const marker = new THREE.Mesh(
          markerGeometry.clone(),
          new THREE.MeshBasicMaterial({ color: index === 0 ? 0x22c55e : 0x2563eb, depthTest: false }),
        );
        marker.position.set(point.x, point.y, point.z || 0);
        marker.renderOrder = 10;
        guide.add(marker);
      });
      if (points.length === 2) {
        const geometry = new THREE.BufferGeometry().setFromPoints(
          points.map(point => new THREE.Vector3(point.x, point.y, point.z || 0)),
        );
        const line = new THREE.Line(
          geometry,
          new THREE.LineBasicMaterial({ color: 0x2563eb, depthTest: false }),
        );
        line.renderOrder = 9;
        guide.add(line);
      }
      calibrationGuideRef.current = guide;
      scene.add(guide);
    };

    const handleClick = (event: MouseEvent) => {
      if (!containerRef.current) return;
      const rect = renderer.domElement.getBoundingClientRect();
      mouseRef.current.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouseRef.current.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycasterRef.current.setFromCamera(mouseRef.current, camera);
      const meshObjects = meshesRef.current.map(m => m.mesh);
      const intersects = raycasterRef.current.intersectObjects(meshObjects, false);

      if (CalibrationManager.getState().scaleMode) {
        if (intersects.length > 0) {
          const point = intersects[0].point;
          CalibrationManager.addPoint({ x: point.x, y: point.y, z: point.z, space: 'ifc' });
          updateCalibrationGuide();
        }
        return;
      }

      if (intersects.length > 0) {
        const hit = meshesRef.current.find(m => m.mesh === intersects[0].object);
        if (hit) {
          void inspectElement(hit.expressID);
        }
      } else {
        setSelectedElement(null);
      }
    };
    renderer.domElement.addEventListener('click', handleClick);
    const unsubscribeCalibration = CalibrationManager.subscribe(updateCalibrationGuide);

    return () => {
      renderer.domElement.removeEventListener('click', handleClick);
      unsubscribeCalibration();
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      controls.dispose();
      renderer.dispose();
      meshesRef.current.forEach(({ mesh }) => {
        mesh.geometry.dispose();
        if (Array.isArray(mesh.material)) {
          mesh.material.forEach(m => m.dispose());
        } else {
          mesh.material.dispose();
        }
      });
      meshesRef.current = [];
      if (calibrationGuideRef.current) scene.remove(calibrationGuideRef.current);
      calibrationGuideRef.current = null;
    };
    // Intentionally only re-run scene setup if the canvas dimensions change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [width, height]);

  // --- IFC loading (per file change) ---
  useEffect(() => {
    if (!file) {
      setLoading(false);
      return;
    }

    let cancelled = false;

    const loadIFC = async () => {
      try {
        setLoading(true);
        setError(null);
        setLoadProgress(0);
        setSelectedElement(null);

        const buffer = await file.arrayBuffer();
        const data = new Uint8Array(buffer);

        const ifcApi = new IfcAPI();
        ifcApi.SetWasmPath(WASM_PATH);
        await ifcApi.Init();
        if (cancelled) return;
        ifcApiRef.current = ifcApi;

        const modelID = ifcApi.OpenModel(data);
        modelIDRef.current = modelID;

        const scene = sceneRef.current;
        if (!scene) return;

        // Clear any previously loaded model
        meshesRef.current.forEach(({ mesh }) => {
          scene.remove(mesh);
          mesh.geometry.dispose();
        });
        meshesRef.current = [];

        // web-ifc streams meshes per IFC product. Each callback gives
        // one flattened mesh (color-coded sub-geometries already
        // merged) representing a single building element.
        let processed = 0;
        const group = new THREE.Group();

        ifcApi.StreamAllMeshes(modelID, (ifcMesh: any) => {
          const placedGeometries = ifcMesh.geometries;
          const elementMaterials: THREE.Material[] = [];
          const geometry = new THREE.BufferGeometry();
          const positions: number[] = [];
          const normals: number[] = [];
          const indices: number[] = [];
          let indexOffset = 0;

          for (let i = 0; i < placedGeometries.size(); i++) {
            const placedGeometry = placedGeometries.get(i);
            const geom = ifcApi.GetGeometry(modelID, placedGeometry.geometryExpressID);

            const vertexData = ifcApi.GetVertexArray(
              geom.GetVertexData(),
              geom.GetVertexDataSize()
            );
            const indexData = ifcApi.GetIndexArray(
              geom.GetIndexData(),
              geom.GetIndexDataSize()
            );

            // web-ifc vertex format: [x,y,z, nx,ny,nz] interleaved
            const matrix = new THREE.Matrix4().fromArray(placedGeometry.flatTransformation);
            for (let v = 0; v < vertexData.length; v += 6) {
              const pos = new THREE.Vector3(vertexData[v], vertexData[v + 1], vertexData[v + 2]);
              pos.applyMatrix4(matrix);
              positions.push(pos.x, pos.y, pos.z);

              const norm = new THREE.Vector3(vertexData[v + 3], vertexData[v + 4], vertexData[v + 5]);
              const normalMatrix = new THREE.Matrix3().getNormalMatrix(matrix);
              norm.applyMatrix3(normalMatrix).normalize();
              normals.push(norm.x, norm.y, norm.z);
            }
            for (let idx = 0; idx < indexData.length; idx++) {
              indices.push(indexData[idx] + indexOffset);
            }
            indexOffset += vertexData.length / 6;

            const c = placedGeometry.color;
            elementMaterials.push(
              new THREE.MeshStandardMaterial({
                color: new THREE.Color(c.x, c.y, c.z),
                opacity: c.w,
                transparent: c.w < 1,
                side: THREE.DoubleSide,
                roughness: 0.7,
                metalness: 0.05,
              })
            );

            geom.delete();
          }

          if (positions.length === 0) return;

          geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
          geometry.setAttribute('normal', new THREE.Float32BufferAttribute(normals, 3));
          geometry.setIndex(indices);

          // Use the first material as representative; mixed-material
          // elements are uncommon enough for a BOQ-focused viewer that
          // this keeps the renderer simple. Refine later if needed.
          const material = elementMaterials[0] || new THREE.MeshStandardMaterial({ color: 0x999999 });
          const mesh = new THREE.Mesh(geometry, material);
          mesh.userData.expressID = ifcMesh.expressID;

          group.add(mesh);
          meshesRef.current.push({ mesh, expressID: ifcMesh.expressID });

          processed++;
          setLoadProgress(processed);
        });

        scene.add(group);
        setElementCount(meshesRef.current.length);

        // Frame the camera to fit the loaded model
        const box = new THREE.Box3().setFromObject(group);
        if (!box.isEmpty()) {
          const size = box.getSize(new THREE.Vector3());
          const center = box.getCenter(new THREE.Vector3());
          const maxDim = Math.max(size.x, size.y, size.z) || 1;
          const camera = cameraRef.current!;
          const controls = controlsRef.current!;
          const distance = maxDim * 1.8;

          camera.position.set(
            center.x + distance,
            center.y + distance * 0.7,
            center.z + distance
          );
          camera.near = maxDim / 1000;
          camera.far = maxDim * 50;
          camera.updateProjectionMatrix();
          controls.target.copy(center);
          controls.update();
        }

        if (!cancelled) setLoading(false);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load IFC file');
          setLoading(false);
        }
      }
    };

    loadIFC();

    return () => {
      cancelled = true;
      if (modelIDRef.current !== null && ifcApiRef.current) {
        try {
          ifcApiRef.current.CloseModel(modelIDRef.current);
        } catch {
          // model already closed
        }
      }
    };
  }, [file]);

  const inspectElement = useCallback(async (expressID: number) => {
    const ifcApi = ifcApiRef.current;
    const modelID = modelIDRef.current;
    if (!ifcApi || modelID === null) return;

    try {
      const props = await ifcApi.properties.getItemProperties(modelID, expressID, true);
      setSelectedElement({ expressID, properties: props });

      // Highlight: tint the selected mesh, restore others
      meshesRef.current.forEach(({ mesh, expressID: id }) => {
        const mat = mesh.material as THREE.MeshStandardMaterial;
        if (id === expressID) {
          mat.emissive = new THREE.Color(0xff8800);
          mat.emissiveIntensity = 0.4;
        } else {
          mat.emissive = new THREE.Color(0x000000);
          mat.emissiveIntensity = 0;
        }
      });
    } catch {
      setSelectedElement({ expressID, properties: {} });
    }
  }, []);

  const resetCamera = useCallback(() => {
    const scene = sceneRef.current;
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    if (!scene || !camera || !controls) return;

    const meshGroup = meshesRef.current.map(m => m.mesh);
    if (meshGroup.length === 0) return;

    const box = new THREE.Box3();
    meshGroup.forEach(m => box.expandByObject(m));
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z) || 1;
    const distance = maxDim * 1.8;

    camera.position.set(center.x + distance, center.y + distance * 0.7, center.z + distance);
    controls.target.copy(center);
    controls.update();
  }, []);

  const toggleWireframe = useCallback(() => {
    setShowWireframe(prev => {
      const next = !prev;
      meshesRef.current.forEach(({ mesh }) => {
        const mat = mesh.material as THREE.MeshStandardMaterial;
        mat.wireframe = next;
      });
      return next;
    });
  }, []);

  if (!file) {
    return (
      <div
        className="flex items-center justify-center bg-gray-50 text-gray-400 text-sm"
        style={{ width, height }}
      >
        No IFC file loaded
      </div>
    );
  }

  return (
    <div className="border border-gray-300 rounded-lg overflow-hidden bg-white" style={{ width }}>
      <div className="flex items-center justify-between p-2 bg-gray-100 border-b">
        <div className="flex items-center gap-2">
          <button
            onClick={resetCamera}
            className="px-3 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300"
          >
            Reset View
          </button>
          <button
            onClick={toggleWireframe}
            className={`px-3 py-1 text-sm rounded hover:bg-gray-300 ${
              showWireframe ? 'bg-gray-400 text-white' : 'bg-gray-200'
            }`}
          >
            Wireframe
          </button>
        </div>
        <div className="text-sm text-gray-600">
          {loading ? `Loading… ${loadProgress} elements` : `Elements: ${elementCount}`}
        </div>
      </div>

      <div style={{ width, height, position: 'relative' }}>
        <div ref={containerRef} style={{ width, height }} />

        {loading && (
          <div
            className="absolute inset-0 flex items-center justify-center bg-white bg-opacity-80"
          >
            <div className="text-gray-500 text-sm">
              Parsing IFC model… {loadProgress > 0 ? `${loadProgress} elements processed` : ''}
            </div>
          </div>
        )}

        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-white">
            <div className="text-red-500 text-sm px-4 text-center">Error: {error}</div>
          </div>
        )}

        {selectedElement && (
          <div className="absolute top-2 right-2 w-72 max-h-80 overflow-y-auto bg-white border border-gray-300 rounded-lg shadow-lg p-3 text-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-gray-800">
                {selectedElement.properties?.Name?.value ||
                  selectedElement.properties?.type ||
                  `Element #${selectedElement.expressID}`}
              </span>
              <button
                onClick={() => setSelectedElement(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>
            <div className="space-y-1 text-xs text-gray-600">
              <div>
                <span className="font-medium">Express ID:</span> {selectedElement.expressID}
              </div>
              {selectedElement.properties?.GlobalId?.value && (
                <div className="truncate">
                  <span className="font-medium">GUID:</span>{' '}
                  {selectedElement.properties.GlobalId.value}
                </div>
              )}
              {selectedElement.properties?.ObjectType?.value && (
                <div>
                  <span className="font-medium">Type:</span>{' '}
                  {selectedElement.properties.ObjectType.value}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="p-2 bg-gray-50 border-t text-sm text-gray-500">
        Left-drag: orbit | Right-drag: pan | Scroll: zoom | Click element: inspect properties
      </div>
    </div>
  );
}

/**
 * SETUP NOTE — web-ifc WASM file:
 *
 * web-ifc ships its parsing engine as a .wasm binary, separate from the
 * JS API you import. Vite does not automatically serve files from
 * node_modules as static assets, so you have two options:
 *
 * Option A (simplest): copy the wasm file into /public at build time.
 *   In package.json:
 *     "postinstall": "mkdir -p public/wasm && cp node_modules/web-ifc/web-ifc.wasm public/wasm/ && cp node_modules/web-ifc/web-ifc-mt.wasm public/wasm/ 2>/dev/null || true"
 *   This matches the WASM_PATH = '/wasm/' constant above.
 *
 * Option B: use vite-plugin-static-copy to copy it automatically on
 *   every build instead of relying on postinstall:
 *     import { viteStaticCopy } from 'vite-plugin-static-copy';
 *     // in vite.config.ts plugins array:
 *     viteStaticCopy({
 *       targets: [{ src: 'node_modules/web-ifc/*.wasm', dest: 'wasm' }]
 *     })
 *
 * Either way, after building, /wasm/web-ifc.wasm must be reachable at
 * https://yourapp.com/wasm/web-ifc.wasm in production (Vercel serves
 * /public contents at the root automatically, so no extra config needed
 * once the file is actually in /public/wasm/).
 */
