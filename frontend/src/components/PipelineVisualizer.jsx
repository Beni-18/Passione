import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, Cpu, FileText, Database, ShieldAlert, Sparkles } from 'lucide-react';

const STAGES = [
  { id: 0, label: "Reading Film Metadata", desc: "Checking schema formats and input bounds..." },
  { id: 1, label: "Encoding Feature Arrays", desc: "Processing categorical indices and label encodings..." },
  { id: 2, label: "Executing Inference Forest", desc: "Querying model weights and running classifier trees..." },
  { id: 3, label: "Computing Certainty Interval", desc: "Calculating SHAP attribution values and bounds..." },
  { id: 4, label: "Compiling Output Manifest", desc: "Assembling platform predictions card data..." }
];

export default function PipelineVisualizer({ payload, apiEndpoint, onPredictionComplete, onPredictionError }) {
  const [currentStage, setCurrentStage] = useState(0);
  const [stageProgress, setStageProgress] = useState(0);
  const [predictionData, setPredictionData] = useState(null);
  const [apiError, setApiError] = useState(null);

  // Trigger background fetch as soon as we start
  useEffect(() => {
    const runInference = async () => {
      try {
        const res = await fetch(apiEndpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        if (!res.ok) {
          if (res.status === 409) {
            throw new Error("No trained model is currently available");
          }
          const errJson = await res.json().catch(() => ({}));
          if (errJson?.error?.code === "MODEL_NOT_READY") {
            throw new Error("No trained model is currently available");
          }
          throw new Error(errJson?.error?.message || `HTTP error ${res.status}`);
        }

        const data = await res.json();
        setPredictionData(data);
      } catch (err) {
        setApiError(err.message || "Failed to establish API handshake.");
      }
    };

    runInference();
  }, [payload, apiEndpoint]);

  // Run the visual timeline loop
  useEffect(() => {
    let intervalId;
    let timerId;

    const runStage = (stageIdx) => {
      if (stageIdx >= STAGES.length) {
        // Timeline complete! Pass results back to coordinator
        if (apiError) {
          onPredictionError(apiError);
        } else if (predictionData) {
          onPredictionComplete(predictionData);
        } else {
          // If API takes longer, hold on the final stage
          setStageProgress(99);
          // Wait for data
          const checkInterval = setInterval(() => {
            if (predictionData) {
              clearInterval(checkInterval);
              onPredictionComplete(predictionData);
            } else if (apiError) {
              clearInterval(checkInterval);
              onPredictionError(apiError);
            }
          }, 100);
        }
        return;
      }

      setCurrentStage(stageIdx);
      setStageProgress(0);

      // Increment progress bar for current stage
      const stageDuration = stageIdx === 2 ? 1500 : 900; // Give model execution slightly longer weight
      const tickRate = 30;
      const increment = 100 / (stageDuration / tickRate);

      intervalId = setInterval(() => {
        setStageProgress(prev => {
          if (prev >= 100) {
            clearInterval(intervalId);
            runStage(stageIdx + 1);
            return 100;
          }
          return prev + increment;
        });
      }, tickRate);
    };

    runStage(0);

    return () => {
      clearInterval(intervalId);
      clearTimeout(timerId);
    };
  }, [predictionData, apiError, onPredictionComplete, onPredictionError]);

  const getStageIcon = (id) => {
    if (currentStage > id) {
      return (
        <motion.div 
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          className="w-7 h-7 rounded-full bg-accent-blue/10 border border-accent-blue/30 text-accent-blue flex items-center justify-center"
        >
          <Check className="w-4 h-4 stroke-[3]" />
        </motion.div>
      );
    }
    
    if (currentStage === id) {
      return (
        <div className="relative w-7 h-7">
          {/* Pulsing glow behind */}
          <div className="absolute inset-0 rounded-full bg-accent-blue/20 border border-accent-blue animate-ping" />
          <div className="absolute inset-0 rounded-full bg-[#0b0b0c] border border-accent-blue flex items-center justify-center text-accent-blue">
            {id === 0 && <FileText className="w-3.5 h-3.5" />}
            {id === 1 && <Database className="w-3.5 h-3.5" />}
            {id === 2 && <Cpu className="w-3.5 h-3.5 animate-spin [animation-duration:3s]" />}
            {id === 3 && <Sparkles className="w-3.5 h-3.5" />}
            {id === 4 && <Check className="w-3.5 h-3.5" />}
          </div>
        </div>
      );
    }

    return (
      <div className="w-7 h-7 rounded-full border border-white/5 bg-transparent text-white/20 flex items-center justify-center">
        <span className="font-mono text-[10px]">{id + 1}</span>
      </div>
    );
  };

  return (
    <div className="w-full max-w-lg mx-auto p-8 glass-panel rounded-3xl border border-white/5 text-center relative select-none">
      
      {/* Absolute floating lights */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-accent-blue/10 rounded-full filter blur-[80px] pointer-events-none" />

      {/* Progress Core Title */}
      <div className="mb-8">
        <span className="text-[10px] uppercase tracking-[0.25em] text-accent-blue/80 font-bold block mb-1">INFERENCE RUNNING</span>
        <h3 className="text-xl font-bold text-white uppercase tracking-wider">
          Processing Pipeline
        </h3>
        <p className="text-white/40 text-xs mt-1.5 font-sans">
          Deploying film metrics to the active TrendAI neural forest.
        </p>
      </div>

      {/* Sequential Steps list */}
      <div className="space-y-6 text-left relative z-10">
        {STAGES.map((stage) => {
          const isActive = currentStage === stage.id;
          const isCompleted = currentStage > stage.id;
          
          return (
            <div 
              key={stage.id}
              className={`flex items-start space-x-4 transition-all duration-300 ${
                isActive ? 'opacity-100 scale-[1.01]' : isCompleted ? 'opacity-60' : 'opacity-20'
              }`}
            >
              {getStageIcon(stage.id)}
              <div className="flex-1 min-w-0">
                <div className="flex justify-between items-baseline">
                  <h4 className={`text-xs uppercase tracking-wider font-bold ${isActive ? 'text-white' : 'text-white/70'}`}>
                    {stage.label}
                  </h4>
                  {isActive && (
                    <span className="font-mono text-[9px] text-accent-blue animate-pulse font-bold">
                      {Math.round(stageProgress)}%
                    </span>
                  )}
                </div>
                <p className="text-[10px] text-white/30 font-sans mt-0.5 truncate">{stage.desc}</p>
                
                {/* Visualizer inline progress bar slider */}
                {isActive && (
                  <div className="w-full h-[2px] bg-white/5 rounded-full overflow-hidden mt-2 relative">
                    <motion.div 
                      className="h-full bg-accent-blue shadow-[0_0_8px_#4F6BFF]"
                      style={{ width: `${stageProgress}%` }}
                      layout
                    />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* API connection status card */}
      <div className="mt-8 border-t border-white/5 pt-4 flex justify-between items-center text-[9px] font-mono text-white/30 uppercase">
        <div>Handshake Status: ACTIVE</div>
        <div>
          {apiError ? (
            <span className="text-rose-500 font-bold flex items-center">
              <ShieldAlert className="w-3.5 h-3.5 mr-1" /> CORE_ERROR
            </span>
          ) : predictionData ? (
            <span className="text-accent-blue font-bold animate-pulse">
              SYNC_ESTABLISHED
            </span>
          ) : (
            <span className="animate-pulse">AWAITING_API...</span>
          )}
        </div>
      </div>

    </div>
  );
}
