import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { useMemo } from "react";
import * as THREE from "three";

interface BorePoint {
  position: number;
  radius: number;
}

interface BoreVisualizationProps {
  boreProfile: BorePoint[];
  height?: number;
}

function BoreMesh({ boreProfile }: { boreProfile: BorePoint[] }) {
  const geometry = useMemo(() => {
    if (boreProfile.length < 2) return null;

    const segments = boreProfile.length;
    const positions: number[] = [];
    const normals: number[] = [];
    const indices: number[] = [];

    const totalLength = boreProfile[boreProfile.length - 1].position - boreProfile[0].position;
    const scale = 6 / Math.max(totalLength, 0.001);

    for (let i = 0; i < segments; i++) {
      const p = boreProfile[i];
      const y = (p.position - boreProfile[0].position) * scale - 3;
      const r = p.radius * scale * 0.5;

      const ringSegments = 32;
      for (let j = 0; j <= ringSegments; j++) {
        const theta = (j / ringSegments) * Math.PI * 2;
        const nx = Math.cos(theta);
        const nz = Math.sin(theta);

        positions.push(nx * r, y, nz * r);
        normals.push(nx, 0, nz);
      }
    }

    for (let i = 0; i < segments - 1; i++) {
      const ringSegments = 32;
      for (let j = 0; j < ringSegments; j++) {
        const a = i * (ringSegments + 1) + j;
        const b = a + ringSegments + 1;
        const c = a + 1;
        const d = b + 1;

        indices.push(a, b, c);
        indices.push(c, b, d);
      }
    }

    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geo.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
    geo.setIndex(indices);
    geo.computeVertexNormals();
    return geo;
  }, [boreProfile]);

  if (!geometry) return null;

  return (
    <mesh geometry={geometry} castShadow receiveShadow>
      <meshStandardMaterial
        color="#bc6915"
        metalness={0.4}
        roughness={0.5}
        transparent
        opacity={0.85}
        side={THREE.DoubleSide}
      />
    </mesh>
  );
}

export default function BoreVisualization({ boreProfile }: BoreVisualizationProps) {
  if (!boreProfile || boreProfile.length < 2) {
    return (
      <div className="w-full h-64 bg-neutral-900 rounded-xl border border-neutral-700 flex items-center justify-center text-neutral-500 text-sm">
        No bore profile to display
      </div>
    );
  }

  return (
    <div className="relative w-full h-64 bg-neutral-900 rounded-xl border border-neutral-700 overflow-hidden">
      <Canvas camera={{ position: [4, 2, 5], fov: 45 }} shadows>
        <ambientLight intensity={0.4} />
        <directionalLight position={[5, 8, 5]} intensity={0.8} />
        <directionalLight position={[-5, -3, -5]} intensity={0.3} />
        <pointLight position={[0, 0, 3]} intensity={0.5} color="#bc6915" />
        <BoreMesh boreProfile={boreProfile} />
        <OrbitControls enableDamping dampingFactor={0.1} rotateSpeed={0.8} />
      </Canvas>
      <div className="absolute bottom-2 left-2 text-[10px] text-neutral-500 bg-neutral-900/80 px-2 py-1 rounded">
        Drag to rotate | Scroll to zoom
      </div>
      <div className="absolute top-2 right-2 text-[10px] text-neutral-500 bg-neutral-900/80 px-2 py-1 rounded">
        {boreProfile.length} points | {(boreProfile[boreProfile.length - 1].position * 1000).toFixed(0)}mm length
      </div>
    </div>
  );
}
