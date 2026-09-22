import React, { useState, Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { Navbar } from './components/Navbar';
import { NewsAnalyzer } from './components/NewsAnalyzer';
import { ResultsView } from './components/ResultsView';
import { HistoryView } from './components/HistoryView';
import { LearnSection } from './components/LearnSection';
import type { AnalysisResponse } from './services/api';
import { ShieldCheck, AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorBoundaryProps {
  children: ReactNode;
  onReset: () => void;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('TruthLens UI caught render error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="max-w-2xl mx-auto p-6 my-12 bg-white rounded-2xl border border-rose-200 shadow-lg text-center space-y-4">
          <div className="w-12 h-12 rounded-xl bg-rose-100 text-rose-600 flex items-center justify-center mx-auto">
            <AlertCircle className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-bold text-slate-900">Unable to display results</h2>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            {this.state.error?.message || 'An unexpected rendering error occurred. Please try again.'}
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              this.props.onReset();
            }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500 text-slate-950 font-bold text-xs hover:bg-amber-400 transition-colors shadow-sm"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Return to Analyzer</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

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
        <ErrorBoundary onReset={handleNewAnalysis}>
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
        </ErrorBoundary>
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
