import React, { useState, useEffect } from 'react';
import { motion, useTransform } from 'framer-motion';
import { useSceneProgress } from '../hooks/useSceneProgress';

export default function PredictionReveal() {
  const { progress, isActive } = useSceneProgress(4);
  const [percent, setPercent] = useState(0);

  // Map progress to the percentage value (0 to 82)
  const percentValue = useTransform(progress, [0.1, 0.75], [0, 82], { clamp: true });

  useEffect(() => {
    if (!isActive) return;
    
    // Subscribe to percentage updates on scroll scrub
    const unsubscribe = percentValue.on('change', (val) => {
      setPercent(Math.min(82, Math.max(0, Math.round(val))));
    });
    return () => unsubscribe();
  }, [percentValue, isActive]);

  // Framer Motion transformations for entrance/exit
  const opacity = useTransform(progress, [0, 0.2, 0.8, 1], [0, 1, 1, 0], { clamp: true });
  const scale = useTransform(progress, [0, 0.3, 0.75, 1], [0.75, 1, 1, 1.2], { clamp: true });
  
  // Bar width scale mapping
  const barWidth = useTransform(progress, [0.1, 0.75], ["0%", "82%"], { clamp: true });
  
  // Glow intensity mapping
  const glowOpacity = useTransform(progress, [0.4, 0.85], [0.1, 0.6], { clamp: true });

  if (!isActive) return null;

  return (
    <motion.div 
      className="absolute inset-0 flex flex-col items-center justify-center p-6 z-10 select-none overflow-hidden"
      style={{ opacity, scale }}
    >
      {/* Background Stage Header */}
      <div className="absolute top-24 left-1/2 -translate-x-1/2 text-center pointer-events-none z-0">
        <span className="text-[10px] uppercase tracking-[0.3em] text-accent-blue/80 font-bold block mb-2">Stage 04</span>
        <h2 className="text-3xl md:text-5xl font-extrabold tracking-tighter text-white uppercase">
          Likelihood Scored
        </h2>
        <p className="text-white/40 text-xs md:text-sm font-sans mt-2 max-w-sm mx-auto">
          Resolving feature metrics into a qualified prediction index.
        </p>
      </div>

      {/* Massive Number & Percentage Display */}
      <div className="flex flex-col items-center justify-center z-10 max-w-2xl w-full">
        <motion.div 
          className="text-[8rem] md:text-[15rem] font-extrabold tracking-tighter text-white select-none leading-none flex items-baseline font-sans relative"
        >
          {/* Ambient Glow behind number */}
          <motion.div 
            className="absolute inset-0 bg-accent-blue rounded-full filter blur-[100px] pointer-events-none -z-10"
            style={{ opacity: glowOpacity }}
          />
          {percent}
          <span className="text-5xl md:text-8xl text-accent-blue font-bold ml-2">%</span>
        </motion.div>

        {/* Prediction Rating Text */}
        <motion.div 
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-lg md:text-2xl font-light text-white/80 uppercase tracking-[0.15em] mb-8 font-sans"
        >
          Likely To <span className="text-accent-blue font-semibold">Trend</span>
        </motion.div>

        {/* Confidence Progress Bar */}
        <div className="w-full h-[6px] bg-white/5 rounded-full overflow-hidden border border-white/5 max-w-lg relative">
          <motion.div 
            className="h-full bg-gradient-to-r from-accent-blue to-accent-violet rounded-full shadow-[0_0_12px_#4F6BFF]"
            style={{ width: barWidth }}
          />
        </div>

        {/* HUD Sub-Labels */}
        <div className="flex justify-between w-full max-w-lg mt-4 font-mono text-[9px] text-white/30 uppercase">
          <div>Confidence Threshold: 65.0%</div>
          <div className="text-right text-accent-blue">Grounded prediction: TRUE</div>
        </div>

        {/* Detailed Metrics Panel */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="grid grid-cols-3 gap-6 mt-12 w-full max-w-lg glass-panel px-6 py-4 rounded-xl border border-white/5"
        >
          <div className="text-center">
            <div className="text-[10px] text-white/40 uppercase tracking-wider mb-1 font-sans">Metrics Split</div>
            <div className="font-mono text-sm text-white font-bold">80/20 Test</div>
          </div>
          <div className="text-center border-x border-white/5">
            <div className="text-[10px] text-white/40 uppercase tracking-wider mb-1 font-sans">Model Precision</div>
            <div className="font-mono text-sm text-accent-blue font-bold">89.4%</div>
          </div>
          <div className="text-center">
            <div className="text-[10px] text-white/40 uppercase tracking-wider mb-1 font-sans">ROC AUC Bar</div>
            <div className="font-mono text-sm text-accent-violet font-bold">0.912</div>
          </div>
        </motion.div>
      </div>

      {/* Ambient lighting */}
      <div className="bloom-glow-cyan top-1/3 left-1/3 animate-pulse-slow" />
      <div className="bloom-glow bottom-1/3 right-1/3 animate-pulse-slow" style={{ animationDelay: '1.5s' }} />
    </motion.div>
  );
}
