import React from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck, ShieldAlert, Cpu } from 'lucide-react';

export default function HealthStatus({ modelHealth }) {
  if (!modelHealth) return null;

  const isDegraded = modelHealth.status === 'degraded';
  const isLoaded = modelHealth.model_loaded;
  
  // Render status, model_loaded, ready exactly as returned (or computed fallback for ready)
  const isReady = modelHealth.ready !== undefined 
    ? modelHealth.ready 
    : (modelHealth.status === 'ok' && isLoaded);

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="glass-panel border border-white/5 rounded-2xl p-5 md:p-6 space-y-4"
    >
      <div className="flex justify-between items-center border-b border-white/5 pb-3">
        <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center">
          <Cpu className="w-3.5 h-3.5 mr-2 text-accent-blue" />
          Model Service Health
        </h4>
        <div>
          {isDegraded ? (
            <span className="text-[9px] bg-rose-500/10 border border-rose-500/20 text-rose-400 font-bold px-2 py-0.5 rounded font-mono uppercase">
              DEGRADED
            </span>
          ) : (
            <span className="text-[9px] bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-bold px-2 py-0.5 rounded font-mono uppercase">
              HEALTHY
            </span>
          )}
        </div>
      </div>

      {/* Grid of properties exactly as returned */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-[10px] text-white/70">
        <div className="bg-white/5 border border-white/10 rounded-lg p-2.5">
          <span className="text-white/30 block mb-0.5 text-[8px] uppercase font-sans">Status</span>
          <span className="font-bold text-white uppercase">{modelHealth.status}</span>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-lg p-2.5">
          <span className="text-white/30 block mb-0.5 text-[8px] uppercase font-sans">Model Loaded</span>
          <span className={`font-bold ${isLoaded ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isLoaded ? 'TRUE' : 'FALSE'}
          </span>
        </div>
        <div className="bg-white/5 border border-white/10 rounded-lg p-2.5">
          <span className="text-white/30 block mb-0.5 text-[8px] uppercase font-sans">Ready</span>
          <span className={`font-bold ${isReady ? 'text-emerald-400' : 'text-rose-400'}`}>
            {isReady ? 'TRUE' : 'FALSE'}
          </span>
        </div>
      </div>

      {/* Warning/Readiness state */}
      {isDegraded && (
        <div className="bg-amber-500/5 border border-amber-500/15 p-3.5 rounded-xl flex items-start space-x-3 text-[10px] text-amber-500 font-sans leading-relaxed">
          <ShieldAlert className="w-4 h-4 mt-0.5 shrink-0" />
          <div>
            <strong>Model not available yet.</strong> Evaluated precision bounds or configuration layers are degraded. Training or activation action required.
          </div>
        </div>
      )}

      {!isDegraded && isLoaded && (
        <div className="bg-emerald-500/5 border border-emerald-500/15 p-3.5 rounded-xl flex items-start space-x-3 text-[10px] text-emerald-400 font-sans leading-relaxed">
          <ShieldCheck className="w-4 h-4 mt-0.5 shrink-0" />
          <div>
            <strong>Service status normalized.</strong> Active model version <strong>{modelHealth.model_version || 'N/A'}</strong> is running. Predict queries will return grounded outputs.
          </div>
        </div>
      )}

    </motion.div>
  );
}
