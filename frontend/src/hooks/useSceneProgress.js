import { useTransform } from 'framer-motion';
import { useGlobalScroll } from '../components/ScrollProvider';
import { useState, useEffect } from 'react';

export const SCENE_RANGES = [
  { start: 0.00, end: 0.20, name: "Hero" },
  { start: 0.15, end: 0.38, name: "Metadata" },
  { start: 0.32, end: 0.55, name: "HUD" },
  { start: 0.48, end: 0.72, name: "Sphere" },
  { start: 0.65, end: 0.86, name: "Prediction" },
  { start: 0.80, end: 1.00, name: "Platform" }
];

export function useSceneProgress(index) {
  const { scrollYProgress } = useGlobalScroll();
  const range = SCENE_RANGES[index];
  
  // Transform the global scroll progress to [0, 1] relative to the scene's window
  const progress = useTransform(
    scrollYProgress,
    [range.start, range.end],
    [0, 1],
    { clamp: true }
  );

  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    // Detect whether the current scroll position is in the scene's window
    const checkActive = (val) => {
      const active = val >= range.start && val <= range.end;
      setIsActive(active);
    };

    // Initialize
    checkActive(scrollYProgress.get());

    const unsubscribe = scrollYProgress.on('change', checkActive);
    return () => unsubscribe();
  }, [scrollYProgress, range.start, range.end]);

  return { progress, isActive, globalProgress: scrollYProgress };
}
