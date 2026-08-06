import React from 'react';
import { motion, useTransform } from 'framer-motion';
import { useSceneProgress } from '../hooks/useSceneProgress';

export default function HeroVideo() {
  const { progress, isActive } = useSceneProgress(0);

  // Map progress to transformations
  const titleScale = useTransform(progress, [0, 0.8], [1, 2.8], { clamp: true });
  const titleOpacity = useTransform(progress, [0.4, 0.95], [1, 0], { clamp: true });
  const subtitleY = useTransform(progress, [0, 0.8], [0, -60], { clamp: true });
  const subtitleOpacity = useTransform(progress, [0.3, 0.75], [1, 0], { clamp: true });
  const indicatorOpacity = useTransform(progress, [0, 0.3], [1, 0], { clamp: true });
  const blurValue = useTransform(progress, [0.3, 0.95], ["blur(0px)", "blur(12px)"], { clamp: true });

  if (!isActive) return null;

  return (
    <motion.div 
      className="absolute inset-0 flex flex-col items-center justify-center text-center p-6 z-10 select-none"
      style={{ opacity: titleOpacity, filter: blurValue }}
    >
      <div className="max-w-4xl flex flex-col items-center z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          style={{ scale: titleScale }}
          className="flex flex-col items-center"
        >
          <h1 className="text-7xl md:text-[10rem] font-extrabold tracking-tighter text-white uppercase leading-none">
            Trend<span className="text-transparent bg-clip-text bg-gradient-to-r from-accent-blue to-accent-violet">AI</span>
          </h1>
        </motion.div>
        
        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 1.0 }}
          className="mt-8 text-lg md:text-xl font-light text-white/50 max-w-lg leading-relaxed font-sans"
          style={{ y: subtitleY, opacity: subtitleOpacity }}
        >
          We don't explain predictions. We predict film performance in real-time, one frame at a time.
        </motion.p>
      </div>

      <motion.div 
        className="absolute bottom-12 flex flex-col items-center z-10"
        style={{ opacity: indicatorOpacity }}
      >
        <span className="text-[10px] uppercase tracking-[0.2em] text-white/40 mb-3 font-medium">Scroll to Predict</span>
        <div className="w-[22px] h-[38px] border border-white/25 rounded-full flex justify-center p-1.5 backdrop-blur-sm">
          <motion.div 
            className="w-1.5 h-1.5 bg-accent-blue rounded-full"
            animate={{ y: [0, 14, 0] }}
            transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
          />
        </div>
      </motion.div>
    </motion.div>
  );
}
