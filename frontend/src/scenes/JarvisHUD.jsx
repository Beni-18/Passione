import React, { useEffect, useRef } from 'react';
import { motion, useTransform } from 'framer-motion';
import { useSceneProgress } from '../hooks/useSceneProgress';

export default function JarvisHUD() {
  const { progress, isActive } = useSceneProgress(2);
  const canvasRef = useRef(null);

  // SVG drawing transformations
  const pathLength1 = useTransform(progress, [0.0, 0.6], [0, 1]);
  const pathLength2 = useTransform(progress, [0.1, 0.7], [0, 1]);
  const pathLength3 = useTransform(progress, [0.2, 0.8], [0, 1]);
  
  const hudRotate1 = useTransform(progress, [0, 1], [0, 180]);
  const hudRotate2 = useTransform(progress, [0, 1], [360, 90]);
  
  const opacity = useTransform(progress, [0, 0.2, 0.8, 1], [0, 1, 1, 0]);
  const hudScale = useTransform(progress, [0, 0.3, 0.8, 1], [0.8, 1, 1, 0.7]);

  // Particle simulation loop
  useEffect(() => {
    if (!isActive || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    let animationFrameId;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // Create particles originating from edges and flowing to center
    const particles = [];
    const maxParticles = 120;
    const centerX = width / 2;
    const centerY = height / 2;

    class Particle {
      constructor() {
        this.reset();
      }

      reset() {
        // Start on a random circle around center
        const angle = Math.random() * Math.PI * 2;
        const distance = Math.max(width, height) * 0.5 * (1 + Math.random() * 0.2);
        this.x = centerX + Math.cos(angle) * distance;
        this.y = centerY + Math.sin(angle) * distance;
        this.speed = 1.5 + Math.random() * 3.5;
        this.size = 1 + Math.random() * 2;
        
        // Custom orbit offset
        this.orbitOffset = (Math.random() - 0.5) * 50;
        
        // Random color accent (blue or violet)
        this.color = Math.random() > 0.4 ? 'rgba(79, 107, 255,' : 'rgba(124, 92, 255,';
        this.alpha = 0.1;
      }

      update(scrollVal) {
        // Direct vector to center
        const dx = centerX - this.x;
        const dy = centerY - this.y;
        const dist = Math.sqrt(dx * dx + dy * dy);

        if (dist < 10) {
          this.reset();
          return;
        }

        // Particle speed increases as it gets closer and based on scroll acceleration
        const currentSpeed = this.speed * (1 + scrollVal * 3) * (1 - dist / Math.max(width, height));
        
        // Move towards center with slightly spiral behavior
        const angle = Math.atan2(dy, dx);
        // Add orbit drift
        const orbitAngle = angle + (dist > 100 ? (this.orbitOffset / dist) : 0);
        
        this.x += Math.cos(orbitAngle) * currentSpeed;
        this.y += Math.sin(orbitAngle) * currentSpeed;
        
        // Fade in as it enters workspace, then fade out near center core
        if (dist > 300) {
          this.alpha = Math.min(0.8, this.alpha + 0.05);
        } else {
          this.alpha = Math.max(0.1, dist / 300);
        }
      }

      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fillStyle = `${this.color}${this.alpha})`;
        ctx.shadowBlur = 4;
        ctx.shadowColor = this.color.includes('79') ? '#4F6BFF' : '#7C5CFF';
        ctx.fill();
      }
    }

    // Initialize particles
    for (let i = 0; i < maxParticles; i++) {
      particles.push(new Particle());
    }

    // Main drawing loop
    const render = () => {
      // Clear with slight alpha to create trail effect
      ctx.fillStyle = 'rgba(7, 7, 8, 0.3)';
      ctx.fillRect(0, 0, width, height);

      // Get latest scroll progress
      const scrollVal = progress.get();

      particles.forEach((p) => {
        p.update(scrollVal);
        p.draw();
      });

      // Optional: Draw connector lines between nearby particles when scroll progress is high
      if (scrollVal > 0.5) {
        ctx.strokeStyle = 'rgba(79, 107, 255, 0.08)';
        ctx.lineWidth = 0.5;
        for (let i = 0; i < particles.length; i++) {
          for (let j = i + 1; j < particles.length; j++) {
            const dx = particles[i].x - particles[j].x;
            const dy = particles[i].y - particles[j].y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 80) {
              ctx.beginPath();
              ctx.moveTo(particles[i].x, particles[i].y);
              ctx.lineTo(particles[j].x, particles[j].y);
              ctx.stroke();
            }
          }
        }
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
    };
  }, [isActive, progress]);

  if (!isActive) return null;

  return (
    <motion.div 
      className="absolute inset-0 flex flex-col items-center justify-center p-6 z-10 select-none overflow-hidden"
      style={{ opacity }}
    >
      {/* Simulation canvas */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />

      {/* SVG Jarvis Rings HUD */}
      <motion.div 
        className="relative w-[320px] h-[320px] md:w-[500px] md:h-[500px] flex items-center justify-center pointer-events-none z-10"
        style={{ scale: hudScale }}
      >
        <svg viewBox="0 0 200 200" className="w-full h-full absolute">
          {/* Outer Segmented Circle */}
          <motion.circle
            cx="100"
            cy="100"
            r="90"
            stroke="url(#blue-violet)"
            strokeWidth="0.5"
            fill="none"
            strokeDasharray="6 2 12 4 48 6"
            style={{ pathLength: pathLength1, rotate: hudRotate1 }}
          />

          {/* Middle Ring */}
          <motion.circle
            cx="100"
            cy="100"
            r="75"
            stroke="#4F6BFF"
            strokeWidth="1"
            fill="none"
            strokeDasharray="180 40 10 20"
            style={{ pathLength: pathLength2, rotate: hudRotate2 }}
          />

          {/* Inner Dotted Ring */}
          <motion.circle
            cx="100"
            cy="100"
            r="60"
            stroke="#7C5CFF"
            strokeWidth="0.75"
            fill="none"
            strokeDasharray="1 4"
            style={{ pathLength: pathLength3, rotate: hudRotate1 }}
          />

          {/* Target Scopes / Crosshairs */}
          <motion.path
            d="M 100 15 L 100 25 M 100 175 L 100 185 M 15 100 L 25 100 M 175 100 L 185 100"
            stroke="rgba(255,255,255,0.25)"
            strokeWidth="0.75"
            style={{ pathLength: pathLength1 }}
          />

          {/* Gradients */}
          <defs>
            <linearGradient id="blue-violet" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#4F6BFF" />
              <stop offset="100%" stopColor="#7C5CFF" />
            </linearGradient>
          </defs>
        </svg>

        {/* Center Loading Data Text */}
        <div className="text-center flex flex-col items-center">
          <span className="text-[9px] uppercase tracking-[0.25em] text-white/40 mb-1">Processing Pipeline</span>
          <div className="font-mono text-xs md:text-sm text-accent-blue font-bold flex items-center">
            <span className="w-1.5 h-1.5 rounded-full bg-accent-blue animate-pulse mr-2" />
            NEURAL_ENCODING_ACTIVATED
          </div>
          <span className="font-mono text-[9px] text-white/30 mt-1">
            EPOCH: {Math.floor(progress.get() * 100)} / 100
          </span>
        </div>
      </motion.div>

      {/* Title Header */}
      <div className="absolute top-24 left-1/2 -translate-x-1/2 text-center pointer-events-none z-0">
        <span className="text-[10px] uppercase tracking-[0.3em] text-accent-violet/80 font-bold block mb-2">Stage 02</span>
        <h2 className="text-3xl md:text-5xl font-extrabold tracking-tighter text-white uppercase">
          AI Processing Core
        </h2>
        <p className="text-white/40 text-xs md:text-sm font-sans mt-2 max-w-sm mx-auto">
          Aggregating features and weights within the deep network layers.
        </p>
      </div>
    </motion.div>
  );
}
