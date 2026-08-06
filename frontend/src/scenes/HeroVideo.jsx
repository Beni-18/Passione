import React from 'react';
import { motion, useTransform, useSpring } from 'framer-motion';
import { useSceneProgress } from '../hooks/useSceneProgress';

export default function HeroVideo() {
  const { progress, isActive } = useSceneProgress(0);

  // Raw transformation maps
  const titleScale = useTransform(progress, [0, 0.8], [1, 2.5], { clamp: true });
  const titleOpacity = useTransform(progress, [0.4, 0.95], [1, 0], { clamp: true });
  const subtitleY = useTransform(progress, [0, 0.8], [0, -40], { clamp: true });
  const subtitleOpacity = useTransform(progress, [0.25, 0.70], [1, 0], { clamp: true });
  const indicatorOpacity = useTransform(progress, [0, 0.3], [1, 0], { clamp: true });
  const blurValue = useTransform(progress, [0.3, 0.95], ["blur(0px)", "blur(10px)"], { clamp: true });

  // Drift offsets for each character of "TRENDS" (T-R-E-N-D-S)
  const driftT_X = useTransform(progress, [0.15, 0.85], [0, -320], { clamp: true });
  const driftT_Y = useTransform(progress, [0.15, 0.85], [0, -180], { clamp: true });
  const springT_X = useSpring(driftT_X, { stiffness: 85, damping: 18 });
  const springT_Y = useSpring(driftT_Y, { stiffness: 85, damping: 18 });

  const driftR_X = useTransform(progress, [0.15, 0.85], [0, 240], { clamp: true });
  const driftR_Y = useTransform(progress, [0.15, 0.85], [0, -220], { clamp: true });
  const springR_X = useSpring(driftR_X, { stiffness: 85, damping: 18 });
  const springR_Y = useSpring(driftR_Y, { stiffness: 85, damping: 18 });

  const driftE_X = useTransform(progress, [0.15, 0.85], [0, -240], { clamp: true });
  const driftE_Y = useTransform(progress, [0.15, 0.85], [0, 160], { clamp: true });
  const springE_X = useSpring(driftE_X, { stiffness: 85, damping: 18 });
  const springE_Y = useSpring(driftE_Y, { stiffness: 85, damping: 18 });

  const driftN_X = useTransform(progress, [0.15, 0.85], [0, 290], { clamp: true });
  const driftN_Y = useTransform(progress, [0.15, 0.85], [0, 200], { clamp: true });
  const springN_X = useSpring(driftN_X, { stiffness: 85, damping: 18 });
  const springN_Y = useSpring(driftN_Y, { stiffness: 85, damping: 18 });

  const driftD_X = useTransform(progress, [0.15, 0.85], [0, -80], { clamp: true });
  const driftD_Y = useTransform(progress, [0.15, 0.85], [0, -280], { clamp: true });
  const springD_X = useSpring(driftD_X, { stiffness: 85, damping: 18 });
  const springD_Y = useSpring(driftD_Y, { stiffness: 85, damping: 18 });

  const driftS_X = useTransform(progress, [0.15, 0.85], [0, 80], { clamp: true });
  const driftS_Y = useTransform(progress, [0.15, 0.85], [0, 260], { clamp: true });
  const springS_X = useSpring(driftS_X, { stiffness: 85, damping: 18 });
  const springS_Y = useSpring(driftS_Y, { stiffness: 85, damping: 18 });

  if (!isActive) return null;

  return (
    <motion.div 
      className="absolute inset-0 flex flex-col items-center justify-center text-center p-6 z-10 select-none overflow-hidden"
      style={{ opacity: titleOpacity, filter: blurValue }}
    >
      {/* Vignette film frame shadow overlays */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_40%,rgba(0,0,0,0.65))] pointer-events-none z-1" />
      <div className="absolute inset-x-0 top-0 h-20 bg-gradient-to-b from-[#050506]/85 to-transparent pointer-events-none z-1" />
      <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-[#050506]/85 to-transparent pointer-events-none z-1" />

      <div className="max-w-4xl flex flex-col items-center z-10 relative">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          style={{ scale: titleScale }}
          className="flex flex-col items-center select-none"
        >
          {/* Subtitle / Label */}
          <span className="text-[10px] uppercase tracking-[0.35em] text-accent-blue/80 font-bold mb-4 font-mono">
            TrendAI Cinematic Inference
          </span>

          {/* Editorial Title Headline */}
          <div className="flex flex-col items-center space-y-1">
            <h1 className="text-3xl md:text-5xl font-extralight tracking-[0.25em] text-white/80 uppercase">
              Predict
            </h1>
            
            {/* Morphing Word: T-R-E-N-D-S */}
            <h2 className="text-6xl md:text-9xl font-black uppercase tracking-tighter text-white flex items-center justify-center">
              <motion.span style={{ x: springT_X, y: springT_Y }} className="inline-block">T</motion.span>
              <motion.span style={{ x: springR_X, y: springR_Y }} className="inline-block">R</motion.span>
              <motion.span style={{ x: springE_X, y: springE_Y }} className="inline-block">E</motion.span>
              <motion.span style={{ x: springN_X, y: springN_Y }} className="inline-block">N</motion.span>
              <motion.span style={{ x: springD_X, y: springD_Y }} className="inline-block">D</motion.span>
              <motion.span style={{ x: springS_X, y: springS_Y }} className="inline-block">S</motion.span>
            </h2>

            <h3 className="text-4xl md:text-6xl font-extrabold uppercase tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-accent-blue via-accent-violet to-purple-500 pt-1">
              Next.
            </h3>
          </div>
        </motion.div>
        
        {/* Compact 2-line Subtitle */}
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 1.0 }}
          className="mt-10 text-sm md:text-base font-light text-white/50 max-w-md leading-relaxed font-sans"
          style={{ y: subtitleY, opacity: subtitleOpacity }}
        >
          Predict film popularity and sentiment attributes.<br />
          Before audiences do.
        </motion.p>
      </div>

      {/* Pulse / Bounce Enter Prompt */}
      <motion.div 
        className="absolute bottom-12 flex flex-col items-center z-10 cursor-pointer"
        style={{ opacity: indicatorOpacity }}
      >
        <span className="text-[10px] uppercase tracking-[0.25em] text-white/50 mb-3.5 font-bold flex items-center">
          ↓ Enter The AI
        </span>
        <div className="w-[20px] h-[34px] border border-white/20 rounded-full flex justify-center p-1.5 backdrop-blur-xs">
          <motion.div 
            className="w-1.5 h-1.5 bg-accent-blue rounded-full"
            animate={{ y: [0, 12, 0] }}
            transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
          />
        </div>
      </motion.div>
    </motion.div>
  );
}
