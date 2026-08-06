import React from 'react';
import { motion } from 'framer-motion';
import { RefreshCw, CheckCircle, AlertTriangle, Cpu, TrendingUp, Info } from 'lucide-react';

export default function PredictionResult({ prediction, payload, onReset }) {
  const isGrounded = prediction?.grounded;
  const scorePercent = isGrounded ? Math.round(prediction.trending_probability * 100) : null;
  const predictedLabel = prediction?.predicted_label;
  const topFeatures = prediction?.top_features || [];
  const modelVersion = prediction?.model_version || 'rf_v3';

  // Circular gauge config
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const strokeOffset = circumference - (scorePercent / 100) * circumference;

  return (
    <div className="w-full max-w-4xl mx-auto glass-panel rounded-3xl p-6 md:p-8 border border-white/5 relative z-10 select-none">
      
      {/* Background radial spotlights */}
      <div className="absolute top-0 left-0 w-64 h-64 bg-accent-blue/10 rounded-full filter blur-[100px] pointer-events-none -z-10" />
      <div className="absolute bottom-0 right-0 w-64 h-64 bg-accent-violet/5 rounded-full filter blur-[100px] pointer-events-none -z-10" />

      {/* Card Header */}
      <div className="flex justify-between items-center pb-6 border-b border-white/5 mb-8">
        <div>
          <span className="text-[10px] uppercase tracking-[0.25em] text-accent-blue/80 font-bold block mb-1">INFERENCE RESULT</span>
          <h3 className="text-xl font-extrabold text-white uppercase tracking-wider">
            Prediction Dashboard
          </h3>
        </div>
        <div className="flex items-center space-x-3 text-xs font-mono text-white/50 bg-white/5 px-3.5 py-1.5 rounded-lg border border-white/5">
          <Cpu className="w-4 h-4 text-accent-blue" />
          <span>Active Model: {modelVersion}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        
        {/* Left column: Circular gauge */}
        <div className="lg:col-span-5 flex flex-col items-center justify-center text-center">
          {isGrounded ? (
            <div className="relative flex items-center justify-center w-48 h-48 mb-4">
              {/* SVG Radial Progress */}
              <svg className="w-full h-full transform -rotate-90">
                {/* Track circle */}
                <circle
                  cx="96"
                  cy="96"
                  r={radius}
                  stroke="rgba(255,255,255,0.03)"
                  strokeWidth="8"
                  fill="none"
                />
                {/* Progress circle */}
                <motion.circle
                  cx="96"
                  cy="96"
                  r={radius}
                  stroke="url(#result-gradient)"
                  strokeWidth="8"
                  strokeDasharray={circumference}
                  initial={{ strokeDashoffset: circumference }}
                  animate={{ strokeDashoffset: strokeOffset }}
                  transition={{ duration: 1.5, ease: "easeOut" }}
                  fill="none"
                  strokeLinecap="round"
                />
                
                {/* Linear gradient definitions */}
                <defs>
                  <linearGradient id="result-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#4F6BFF" />
                    <stop offset="100%" stopColor="#7C5CFF" />
                  </linearGradient>
                </defs>
              </svg>

              {/* Inside text */}
              <div className="absolute text-center flex flex-col items-center">
                <span className="text-[9px] uppercase tracking-widest text-white/30 font-mono mb-1">SCORE</span>
                <span className="text-4xl font-black text-white font-sans">{scorePercent}%</span>
                <span className="text-[10px] text-accent-blue uppercase tracking-wider font-semibold font-mono mt-1 bg-accent-blue/10 border border-accent-blue/15 px-2 py-0.5 rounded">
                  {predictedLabel}
                </span>
              </div>
            </div>
          ) : (
            <div className="w-40 h-40 rounded-full bg-amber-500/5 border border-amber-500/10 flex items-center justify-center mb-4 relative">
              <div className="absolute inset-0 rounded-full bg-amber-500/10 animate-ping [animation-duration:3s]" />
              <AlertTriangle className="w-12 h-12 text-amber-500" />
            </div>
          )}

          <div className="text-center">
            <h4 className="text-sm font-bold text-white uppercase tracking-wider">
              {isGrounded ? 'Prediction Settled' : 'Ungrounded Prediction'}
            </h4>
            <p className="text-xs text-white/40 font-sans mt-2 max-w-xs leading-relaxed">
              {isGrounded 
                ? `TrendAI model predicts a ${scorePercent}% likelihood that '${payload.title}' will trends in targeted region.`
                : 'The parameters provided triggers out-of-distribution limits or failed certainty checks.'}
            </p>
          </div>
        </div>

        {/* Right column: Attribution / Metrics */}
        <div className="lg:col-span-7 space-y-6">
          
          {isGrounded ? (
            // Key Attribution details
            <div className="space-y-3.5">
              <h4 className="text-[10px] font-mono uppercase tracking-widest text-white/40 flex items-center">
                <TrendingUp className="w-4 h-4 mr-2 text-accent-blue" />
                Attribution Analysis (SHAP)
              </h4>
              
              {topFeatures.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {topFeatures.map((feat, idx) => (
                    <span 
                      key={idx} 
                      className="text-[10px] font-mono bg-white/5 border border-white/10 px-3 py-1.5 rounded-lg text-white/70 flex items-center"
                    >
                      <span className="w-1 h-1 rounded-full bg-accent-blue mr-2" />
                      {feat}
                    </span>
                  ))}
                </div>
              ) : (
                <div className="bg-white/[0.01] border border-white/5 rounded-xl p-3.5 text-center text-xs text-white/30 font-sans font-light">
                  No dominant attribution indicators parsed.
                </div>
              )}
              <p className="text-[10px] text-white/35 font-sans leading-relaxed pt-1.5">
                 Attributions indicate which input values contributed most to the Trending label forecast.
              </p>
            </div>
          ) : (
            // Reason details
            <div className="space-y-4 bg-amber-500/5 border border-amber-500/25 rounded-2xl p-5">
              <h4 className="text-xs font-bold text-amber-500 uppercase tracking-wider flex items-center font-mono">
                <AlertTriangle className="w-4 h-4 mr-2" /> Warning Code
              </h4>
              <p className="text-xs text-white/70 leading-relaxed font-sans font-light">
                This film configuration contains attributes that have never been seen in the historical dataset, or metadata is insufficient to construct a safe prediction.
              </p>
              <div className="bg-black/30 border border-amber-500/10 p-3 rounded-lg font-mono text-[10px] text-amber-500/90 leading-relaxed">
                REASON: {prediction?.reason || 'Calculated confidence levels fall below model grounding filters.'}
              </div>
            </div>
          )}

          {/* Core metadata summary */}
          <div className="border-t border-white/5 pt-5 space-y-3">
            <span className="text-[10px] font-mono text-white/40 uppercase tracking-wider block">Attribute Snapshot</span>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 font-mono text-[10px] text-white/60">
              <div className="bg-white/5 border border-white/10 rounded-lg p-2.5">
                <span className="text-white/30 block mb-1 text-[8px] uppercase tracking-wider font-sans">Title</span>
                <span className="truncate block font-bold text-white">{payload.title}</span>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-lg p-2.5">
                <span className="text-white/30 block mb-1 text-[8px] uppercase tracking-wider font-sans">Genre</span>
                <span className="truncate block font-bold text-white">{payload.genre}</span>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-lg p-2.5">
                <span className="text-white/30 block mb-1 text-[8px] uppercase tracking-wider font-sans">Duration</span>
                <span className="truncate block font-bold text-white">{payload.duration_minutes}m</span>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-lg p-2.5">
                <span className="text-white/30 block mb-1 text-[8px] uppercase tracking-wider font-sans">Language</span>
                <span className="truncate block font-bold text-white">{payload.language}</span>
              </div>
            </div>
          </div>

        </div>

      </div>

      {/* Bottom Reset CTA */}
      <div className="mt-8 border-t border-white/5 pt-6 flex justify-end">
        <button
          onClick={onReset}
          className="bg-white/5 hover:bg-white/10 border border-white/10 text-white font-bold font-mono tracking-widest text-[10px] uppercase px-5 py-3 rounded-lg flex items-center transition-colors cursor-pointer"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Run another prediction
        </button>
      </div>

    </div>
  );
}
