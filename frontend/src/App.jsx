import React, { useEffect } from 'react';
import { motion, useTransform, useMotionValue, useSpring } from 'framer-motion';
import { ScrollProvider, useGlobalScroll } from './components/ScrollProvider';
import HeroVideo from './scenes/HeroVideo';
import MetadataCloud from './scenes/MetadataCloud';
import JarvisHUD from './scenes/JarvisHUD';
import AISphere from './scenes/AISphere';
import PredictionReveal from './scenes/PredictionReveal';
import PlatformLaunch from './scenes/PlatformLaunch';

const PIPELINE_STAGES = [
  { label: "Hero", scrollPos: 0.08 },
  { label: "Metadata", scrollPos: 0.25 },
  { label: "Features", scrollPos: 0.42 },
  { label: "AI", scrollPos: 0.60 },
  { label: "Predict", scrollPos: 0.75 },
  { label: "Platform", scrollPos: 0.92 }
];

// Inner Coordinator layout that consumes ScrollContext
function MainLayout() {
  const { scrollYProgress } = useGlobalScroll();

  // Mouse Cursor Spot Trail
  const cursorX = useMotionValue(-100);
  const cursorY = useMotionValue(-100);
  const springCursorX = useSpring(cursorX, { stiffness: 220, damping: 22 });
  const springCursorY = useSpring(cursorY, { stiffness: 220, damping: 22 });

  useEffect(() => {
    const handleMouseMove = (e) => {
      // Offset cursor center
      cursorX.set(e.clientX - 12);
      cursorY.set(e.clientY - 12);
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, [cursorX, cursorY]);

  // Video Background Transformations
  // As user scrolls, video gets slightly blurred and dims to focus visual attention on HUD and text
  const videoOpacity = useTransform(scrollYProgress, [0.0, 0.2, 0.8, 1.0], [0.75, 0.3, 0.15, 0.05], { clamp: true });
  const videoBlur = useTransform(scrollYProgress, [0.0, 0.15, 0.4, 0.9], ["blur(0px)", "blur(4px)", "blur(8px)", "blur(12px)"], { clamp: true });
  const videoScale = useTransform(scrollYProgress, [0, 1], [1, 1.15], { clamp: true });

  const handleStageClick = (index) => {
    const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrollTarget = scrollHeight * PIPELINE_STAGES[index].scrollPos;
    
    if (window.lenis) {
      window.lenis.scrollTo(scrollTarget, { duration: 1.5 });
    } else {
      window.scrollTo({
        top: scrollTarget,
        behavior: 'smooth'
      });
    }
  };

  return (
    <div className="relative w-full h-[700vh] bg-bg-dark text-white select-none">
      
      {/* Absolute Cursor-Bot Spotlight */}
      <motion.div 
        className="hidden md:block fixed w-6 h-6 rounded-full border border-accent-blue/30 bg-accent-blue/5 shadow-[0_0_15px_rgba(79,107,255,0.4)] pointer-events-none z-50 mix-blend-screen"
        style={{
          x: springCursorX,
          y: springCursorY
        }}
      />

      {/* Persistent Tiny Header / Navbar */}
      <nav className="fixed top-0 inset-x-0 h-16 flex items-center justify-between px-6 md:px-12 z-40 select-none backdrop-blur-xs border-b border-white/[0.02]">
        <div className="font-bold tracking-tight text-white uppercase text-sm">
          Trend<span className="text-accent-blue">AI</span>
        </div>
        <div className="hidden md:flex items-center space-x-6 text-[10px] tracking-[0.2em] uppercase font-mono text-white/50">
          <span className="hover:text-white transition-colors cursor-pointer">Experience</span>
          <span className="hover:text-white transition-colors cursor-pointer">Pipeline</span>
          <span className="hover:text-white transition-colors cursor-pointer">Platform</span>
          <span className="hover:text-white transition-colors cursor-pointer">About</span>
        </div>
        <button 
          onClick={() => handleStageClick(5)}
          className="px-4 py-1.5 rounded-full border border-white/10 hover:border-accent-blue/40 bg-white/5 text-[10px] font-bold font-mono tracking-widest text-white cursor-pointer transition-colors"
        >
          Launch App
        </button>
      </nav>

      {/* Fixed Fullscreen Viewport Layer */}
      <div className="fixed inset-0 w-screen h-screen overflow-hidden bg-grid">
        
        {/* Global Video Layer */}
        <motion.video
          autoPlay
          loop
          muted
          playsInline
          src="/background.mp4"
          className="absolute inset-0 w-full h-full object-cover z-0"
          style={{
            opacity: videoOpacity,
            filter: videoBlur,
            scale: videoScale
          }}
        />

        {/* Scene Stack */}
        <HeroVideo />
        <MetadataCloud />
        <JarvisHUD />
        <AISphere />
        <PredictionReveal />
        <PlatformLaunch />

        {/* HUD Sidebar Navigation */}
        <div className="fixed right-6 md:right-12 top-1/2 -translate-y-1/2 flex flex-col space-y-4 z-40">
          {PIPELINE_STAGES.map((stage, idx) => {
            // Highlight step if progress is near it
            const startVal = idx === 0 ? 0 : PIPELINE_STAGES[idx].scrollPos - 0.07;
            const endVal = idx === PIPELINE_STAGES.length - 1 ? 1.0 : PIPELINE_STAGES[idx].scrollPos + 0.07;
            
            const dotColor = useTransform(
              scrollYProgress,
              [startVal, PIPELINE_STAGES[idx].scrollPos, endVal],
              ["rgba(255, 255, 255, 0.2)", "rgba(79, 107, 255, 1)", "rgba(255, 255, 255, 0.2)"],
              { clamp: true }
            );
            
            const labelOpacity = useTransform(
              scrollYProgress,
              [startVal, PIPELINE_STAGES[idx].scrollPos, endVal],
              [0.2, 1.0, 0.2],
              { clamp: true }
            );


            return (
              <button 
                key={idx}
                onClick={() => handleStageClick(idx)}
                className="flex items-center justify-end group text-right cursor-pointer outline-none space-x-2.5"
              >
                <motion.span 
                  className="font-sans text-[10px] tracking-wider text-white hidden md:block select-none pointer-events-none uppercase font-bold"
                  style={{ opacity: labelOpacity }}
                >
                  {stage.label}
                </motion.span>
                <motion.div 
                  className="w-1.5 h-1.5 rounded-full border border-white/20 group-hover:border-accent-blue/50 transition-colors"
                  style={{ backgroundColor: dotColor }}
                />
              </button>
            );
          })}
        </div>

        {/* Horizontal Overall Progress Bar */}
        <div className="fixed bottom-0 left-0 w-full h-[2px] bg-white/[0.02] z-40">
          <motion.div 
            className="h-full bg-gradient-to-r from-accent-blue to-accent-violet shadow-[0_0_8px_#4F6BFF]"
            style={{
              scaleX: scrollYProgress,
              transformOrigin: "left"
            }}
          />
        </div>
      </div>
      
    </div>
  );
}

export default function App() {
  return (
    <ScrollProvider>
      <MainLayout />
    </ScrollProvider>
  );
}
