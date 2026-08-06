import React from 'react';
import { motion, useTransform } from 'framer-motion';
import { useSceneProgress } from '../hooks/useSceneProgress';
import InferenceStudio from '../components/InferenceStudio';

export default function PlatformLaunch() {
  const { progress, isActive } = useSceneProgress(6);

  // Entrance animations based on scroll progress of the final scene (Stage 6)
  const opacity = useTransform(progress, [0, 0.25], [0, 1], { clamp: true });
  const scale = useTransform(progress, [0, 0.25], [0.96, 1], { clamp: true });

  if (!isActive) return null;

  return (
    <motion.div 
      className="absolute inset-0 flex flex-col items-center justify-center p-4 md:p-8 z-10 overflow-y-auto select-none"
      style={{ opacity, scale }}
    >
      <InferenceStudio />
    </motion.div>
  );
}
