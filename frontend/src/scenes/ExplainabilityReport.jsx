import React from 'react';
import { motion, useTransform } from 'framer-motion';
import { useSceneProgress } from '../hooks/useSceneProgress';

const FEATURES = [
  {
    title: "Genre Influence",
    feature: "Genre = Thriller",
    weight: "+32.4%",
    desc: "Thriller content maintains high audience velocity in early hours. High conversion rates observed.",
    color: "text-accent-blue border-accent-blue/20",
    glow: "rgba(79, 107, 255, 0.05)"
  },
  {
    title: "Upload Window",
    feature: "Upload Hour = 18",
    weight: "+21.1%",
    desc: "Uploaded during peak afternoon user traffic window, maximizing initial seeding impressions.",
    color: "text-accent-violet border-accent-violet/20",
    glow: "rgba(124, 92, 255, 0.05)"
  },
  {
    title: "Runtime Factor",
    feature: "Duration = 24m",
    weight: "+18.5%",
    desc: "Short-form duration range (15-30 mins) drives higher completion rates, boosting recommendation ranks.",
    color: "text-accent-blue border-accent-blue/20",
    glow: "rgba(79, 107, 255, 0.05)"
  },
  {
    title: "Metadata Density",
    feature: "Tag Count = 3",
    weight: "+11.2%",
    desc: "High contextual density with optimized tag volume improves index relevance and recommendation search alignment.",
    color: "text-accent-violet border-accent-violet/20",
    glow: "rgba(124, 92, 255, 0.05)"
  }
];

export default function ExplainabilityReport() {
  const { progress, isActive } = useSceneProgress(5);

  // Layout animations
  const opacity = useTransform(progress, [0, 0.2, 0.85, 1], [0, 1, 1, 0], { clamp: true });
  const scale = useTransform(progress, [0, 0.25, 0.85, 1], [0.85, 1, 1, 0.8], { clamp: true });
  
  // SVG drawing line progress
  const lineProgress = useTransform(progress, [0.15, 0.6], [0, 1], { clamp: true });

  if (!isActive) return null;

  return (
    <motion.div 
      className="absolute inset-0 flex flex-col items-center justify-center p-6 z-10 select-none overflow-hidden"
      style={{ opacity, scale }}
    >
      {/* Background SVG Connective Network Lines */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none z-0">
        <motion.path
          d="M 100 100 L 900 100 M 100 300 L 900 300 M 100 100 L 100 300 M 900 100 L 900 300"
          stroke="rgba(79, 107, 255, 0.06)"
          strokeWidth="1"
          fill="none"
          className="hidden md:block"
        />
        {/* Dynamic growing crosshair lines connecting grid columns */}
        <motion.line
          x1="50%" y1="20%" x2="50%" y2="80%"
          stroke="rgba(124, 92, 255, 0.12)"
          strokeWidth="1.5"
          style={{ pathLength: lineProgress }}
        />
        <motion.line
          x1="15%" y1="50%" x2="85%" y2="50%"
          stroke="rgba(79, 107, 255, 0.12)"
          strokeWidth="1.5"
          style={{ pathLength: lineProgress }}
        />
      </svg>

      {/* Stage Header */}
      <div className="absolute top-24 left-1/2 -translate-x-1/2 text-center pointer-events-none z-10">
        <span className="text-[10px] uppercase tracking-[0.3em] text-accent-violet/80 font-bold block mb-2">Stage 05</span>
        <h2 className="text-3xl md:text-5xl font-extrabold tracking-tighter text-white uppercase">
          Explainability Report
        </h2>
        <p className="text-white/40 text-xs md:text-sm font-sans mt-2 max-w-sm mx-auto">
          Unfolding the SHAP attribution values driving the prediction weights.
        </p>
      </div>

      {/* Grid of Glass Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-5xl z-10 px-4 mt-16">
        {FEATURES.map((item, index) => {
          // Slide cards from different directions based on scroll
          const slideX = index % 2 === 0 ? -120 : 120;
          const slideY = index < 2 ? -60 : 60;
          
          const cardX = useTransform(progress, [0, 0.35], [slideX, 0], { clamp: true });
          const cardY = useTransform(progress, [0, 0.35], [slideY, 0], { clamp: true });
          const cardOpacity = useTransform(progress, [0, 0.25], [0, 1], { clamp: true });

          return (
            <motion.div
              key={index}
              className="glass-panel px-6 py-6 rounded-2xl border border-white/5 relative group cursor-default"
              style={{
                x: cardX,
                y: cardY,
                opacity: cardOpacity,
                boxShadow: `0 10px 40px -10px rgba(0,0,0,0.5), inset 0 0 20px ${item.glow}`
              }}
              whileHover={{ 
                scale: 1.02, 
                borderColor: index % 2 === 0 ? 'rgba(79, 107, 255, 0.25)' : 'rgba(124, 92, 255, 0.25)' 
              }}
              transition={{ type: "spring", stiffness: 100, damping: 20 }}
            >
              {/* Header inside card */}
              <div className="flex justify-between items-start mb-3">
                <span className="text-[10px] uppercase tracking-wider text-white/35 font-mono">Weight Allocation</span>
                <span className={`text-xl font-bold font-mono ${item.color.split(' ')[0]}`}>{item.weight}</span>
              </div>
              
              <h3 className="text-white text-lg font-bold tracking-tight mb-1">{item.title}</h3>
              <div className={`text-xs font-mono py-1 px-2.5 rounded bg-white/5 w-fit border ${item.color.split(' ')[1]} text-white/80 mb-3`}>
                {item.feature}
              </div>
              
              <p className="text-white/50 text-xs md:text-sm leading-relaxed font-sans font-light">
                {item.desc}
              </p>
            </motion.div>
          );
        })}
      </div>

      {/* Ambient Radial Bloom */}
      <div className="bloom-glow top-1/4 right-1/4 animate-pulse-slow" />
      <div className="bloom-glow-cyan bottom-1/4 left-1/4 animate-pulse-slow" style={{ animationDelay: '2s' }} />
    </motion.div>
  );
}
