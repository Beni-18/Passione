import React, { useState, useEffect } from 'react';
import { motion, useTransform, useSpring } from 'framer-motion';
import { useSceneProgress } from '../hooks/useSceneProgress';
import InferenceStudio from '../components/InferenceStudio';

export default function PlatformLaunch() {
  const { progress, isActive } = useSceneProgress(5);
  
  // Track viewport sizes for responsive layout offsets
  const [offsets, setOffsets] = useState({ x: 382, y: -312 });

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setOffsets({ x: 0, y: -350 }); // Mobile: center-top position
      } else if (window.innerWidth < 1024) {
        setOffsets({ x: 280, y: -320 }); // Tablet / small desktop
      } else {
        setOffsets({ x: 382, y: -312 }); // Standard desktop coordinates
      }
    };
    
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // 1. Percentage Morphing Coordinates (Centered Reveal -> Header chip)
  const percentScale = useTransform(progress, [0.0, 0.40], [2.2, 0.32], { clamp: true });
  const percentX = useTransform(progress, [0.0, 0.40], [0, offsets.x], { clamp: true });
  const percentY = useTransform(progress, [0.0, 0.40], [0, offsets.y], { clamp: true });

  const springScale = useSpring(percentScale, { stiffness: 130, damping: 24 });
  const springX = useSpring(percentX, { stiffness: 130, damping: 24 });
  const springY = useSpring(percentY, { stiffness: 130, damping: 24 });

  // 2. Backdrop dimmer opacity
  const backdropOpacity = useTransform(progress, [0.0, 0.35], [0.0, 0.65], { clamp: true });

  // 3. Panel Entrance MotionValues & Springs
  const headerOpacity = useTransform(progress, [0.3, 0.55], [0.0, 1.0], { clamp: true });
  const headerY = useTransform(progress, [0.3, 0.55], [-40, 0], { clamp: true });
  const springHeaderY = useSpring(headerY, { stiffness: 110, damping: 22 });

  const leftOpacity = useTransform(progress, [0.45, 0.75], [0.0, 1.0], { clamp: true });
  const leftX = useTransform(progress, [0.45, 0.75], [-150, 0], { clamp: true });
  const springLeftX = useSpring(leftX, { stiffness: 100, damping: 20 });

  const rightOpacity = useTransform(progress, [0.55, 0.85], [0.0, 1.0], { clamp: true });
  const rightX = useTransform(progress, [0.55, 0.85], [150, 0], { clamp: true });
  const springRightX = useSpring(rightX, { stiffness: 100, damping: 20 });

  const bottomOpacity = useTransform(progress, [0.65, 0.90], [0.0, 1.0], { clamp: true });
  const bottomY = useTransform(progress, [0.65, 0.90], [60, 0], { clamp: true });
  const springBottomY = useSpring(bottomY, { stiffness: 110, damping: 22 });

  // 4. Interactivity Gating (Interactive only when fully settled in scroll)
  const [isInteractive, setIsInteractive] = useState(false);
  useEffect(() => {
    const unsubscribe = progress.on('change', (val) => {
      setIsInteractive(val >= 0.92);
    });
    return () => unsubscribe();
  }, [progress]);

  if (!isActive) return null;

  return (
    <motion.div 
      className="absolute inset-0 flex flex-col items-center justify-center p-4 md:p-8 z-10 overflow-y-auto"
    >
      {/* Background Dimmer Layer */}
      <motion.div 
        className="absolute inset-0 bg-[#070708] pointer-events-none z-0"
        style={{ opacity: backdropOpacity }}
      />

      {/* Morphing Percentage Element */}
      <motion.div
        style={{
          scale: springScale,
          x: springX,
          y: springY,
        }}
        className="fixed pointer-events-none z-50 font-extrabold text-white tracking-tighter uppercase leading-none select-none flex items-baseline filter drop-shadow-[0_0_15px_rgba(79,107,255,0.4)]"
      >
        82<span className="text-4xl text-accent-blue font-bold ml-1">%</span>
      </motion.div>

      {/* Inference Workspace App */}
      <InferenceStudio 
        isInteractive={isInteractive}
        headerOpacity={headerOpacity}
        springHeaderY={springHeaderY}
        leftOpacity={leftOpacity}
        springLeftX={springLeftX}
        rightOpacity={rightOpacity}
        springRightX={springRightX}
        bottomOpacity={bottomOpacity}
        springBottomY={springBottomY}
      />
    </motion.div>
  );
}
