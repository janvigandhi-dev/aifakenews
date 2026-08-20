import React, { useState } from 'react';
import { Sliders, RefreshCw, CheckCircle2, AlertCircle, Database, Server, Sparkles, Layers } from 'lucide-react';
import { api } from '../services/api';

interface AdminStudioProps {
  models: Array<{ key: string; name: string; is_active: boolean }>;
  activeModel: string;
  onSwitchModel: (key: string) => void;
}

export const AdminStudio: React.FC<AdminStudioProps> = ({ models, activeModel, onSwitchModel }) => {
  const [retraining, setRetraining] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleRetrain = async () => {
    if (!window.confirm('Trigger full retraining of all 5 classifiers on the benchmark dataset?')) return;
    try {
      setRetraining(true);
      setMessage(null);
      const res = await api.retrainModels();
      setMessage(res.message || 'Model retraining successfully started!');
    } catch (err: any) {
      setMessage(`Error: ${err.message}`);
    } finally {
      setRetraining(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-16">
      
      {/* Header */}
      <div className="space-y-1">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/25 text-amber-400 text-xs font-mono">
          <Sliders className="w-3.5 h-3.5" />
          <span>System Management & ML Studio</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
          Admin & Training Studio
        </h2>
        <p className="text-slate-400 text-sm max-w-2xl">
          Manage active production classifiers, inspect benchmark training data, and trigger background model retraining.
        </p>
      </div>

      {message && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0" />
          <span>{message}</span>
        </div>
      )}

      {/* Dataset & Training Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-6 shadow-xl">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div className="space-y-1">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Database className="w-4 h-4 text-amber-400" />
              <span>Benchmark Dataset & Model Retraining</span>
            </h3>
            <p className="text-xs text-slate-400">
              1,400 curated multi-domain articles (Politics, Health, Science, Financial clickbait, Conspiracies).
            </p>
          </div>

          <button
            onClick={handleRetrain}
            disabled={retraining}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-rose-500 hover:from-amber-400 hover:to-rose-400 text-slate-950 font-bold text-xs shadow-md shadow-amber-500/20 disabled:opacity-50 transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${retraining ? 'animate-spin' : ''}`} />
            <span>{retraining ? 'Retraining Models...' : 'Retrain All 5 Classifiers'}</span>
          </button>
        </div>

        {/* Dataset Breakdown Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <span className="text-[10px] font-mono uppercase text-slate-400">Total Benchmark Records</span>
            <div className="text-xl font-bold text-white font-mono">1,400</div>
            <span className="text-[11px] text-slate-500">700 Real / 700 Misleading</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <span className="text-[10px] font-mono uppercase text-slate-400">Feature Vocabulary</span>
            <div className="text-xl font-bold text-amber-400 font-mono">12,000 TF-IDF n-grams</div>
            <span className="text-[11px] text-slate-500">Sublinear scaling (1,2 n-grams)</span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
            <span className="text-[10px] font-mono uppercase text-slate-400">Evaluation Strategy</span>
            <div className="text-xl font-bold text-emerald-400 font-mono">70 / 15 / 15 Split</div>
            <span className="text-[11px] text-slate-500">Stratified train / val / test</span>
          </div>
        </div>
      </div>

      {/* Production Model Selector */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 space-y-5 shadow-xl">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Layers className="w-4 h-4 text-amber-400" />
          <span>Production Classifier Registry</span>
        </h3>
        <p className="text-xs text-slate-400">
          Select which classifier serves as the default production analysis engine for incoming API requests.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {models.map((m) => {
            const isActive = m.key === activeModel;
            return (
              <div
                key={m.key}
                onClick={() => onSwitchModel(m.key)}
                className={`p-4 rounded-xl bg-slate-950 border cursor-pointer transition-all flex flex-col justify-between gap-3 ${
                  isActive ? 'border-amber-500 ring-1 ring-amber-500/50 shadow-md shadow-amber-500/10' : 'border-slate-800 hover:border-slate-700'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="text-xs font-bold text-white">{m.name}</span>
                    {isActive && (
                      <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30">
                        Default
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] font-mono text-slate-500">{m.key}</span>
                </div>

                <button
                  type="button"
                  className={`w-full py-1.5 px-3 rounded-lg text-xs font-medium transition-colors ${
                    isActive ? 'bg-amber-500 text-slate-950 font-bold' : 'bg-slate-900 text-slate-300 hover:bg-slate-800'
                  }`}
                >
                  {isActive ? 'Active Engine' : 'Switch to this Model'}
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Backend Infrastructure Diagnostics */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
        <h3 className="text-base font-bold text-white flex items-center gap-2">
          <Server className="w-4 h-4 text-emerald-400" />
          <span>System Environment & Diagnostics</span>
        </h3>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-slate-500 block text-[10px]">API Framework</span>
            <span className="text-slate-200">FastAPI 0.139.0</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-slate-500 block text-[10px]">Python Runtime</span>
            <span className="text-slate-200">Python 3.14.6</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-slate-500 block text-[10px]">Evidence Engine</span>
            <span className="text-slate-200">Groq GPT-OSS-20B</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
            <span className="text-slate-500 block text-[10px]">Storage Engine</span>
            <span className="text-slate-200">SQLite (truthlens.db)</span>
          </div>
        </div>
      </div>

    </div>
  );
};
