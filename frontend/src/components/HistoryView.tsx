import React, { useState, useEffect } from 'react';
import { History, Search, Download, Trash2, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import type { AnalysisResponse } from '../services/api';

interface HistoryViewProps {
  onSelectAnalysis: (result: AnalysisResponse) => void;
}

export const HistoryView: React.FC<HistoryViewProps> = ({ onSelectAnalysis }) => {
  const [history, setHistory] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedFilter, setSelectedFilter] = useState<string>('all');

  useEffect(() => {
    loadHistory();
  }, [search]);

  const loadHistory = async () => {
    try {
      setLoading(true);
      const data = await api.getHistory(search);
      setHistory(data.history || []);
    } catch (err) {
      console.error('Failed to load history', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (!window.confirm('Delete this analysis record from history?')) return;
    try {
      await api.deleteHistoryItem(id);
      setHistory((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      alert('Failed to delete history record.');
    }
  };

  const handleOpenDetail = async (id: string) => {
    try {
      const detail = await api.getHistoryDetail(id);
      if (detail && detail.full_payload) {
        detail.full_payload.id = detail.id;
        detail.full_payload.headline = detail.headline;
        detail.full_payload.url = detail.url;
        onSelectAnalysis(detail.full_payload);
      }
    } catch (err) {
      alert('Failed to load full analysis details.');
    }
  };

  const filteredHistory = history.filter((item) => {
    if (selectedFilter === 'all') return true;
    if (selectedFilter === 'misleading') return item.verdict === 'LIKELY MISLEADING';
    if (selectedFilter === 'review') return item.verdict?.includes('SUSPICIOUS');
    if (selectedFilter === 'real') return item.verdict === 'REAL / LOW RISK';
    return true;
  });

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Past Analyses ({history.length})
          </h2>
          <p className="text-xs text-slate-500">
            Audit history of your previously verified news articles.
          </p>
        </div>

        {/* Search & Filter Bar */}
        <div className="flex flex-wrap items-center gap-2.5 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-60">
            <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search history..."
              className="w-full bg-white border border-slate-300 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-amber-500 shadow-sm"
            />
          </div>

          <div className="flex items-center gap-1 bg-white p-1 rounded-xl border border-slate-200 text-xs shadow-sm">
            <button
              onClick={() => setSelectedFilter('all')}
              className={`px-2.5 py-1 rounded-lg transition-all ${
                selectedFilter === 'all' ? 'bg-amber-500 text-slate-950 font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setSelectedFilter('misleading')}
              className={`px-2.5 py-1 rounded-lg transition-all ${
                selectedFilter === 'misleading' ? 'bg-rose-600 text-white font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Misleading
            </button>
            <button
              onClick={() => setSelectedFilter('review')}
              className={`px-2.5 py-1 rounded-lg transition-all ${
                selectedFilter === 'review' ? 'bg-amber-500 text-slate-950 font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Review
            </button>
            <button
              onClick={() => setSelectedFilter('real')}
              className={`px-2.5 py-1 rounded-lg transition-all ${
                selectedFilter === 'real' ? 'bg-emerald-600 text-white font-bold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Low Risk
            </button>
          </div>
        </div>
      </div>

      {/* History List */}
      {loading ? (
        <div className="flex items-center justify-center py-20 text-slate-400 gap-3">
          <RefreshCw className="w-5 h-5 animate-spin text-amber-500" />
          <span>Loading history...</span>
        </div>
      ) : filteredHistory.length === 0 ? (
        <div className="p-12 text-center bg-white border border-slate-200 rounded-2xl space-y-3 shadow-sm">
          <History className="w-10 h-10 text-slate-300 mx-auto" />
          <p className="text-slate-700 font-semibold text-sm">No past analyses found.</p>
          <p className="text-slate-400 text-xs">Run a news analysis to begin building your history.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredHistory.map((item) => {
            const isMis = item.verdict === 'LIKELY MISLEADING';
            const isRev = item.verdict?.includes('SUSPICIOUS');

            return (
              <div
                key={item.id}
                onClick={() => handleOpenDetail(item.id)}
                className="p-4 rounded-xl bg-white border border-slate-200 hover:border-amber-400 hover:bg-amber-50/20 transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 group shadow-sm"
              >
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                      isMis ? 'bg-rose-100 text-rose-800 border border-rose-200' :
                      isRev ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                      'bg-emerald-100 text-emerald-800 border border-emerald-200'
                    }`}>
                      {item.verdict}
                    </span>
                    <span className="text-[11px] font-mono text-slate-400">
                      {item.created_at}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-slate-900 group-hover:text-amber-700 transition-colors truncate">
                    {item.headline || item.url || 'Untitled Submission'}
                  </h3>

                  <p className="text-xs text-slate-500 line-clamp-1">
                    {item.content_preview}
                  </p>
                </div>

                <div className="flex items-center gap-3 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-100">
                  <div className="text-right font-mono text-xs hidden md:block">
                    <div className="text-slate-700 font-bold">{item.confidence}% Conf.</div>
                    <div className="text-rose-600 text-[11px]">Risk: {item.risk_score}/100</div>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      window.open(api.getPdfExportUrl(item.id), '_blank');
                    }}
                    title="Export PDF Report"
                    className="p-2 rounded-lg bg-slate-50 border border-slate-200 hover:border-amber-400 text-slate-600 hover:text-amber-700 transition-colors"
                  >
                    <Download className="w-4 h-4" />
                  </button>

                  <button
                    onClick={(e) => handleDelete(e, item.id)}
                    title="Delete record"
                    className="p-2 rounded-lg bg-slate-50 border border-slate-200 hover:border-rose-300 text-slate-400 hover:text-rose-600 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

    </div>
  );
};
