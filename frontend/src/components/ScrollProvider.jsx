import React, { useEffect, createContext, useContext } from 'react';
import Lenis from 'lenis';
import { useScroll } from 'framer-motion';

const ScrollContext = createContext(null);

export function ScrollProvider({ children }) {
  const { scrollYProgress } = useScroll();

  useEffect(() => {
    // Check if we are on a desktop device
    const isMobile = window.innerWidth < 768;
    if (isMobile) return;

    const lenis = new Lenis({
      duration: 1.4,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: 'vertical',
      gestureOrientation: 'vertical',
      smoothWheel: true,
      wheelMultiplier: 1.0,
      touchMultiplier: 1.2,
      infinite: false,
    });

    function raf(time) {
      lenis.raf(time);
      requestAnimationFrame(raf);
    }

    requestAnimationFrame(raf);
    window.lenis = lenis;

    return () => {
      lenis.destroy();
      delete window.lenis;
    };
  }, []);

  return (
    <ScrollContext.Provider value={{ scrollYProgress }}>
      {children}
    </ScrollContext.Provider>
  );
}

export function useGlobalScroll() {
  const context = useContext(ScrollContext);
  if (!context) {
    throw new Error('useGlobalScroll must be used within a ScrollProvider');
  }
  return context;
}
