import React, { useEffect } from 'react';
import { motion, useTransform, useSpring, useMotionValue } from 'framer-motion';
import { useSceneProgress } from '../hooks/useSceneProgress';

const METADATA_ITEMS = [
  { text: "Title: Midnight Run", x: "-25%", y: "-30%", speed: 0.15, size: "text-lg", glow: true },
  { text: "Genre: Thriller", x: "28%", y: "-22%", speed: 0.2, size: "text-base", glow: false, watermark: "T" },
  { text: "Duration: 24 Min", x: "-32%", y: "15%", speed: 0.25, size: "text-base", glow: false, watermark: "R" },
  { text: "Lang: English (en)", x: "32%", y: "20%", speed: 0.18, size: "text-sm", glow: false, watermark: "E" },
  { text: "Tag: #suspense", x: "-10%", y: "-40%", speed: 0.12, size: "text-xs", glow: false },
  { text: "Tag: #indie", x: "12%", y: "-35%", speed: 0.22, size: "text-xs", glow: true },
  { text: "Tag: #short-film", x: "-18%", y: "35%", speed: 0.16, size: "text-sm", glow: false, watermark: "D" },
  { text: "Tag: #cinematic", x: "18%", y: "38%", speed: 0.28, size: "text-base", glow: true },
  { text: "Encoding: H.264", x: "-40%", y: "-10%", speed: 0.3, size: "text-xs", glow: false, watermark: "N" },
  { text: "Aspect: 2.39:1", x: "42%", y: "-5%", speed: 0.24, size: "text-xs", glow: false, watermark: "S" },
  { text: "Upload Hour: 18:30", x: "5%", y: "28%", speed: 0.14, size: "text-xs", glow: false },
  { text: "Resolution: 4K UHD", x: "-5%", y: "8%", speed: 0.1, size: "text-xl font-bold border-accent-blue/30", glow: true }
];

// Extracted metadata chip child component to comply with Rules of Hooks
function MetadataChip({ item, progress, springX, springY }) {
  // 1. Scatter items outward on scroll exit
  const individualX = useTransform(
    progress,
    [0, 0.3, 0.7, 1],
    [
      `calc(${item.x} * 1.3)`, 
      item.x, 
      item.x, 
      `calc(${item.x} * 2.8)`
    ]
  );
  
  const individualY = useTransform(
    progress,
    [0, 0.3, 0.7, 1],
    [
      `calc(${item.y} * 1.3 + 30px)`, 
      item.y, 
      item.y, 
      `calc(${item.y} * 2.8 - 60px)`
    ]
  );

  // 2. Parallax mouse movements
  const px = useTransform(springX, (val) => val * item.speed);
  const py = useTransform(springY, (val) => val * item.speed);

  // Combine positional mappings
  const xCombined = useTransform([individualX, px], ([ix, pxVal]) => {
    return `calc(${ix} + ${pxVal}px)`;
  });
  
  const yCombined = useTransform([individualY, py], ([iy, pyVal]) => {
    return `calc(${iy} + ${pyVal}px)`;
  });

  return (
    <motion.div
      className={`absolute glass-panel ${
        item.glow ? 'border-accent-blue/20 bg-accent-blue/5' : ''
      } px-5 py-3 rounded-2xl flex items-center justify-center font-sans tracking-wide text-white/80 cursor-default transition-all duration-300 hover:border-accent-violet/50 hover:bg-white/5 hover:text-white ${item.size} overflow-hidden`}
      style={{
        left: "50%",
        top: "50%",
        x: xCombined,
        y: yCombined,
      }}
      whileHover={{ scale: 1.05 }}
    >
      {/* Background morphed letter watermark */}
      {item.watermark && (
        <span className="absolute -left-2 -bottom-2 text-3xl font-black text-accent-blue/15 pointer-events-none select-none font-mono">
          {item.watermark}
        </span>
      )}
      
      {item.glow && (
        <span className="w-1.5 h-1.5 rounded-full bg-accent-blue mr-2 animate-ping" />
      )}
      <span className="relative z-10">{item.text}</span>
    </motion.div>
  );
}

export default function MetadataCloud() {
  const { progress, isActive } = useSceneProgress(1);

  // Mouse Parallax MotionValues
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const springX = useSpring(mouseX, { stiffness: 55, damping: 18 });
  const springY = useSpring(mouseY, { stiffness: 55, damping: 18 });

  useEffect(() => {
    if (!isActive) return;

    const handleMouseMove = (e) => {
      const { innerWidth, innerHeight } = window;
      const x = ((e.clientX / innerWidth) - 0.5) * 110;
      const y = ((e.clientY / innerHeight) - 0.5) * 110;
      mouseX.set(x);
      mouseY.set(y);
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [isActive, mouseX, mouseY]);

  // Entrance & Exit transitions
  const opacity = useTransform(progress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);
  const cloudScale = useTransform(progress, [0, 0.4, 0.8, 1], [0.85, 1, 1, 1.15]);
  const blurValue = useTransform(progress, [0, 0.2, 0.8, 1], ["blur(10px)", "blur(0px)", "blur(0px)", "blur(12px)"]);

  if (!isActive) return null;

  return (
    <motion.div 
      className="absolute inset-0 flex flex-col items-center justify-center p-6 z-10 select-none overflow-hidden"
      style={{ opacity, filter: blurValue, scale: cloudScale }}
    >
      {/* Background Section Header */}
      <div className="absolute top-24 left-1/2 -translate-x-1/2 text-center pointer-events-none z-0">
        <span className="text-[10px] uppercase tracking-[0.3em] text-accent-blue/80 font-bold block mb-2">Stage 01</span>
        <h2 className="text-3xl md:text-5xl font-extrabold tracking-tighter text-white uppercase">
          Metadata Extraction
        </h2>
        <p className="text-white/40 text-xs md:text-sm font-sans mt-2 max-w-sm mx-auto leading-relaxed">
          Parsing film properties, timestamps, linguistic metrics, and descriptive markers.
        </p>
      </div>

      {/* Floating Chips Cloud */}
      <div className="relative w-full h-[60vh] max-w-5xl flex items-center justify-center">
        {METADATA_ITEMS.map((item, index) => (
          <MetadataChip
            key={index}
            item={item}
            progress={progress}
            springX={springX}
            springY={springY}
          />
        ))}
      </div>

      {/* Ambient background glows */}
      <div className="bloom-glow top-1/4 left-1/4 animate-pulse-slow pointer-events-none" />
      <div className="bloom-glow-cyan bottom-1/4 right-1/4 animate-pulse-slow pointer-events-none" style={{ animationDelay: '2s' }} />
    </motion.div>
  );
}
