import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { useEffect, useRef, useState, useMemo } from "react";
import * as THREE from "three";
import { STLLoader } from "three/addons/loaders/STLLoader.js";

interface STLViewerProps {
  file?: File | null;
  url?: string;
}

/** Fallback demo bore shown when no STL file is loaded. */
function DemoBore() {
  const geometry = useMemo(() => {
    return new THREE.CylinderGeometry(1.1, 0.9, 6, 64);
  }, []);

  const ref = useRef<THREE.Mesh>(null);

  return (
    <>
      <ambientLight intensity={0.4} />
      <directionalLight position={[5, 8, 5]} intensity={0.8} />
      <directionalLight position={[-5, -3, -5]} intensity={0.3} />
      <pointLight position={[0, 0, 3]} intensity={0.5} color="#bc6915" />
      <mesh ref={ref} geometry={geometry} rotation={[Math.PI / 2, 0, 0]}>
        <meshStandardMaterial
          color="#bc6915"
          metalness={0.4}
          roughness={0.5}
          transparent
          opacity={0.85}
          side={THREE.DoubleSide}
        />
      </mesh>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0, 0.9, 64]} />
        <meshStandardMaterial color="#1a1a1a" side={THREE.DoubleSide} />
      </mesh>
      <OrbitControls enableDamping dampingFactor={0.1} rotateSpeed={0.8} />
    </>
  );
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
        <meshStandardMaterial color="#bc6915" metalness={0.3} roughness={0.6} />
      </mesh>
      <OrbitControls enableDamping dampingFactor={0.1} rotateSpeed={0.8} />
    </>
  );
}

export default function STLViewer({ file, url }: STLViewerProps) {
  const [geometry, setGeometry] = useState<THREE.BufferGeometry | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!file && !url) {
      setLoading(false);
      return;
    }
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
      file.arrayBuffer().then(loadSTL).catch(() => {
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
    }
  }, [file, url]);

  return (
    <div className="relative w-full h-80 bg-neutral-900 rounded-xl border border-neutral-700 overflow-hidden">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center text-neutral-400 text-sm z-10">
          Loading 3D model...
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center text-red-400 text-sm z-10">
          {error}
        </div>
      )}
      {geometry ? (
        <Canvas camera={{ position: [0, 0, 6], fov: 50 }} shadows>
          <STLScene geometry={geometry} />
        </Canvas>
      ) : !loading && !error ? (
        <Canvas camera={{ position: [4, 2, 5], fov: 45 }} shadows>
          <DemoBore />
        </Canvas>
      ) : null}
      {geometry && (
        <div className="absolute bottom-2 left-2 text-[10px] text-neutral-500 bg-neutral-900/80 px-2 py-1 rounded">
          Drag to rotate · Scroll to zoom
        </div>
      )}
    </div>
  );
}
