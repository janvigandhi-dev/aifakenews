import React, { useState, useEffect } from 'react';
import { Cpu, CheckCircle2, BarChart2, Check, RefreshCw, Layers, Sparkles, Shield, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

interface ModelDashboardProps {
  onSwitchModel: (key: string) => void;
  activeModel: string;
}

export const ModelDashboard: React.FC<ModelDashboardProps> = ({ onSwitchModel, activeModel }) => {
  const [performanceData, setPerformanceData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [selectedModelKey, setSelectedModelKey] = useState<string>(activeModel || 'linear_svm');

  useEffect(() => {
    loadPerformance();
  }, []);

  const loadPerformance = async () => {
    try {
      setLoading(true);
      const data = await api.getModelPerformance();
      setPerformanceData(data);
    } catch (err) {
      console.error('Failed to load performance data', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !performanceData) {
    return (
      <div className="flex items-center justify-center py-24 text-slate-400 gap-3">
        <RefreshCw className="w-6 h-6 animate-spin text-amber-400" />
        <span>Loading Benchmark Metrics & Evaluation Matrices...</span>
      </div>
    );
  }

  const modelsList = Object.values(performanceData.models || {}) as any[];
  const selectedModel = performanceData.models?.[selectedModelKey] || modelsList[0];

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-12">
      
      {/* Header */}
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/25 text-amber-400 text-xs font-mono">
          <Cpu className="w-3.5 h-3.5" />
          <span>Empirical Model Evaluation & Benchmark Registry</span>
        </div>
        <h2 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
          Multi-Classifier Performance Benchmark
        </h2>
        <p className="text-slate-400 text-sm max-w-2xl">
          Comparative evaluation of 5 machine-learning architectures trained on stratified multi-domain fake news benchmarks.
        </p>
      </div>

      {/* Dataset & Benchmark Meta Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-[11px] font-mono uppercase text-slate-400">Total Benchmark Corpus</span>
          <div className="text-2xl font-bold text-white font-mono">{performanceData.total_samples} articles</div>
          <span className="text-[10px] text-slate-500">50% Real / 50% Fake (Balanced)</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-[11px] font-mono uppercase text-slate-400">Train Split (70%)</span>
          <div className="text-2xl font-bold text-slate-200 font-mono">{performanceData.train_samples} samples</div>
          <span className="text-[10px] text-slate-500">Stratified cross-domain</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
          <span className="text-[11px] font-mono uppercase text-slate-400">Holdout Test (15%)</span>
          <div className="text-2xl font-bold text-slate-200 font-mono">{performanceData.test_samples} samples</div>
          <span className="text-[10px] text-slate-500">Unseen test set</span>
        </div>
        <div className="p-4 rounded-xl bg-slate-900 border border-amber-500/30 space-y-1">
          <span className="text-[11px] font-mono uppercase text-amber-400">Benchmark Winner</span>
          <div className="text-2xl font-bold text-amber-400 font-mono">
            {performanceData.best_model ? performanceData.models[performanceData.best_model]?.name : 'Linear SVM'}
          </div>
          <span className="text-[10px] text-slate-500">Highest F1 Score</span>
        </div>
      </div>

      {/* Comparative Performance Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden">
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-amber-400" />
              <span>Model Comparison Matrix</span>
            </h3>
            <p className="text-xs text-slate-400">
              Evaluated on accuracy, precision, recall, weighted F1, and Area Under ROC Curve.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-slate-400 font-mono uppercase text-[11px] border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4 font-semibold">Model Architecture</th>
                <th className="py-3.5 px-3 font-semibold">Type</th>
                <th className="py-3.5 px-3 font-semibold">Accuracy</th>
                <th className="py-3.5 px-3 font-semibold">Precision</th>
                <th className="py-3.5 px-3 font-semibold">Recall</th>
                <th className="py-3.5 px-3 font-semibold text-amber-400">F1-Score</th>
                <th className="py-3.5 px-3 font-semibold">ROC-AUC</th>
                <th className="py-3.5 px-4 text-right font-semibold">Status / Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {modelsList.map((m) => {
                const isActive = m.key === activeModel;
                return (
                  <tr 
                    key={m.key} 
                    onClick={() => setSelectedModelKey(m.key)}
                    className={`hover:bg-slate-800/40 cursor-pointer transition-colors ${
                      selectedModelKey === m.key ? 'bg-slate-800/30' : ''
                    }`}
                  >
                    <td className="py-3 px-4 font-sans font-semibold text-white flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${isActive ? 'bg-amber-400' : 'bg-slate-600'}`} />
                      <span>{m.name}</span>
                    </td>
                    <td className="py-3 px-3 text-slate-400 text-[11px]">{m.type}</td>
                    <td className="py-3 px-3 text-slate-200">{(m.accuracy * 100).toFixed(1)}%</td>
                    <td className="py-3 px-3 text-slate-200">{(m.precision * 100).toFixed(1)}%</td>
                    <td className="py-3 px-3 text-slate-200">{(m.recall * 100).toFixed(1)}%</td>
                    <td className="py-3 px-3 text-amber-400 font-bold">{(m.f1_score * 100).toFixed(1)}%</td>
                    <td className="py-3 px-3 text-emerald-400 font-semibold">{m.roc_auc.toFixed(4)}</td>
                    <td className="py-3 px-4 text-right">
                      {isActive ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-amber-500/20 text-amber-400 border border-amber-500/30 text-[10px] font-sans font-bold">
                          <Check className="w-3 h-3" /> Active Default
                        </span>
                      ) : (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onSwitchModel(m.key);
                          }}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-amber-500 hover:text-slate-950 text-slate-300 border border-slate-700 text-[10px] font-sans font-semibold transition-colors"
                        >
                          Set as Production
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Selected Model Deep Dive & Confusion Matrix */}
      {selectedModel && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Model Profile */}
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-amber-400" />
                  <span>Architecture Deep Dive: {selectedModel.name}</span>
                </h3>
                <span className="text-xs text-slate-400 font-mono">{selectedModel.type}</span>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-950 text-amber-400 border border-slate-800">
                F1 Score: {(selectedModel.f1_score * 100).toFixed(2)}%
              </span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              {selectedModel.description}
            </p>

            {/* Visual Metrics Bars */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center space-y-1">
                <span className="text-[10px] font-mono text-slate-400 uppercase">Accuracy</span>
                <div className="text-lg font-bold text-white font-mono">{(selectedModel.accuracy * 100).toFixed(1)}%</div>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center space-y-1">
                <span className="text-[10px] font-mono text-slate-400 uppercase">Precision</span>
                <div className="text-lg font-bold text-white font-mono">{(selectedModel.precision * 100).toFixed(1)}%</div>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center space-y-1">
                <span className="text-[10px] font-mono text-slate-400 uppercase">Recall</span>
                <div className="text-lg font-bold text-white font-mono">{(selectedModel.recall * 100).toFixed(1)}%</div>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-center space-y-1">
                <span className="text-[10px] font-mono text-slate-400 uppercase">ROC-AUC</span>
                <div className="text-lg font-bold text-emerald-400 font-mono">{selectedModel.roc_auc.toFixed(3)}</div>
              </div>
            </div>
          </div>

          {/* Confusion Matrix Visualizer */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-amber-400" />
              <span>Confusion Matrix (Holdout Test Set)</span>
            </h3>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
              <div className="grid grid-cols-2 gap-2 text-center text-xs font-mono">
                
                {/* True Negative */}
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 space-y-1">
                  <span className="text-[10px] text-emerald-400 uppercase block font-sans">True Negative (Real)</span>
                  <span className="text-xl font-bold text-white">{selectedModel.confusion_matrix.tn}</span>
                  <span className="text-[9px] text-slate-400 block">Correctly identified Real</span>
                </div>

                {/* False Positive */}
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 space-y-1">
                  <span className="text-[10px] text-rose-400 uppercase block font-sans">False Positive</span>
                  <span className="text-xl font-bold text-white">{selectedModel.confusion_matrix.fp}</span>
                  <span className="text-[9px] text-slate-400 block">Real flagged as Fake</span>
                </div>

                {/* False Negative */}
                <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 space-y-1">
                  <span className="text-[10px] text-amber-400 uppercase block font-sans">False Negative</span>
                  <span className="text-xl font-bold text-white">{selectedModel.confusion_matrix.fn}</span>
                  <span className="text-[9px] text-slate-400 block">Fake missed as Real</span>
                </div>

                {/* True Positive */}
                <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 space-y-1">
                  <span className="text-[10px] text-emerald-400 uppercase block font-sans">True Positive (Fake)</span>
                  <span className="text-xl font-bold text-white">{selectedModel.confusion_matrix.tp}</span>
                  <span className="text-[9px] text-slate-400 block">Correctly identified Fake</span>
                </div>

              </div>

              <div className="text-[10px] text-slate-400 font-mono text-center pt-1 border-t border-slate-800">
                Test Sample Size: {selectedModel.test_samples} verified articles
              </div>
            </div>

          </div>

        </div>
      )}

    </div>
  );
};
