import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react';

export default function TrainingStatus({
  status,
  jobId,
  rowsTotal,
  rowsProcessed,
  rowsFailed,
  message,
  metrics,
  onReset
}) {
  const isComplete = status === 'complete';
  const isFailed = status === 'failed';
  const isRunning = status === 'training' || status === 'queued';

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="glass-panel border border-white/5 rounded-2xl p-5 md:p-6 space-y-5"
    >
      <div className="flex justify-between items-center border-b border-white/5 pb-3">
        <h4 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
          Training Monitor
        </h4>
        <div className="text-[9px] font-mono text-white/40">
          JOB_ID: {jobId}
        </div>
      </div>

      {/* Status Indicators */}
      <div className="flex items-center space-x-3">
        {isRunning && (
          <div className="flex items-center text-accent-blue text-xs font-bold uppercase tracking-wider font-mono">
            <Loader2 className="w-4 h-4 mr-2 animate-spin text-accent-blue" />
            Job {status === 'queued' ? 'Queued' : 'Processing'}...
          </div>
        )}
        {isComplete && (
          <div className="flex items-center text-emerald-400 text-xs font-bold uppercase tracking-wider font-mono">
            <CheckCircle2 className="w-4 h-4 mr-2" />
            Training Complete
          </div>
        )}
        {isFailed && (
          <div className="flex items-center text-rose-400 text-xs font-bold uppercase tracking-wider font-mono">
            <AlertTriangle className="w-4 h-4 mr-2" />
            Training Failed
          </div>
        )}
      </div>

      {/* Rows stats */}
      <div className="grid grid-cols-3 gap-3 bg-white/[0.01] border border-white/5 p-3.5 rounded-xl text-center font-mono">
        <div>
          <span className="text-[8px] text-white/30 uppercase tracking-wider block mb-0.5">Rows Total</span>
          <span className="text-xs text-white/80">{rowsTotal}</span>
        </div>
        <div>
          <span className="text-[8px] text-white/30 uppercase tracking-wider block mb-0.5">Processed</span>
          <span className="text-xs text-white/80">{rowsProcessed}</span>
        </div>
        <div>
          <span className="text-[8px] text-white/30 uppercase tracking-wider block mb-0.5">Failed</span>
          <span className="text-xs text-rose-400/90">{rowsFailed}</span>
        </div>
      </div>

      {/* Metrics Card */}
      {isComplete && (
        <div className="space-y-3">
          <span className="text-[9px] font-mono text-white/40 uppercase tracking-widest block">Model Performance Metrics</span>
          {metrics ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 font-mono text-[10px] text-white/70">
              <div className="bg-white/5 border border-white/10 rounded-lg p-2">
                <span className="text-white/30 block mb-0.5 text-[8px] uppercase font-sans">Accuracy</span>
                <span className="font-bold text-white">{(metrics.accuracy * 100).toFixed(1)}%</span>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-lg p-2">
                <span className="text-white/30 block mb-0.5 text-[8px] uppercase font-sans">Precision</span>
                <span className="font-bold text-white">{metrics.precision?.toFixed(3)}</span>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-lg p-2">
                <span className="text-white/30 block mb-0.5 text-[8px] uppercase font-sans">Recall</span>
                <span className="font-bold text-white">{metrics.recall?.toFixed(3)}</span>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-lg p-2">
                <span className="text-white/30 block mb-0.5 text-[8px] uppercase font-sans">F1 Score</span>
                <span className="font-bold text-white">{metrics.f1?.toFixed(3)}</span>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-lg p-2">
                <span className="text-white/30 block mb-0.5 text-[8px] uppercase font-sans">ROC AUC</span>
                <span className="font-bold text-white">{metrics.roc_auc?.toFixed(3)}</span>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-lg p-2">
                <span className="text-white/30 block mb-0.5 text-[8px] uppercase font-sans">Seed</span>
                <span className="font-bold text-white">{metrics.random_seed}</span>
              </div>
            </div>
          ) : (
            <div className="text-[10px] text-white/40 font-mono italic">
              No training metrics available yet.
            </div>
          )}
        </div>
      )}

      {/* Fail message details */}
      {isFailed && message && (
        <div className="bg-rose-500/5 border border-rose-500/10 p-3 rounded-xl text-[10px] text-rose-400 font-mono leading-relaxed">
          MESSAGE: {message}
        </div>
      )}

      {/* Actions */}
      {!isRunning && (
        <div className="flex justify-end pt-2">
          <button
            onClick={onReset}
            className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-mono text-[9px] uppercase tracking-wider rounded-lg transition-colors cursor-pointer"
          >
            Acknowledge & Clear
          </button>
        </div>
      )}
    </motion.div>
  );
}
