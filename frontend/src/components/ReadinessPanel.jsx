import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Sparkles, ArrowRight, ShieldCheck, CheckCircle2, ShieldAlert } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function ReadinessPanel({ formData, onPredictClick }) {
  const [health, setHealth] = useState(null);
  const [loadingHealth, setLoadingHealth] = useState(true);

  useEffect(() => {
    fetchHealth();
  }, []);

  const fetchHealth = async () => {
    setLoadingHealth(true);
    try {
      const res = await fetch(`${API_BASE}/health`);
      if (res.ok) {
        setHealth(await res.json());
      }
    } catch (e) {
      console.warn("API health endpoint offline.", e);
    } finally {
      setLoadingHealth(false);
    }
  };

  // Define fields and check completion
  const requiredFields = [
    { key: 'title', label: 'Film Title' },
    { key: 'genre', label: 'Content Genre' },
    { key: 'duration_minutes', label: 'Film Duration' },
    { key: 'language', label: 'Primary Language' },
    { key: 'upload_time', label: 'Release Schedule' }
  ];

  const optionalFields = [
    { key: 'budget', label: 'Production Budget' },
    { key: 'target_region', label: 'Target Audience Region' },
    { key: 'distribution', label: 'Distribution Channel' },
    { key: 'pace', label: 'Narrative Pace' },
    { key: 'tags', label: 'Metadata Tags' },
    { key: 'star_power', label: 'Lead Actor Status' },
    { key: 'marketing_campaign', label: 'Marketing Campaign Scale' }
  ];

  const completedRequired = requiredFields.filter(f => !!formData[f.key]);
  const completedOptional = optionalFields.filter(f => {
    const val = formData[f.key];
    return val !== undefined && val !== null && val !== "";
  });

  const totalRequiredCount = requiredFields.length;
  const totalOptionalCount = optionalFields.length;
  const totalCount = totalRequiredCount + totalOptionalCount;
  const totalCompletedCount = completedRequired.length + completedOptional.length;

  const requiredOk = completedRequired.length === totalRequiredCount;
  const completionPercent = Math.round((totalCompletedCount / totalCount) * 100);

  return (
    <div className="glass-panel rounded-2xl p-6 border border-white/5 flex flex-col justify-between h-full relative overflow-hidden">
      
      {/* Background radial glow */}
      <div className="absolute top-0 right-0 w-48 h-48 bg-accent-blue/5 rounded-full filter blur-3xl pointer-events-none -z-10" />

      <div className="space-y-6">
        {/* Panel Header */}
        <div className="flex justify-between items-center pb-4 border-b border-white/5">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center">
            <Sparkles className="w-4 h-4 mr-2 text-accent-blue" />
            AI Readiness
          </h3>

          {/* API Health State */}
          <div className="flex items-center text-[10px] font-mono">
            {loadingHealth ? (
              <span className="text-white/30 animate-pulse">CHECKING...</span>
            ) : health?.status === 'ok' ? (
              <span className="text-emerald-500 font-bold flex items-center bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">
                MODEL: {health.model_version || 'ACTIVE'}
              </span>
            ) : (
              <span className="text-amber-500 font-bold flex items-center bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded">
                STUB ACTIVE
              </span>
            )}
          </div>
        </div>

        {/* Live Completion Bar */}
        <div className="space-y-2">
          <div className="flex justify-between items-end font-mono text-[10px]">
            <span className="text-white/40 uppercase tracking-widest">Pipeline Integration</span>
            <span className="text-white font-bold text-xs">{completionPercent}%</span>
          </div>

          {/* Bar track */}
          <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden border border-white/5 relative">
            <motion.div
              className={`h-full rounded-full transition-all duration-500 ${
                requiredOk
                  ? "bg-gradient-to-r from-accent-blue to-accent-violet shadow-[0_0_10px_#4F6BFF]"
                  : "bg-amber-500 shadow-[0_0_10px_#f59e0b]"
              }`}
              style={{ width: `${completionPercent}%` }}
              layout
            />
          </div>
          <div className="flex justify-between font-mono text-[9px] text-white/30">
            <span>Features parsed: {totalCompletedCount} / {totalCount}</span>
            <span>Grounded predictions: {requiredOk ? 'AVAILABLE' : 'PENDING'}</span>
          </div>
        </div>

        {/* Validation Steps */}
        <div className="space-y-4 pt-2">
          {/* Required Fields Block */}
          <div className="space-y-2.5">
            <h4 className="text-[10px] font-mono uppercase tracking-widest text-white/40 flex items-center">
              {requiredOk ? (
                <ShieldCheck className="w-4 h-4 mr-2 text-accent-blue" />
              ) : (
                <ShieldAlert className="w-4 h-4 mr-2 text-amber-500 animate-pulse" />
              )}
              Required Features ({completedRequired.length}/{totalRequiredCount})
            </h4>

            <div className="grid grid-cols-2 gap-2">
              {requiredFields.map(f => {
                const filled = !!formData[f.key];
                return (
                  <div
                    key={f.key}
                    className={`flex items-center space-x-2 border rounded-lg p-2 font-mono text-[9px] transition-colors duration-300 ${
                      filled
                        ? "border-accent-blue/20 bg-accent-blue/5 text-white"
                        : "border-white/5 bg-white/[0.01] text-white/30"
                    }`}
                  >
                    <CheckCircle2 className={`w-3.5 h-3.5 flex-shrink-0 ${filled ? 'text-accent-blue' : 'text-white/10'}`} />
                    <span className="truncate">{f.label}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Optional Extended Attributes */}
          <div className="space-y-2.5 pt-2">
            <h4 className="text-[10px] font-mono uppercase tracking-widest text-white/40 flex items-center">
              <CheckCircle2 className="w-4 h-4 mr-2 text-white/20" />
              Extended Parameters ({completedOptional.length}/{totalOptionalCount})
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {optionalFields.map(f => {
                const filled = formData[f.key] !== undefined && formData[f.key] !== null && formData[f.key] !== "";
                return (
                  <span
                    key={f.key}
                    className={`text-[8px] font-mono px-2 py-1 rounded-md border tracking-wider transition-colors duration-300 ${
                      filled
                        ? "border-accent-violet/30 bg-accent-violet/5 text-accent-violet-light font-bold"
                        : "border-white/5 bg-transparent text-white/20"
                    }`}
                  >
                    {f.label}
                  </span>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Actionpredict Trigger */}
      <div className="pt-6 mt-6 border-t border-white/5">
        <motion.button
          onClick={onPredictClick}
          disabled={!requiredOk}
          whileHover={requiredOk ? { scale: 1.02, y: -1 } : {}}
          whileTap={requiredOk ? { scale: 0.98 } : {}}
          className={`w-full py-4 rounded-xl text-xs font-bold uppercase tracking-[0.2em] transition-all duration-300 flex items-center justify-center cursor-pointer ${
            requiredOk
              ? "bg-gradient-to-r from-accent-blue to-accent-violet text-white shadow-[0_0_20px_rgba(79,107,255,0.3)] hover:shadow-[0_0_30px_rgba(124,92,255,0.4)] border border-accent-blue/30"
              : "bg-white/5 border border-white/5 text-white/20 cursor-not-allowed"
          }`}
        >
          Generate Prediction
          <motion.span
            animate={requiredOk ? { x: [0, 5, 0] } : {}}
            transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          >
            <ArrowRight className="w-4 h-4 ml-2.5" />
          </motion.span>
        </motion.button>
        {!requiredOk && (
          <p className="text-[9px] text-center text-white/25 mt-2.5 font-sans leading-relaxed">
            Fill in all required basic information fields to run prediction.
          </p>
        )}
      </div>

    </div>
  );
}
