import { useState } from 'react';
import { Navbar } from './components/Navbar';
import { NewsAnalyzer } from './components/NewsAnalyzer';
import { ResultsView } from './components/ResultsView';
import { HistoryView } from './components/HistoryView';
import { LearnSection } from './components/LearnSection';
import type { AnalysisResponse } from './services/api';
import { ShieldCheck } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState<'analyzer' | 'history' | 'learn'>('analyzer');
  const [currentResult, setCurrentResult] = useState<AnalysisResponse | null>(null);

  const handleAnalysisComplete = (result: AnalysisResponse) => {
    setCurrentResult(result);
  };

  const handleNewAnalysis = () => {
    setCurrentResult(null);
    setActiveTab('analyzer');
  };

  const handleSelectFromHistory = (result: AnalysisResponse) => {
    setCurrentResult(result);
    setActiveTab('analyzer');
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col selection:bg-amber-300 selection:text-slate-950 font-sans">
      
      {/* Navigation Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={(tab) => {
          setActiveTab(tab);
        }}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 pt-6 pb-12">
        {activeTab === 'analyzer' && (
          currentResult ? (
            <ResultsView
              result={currentResult}
              onNewAnalysis={handleNewAnalysis}
            />
          ) : (
            <NewsAnalyzer
              onAnalysisComplete={handleAnalysisComplete}
            />
          )
        )}

        {activeTab === 'history' && (
          <HistoryView
            onSelectAnalysis={handleSelectFromHistory}
          />
        )}

        {activeTab === 'learn' && (
          <LearnSection />
        )}
      </main>

      {/* Clean Light Footer */}
      <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500 space-y-1.5 shadow-sm">
        <div className="flex items-center justify-center gap-1.5">
          <ShieldCheck className="w-4 h-4 text-amber-500" />
          <span className="font-semibold text-slate-800">TruthLens</span>
          <span>— Explainable AI Misinformation Checker</span>
        </div>
        <p className="text-[11px] text-slate-400">
          Always verify critical breaking news with primary accredited wire agencies.
        </p>
      </footer>

    </div>
  );
}

export default App;
