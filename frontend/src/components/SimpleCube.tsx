import { Canvas, useFrame } from '@react-three/fiber';
import { useRef } from 'react';
import * as THREE from 'three';

function RotatingCube() {
    const meshRef = useRef<THREE.Mesh>(null);
    useFrame(() => {
        if (meshRef.current) {
            meshRef.current.rotation.x += 0.01;
            meshRef.current.rotation.y += 0.01;
        }
    });
    return (
        <mesh ref={meshRef} scale={1.5}>
            <boxGeometry args={[1, 1, 1]} />
            <meshStandardMaterial color="#00D4FF" />
        </mesh>
    );
}

export default function SimpleCube() {
    return (
        <Canvas camera={{ position: [2, 2, 5] as [number, number, number] }} style={{ height: '200px', width: '200px' }}>            <ambientLight intensity={0.5} />
            <directionalLight position={[5, 5, 5]} intensity={0.8} />
            <RotatingCube />
        </Canvas>
    );
}
