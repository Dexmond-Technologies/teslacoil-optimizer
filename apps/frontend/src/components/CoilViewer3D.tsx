import { useMemo, useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

interface CoilViewer3DProps {
  priTurns: number;
  secTurns: number;
}

const CoilModel = ({ priTurns, secTurns }: CoilViewer3DProps) => {
  const secondaryRef = useRef<THREE.Mesh>(null);
  const primaryRef = useRef<THREE.Mesh>(null);
  const toploadRef = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    const time = state.clock.getElapsedTime();
    if (secondaryRef.current) {
      secondaryRef.current.rotation.y = time * 0.2;
    }
    // Rotate the primary coil slowly
    if (primaryRef.current) {
      primaryRef.current.rotation.y = time * -0.1;
    }
  });

  // Calculate visual scales based on turns.
  // We map the physical parameters (e.g., 100 to 5000 turns) into a reasonable 3D visual scale
  const secHeight = Math.min(Math.max(secTurns / 300, 2), 5); 
  const secRadius = 0.4;
  
  // Create a primary coil flat spiral geometry path
  const primarySpiral = useMemo(() => {
    const points = [];
    const startRadius = secRadius + 0.2; 
    const spacing = 0.15; // spacing between turns
    
    // Total angle based on number of turns
    const totalAngle = priTurns * Math.PI * 2;
    
    for (let i = 0; i <= 100; i++) {
      const t = i / 100;
      const angle = t * totalAngle;
      const radius = startRadius + (angle / (Math.PI * 2)) * spacing;
      
      // Flat spiral on the XZ plane (y=0)
      points.push(new THREE.Vector3(
        Math.cos(angle) * radius,
        0,
        Math.sin(angle) * radius
      ));
    }
    return new THREE.CatmullRomCurve3(points);
  }, [priTurns, secRadius]);

  return (
    <group position={[0, -secHeight / 2, 0]}>
      {/* Secondary Coil Cylinder (approximated with horizontal segments) */}
      <mesh ref={secondaryRef} position={[0, secHeight / 2, 0]}>
        {/* We use height segments to simulate dense windings */}
        <cylinderGeometry args={[secRadius, secRadius, secHeight, 32, Math.min(Math.floor(secTurns / 10), 100)]} />
        <meshBasicMaterial color="#00BFFF" wireframe transparent opacity={0.4} />
      </mesh>

      {/* Primary Coil Flat Spiral */}
      <mesh ref={primaryRef} position={[0, 0.2, 0]}>
        <tubeGeometry args={[primarySpiral, 100, 0.03, 8, false]} />
        <meshBasicMaterial color="#FF8C00" wireframe />
      </mesh>

      {/* Top Load (Toroid) */}
      <mesh ref={toploadRef} position={[0, secHeight + 0.15, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.2, 0.35, 16, 64]} />
        <meshStandardMaterial color="#E2E8F0" metalness={0.9} roughness={0.1} wireframe={false} transparent opacity={0.8} />
      </mesh>
      
      {/* Ground plane glow */}
      <mesh position={[0, 0, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[3, 32]} />
        <meshBasicMaterial color="#00BFFF" transparent opacity={0.05} />
      </mesh>
    </group>
  );
};

export default function CoilViewer3D({ priTurns, secTurns }: CoilViewer3DProps) {
  return (
    <div className="w-full h-full relative border border-[rgba(0,191,255,0.2)] rounded-sm overflow-hidden bg-[#020204]">
      <Canvas camera={{ position: [4, 3, 4], fov: 50 }}>
        <color attach="background" args={['#020204']} />
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1.5} color="#00BFFF" />
        <pointLight position={[-10, -10, -10]} intensity={0.8} color="#FF003C" />
        
        <CoilModel priTurns={priTurns} secTurns={secTurns} />
        <OrbitControls enablePan={true} enableZoom={true} />
        
        <gridHelper args={[10, 20, '#00BFFF', '#020204']} position={[0, -0.01, 0]} />
      </Canvas>
      
      {/* Overlays */}
      <div className="absolute top-0 left-0 w-full p-2 flex justify-between pointer-events-none z-10">
        <h3 className="text-[10px] font-orbitron text-metallic-steel tracking-widest bg-black/70 px-2 py-1 border border-neon-cyan/30 rounded">
          WEBGL / 3D PARAMETRIC HOLOGRAPH
        </h3>
        <div className="flex gap-2">
          <span className="text-[10px] text-neon-cyan bg-black/70 px-2 py-1 border border-neon-cyan/30 rounded">PRI: {priTurns.toFixed(1)}T</span>
          <span className="text-[10px] text-neon-blue bg-black/70 px-2 py-1 border border-neon-cyan/30 rounded">SEC: {Math.round(secTurns)}T</span>
        </div>
      </div>
      <div className="absolute bottom-2 right-2 pointer-events-none z-10">
        <p className="text-[9px] text-metallic-silver uppercase tracking-widest bg-black/50 px-2 py-1 rounded">
          [ DRAG ROTATE // SCROLL ZOOM ]
        </p>
      </div>
      
      {/* Scanline overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(0,0,0,0)_50%,rgba(0,191,255,0.03)_50%)] bg-[length:100%_4px] pointer-events-none z-0"></div>
    </div>
  );
}
