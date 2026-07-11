import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { STLLoader } from "three/addons/loaders/STLLoader.js";

interface STLViewerProps {
  file?: File | null;
  url?: string;
}

function STLScene({ geometry }: { geometry: THREE.BufferGeometry }) {
  const ref = useRef<THREE.Mesh>(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.geometry.computeVertexNormals();
    }
  }, [geometry]);

  return (
    <>
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 5]} intensity={1} />
      <directionalLight position={[-10, -5, -5]} intensity={0.3} />
      <mesh ref={ref} geometry={geometry} castShadow receiveShadow>
        <meshStandardMaterial
          color="#bc6915"
          metalness={0.3}
          roughness={0.6}
        />
      </mesh>
      <OrbitControls enableDamping dampingFactor={0.1} rotateSpeed={0.8} />
    </>
  );
}

export default function STLViewer({ file, url }: STLViewerProps) {
  const [geometry, setGeometry] = useState<THREE.BufferGeometry | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setGeometry(null);

    const loadSTL = async (data: ArrayBuffer) => {
      try {
        const loader = new STLLoader();
        const result = loader.parse(data);
        if (result instanceof THREE.BufferGeometry) {
          result.computeBoundingBox();
          const box = result.boundingBox!;
          const center = new THREE.Vector3();
          box.getCenter(center);
          result.translate(-center.x, -center.y, -center.z);
          const size = new THREE.Vector3();
          box.getSize(size);
          const maxDim = Math.max(size.x, size.y, size.z);
          const scale = 4 / maxDim;
          result.scale(scale, scale, scale);
          setGeometry(result);
        }
        setLoading(false);
      } catch {
        setError("Failed to parse STL data");
        setLoading(false);
      }
    };

    if (file) {
      file
        .arrayBuffer()
        .then(loadSTL)
        .catch(() => {
          setError("Failed to read file");
          setLoading(false);
        });
    } else if (url) {
      fetch(url)
        .then((r) => r.arrayBuffer())
        .then(loadSTL)
        .catch(() => {
          setError("Failed to fetch STL");
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, [file, url]);

  return (
    <div className="relative w-full h-80 bg-neutral-900 rounded-xl border border-neutral-700 overflow-hidden">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center text-neutral-400 text-sm">
          Loading 3D model...
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center text-red-400 text-sm">
          {error}
        </div>
      )}
      {!file && !url && !error && (
        <div className="absolute inset-0 flex items-center justify-center text-neutral-500 text-sm text-center px-4">
          Generate or load an instrument to preview its 3D model
        </div>
      )}
      {geometry && (
        <Canvas camera={{ position: [0, 0, 6], fov: 50 }} shadows>
          <STLScene geometry={geometry} />
        </Canvas>
      )}
    </div>
  );
}
