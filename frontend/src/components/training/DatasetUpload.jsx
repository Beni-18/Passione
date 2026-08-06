import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileSpreadsheet, Loader2, Play } from 'lucide-react';
import { useTrainingJob } from '../../hooks/useTrainingJob';
import TrainingStatus from './TrainingStatus';
import HealthStatus from './HealthStatus';

export default function DatasetUpload() {
  const {
    jobId,
    status,
    rowsTotal,
    rowsProcessed,
    rowsFailed,
    message,
    metrics,
    modelHealth,
    loading,
    error,
    submitJob,
    resetJob,
  } = useTrainingJob();

  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [seed, setSeed] = useState(42);
  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.name.toLowerCase().endsWith('.csv')) {
        setSelectedFile(file);
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const triggerFileSelect = () => {
    if (loading || jobId) return;
    fileInputRef.current?.click();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;
    await submitJob(selectedFile, seed);
  };

  const handleClear = () => {
    setSelectedFile(null);
    resetJob();
  };

  const isTrainingActive = jobId !== null;

  return (
    <div className="space-y-6">
      {/* Upload Panel */}
      <div className="glass-panel border border-white/5 rounded-2xl p-5 md:p-6 space-y-6 relative overflow-hidden">
        <div>
          <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2 font-mono">
            Model Dataset Training
          </h3>
          <p className="text-[11px] text-white/35 font-sans leading-relaxed">
            Submit a multi-row CSV dataset directly to fit or update the prediction forest model. Only CSV uploads are supported.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {/* File Input and Drag/Drop Zone */}
          <div
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            onClick={triggerFileSelect}
            className={`border border-dashed p-6 rounded-xl text-center transition-all duration-300 relative select-none ${
              isTrainingActive ? 'opacity-40 pointer-events-none cursor-default' : 'cursor-pointer'
            } ${
              dragActive 
                ? 'border-accent-blue bg-accent-blue/5' 
                : selectedFile 
                  ? 'border-emerald-500/30 bg-emerald-500/[0.02]' 
                  : 'border-white/10 hover:border-white/20 bg-white/[0.01]'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={handleFileChange}
              disabled={isTrainingActive}
            />

            <div className="flex flex-col items-center space-y-2">
              {selectedFile ? (
                <>
                  <FileSpreadsheet className="w-8 h-8 text-emerald-400" />
                  <span className="text-xs text-white/80 font-mono font-medium max-w-[240px] truncate block">
                    {selectedFile.name}
                  </span>
                  <span className="text-[9px] text-white/30 font-mono">
                    {(selectedFile.size / 1024).toFixed(1)} KB
                  </span>
                </>
              ) : (
                <>
                  <Upload className="w-8 h-8 text-white/30 group-hover:text-white transition-colors" />
                  <span className="text-xs text-white/60 font-sans">
                    Drag and drop CSV or click to browse
                  </span>
                  <span className="text-[9px] text-white/30 font-mono">
                    MAX_FILE_SIZE: 50MB
                  </span>
                </>
              )}
            </div>
          </div>

          {/* Random Seed Input and Train Trigger */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
            <div className="flex items-center space-x-3 bg-white/5 border border-white/5 px-3.5 py-2 rounded-lg shrink-0">
              <span className="text-[9px] font-mono text-white/40 uppercase tracking-wider">Seed:</span>
              <input
                type="number"
                value={seed}
                onChange={(e) => setSeed(parseInt(e.target.value, 10) || 42)}
                disabled={isTrainingActive}
                className="w-16 bg-transparent text-white focus:outline-none text-xs font-mono font-bold"
              />
            </div>

            <div className="flex items-center space-x-3 flex-1 justify-end">
              {selectedFile && !isTrainingActive && (
                <button
                  type="button"
                  onClick={handleClear}
                  className="px-4 py-2 text-[10px] uppercase font-mono tracking-widest text-white/40 hover:text-white transition-colors cursor-pointer"
                >
                  Clear
                </button>
              )}
              
              <button
                type="submit"
                disabled={!selectedFile || isTrainingActive}
                className={`w-full sm:w-auto px-5 py-2.5 rounded-lg border font-bold font-mono tracking-widest text-[9px] uppercase transition-colors cursor-pointer flex items-center justify-center ${
                  !selectedFile 
                    ? 'border-white/5 text-white/20 bg-transparent pointer-events-none' 
                    : isTrainingActive 
                      ? 'border-accent-blue/20 text-accent-blue/40 bg-accent-blue/5' 
                      : 'border-accent-blue/40 hover:border-accent-blue text-white bg-accent-blue/10 hover:bg-accent-blue/20'
                }`}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 mr-2 animate-spin text-accent-blue" />
                    QUEUING...
                  </>
                ) : (
                  <>
                    <Play className="w-3 h-3 mr-2" />
                    Run Training
                  </>
                )}
              </button>
            </div>
          </div>
        </form>

        {/* Local Hook Errors */}
        {error && (
          <div className="bg-rose-500/5 border border-rose-500/10 p-3.5 rounded-xl text-[10px] text-rose-400 font-mono leading-relaxed mt-4">
            ERROR: {error}
          </div>
        )}
      </div>

      {/* Polling Training Status */}
      <AnimatePresence mode="wait">
        {isTrainingActive && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-6 overflow-hidden"
          >
            <TrainingStatus
              status={status}
              jobId={jobId}
              rowsTotal={rowsTotal}
              rowsProcessed={rowsProcessed}
              rowsFailed={rowsFailed}
              message={message}
              metrics={metrics}
              onReset={handleClear}
            />

            {/* Health status details */}
            {status === 'complete' && modelHealth && (
              <HealthStatus modelHealth={modelHealth} />
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
