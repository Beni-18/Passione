import React, { useEffect } from 'react';
import { motion, useTransform, useSpring, useMotionValue } from 'framer-motion';
import { useSceneProgress } from '../hooks/useSceneProgress';

const METADATA_ITEMS = [
  { text: "Title: Midnight Run", x: "-25%", y: "-30%", speed: 0.15, size: "text-lg", glow: true },
  { text: "Genre: Thriller", x: "28%", y: "-22%", speed: 0.2, size: "text-base", glow: false },
  { text: "Duration: 24 Min", x: "-32%", y: "15%", speed: 0.25, size: "text-base", glow: false },
  { text: "Lang: English (en)", x: "32%", y: "20%", speed: 0.18, size: "text-sm", glow: false },
  { text: "Tag: #suspense", x: "-10%", y: "-40%", speed: 0.12, size: "text-xs", glow: false },
  { text: "Tag: #indie", x: "12%", y: "-35%", speed: 0.22, size: "text-xs", glow: true },
  { text: "Tag: #short-film", x: "-18%", y: "35%", speed: 0.16, size: "text-sm", glow: false },
  { text: "Tag: #cinematic", x: "18%", y: "38%", speed: 0.28, size: "text-base", glow: true },
  { text: "Encoding: H.264", x: "-40%", y: "-10%", speed: 0.3, size: "text-xs", glow: false },
  { text: "Aspect: 2.39:1", x: "42%", y: "-5%", speed: 0.24, size: "text-xs", glow: false },
  { text: "Upload Hour: 18:30", x: "5%", y: "28%", speed: 0.14, size: "text-xs", glow: false },
  { text: "Resolution: 4K UHD", x: "-5%", y: "8%", speed: 0.1, size: "text-xl font-bold border-accent-blue/30", glow: true }
];

export default function MetadataCloud() {
  const { progress, isActive } = useSceneProgress(1);

  // Mouse Parallax Setup
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const springX = useSpring(mouseX, { stiffness: 50, damping: 15 });
  const springY = useSpring(mouseY, { stiffness: 50, damping: 15 });

  useEffect(() => {
    if (!isActive) return;

    const handleMouseMove = (e) => {
      const { innerWidth, innerHeight } = window;
      // Map to values between -100 and 100
      const x = ((e.clientX / innerWidth) - 0.5) * 120;
      const y = ((e.clientY / innerHeight) - 0.5) * 120;
      mouseX.set(x);
      mouseY.set(y);
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [isActive, mouseX, mouseY]);

  // Entrance & Exit transformations
  const opacity = useTransform(progress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);
  const cloudScale = useTransform(progress, [0, 0.4, 0.8, 1], [0.8, 1, 1, 1.2]);
  const blurValue = useTransform(progress, [0, 0.2, 0.8, 1], ["blur(12px)", "blur(0px)", "blur(0px)", "blur(15px)"]);

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
        <p className="text-white/40 text-xs md:text-sm font-sans mt-2 max-w-sm mx-auto">
          Parsing film properties, timestamps, linguistic metrics, and descriptive markers.
        </p>
      </div>

      {/* Floating Chips Cloud */}
      <div className="relative w-full h-[60vh] max-w-5xl flex items-center justify-center">
        {METADATA_ITEMS.map((item, index) => {
          // Calculate individual offsets based on scroll progress
          // Scatter items outward on scroll exit
          const indexOffset = index * 0.02;
          const individualX = useTransform(
            progress,
            [0, 0.3, 0.7, 1],
            [
              `calc(${item.x} * 1.5)`, 
              item.x, 
              item.x, 
              `calc(${item.x} * 3)`
            ]
          );
          const individualY = useTransform(
            progress,
            [0, 0.3, 0.7, 1],
            [
              `calc(${item.y} * 1.5 + 50px)`, 
              item.y, 
              item.y, 
              `calc(${item.y} * 3 - 100px)`
            ]
          );

          // Spring physics mouse parallax offsets
          const px = useTransform(springX, (val) => val * item.speed);
          const py = useTransform(springY, (val) => val * item.speed);

          return (
            <motion.div
              key={index}
              className={`absolute glass-panel ${
                item.glow ? 'border-accent-blue/20 bg-accent-blue/5' : ''
              } px-4 py-2.5 rounded-full flex items-center justify-center font-sans tracking-wide text-white/80 cursor-default transition-all duration-300 hover:border-accent-violet/50 hover:bg-white/5 hover:text-white ${item.size}`}
              style={{
                left: `calc(50% + ${item.x})`,
                top: `calc(50% + ${item.y})`,
                x: px,
                y: py,
              }}
              whileHover={{ scale: 1.05 }}
            >
              {item.glow && (
                <span className="w-1.5 h-1.5 rounded-full bg-accent-blue mr-2 animate-ping" />
              )}
              {item.text}
            </motion.div>
          );
        })}
      </div>

      {/* Ambient backgrounds */}
      <div className="bloom-glow top-1/4 left-1/4 animate-pulse-slow" />
      <div className="bloom-glow-cyan bottom-1/4 right-1/4 animate-pulse-slow" style={{ animationDelay: '2s' }} />
    </motion.div>
  );
}
