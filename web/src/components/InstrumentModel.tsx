import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import * as THREE from "three";

// ── Types ────────────────────────────────────────────────────────────────

export interface BorePoint {
  position: number;
  radius: number;
}

export interface HolePoint {
  position: number;
  diameter: number;
  open: boolean;
}

export interface BellPoint {
  position: number;
  radius: number;
}

export interface MaterialConfig {
  type: "brass" | "wood" | "plastic" | "pvc" | "bamboo" | "silver";
  color: string;
  metalness: number;
  roughness: number;
}

export const MATERIALS: Record<MaterialConfig["type"], MaterialConfig> = {
  brass: { type: "brass", color: "#bc6915", metalness: 0.7, roughness: 0.3 },
  wood: { type: "wood", color: "#3d2314", metalness: 0.0, roughness: 0.8 },
  plastic: { type: "plastic", color: "#1a1a2e", metalness: 0.1, roughness: 0.5 },
  pvc: { type: "pvc", color: "#e8e8e8", metalness: 0.05, roughness: 0.4 },
  bamboo: { type: "bamboo", color: "#c4a35a", metalness: 0.0, roughness: 0.9 },
  silver: { type: "silver", color: "#c0c0c0", metalness: 0.9, roughness: 0.15 },
};

export interface InstrumentModelProps {
  boreProfile: BorePoint[];
  holes?: HolePoint[];
  bellProfile?: BellPoint[];
  material?: MaterialConfig;
  crossSection?: boolean;
  showHoles?: boolean;
  height?: number;
  autoRotate?: boolean;
}

// ── Constants ─────────────────────────────────────────────────────────────

const RING_SEGMENTS = 32;
const HALF_PI = Math.PI / 2;

// ── Bore Mesh (LatheGeometry) ────────────────────────────────────────────

function BoreMesh({
  boreProfile,
  bellProfile,
}: {
  boreProfile: BorePoint[];
  bellProfile?: BellPoint[];
  material: MaterialConfig;
}) {
  // Build combined profile with bell flare
  const geometry = useMemo(() => {
    if (boreProfile.length < 2) return null;

    // Combine bore + bell points into a single lathe profile
    const points: THREE.Vector2[] = [];
    const totalLength = boreProfile[boreProfile.length - 1].position;
    const scale = 6 / Math.max(totalLength, 0.001);

    // Normalize function
    const n = (pos: number, rad: number) => {
      const y = (pos - boreProfile[0].position) * scale - 3;
      const r = rad * scale;
      return new THREE.Vector2(r, y);
    };

    // Add bore profile points
    for (const p of boreProfile) {
      points.push(n(p.position, p.radius));
    }

    // Add bell flare if provided
    if (bellProfile && bellProfile.length > 0) {
      for (const bp of bellProfile) {
        points.push(n(bp.position, bp.radius));
      }
    }

    const geo = new THREE.LatheGeometry(points, RING_SEGMENTS);
    geo.computeVertexNormals();
    return geo;
  }, [boreProfile, bellProfile]);

  if (!geometry) return null;

  return (
    <mesh geometry={geometry} castShadow receiveShadow>
      <meshStandardMaterial
        color={material.color}
        metalness={material.metalness}
        roughness={material.roughness}
        side={THREE.DoubleSide}
      />
    </mesh>
  );
}

// ── Hole Mesh (small cylinders on bore surface) ──────────────────────────

function HoleMarkers({
  holes,
  boreProfile,
  material,
}: {
  holes: HolePoint[];
  boreProfile: BorePoint[];
  material: MaterialConfig;
}) {
  const group = useMemo(() => {
    const totalLength = boreProfile[boreProfile.length - 1].position;
    const scale = 6 / Math.max(totalLength, 0.001);

    const objs: { pos: THREE.Vector3; radius: number }[] = [];
    for (const hole of holes) {
      const y = (hole.position - boreProfile[0].position) * scale - 3;
      const r = (hole.diameter / 2) * scale * 0.5;

      // Find bore radius at this position (interpolate)
      let boreR = 0;
      for (let i = 0; i < boreProfile.length - 1; i++) {
        if (
          hole.position >= boreProfile[i].position &&
          hole.position <= boreProfile[i + 1].position
        ) {
          const t =
            (hole.position - boreProfile[i].position) /
            (boreProfile[i + 1].position - boreProfile[i].position);
          boreR = (boreProfile[i].radius + (boreProfile[i + 1].radius - boreProfile[i].radius) * t) * scale;
          break;
        }
      }
      if (boreR === 0) boreR = boreProfile[boreProfile.length - 1].radius * scale;

      objs.push({
        pos: new THREE.Vector3(boreR, y, 0),
        radius: Math.max(r, 0.01),
      });
    }
    return objs;
  }, [holes, boreProfile]);

  return (
    <group>
      {group.map((g, i) => (
        <mesh key={i} position={g.pos} rotation={[0, 0, HALF_PI]}>
          <cylinderGeometry args={[g.radius, g.radius, g.radius * 0.5, 12]} />
          <meshStandardMaterial
            color={
              holes[i]?.open
                ? "#ef4444"
                : "#22c55e"
            }
            emissive={
              holes[i]?.open
                ? "#ef4444"
                : "#22c55e"
            }
            emissiveIntensity={0.3}
            metalness={material.metalness}
            roughness={material.roughness}
          />
        </mesh>
      ))}
    </group>
  );
}

// ── Cross-section plane ──────────────────────────────────────────────────

function CrossSectionPlane() {
  const meshRef = useRef<THREE.Mesh>(null!);
  useFrame(() => {
    // Keep plane always visible
  });

  return (
    <mesh ref={meshRef} rotation={[0, 0, 0]} position={[0, 0, 0]}>
      <planeGeometry args={[8, 8]} />
      <meshBasicMaterial
        color="#1a1a2e"
        transparent
        opacity={0.3}
        side={THREE.DoubleSide}
        depthWrite={false}
      />
    </mesh>
  );
}

// ── Ground grid ──────────────────────────────────────────────────────────

function GroundGrid() {
  return (
    <gridHelper
      args={[12, 12, "#333333", "#222222"]}
      position={[0, -3.5, 0]}
    />
  );
}

// ── Main Component ───────────────────────────────────────────────────────

export default function InstrumentModel({
  boreProfile,
  holes,
  bellProfile,
  material = MATERIALS.brass,
  crossSection = false,
  showHoles = true,
  height = 400,
  autoRotate = false,
}: InstrumentModelProps) {
  if (!boreProfile || boreProfile.length < 2) {
    return (
      <div
        className="w-full bg-neutral-900 rounded-xl border border-neutral-700 flex items-center justify-center text-neutral-500 text-sm"
        style={{ height }}
      >
        No bore profile to display
      </div>
    );
  }

  return (
    <div
      className="relative w-full bg-neutral-900 rounded-xl border border-neutral-700 overflow-hidden"
      style={{ height }}
    >
      <Canvas
        camera={{ position: [4, 1, 5], fov: 40 }}
        shadows
        gl={{ antialias: true }}
      >
        <ambientLight intensity={0.3} />
        <directionalLight position={[5, 8, 5]} intensity={0.6} />
        <directionalLight position={[-5, -3, -5]} intensity={0.2} />
        <pointLight position={[0, 0, 3]} intensity={0.4} color={material.color} />

        <BoreMesh
          boreProfile={boreProfile}
          bellProfile={bellProfile}
          material={material}
        />

        {showHoles && holes && holes.length > 0 && (
          <HoleMarkers
            holes={holes}
            boreProfile={boreProfile}
            material={material}
          />
        )}

        {crossSection && <CrossSectionPlane />}

        <GroundGrid />

        <OrbitControls
          enableDamping
          dampingFactor={0.1}
          rotateSpeed={0.8}
          autoRotate={autoRotate}
          autoRotateSpeed={2}
          minDistance={2}
          maxDistance={15}
        />
      </Canvas>

      {/* Overlay info */}
      <div className="absolute bottom-2 left-2 text-[10px] text-neutral-500 bg-neutral-900/80 px-2 py-1 rounded">
        Drag to rotate | Scroll to zoom{autoRotate ? " | Auto-rotate" : ""}
      </div>
      <div className="absolute top-2 right-2 text-[10px] text-neutral-500 bg-neutral-900/80 px-2 py-1 rounded flex items-center gap-2">
        <span
          className="w-2 h-2 rounded-full inline-block"
          style={{ backgroundColor: material.color }}
        />
        <span>{boreProfile.length} pts</span>
        <span>
          {(boreProfile[boreProfile.length - 1].position * 1000).toFixed(0)}mm
        </span>
        {holes && <span>{holes.length} holes</span>}
      </div>
    </div>
  );
}
