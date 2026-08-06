import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileSpreadsheet, Keyboard, ArrowLeft, Cpu } from 'lucide-react';
import CSVUploader from './CSVUploader';
import ManualBuilder from './ManualBuilder';
import ReadinessPanel from './ReadinessPanel';
import PipelineVisualizer from './PipelineVisualizer';
import PredictionResult from './PredictionResult';

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

export default function InferenceStudio() {
  const [inputMode, setInputMode] = useState('select'); // 'select' | 'csv' | 'manual'
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
    setInputMode('select');
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
    <div className="w-full min-h-screen text-white flex flex-col justify-center px-4 py-8 relative">
      
      <AnimatePresence mode="wait">
        {studioState === 'pipeline' && (
          <motion.div
            key="pipeline"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="flex items-center justify-center py-20"
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
          >
            <PredictionResult
              prediction={prediction}
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
            className="w-full max-w-6xl mx-auto"
          >
            {inputMode === 'select' ? (
              // Inception selection cards
              <div className="space-y-8 py-8">
                <div className="text-center max-w-lg mx-auto mb-10 pointer-events-none">
                  <span className="text-[10px] uppercase tracking-[0.3em] text-accent-blue/80 font-bold block mb-2">INTEGRATION HUB</span>
                  <h2 className="text-3xl md:text-5xl font-extrabold tracking-tighter text-white uppercase leading-none">
                    Inference Studio
                  </h2>
                  <p className="text-white/40 text-xs md:text-sm font-sans mt-2.5">
                    Choose your workspace input method to evaluate trending likelihood index scores.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
                  {/* Upload CSV Card */}
                  <motion.div
                    whileHover={{ scale: 1.02, y: -4 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setInputMode('csv')}
                    className="glass-panel hover:border-accent-blue/30 rounded-3xl p-8 cursor-pointer flex flex-col justify-between items-start text-left h-[300px] relative overflow-hidden group transition-colors duration-300"
                  >
                    <div className="absolute top-0 right-0 w-32 h-32 bg-accent-blue/5 rounded-full filter blur-2xl pointer-events-none -z-10 group-hover:bg-accent-blue/10 transition-colors" />
                    
                    <div className="p-4 rounded-2xl bg-white/5 border border-white/5 text-white/50 group-hover:text-accent-blue group-hover:border-accent-blue/20 transition-all duration-300">
                      <FileSpreadsheet className="w-8 h-8" />
                    </div>

                    <div>
                      <h3 className="text-lg font-bold text-white uppercase tracking-wider group-hover:text-accent-blue transition-colors">
                        Upload Inference CSV
                      </h3>
                      <p className="text-xs text-white/40 font-sans mt-2 leading-relaxed">
                        Parse bulk film records or pre-arranged metrics directly from local spreadsheet layouts.
                      </p>
                      <ul className="text-[10px] font-mono text-white/30 space-y-1 mt-4">
                        <li>• Local CSV parsing</li>
                        <li>• Validation check integration</li>
                        <li>• Synchronous API inference run</li>
                      </ul>
                    </div>
                  </motion.div>

                  {/* Manual Builder Card */}
                  <motion.div
                    whileHover={{ scale: 1.02, y: -4 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setInputMode('manual')}
                    className="glass-panel hover:border-accent-violet/30 rounded-3xl p-8 cursor-pointer flex flex-col justify-between items-start text-left h-[300px] relative overflow-hidden group transition-colors duration-300"
                  >
                    <div className="absolute top-0 right-0 w-32 h-32 bg-accent-violet/5 rounded-full filter blur-2xl pointer-events-none -z-10 group-hover:bg-accent-violet/10 transition-colors" />

                    <div className="p-4 rounded-2xl bg-white/5 border border-white/5 text-white/50 group-hover:text-accent-violet group-hover:border-accent-violet/20 transition-all duration-300">
                      <Keyboard className="w-8 h-8" />
                    </div>

                    <div>
                      <h3 className="text-lg font-bold text-white uppercase tracking-wider group-hover:text-accent-violet transition-colors">
                        Build Metadata Manual
                      </h3>
                      <p className="text-xs text-white/40 font-sans mt-2 leading-relaxed">
                        Manually configure narrative paces, marketing campaign weights, casting status and regional targets.
                      </p>
                      <ul className="text-[10px] font-mono text-white/30 space-y-1 mt-4">
                        <li>• 4 distinct attribute blocks</li>
                        <li>• Real-time completeness metrics</li>
                        <li>• Custom feature weight overrides</li>
                      </ul>
                    </div>
                  </motion.div>
                </div>
              </div>
            ) : (
              // Two-panel layout once method is chosen
              <div className="space-y-6">
                {/* Back Link */}
                <button
                  onClick={() => setInputMode('select')}
                  className="flex items-center text-[10px] uppercase font-mono tracking-widest text-white/40 hover:text-white transition-colors cursor-pointer"
                >
                  <ArrowLeft className="w-3.5 h-3.5 mr-2" />
                  Back to selection
                </button>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                  {/* Left Column: Form / Uploader (60% width equivalent) */}
                  <div className="lg:col-span-7">
                    <AnimatePresence mode="wait">
                      {inputMode === 'csv' ? (
                        <motion.div
                          key="csv"
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: 10 }}
                        >
                          <CSVUploader 
                            onUploadSuccess={handleCSVUploadSuccess}
                            onReset={handleResetForm}
                          />
                        </motion.div>
                      ) : (
                        <motion.div
                          key="manual"
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: 10 }}
                        >
                          <ManualBuilder 
                            formData={formData}
                            onChange={handleInputChange}
                          />
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* Right Column: AI Readiness (40% width equivalent) */}
                  <div className="lg:col-span-5 h-full">
                    <ReadinessPanel 
                      formData={formData}
                      onPredictClick={startInference}
                    />
                  </div>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
}
