import React, { useState } from 'react';
import { 
  FileText, Link2, Sparkles, Send, RefreshCw, AlertCircle, Search, ExternalLink, ArrowRight
} from 'lucide-react';
import { api } from '../services/api';
import type { AnalysisResponse } from '../services/api';

interface NewsAnalyzerProps {
  onAnalysisComplete: (result: AnalysisResponse) => void;
}

const DEMO_PRESETS = [
  {
    id: "conspiracy-cure",
    title: "Viral Cancer Hoax",
    badge: "Misinformation Sample",
    badgeColor: "text-rose-700 bg-rose-50 border-rose-200",
    headline: "SHOCKING: Secret Government Documents Leaked Proving All Cancer Cures Were Suppressed for Decades!",
    content: "A heroic whistleblower has just LEAKED explosive classified files that the deep state pharmaceutical mafia NEVER wanted you to see! The mind-blowing documents confirm that a 100% natural herbal remedy discovered in 1952 cures all forms of terminal cancer in just 48 hours, but corrupt billionaire elites buried it to protect their multi-trillion dollar profits! Mainstream media is under complete blackout! You won't believe what happens when you drink this everyday kitchen juice! Share this VIRAL warning before it gets banned and deleted from the internet forever! Wake up sheeple!"
  },
  {
    id: "genuine-reuters",
    title: "Federal Reserve News",
    badge: "Legitimate News Sample",
    badgeColor: "text-emerald-700 bg-emerald-50 border-emerald-200",
    headline: "Federal Reserve Holds Interest Rates Steady Amid Cooling Inflation Indicators",
    content: "The Federal Reserve concluded its two-day Federal Open Market Committee meeting on Wednesday, voting unanimously to maintain the benchmark federal funds rate. In the post-meeting statement, Fed officials cited easing consumer price index data and stable labor market conditions as justification for holding policy steady. Economists surveyed by Reuters noted that core inflation dropped 0.2 percentage points over the past quarter, reflecting tighter credit conditions. Fed Chairman Powell emphasized during the news conference that upcoming policy decisions will remain strictly data-dependent."
  },
  {
    id: "space-discovery",
    title: "NASA Space Discovery",
    badge: "Verified Science Sample",
    badgeColor: "text-blue-700 bg-blue-50 border-blue-200",
    headline: "NASA James Webb Space Telescope Identifies Atmospheric Water Vapor in Exoplanet Orbit",
    content: "Astrophysicists analyzing spectroscopic data from the James Webb Space Telescope have confirmed the presence of atmospheric water vapor on exoplanet WASP-96b, located approximately 1,150 light-years away. The peer-reviewed study, published in the journal Nature Astronomy, utilized near-infrared instruments to measure chemical absorption signatures during planetary transit. Lead researcher Dr. Elena Vance explained that while the high atmospheric temperatures make the planet uninhabitable, the precision measurements provide critical insights into planetary formation models."
  },
  {
    id: "clickbait-finance",
    title: "Secret Debt Loophole",
    badge: "Clickbait Sample",
    badgeColor: "text-amber-800 bg-amber-50 border-amber-200",
    headline: "YOU WON'T BELIEVE THIS: Rogue Whistleblower Exposes One Secret Trick That Instantly Eliminates All Debt!",
    content: "Banks and Wall Street millionaires are FURIOUS after an anonymous rogue mathematician exposed this one simple secret loop-hole that completely wipes out your mortgage, credit cards, and student loans overnight! Federal authorities are scrambling to shut down this webpage immediately! Doctors and financial advisors hate him for exposing the hidden truth! Click here right now to see the shocking video before corrupt bankers take it down!"
  }
];

const WORKING_URL_SAMPLES = [
  {
    name: "BBC News",
    url: "https://www.bbc.com/news"
  },
  {
    name: "NASA News",
    url: "https://www.nasa.gov/news-release/nasa-highlights-science-breakthroughs/"
  },
  {
    name: "NPR News",
    url: "https://www.npr.org/sections/news/"
  }
];

export const NewsAnalyzer: React.FC<NewsAnalyzerProps> = ({ onAnalysisComplete }) => {
  const [inputMode, setInputMode] = useState<'text' | 'url'>('text');
  const [headline, setHeadline] = useState('');
  const [content, setContent] = useState('');
  const [url, setUrl] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const stages = [
    "Reading and scanning text structure...",
    "Analyzing emotional tone and sensational language...",
    "Checking for clickbait and exaggerated claims...",
    "Examining patterns against verified facts...",
    "Generating your easy-to-read explanation..."
  ];

  const handlePresetSelect = (preset: typeof DEMO_PRESETS[0]) => {
    setInputMode('text');
    setHeadline(preset.headline);
    setContent(preset.content);
    setError(null);
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (inputMode === 'text' && !headline.trim() && !content.trim()) {
      setError('Please enter a headline or paste some news text.');
      return;
    }

    if (inputMode === 'url' && !url.trim()) {
      setError('Please enter a valid website link starting with https://');
      return;
    }

    setLoading(true);
    setLoadingStage(0);

    const interval = setInterval(() => {
      setLoadingStage((prev) => (prev < stages.length - 1 ? prev + 1 : prev));
    }, 450);

    try {
      let result: AnalysisResponse;
      if (inputMode === 'url') {
        result = await api.analyzeUrl({
          url: url.trim(),
          verify_evidence: true
        });
      } else {
        result = await api.analyzeText({
          headline: headline.trim(),
          content: content.trim(),
          verify_evidence: true
        });
      }

      clearInterval(interval);
      setLoading(false);
      onAnalysisComplete(result);
    } catch (err: any) {
      clearInterval(interval);
      setLoading(false);
      setError(err.message || 'Unable to analyze content. Please try again or paste the text directly.');
    }
  };

  const totalWords = (headline + ' ' + content).trim().split(/\s+/).filter(Boolean).length;

  return (
    <div className="max-w-4xl mx-auto space-y-7">
      
      {/* Headline */}
      <div className="text-center space-y-2.5 pt-2">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          Is that news article <span className="text-amber-600">real</span> or <span className="text-rose-600">fake</span>?
        </h1>
        <p className="text-slate-600 text-sm max-w-lg mx-auto">
          Paste any news article, headline, or website link below. TruthLens analyzes the text, reveals sensational wording, and explains why.
        </p>
      </div>

      {/* 1-Click Samples Bar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm space-y-2.5">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
          <Sparkles className="w-4 h-4 text-amber-500" />
          <span>TRY A DEMO SAMPLE WITH 1 CLICK:</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
          {DEMO_PRESETS.map((preset) => (
            <button
              key={preset.id}
              onClick={() => handlePresetSelect(preset)}
              className="text-left p-3 rounded-xl bg-slate-50 border border-slate-200 hover:border-amber-400 hover:bg-amber-50/50 transition-all group"
            >
              <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded border inline-block mb-1 ${preset.badgeColor}`}>
                {preset.badge}
              </span>
              <p className="text-xs font-semibold text-slate-800 group-hover:text-amber-700 transition-colors truncate">
                {preset.title}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Main Input Box */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-lg overflow-hidden">
        
        {/* Toggle Mode */}
        <div className="flex border-b border-slate-200 bg-slate-50 p-2 gap-2">
          <button
            type="button"
            onClick={() => { setInputMode('text'); setError(null); }}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold transition-all ${
              inputMode === 'text'
                ? 'bg-amber-500 text-slate-950 shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Paste News Text</span>
          </button>

          <button
            type="button"
            onClick={() => { setInputMode('url'); setError(null); }}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold transition-all ${
              inputMode === 'url'
                ? 'bg-amber-500 text-slate-950 shadow-sm'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Link2 className="w-4 h-4" />
            <span>Check a Website Link</span>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleAnalyze} className="p-5 sm:p-7 space-y-4">
          
          {inputMode === 'text' ? (
            <>
              {/* Headline */}
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-700">
                  Headline or Title <span className="text-slate-400 font-normal">(optional)</span>
                </label>
                <input
                  type="text"
                  value={headline}
                  onChange={(e) => setHeadline(e.target.value)}
                  placeholder="e.g. Breaking: Miracle cure for cancer discovered..."
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500/40 focus:border-amber-500 focus:bg-white"
                />
              </div>

              {/* Body */}
              <div className="space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <label className="font-semibold text-slate-700">
                    Article Text or Message
                  </label>
                  {totalWords > 0 && (
                    <span className="text-slate-500 font-mono text-[11px]">{totalWords} words</span>
                  )}
                </div>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  rows={6}
                  placeholder="Paste the full article, social media post, or WhatsApp forward here..."
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-4 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500/40 focus:border-amber-500 focus:bg-white resize-y leading-relaxed"
                />
              </div>
            </>
          ) : (
            /* URL Mode */
            <div className="space-y-3 py-2">
              <label className="text-xs font-semibold text-slate-700">
                Website Link (URL)
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Search className="w-4 h-4" />
                </div>
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://www.bbc.com/news/..."
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl pl-10 pr-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500/40 focus:border-amber-500 focus:bg-white font-mono"
                />
              </div>

              {/* Quick Sample Links */}
              <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
                <span className="text-slate-500 text-[11px]">Quick link examples:</span>
                {WORKING_URL_SAMPLES.map((sample, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => { setUrl(sample.url); setError(null); }}
                    className="px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-slate-700 hover:text-amber-700 hover:border-amber-400 hover:bg-amber-50 transition-colors text-[11px] font-mono flex items-center gap-1"
                  >
                    <span>{sample.name}</span>
                    <ExternalLink className="w-2.5 h-2.5" />
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Friendly Error with Quick Switch */}
          {error && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 space-y-2 text-rose-800 text-xs">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
                <span>{error}</span>
              </div>
              {inputMode === 'url' && (
                <button
                  type="button"
                  onClick={() => {
                    setInputMode('text');
                    setError(null);
                  }}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-100 text-rose-800 hover:bg-rose-200 border border-rose-300 font-semibold text-xs transition-colors"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>Switch to "Paste News Text" tab</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          )}

          {/* Action Button */}
          <div className="pt-2">
            {loading ? (
              <div className="p-4 rounded-xl bg-slate-50 border border-amber-300 space-y-2.5 text-center">
                <div className="flex items-center justify-center gap-2 text-xs font-semibold text-amber-700">
                  <RefreshCw className="w-4 h-4 animate-spin text-amber-600" />
                  <span>Checking this article...</span>
                </div>
                <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                  <div 
                    className="bg-gradient-to-r from-amber-500 to-rose-500 h-full rounded-full transition-all duration-300"
                    style={{ width: `${((loadingStage + 1) / stages.length) * 100}%` }}
                  />
                </div>
                <p className="text-xs text-slate-600 font-mono">
                  {stages[loadingStage]}
                </p>
              </div>
            ) : (
              <button
                type="submit"
                className="w-full py-3.5 px-6 rounded-xl bg-gradient-to-r from-amber-500 to-rose-500 hover:from-amber-400 hover:to-rose-400 text-slate-950 font-bold text-sm sm:text-base flex items-center justify-center gap-2 shadow-md hover:shadow-lg transition-all"
              >
                <Send className="w-4 h-4" />
                <span>Check News with TruthLens</span>
              </button>
            )}
          </div>

        </form>

      </div>

    </div>
  );
};
