import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, CheckCircle, Circle } from 'lucide-react';

const GENRES = ["Thriller", "Action", "Drama", "Sci-Fi", "Comedy", "Indie", "Documentary", "Horror"];
const LANGUAGES = [
  { code: "en", name: "English (en)" },
  { code: "fr", name: "French (fr)" },
  { code: "es", name: "Spanish (es)" },
  { code: "de", name: "German (de)" },
  { code: "ja", name: "Japanese (ja)" }
];
const REGIONS = ["Global", "North America", "Europe", "Asia-Pacific", "Latin America"];
const DISTRIBUTION = ["Streaming (SVOD)", "Theatrical Release", "Indie / Festival Run", "Direct-to-Web"];
const PACE = ["Slow-burn", "Balanced", "Fast-paced", "Action-heavy"];
const STAR_POWER = ["None / Indie Cast", "Rising Talent", "A-List Headline", "Ensemble Cast"];
const CAMPAIGN = ["Minimal (Organic)", "Standard Digital", "Aggressive / Multi-Channel"];

export default function ManualBuilder({ formData, onChange }) {
  const [openSection, setOpenSection] = useState(0);

  // Helper to determine completion state of each section
  const getSectionStatus = (index) => {
    switch (index) {
      case 0: // Basic Info
        const basicOk = !!(formData.title && formData.genre && formData.duration_minutes && formData.language && formData.upload_time);
        return { completed: basicOk, count: [formData.title, formData.genre, formData.duration_minutes, formData.language, formData.upload_time].filter(Boolean).length, total: 5 };
      case 1: // Popularity Metrics
        const popCount = [formData.budget, formData.target_region, formData.distribution].filter(Boolean).length;
        return { completed: popCount === 3, count: popCount, total: 3 };
      case 2: // Content Attributes
        const attrCount = [formData.tags, formData.pace].filter(Boolean).length;
        return { completed: attrCount === 2, count: attrCount, total: 2 };
      case 3: // Engagement Signals
        const engCount = [formData.teaser_released !== undefined, formData.star_power, formData.marketing_campaign].filter(val => val !== undefined && val !== "").length;
        return { completed: engCount === 3, count: engCount, total: 3 };
      default:
        return { completed: false, count: 0, total: 0 };
    }
  };

  const toggleSection = (index) => {
    setOpenSection(openSection === index ? -1 : index);
  };

  const sections = [
    {
      title: "Basic Information",
      subtitle: "Required core attributes",
      index: "01",
      fields: (
        <div className="space-y-4">
          <div>
            <label className="block text-[10px] uppercase tracking-wider text-white/40 font-mono mb-1.5">Film Title</label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={onChange}
              placeholder="e.g. Midnight Run"
              required
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3.5 py-2.5 text-xs text-white placeholder-white/20 outline-none focus:border-accent-blue/50 transition-colors"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-white/40 font-mono mb-1.5">Genre</label>
              <select
                name="genre"
                value={formData.genre}
                onChange={onChange}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3.5 py-2.5 text-xs text-white outline-none focus:border-accent-blue/50 transition-colors"
              >
                {GENRES.map(g => <option key={g} value={g} className="bg-[#0b0b0c] text-white">{g}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-[10px] uppercase tracking-wider text-white/40 font-mono mb-1.5">Duration (min)</label>
              <input
                type="number"
                name="duration_minutes"
                value={formData.duration_minutes}
                onChange={onChange}
                required
                min="1"
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3.5 py-2.5 text-xs text-white outline-none focus:border-accent-blue/50 transition-colors"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-white/40 font-mono mb-1.5">Language</label>
              <select
                name="language"
                value={formData.language}
                onChange={onChange}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3.5 py-2.5 text-xs text-white outline-none focus:border-accent-blue/50 transition-colors"
              >
                {LANGUAGES.map(l => <option key={l.code} value={l.code} className="bg-[#0b0b0c] text-white">{l.name}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-[10px] uppercase tracking-wider text-white/40 font-mono mb-1.5">Release Date & Time</label>
              <input
                type="datetime-local"
                name="upload_time"
                value={formData.upload_time}
                onChange={onChange}
                required
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3.5 py-2 text-xs text-white outline-none focus:border-accent-blue/50 transition-colors"
              />
            </div>
          </div>
        </div>
      )
    },
    {
      title: "Popularity Metrics",
      subtitle: "Budgetary and deployment scope",
      index: "02",
      fields: (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-[10px] uppercase tracking-wider text-white/40 font-mono mb-1.5">Production Budget</label>
            <select
              name="budget"
              value={formData.budget}
              onChange={onChange}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3.5 py-2.5 text-xs text-white outline-none focus:border-accent-blue/50 transition-colors"
            >
              <option value="" className="bg-[#0b0b0c] text-white/40">Select Budget Range</option>
              <option value="Low" className="bg-[#0b0b0c]">Indie (Under $1M)</option>
              <option value="Mid" className="bg-[#0b0b0c]">Mid-Budget ($1M - $15M)</option>
              <option value="High" className="bg-[#0b0b0c]">Major Production ($15M+)</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] uppercase tracking-wider text-white/40 font-mono mb-1.5">Target Audience Region</label>
            <select
              name="target_region"
              value={formData.target_region}
              onChange={onChange}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3.5 py-2.5 text-xs text-white outline-none focus:border-accent-blue/50 transition-colors"
            >
              <option value="" className="bg-[#0b0b0c] text-white/40">Select Target Region</option>
              {REGIONS.map(r => <option key={r} value={r} className="bg-[#0b0b0c]">{r}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-[10px] uppercase tracking-wider text-white/40 font-mono mb-1.5">Distribution Scale</label>
            <select
              name="distribution"
              value={formData.distribution}
              onChange={onChange}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3.5 py-2.5 text-xs text-white outline-none focus:border-accent-blue/50 transition-colors"
            >
              <option value="" className="bg-[#0b0b0c] text-white/40">Select Distribution Channel</option>
              {DISTRIBUTION.map(d => <option key={d} value={d} className="bg-[#0b0b0c]">{d}</option>)}
            </select>
          </div>
        </div>
      )
    },
    {
      title: "Content Attributes",
      subtitle: "Story pace and tag attributes",
      index: "03",
      fields: (
        <div className="space-y-4">
          <div>
            <label className="block text-[10px] uppercase tracking-wider text-white/40 font-mono mb-1.5">Narrative Pace</label>
            <select
              name="pace"
              value={formData.pace}
              onChange={onChange}
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3.5 py-2.5 text-xs text-white outline-none focus:border-accent-blue/50 transition-colors"
            >
              <option value="" className="bg-[#0b0b0c] text-white/40">Select Narrative Pace</option>
              {PACE.map(p => <option key={p} value={p} className="bg-[#0b0b0c]">{p}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-[10px] uppercase tracking-wider text-white/40 font-mono mb-1.5">Metadata Tags (comma separated)</label>
            <input
              type="text"
              name="tags"
              value={formData.tags}
              onChange={onChange}
              placeholder="e.g. suspense, low-light, neo-noir, sound-design"
              className="w-full bg-white/5 border border-white/10 rounded-lg px-3.5 py-2.5 text-xs text-white placeholder-white/20 outline-none focus:border-accent-blue/50 transition-colors"
            />
          </div>
        </div>
      )
    },
    {
      title: "Engagement Signals",
      subtitle: "Marketing actions and casting",
      index: "04",
      fields: (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-white/40 font-mono mb-1.5">Lead Actor Cast Weight</label>
              <select
                name="star_power"
                value={formData.star_power}
                onChange={onChange}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3.5 py-2.5 text-xs text-white outline-none focus:border-accent-blue/50 transition-colors"
              >
                <option value="" className="bg-[#0b0b0c] text-white/40">Select Actor Status</option>
                {STAR_POWER.map(s => <option key={s} value={s} className="bg-[#0b0b0c]">{s}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-[10px] uppercase tracking-wider text-white/40 font-mono mb-1.5">Marketing Scale</label>
              <select
                name="marketing_campaign"
                value={formData.marketing_campaign}
                onChange={onChange}
                className="w-full bg-white/5 border border-white/10 rounded-lg px-3.5 py-2.5 text-xs text-white outline-none focus:border-accent-blue/50 transition-colors"
              >
                <option value="" className="bg-[#0b0b0c] text-white/40">Select Campaign Scope</option>
                {CAMPAIGN.map(c => <option key={c} value={c} className="bg-[#0b0b0c]">{c}</option>)}
              </select>
            </div>
          </div>

          <div className="flex items-center space-x-3 bg-white/[0.01] border border-white/5 rounded-xl p-3.5">
            <input
              type="checkbox"
              name="teaser_released"
              checked={formData.teaser_released}
              onChange={onChange}
              className="accent-accent-blue rounded cursor-pointer border-white/20 w-4 h-4 bg-white/5"
            />
            <div>
              <span className="text-xs text-white font-medium select-none cursor-pointer" onClick={() => onChange({ target: { name: 'teaser_released', type: 'checkbox', checked: !formData.teaser_released }})}>
                Official Teaser Video Released
              </span>
              <p className="text-[10px] text-white/30 font-sans mt-0.5 select-none">
                Activates early social media scraper models.
              </p>
            </div>
          </div>
        </div>
      )
    }
  ];

  return (
    <div className="space-y-4">
      {sections.map((section, idx) => {
        const { completed, count, total } = getSectionStatus(idx);
        const isOpen = openSection === idx;

        return (
          <div 
            key={idx} 
            className={`border rounded-2xl overflow-hidden transition-all duration-300 ${
              isOpen 
                ? "border-accent-blue/20 bg-accent-blue/[0.01] shadow-[0_4px_30px_rgba(0,0,0,0.2)]" 
                : "border-white/5 bg-white/[0.01]"
            }`}
          >
            {/* Header Trigger */}
            <button
              type="button"
              onClick={() => toggleSection(idx)}
              className="w-full px-5 py-4 flex items-center justify-between hover:bg-white/[0.02] transition-colors text-left cursor-pointer"
            >
              <div className="flex items-center space-x-4">
                <span className="font-mono text-xs text-white/30 tracking-widest">{section.index}</span>
                <div>
                  <h4 className="text-sm font-bold text-white uppercase tracking-wider">{section.title}</h4>
                  <p className="text-[10px] text-white/30 font-sans mt-0.5">{section.subtitle}</p>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                {/* Status Indicator */}
                <div className="flex items-center text-[10px] font-mono text-white/40">
                  {completed ? (
                    <span className="text-accent-blue flex items-center">
                      <CheckCircle className="w-4 h-4 mr-1.5" /> COMPLETE
                    </span>
                  ) : (
                    <span className="flex items-center">
                      <Circle className="w-3.5 h-3.5 mr-1.5 text-white/20" /> {count}/{total}
                    </span>
                  )}
                </div>
                {/* Arrow Icon */}
                <motion.div
                  animate={{ rotate: isOpen ? 180 : 0 }}
                  transition={{ duration: 0.2 }}
                  className="text-white/40"
                >
                  <ChevronDown className="w-4 h-4" />
                </motion.div>
              </div>
            </button>

            {/* Accordion Content */}
            <AnimatePresence initial={false}>
              {isOpen && (
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: "auto" }}
                  exit={{ height: 0 }}
                  transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                  className="overflow-hidden"
                >
                  <div className="px-5 pb-5 pt-2 border-t border-white/[0.04]">
                    {section.fields}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
}
