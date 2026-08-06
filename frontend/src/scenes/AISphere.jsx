import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, useTransform } from 'framer-motion';
import { Canvas, useFrame } from '@react-three/fiber';
import { useSceneProgress } from '../hooks/useSceneProgress';

// 3D Three.js Inner Scene Component
function ThreeCore({ progress }) {
  const sphereRef = useRef();
  const outerParticlesRef = useRef();
  
  // Create coordinate list for particles
  const particleCount = 400;
  const positions = useMemo(() => {
    const arr = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount; i++) {
      // Golden spiral distribution on a sphere
      const theta = Math.acos(1 - (2 * i) / particleCount);
      const phi = Math.PI * (1 + Math.sqrt(5)) * i;
      
      const r = 2.0 + Math.random() * 0.4;
      arr[i * 3] = r * Math.sin(theta) * Math.cos(phi);
      arr[i * 3 + 1] = r * Math.sin(theta) * Math.sin(phi);
      arr[i * 3 + 2] = r * Math.cos(theta);
    }
    return arr;
  }, []);

  useFrame((state, delta) => {
    const scrollVal = progress.get();
    
    // Auto rotations
    if (sphereRef.current) {
      sphereRef.current.rotation.y += delta * 0.2;
      sphereRef.current.rotation.x += delta * 0.08;
      
      // Expand sphere based on scroll progress
      const sphereScale = 1.0 + scrollVal * 1.5;
      sphereRef.current.scale.set(sphereScale, sphereScale, sphereScale);
    }

    if (outerParticlesRef.current) {
      outerParticlesRef.current.rotation.y -= delta * 0.12;
      
      // Expand particles further outward
      const particleScale = 1.1 + scrollVal * 2.6;
      outerParticlesRef.current.scale.set(particleScale, particleScale, particleScale);
    }
  });

  return (
    <group>
      {/* 3D Wireframe Icosahedron Sphere */}
      <mesh ref={sphereRef}>
        <icosahedronGeometry args={[1.5, 3]} />
        <meshBasicMaterial 
          color="#4F6BFF" 
          wireframe 
          transparent 
          opacity={0.4} 
        />
      </mesh>

      {/* Central Solid Glow Sphere */}
      <mesh>
        <sphereGeometry args={[0.4, 16, 16]} />
        <meshBasicMaterial 
          color="#7C5CFF" 
          transparent 
          opacity={0.3} 
        />
      </mesh>

      {/* Outer Orbiting Particles */}
      <points ref={outerParticlesRef}>
        <bufferGeometry>
          <bufferAttribute 
            attach="attributes-position"
            args={[positions, 3]}
          />
        </bufferGeometry>
        <pointsMaterial 
          size={0.06}
          color="#7C5CFF"
          transparent
          opacity={0.7}
          sizeAttenuation={true}
        />
      </points>
    </group>
  );
}

// 2D Canvas Fallback Component
function FallbackCanvas({ progress }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    let animId;
    let width = (canvas.width = 400);
    let height = (canvas.height = 400);
    let angle = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      const scrollVal = progress.get();
      angle += 0.01;

      const centerX = width / 2;
      const centerY = height / 2;

      // Draw outer rotating circle rings
      const radius = 90 + scrollVal * 60;
      
      ctx.strokeStyle = 'rgba(79, 107, 255, 0.4)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
      ctx.stroke();

      ctx.strokeStyle = 'rgba(124, 92, 255, 0.3)';
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius * 0.7, angle, angle + Math.PI * 1.5);
      ctx.stroke();

      // Draw expanding center orb
      const orbRadius = 25 + scrollVal * 30;
      const grad = ctx.createRadialGradient(centerX, centerY, 2, centerX, centerY, orbRadius);
      grad.addColorStop(0, '#7C5CFF');
      grad.addColorStop(1, 'rgba(79, 107, 255, 0)');
      
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(centerX, centerY, orbRadius, 0, Math.PI * 2);
      ctx.fill();

      // Draw orbit dots
      const numDots = 8;
      for (let i = 0; i < numDots; i++) {
        const dotAngle = angle * 2 + (i * Math.PI * 2) / numDots;
        const dx = centerX + Math.cos(dotAngle) * radius;
        const dy = centerY + Math.sin(dotAngle) * radius;

        ctx.fillStyle = '#4F6BFF';
        ctx.beginPath();
        ctx.arc(dx, dy, 3, 0, Math.PI * 2);
        ctx.fill();
      }

      animId = requestAnimationFrame(render);
    };

    render();
    return () => cancelAnimationFrame(animId);
  }, [progress]);

  return (
    <canvas ref={canvasRef} className="w-[400px] h-[400px] bg-transparent" />
  );
}

export default function AISphere() {
  const { progress, isActive } = useSceneProgress(3);
  const [hasWebGL, setHasWebGL] = useState(true);

  // Check for WebGL capability
  useEffect(() => {
    try {
      const canvas = document.createElement('canvas');
      const isSupported = !!(
        window.WebGLRenderingContext && 
        (canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
      );
      setHasWebGL(isSupported);
    } catch (e) {
      setHasWebGL(false);
    }
  }, []);

  const opacity = useTransform(progress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);
  const scale = useTransform(progress, [0, 0.4, 0.8, 1], [0.8, 1, 1, 0.6]);

  if (!isActive) return null;

  return (
    <motion.div 
      className="absolute inset-0 flex flex-col items-center justify-center p-6 z-10 select-none overflow-hidden"
      style={{ opacity, scale }}
    >
      {/* Title Header */}
      <div className="absolute top-24 left-1/2 -translate-x-1/2 text-center pointer-events-none z-0">
        <span className="text-[10px] uppercase tracking-[0.3em] text-accent-blue/80 font-bold block mb-2">Stage 03</span>
        <h2 className="text-3xl md:text-5xl font-extrabold tracking-tighter text-white uppercase">
          Model Projection
        </h2>
        <p className="text-white/40 text-xs md:text-sm font-sans mt-2 max-w-sm mx-auto">
          Distorting parameters through high-dimensional projection space to formulate scoring weights.
        </p>
      </div>

      {/* Main Core Container */}
      <div className="w-full h-[60vh] flex items-center justify-center relative">
        {hasWebGL ? (
          <div className="w-full h-full absolute inset-0">
            <Canvas camera={{ position: [0, 0, 5], fov: 60 }} gl={{ antialias: true }}>
              <ambientLight intensity={0.5} />
              <pointLight position={[10, 10, 10]} intensity={1.5} />
              <ThreeCore progress={progress} />
            </Canvas>
          </div>
        ) : (
          <FallbackCanvas progress={progress} />
        )}
      </div>

      {/* Ambient background bloom */}
      <div className="bloom-glow top-1/3 right-1/4 animate-pulse-slow" />
      <div className="bloom-glow-cyan bottom-1/3 left-1/4 animate-pulse-slow" style={{ animationDelay: '3s' }} />
    </motion.div>
  );
}
