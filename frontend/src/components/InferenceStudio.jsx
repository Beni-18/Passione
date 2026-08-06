import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Cpu } from 'lucide-react';
import CSVUploader from './CSVUploader';
import ManualBuilder from './ManualBuilder';
import ReadinessPanel from './ReadinessPanel';
import PipelineVisualizer from './PipelineVisualizer';
import PredictionResult from './PredictionResult';
import DatasetUpload from './training/DatasetUpload';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const DEFAULT_FORM = {
  title: '',
  genre: 'Thriller',
  duration_minutes: 24,
  upload_time: new Date().toISOString().substring(0, 16),
  language: 'en',
  tags: '',
  budget: '',
  target_region: '',
  distribution: '',
  pace: '',
  star_power: '',
  marketing_campaign: '',
  teaser_released: false
};

export default function InferenceStudio({
  isInteractive,
  headerOpacity,
  springHeaderY,
  leftOpacity,
  springLeftX,
  rightOpacity,
  springRightX,
  bottomOpacity,
  springBottomY
}) {
  const [formData, setFormData] = useState({ ...DEFAULT_FORM });
  const [studioState, setStudioState] = useState('input'); // 'input' | 'pipeline' | 'result'
  const [prediction, setPrediction] = useState(null);
  const [error, setError] = useState(null);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleCSVUploadSuccess = (previewRecord) => {
    // Populate form data from parsed CSV row
    setFormData(prev => ({
      ...prev,
      title: previewRecord.title || '',
      genre: previewRecord.genre || 'Thriller',
      duration_minutes: parseInt(previewRecord.duration_minutes, 10) || 24,
      language: previewRecord.language || 'en',
      upload_time: previewRecord.upload_time 
        ? new Date(previewRecord.upload_time).toISOString().substring(0, 16) 
        : new Date().toISOString().substring(0, 16),
      tags: previewRecord.tags || ''
    }));
  };

  const handleResetForm = () => {
    setFormData({ ...DEFAULT_FORM });
  };

  const startInference = () => {
    setError(null);
    setPrediction(null);
    setStudioState('pipeline');
  };

  const handlePredictionComplete = (result) => {
    setPrediction(result);
    setStudioState('result');
  };

  const handlePredictionError = (errMsg) => {
    setError(errMsg);
    setStudioState('result');
  };

  const handleResetStudio = () => {
    setPrediction(null);
    setError(null);
    setStudioState('input');
    setFormData({ ...DEFAULT_FORM });
  };

  // Payload formatter for the FastAPI predict endpoint
  const getPayload = () => {
    const tagsArray = formData.tags
      .split(',')
      .map(t => t.trim())
      .filter(t => t.length > 0);

    return {
      title: formData.title,
      genre: formData.genre,
      duration_minutes: parseInt(formData.duration_minutes, 10) || 24,
      upload_time: new Date(formData.upload_time).toISOString(),
      language: formData.language,
      tags: tagsArray
    };
  };

  return (
    <div className="w-full text-white flex flex-col justify-center max-w-6xl mx-auto px-4 select-none relative pointer-events-auto">
      
      <AnimatePresence mode="wait">
        {studioState === 'pipeline' && (
          <motion.div
            key="pipeline"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="flex items-center justify-center py-10"
          >
            <PipelineVisualizer
              payload={getPayload()}
              apiEndpoint={`${API_BASE}/predict`}
              onPredictionComplete={handlePredictionComplete}
              onPredictionError={handlePredictionError}
            />
          </motion.div>
        )}

        {studioState === 'result' && (
          <motion.div
            key="result"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="py-6"
          >
            <PredictionResult
              prediction={prediction}
              error={error}
              payload={getPayload()}
              onReset={handleResetStudio}
            />
          </motion.div>
        )}

        {studioState === 'input' && (
          <motion.div
            key="input"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="w-full space-y-6 md:space-y-8"
          >
            {/* Top Workspace Header Panel */}
            <motion.div 
              style={{ opacity: headerOpacity, y: springHeaderY }}
              className="flex items-center justify-between pb-4 border-b border-white/5"
            >
              <div>
                <span className="text-[9px] uppercase tracking-[0.25em] text-accent-blue/80 font-bold block mb-1">INFERENCE PIPELINE</span>
                <h2 className="text-xl md:text-2xl font-black text-white uppercase tracking-tight">
                  Inference Studio
                </h2>
              </div>
              
              {/* Settle box for confidence percentage */}
              <div className="flex items-center space-x-4">
                <div className="hidden sm:flex items-center space-x-2 text-[10px] font-mono text-white/40 bg-white/5 border border-white/5 px-3 py-1.5 rounded-lg">
                  <Cpu className="w-3.5 h-3.5 text-accent-blue" />
                  <span>DECK: READY</span>
                </div>
                <div className="w-24 h-[34px] border border-white/5 bg-white/5 rounded-lg flex items-center justify-center font-mono text-[9px] text-white/20 uppercase tracking-wider relative">
                  {/* Empty anchor container for target percentage number */}
                  CONFIDENCE
                </div>
              </div>
            </motion.div>

            {/* Assembled Columns (CSV on Left, Accordion Builder on Right) */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
              
              {/* Left Panel: CSV Import (5 Columns) */}
              <motion.div 
                style={{ opacity: leftOpacity, x: springLeftX }}
                className="lg:col-span-5 flex flex-col space-y-6"
              >
                <div className="glass-panel border border-white/5 rounded-2xl p-5 md:p-6 flex-1 flex flex-col justify-between space-y-6">
                  <div>
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2 font-mono">
                      01 / Source Import
                    </h3>
                    <p className="text-[11px] text-white/35 font-sans leading-relaxed mb-6">
                      Upload local CSV film records. Populated fields instantly sync with the manual override tuner deck on the right.
                    </p>
                    <CSVUploader 
                      onUploadSuccess={handleCSVUploadSuccess}
                      onReset={handleResetForm}
                    />
                  </div>
                  
                  {/* Optional instruction panel */}
                  <div className="bg-white/[0.01] border border-white/5 rounded-xl p-4 font-sans text-[10px] text-white/45 leading-relaxed">
                    <strong>Developer Tip:</strong> Drag in a file to pre-fill parameters, then expand the categories on the right to manually tweak variables before running the model.
                  </div>
                </div>

                <DatasetUpload />
              </motion.div>

              {/* Right Panel: Accordion builder (7 Columns) */}
              <motion.div 
                style={{ opacity: rightOpacity, x: springRightX }}
                className="lg:col-span-7"
              >
                <div className="glass-panel border border-white/5 rounded-2xl p-5 md:p-6">
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2 font-mono">
                    02 / Parameter Tuning
                  </h3>
                  <p className="text-[11px] text-white/35 font-sans leading-relaxed mb-6">
                    Tweak and adjust features manually. Completion scores update as parameters are resolved.
                  </p>
                  <ManualBuilder 
                    formData={formData}
                    onChange={handleInputChange}
                  />
                </div>
              </motion.div>

            </div>

            {/* Bottom Panel: AI Readiness and Predict CTA */}
            <motion.div
              style={{ opacity: bottomOpacity, y: springBottomY }}
              className="w-full"
            >
              <ReadinessPanel 
                formData={formData}
                onPredictClick={startInference}
              />
            </motion.div>

          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
}
