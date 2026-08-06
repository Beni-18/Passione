import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileText, CheckCircle, AlertCircle, X } from 'lucide-react';

export default function CSVUploader({ onUploadSuccess, onReset }) {
  const [dragActive, setDragActive] = useState(false);
  const [fileInfo, setFileInfo] = useState(null);
  const [error, setError] = useState(null);
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

  const parseCSVHeaders = (text) => {
    try {
      const lines = text.split('\n');
      if (lines.length === 0) throw new Error("Empty file");
      
      const headers = lines[0]
        .split(',')
        .map(h => h.trim().replace(/^["']|["']$/g, '').toLowerCase());

      // Validate required fields
      const required = ['title', 'genre', 'duration_minutes', 'language'];
      const missing = required.filter(field => !headers.includes(field));

      if (missing.length > 0) {
        throw new Error(`Missing required columns: ${missing.join(', ')}`);
      }

      // Extract a preview record (row 2)
      let previewRecord = null;
      if (lines.length > 1 && lines[1].trim()) {
        const values = lines[1].split(',').map(v => v.trim().replace(/^["']|["']$/g, ''));
        previewRecord = {};
        headers.forEach((h, idx) => {
          if (values[idx] !== undefined) {
            previewRecord[h] = values[idx];
          }
        });
      }

      return {
        headers,
        totalRows: lines.filter(line => line.trim()).length - 1,
        previewRecord
      };
    } catch (err) {
      throw new Error(err.message || "Failed to parse CSV columns");
    }
  };

  const processFile = (file) => {
    setError(null);
    if (file.type !== "text/csv" && !file.name.endsWith('.csv')) {
      setError("Only CSV metadata files are supported.");
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target.result;
        const parsed = parseCSVHeaders(text);
        
        setFileInfo({
          name: file.name,
          size: (file.size / 1024).toFixed(1) + " KB",
          rows: parsed.totalRows
        });

        // Pass parsed preview details to parent workspace
        if (parsed.previewRecord) {
          onUploadSuccess(parsed.previewRecord);
        } else {
          setError("CSV file contains headers but no data rows.");
        }
      } catch (err) {
        setError(err.message);
      }
    };
    reader.readAsText(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current.click();
  };

  const clearFile = () => {
    setFileInfo(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
    onReset();
  };

  return (
    <div className="w-full">
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv"
        onChange={handleChange}
        className="hidden"
      />

      {!fileInfo && (
        <motion.div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={triggerFileInput}
          whileHover={{ scale: 1.01 }}
          className={`border border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-300 ${
            dragActive
              ? "border-accent-blue bg-accent-blue/5 shadow-[0_0_20px_rgba(79,107,255,0.15)]"
              : "border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]"
          }`}
        >
          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="p-4 rounded-full bg-white/5 border border-white/5 text-white/50 group-hover:text-white transition-colors">
              <Upload className="w-6 h-6 animate-pulse-slow" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-white uppercase tracking-wider">
                Upload inference CSV
              </h4>
              <p className="text-xs text-white/40 font-sans mt-2 max-w-xs mx-auto">
                Drag and drop your project configuration CSV, or click to browse.
              </p>
            </div>
            <div className="font-mono text-[9px] text-white/30 border border-white/5 bg-black/20 px-3 py-1.5 rounded-lg max-w-sm mx-auto">
              REQUIRED COLUMNS: title, genre, duration_minutes, language
            </div>
          </div>
        </motion.div>
      )}

      {fileInfo && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="border border-accent-blue/20 bg-accent-blue/5 rounded-2xl p-6 flex items-start justify-between relative overflow-hidden"
        >
          <div className="flex items-start space-x-4">
            <div className="p-3 rounded-lg bg-accent-blue/10 border border-accent-blue/20 text-accent-blue">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-white flex items-center">
                {fileInfo.name}
                <span className="text-[10px] font-mono text-accent-blue bg-accent-blue/10 px-2 py-0.5 rounded ml-3">
                  Parsed OK
                </span>
              </h4>
              <div className="flex items-center space-x-4 mt-2 font-mono text-[10px] text-white/40">
                <span>Size: {fileInfo.size}</span>
                <span className="w-1.5 h-1.5 rounded-full bg-white/10" />
                <span>Rows detected: {fileInfo.rows}</span>
              </div>
              <div className="flex items-center text-[10px] text-emerald-400 font-mono mt-3">
                <CheckCircle className="w-3.5 h-3.5 mr-1.5" /> All validation rules satisfied.
              </div>
            </div>
          </div>
          <button
            onClick={clearFile}
            className="p-1 rounded-full border border-white/5 bg-white/5 text-white/40 hover:text-white cursor-pointer transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </motion.div>
      )}

      {error && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="border border-rose-500/20 bg-rose-500/5 rounded-2xl p-6 flex items-start justify-between mt-4"
        >
          <div className="flex items-start space-x-4">
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-500">
              <AlertCircle className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-white uppercase tracking-wider">
                CSV Parse Error
              </h4>
              <p className="text-xs text-white/50 font-sans mt-1.5">
                {error}
              </p>
            </div>
          </div>
          <button
            onClick={clearFile}
            className="p-1 rounded-full border border-white/5 bg-white/5 text-white/40 hover:text-white cursor-pointer transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </motion.div>
      )}
    </div>
  );
}
