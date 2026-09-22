import React, { useState, useRef } from 'react';
import { 
  Sparkles, Send, RefreshCw, AlertCircle, Search, ExternalLink,
  ImagePlus, Upload, X, FileText, Globe, CheckCircle2, Link as LinkIcon
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
    text: "SHOCKING: Secret Government Documents Leaked Proving All Cancer Cures Were Suppressed for Decades!\n\nA heroic whistleblower has just LEAKED explosive classified files that the deep state pharmaceutical mafia NEVER wanted you to see! The mind-blowing documents confirm that a 100% natural herbal remedy discovered in 1952 cures all forms of terminal cancer in just 48 hours, but corrupt billionaire elites buried it to protect their multi-trillion dollar profits! Mainstream media is under complete blackout! You won't believe what happens when you drink this everyday kitchen juice! Share this VIRAL warning before it gets banned and deleted from the internet forever! Wake up sheeple!"
  },
  {
    id: "genuine-reuters",
    title: "Federal Reserve News",
    badge: "Legitimate News Sample",
    badgeColor: "text-emerald-700 bg-emerald-50 border-emerald-200",
    text: "Federal Reserve Holds Interest Rates Steady Amid Cooling Inflation Indicators\n\nThe Federal Reserve concluded its two-day Federal Open Market Committee meeting on Wednesday, voting unanimously to maintain the benchmark federal funds rate. In the post-meeting statement, Fed officials cited easing consumer price index data and stable labor market conditions as justification for holding policy steady. Economists surveyed by Reuters noted that core inflation dropped 0.2 percentage points over the past quarter, reflecting tighter credit conditions. Fed Chairman Powell emphasized during the news conference that upcoming policy decisions will remain strictly data-dependent."
  },
  {
    id: "space-discovery",
    title: "NASA Space Discovery",
    badge: "Verified Science Sample",
    badgeColor: "text-blue-700 bg-blue-50 border-blue-200",
    text: "NASA James Webb Space Telescope Identifies Atmospheric Water Vapor in Exoplanet Orbit\n\nAstrophysicists analyzing spectroscopic data from the James Webb Space Telescope have confirmed the presence of atmospheric water vapor on exoplanet WASP-96b, located approximately 1,150 light-years away. The peer-reviewed study, published in the journal Nature Astronomy, utilized near-infrared instruments to measure chemical absorption signatures during planetary transit. Lead researcher Dr. Elena Vance explained that while the high atmospheric temperatures make the planet uninhabitable, the precision measurements provide critical insights into planetary formation models."
  },
  {
    id: "clickbait-finance",
    title: "Secret Debt Loophole",
    badge: "Clickbait Sample",
    badgeColor: "text-amber-800 bg-amber-50 border-amber-200",
    text: "YOU WON'T BELIEVE THIS: Rogue Whistleblower Exposes One Secret Trick That Instantly Eliminates All Debt!\n\nBanks and Wall Street millionaires are FURIOUS after an anonymous rogue mathematician exposed this one simple secret loop-hole that completely wipes out your mortgage, credit cards, and student loans overnight! Federal authorities are scrambling to shut down this webpage immediately! Doctors and financial advisors hate him for exposing the hidden truth! Click here right now to see the shocking video before corrupt bankers take it down!"
  }
];

export const NewsAnalyzer: React.FC<NewsAnalyzerProps> = ({ onAnalysisComplete }) => {
  const [newsText, setNewsText] = useState('');
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageUrl, setImageUrl] = useState('');
  const [showUrlInput, setShowUrlInput] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const stages = [
    "Reading claim & extracting OCR text from attached image...",
    "Surfing the live internet for news reports & fact-checks...",
    "AI cross-referencing claim with real-world sources...",
    "Evaluating credibility and compiling clickable references..."
  ];

  const handlePresetSelect = (preset: typeof DEMO_PRESETS[0]) => {
    setNewsText(preset.text);
    setImageFile(null);
    setImagePreview(null);
    setImageUrl('');
    setError(null);
  };

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
    if (!validTypes.includes(file.type)) {
      setError('Please upload a valid image (JPG, PNG, or WebP).');
      return;
    }

    if (file.size > 20 * 1024 * 1024) {
      setError('Image file is too large (max 20MB).');
      return;
    }

    setImageFile(file);
    setImageUrl('');
    setError(null);

    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveImage = () => {
    setImageFile(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
      if (!validTypes.includes(file.type)) {
        setError('Please upload a valid image (JPG, PNG, or WebP).');
        return;
      }
      if (file.size > 20 * 1024 * 1024) {
        setError('Image file is too large (max 20MB).');
        return;
      }
      setImageFile(file);
      setImageUrl('');
      setError(null);
      const reader = new FileReader();
      reader.onloadend = () => setImagePreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedText = newsText.trim();
    const trimmedUrl = imageUrl.trim();

    if (!trimmedText && !imageFile && !trimmedUrl) {
      setError('Please enter news text/description or attach an image to analyze.');
      return;
    }

    setLoading(true);
    setLoadingStage(0);

    const interval = setInterval(() => {
      setLoadingStage((prev) => (prev < stages.length - 1 ? prev + 1 : prev));
    }, 1200);

    try {
      const result = await api.analyzeUnified({
        text: trimmedText,
        imageFile: imageFile,
        imageUrl: trimmedUrl,
        model_name: undefined
      });

      clearInterval(interval);
      setLoading(false);
      onAnalysisComplete(result);
    } catch (err: any) {
      clearInterval(interval);
      setLoading(false);
      setError(err.message || 'Unable to complete news verification. Please try again.');
    }
  };

  const wordCount = newsText.trim().split(/\s+/).filter(Boolean).length;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      
      {/* Header Banner */}
      <div className="text-center space-y-2 pt-1">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          Is That News <span className="text-amber-600">Real</span> or <span className="text-rose-600">Fake</span>?
        </h1>
        <p className="text-slate-600 text-sm max-w-xl mx-auto">
          Type or paste any news claim, attach a screenshot/photo, or provide a link. TruthLens extracts text via OCR, surfs the live internet for matching news, and verifies credibility with clickable source references.
        </p>
      </div>

      {/* 1-Click Demo Samples Bar */}
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

      {/* Unified Input Form Card */}
      <div className="bg-white border border-slate-200 rounded-2xl shadow-lg overflow-hidden">
        
        {/* Workflow Subheader Badge */}
        <div className="bg-slate-50 border-b border-slate-200 px-5 py-3 flex flex-wrap items-center justify-between gap-2 text-xs">
          <div className="flex items-center gap-2 text-slate-700 font-semibold">
            <Globe className="w-4 h-4 text-blue-600" />
            <span>Unified Fact-Checking Workflow</span>
          </div>
          <div className="flex items-center gap-1.5 text-[11px] text-slate-500 font-mono">
            <span>OCR Extraction</span>
            <span>➔</span>
            <span>Live Web Search</span>
            <span>➔</span>
            <span>Direct Sources</span>
          </div>
        </div>

        <form onSubmit={handleAnalyze} className="p-5 sm:p-7 space-y-5">
          
          {/* Main Text Area */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-xs">
              <label className="font-semibold text-slate-700 flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-amber-600" />
                <span>News Claim / Article Text / Description</span>
              </label>
              {wordCount > 0 && (
                <span className="text-slate-500 font-mono text-[11px]">{wordCount} words</span>
              )}
            </div>
            
            <textarea
              value={newsText}
              onChange={(e) => setNewsText(e.target.value)}
              rows={5}
              placeholder="Paste the news headline, claim, WhatsApp forward, article text, or describe the screenshot here..."
              className="w-full bg-slate-50 border border-slate-300 rounded-xl p-4 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500/40 focus:border-amber-500 focus:bg-white resize-y leading-relaxed transition-all"
            />
          </div>

          {/* Image Attachment & Drag Drop Zone */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-slate-700 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <ImagePlus className="w-4 h-4 text-blue-600" />
                <span>Attach Image / Screenshot (Optional OCR Scan)</span>
              </span>
              {!showUrlInput && (
                <button
                  type="button"
                  onClick={() => setShowUrlInput(true)}
                  className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1 transition-colors"
                >
                  <LinkIcon className="w-3 h-3" />
                  <span>Or attach web/image link</span>
                </button>
              )}
            </label>

            {!imagePreview ? (
              <div
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-slate-300 rounded-xl p-5 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50/30 transition-all group flex flex-col sm:flex-row items-center justify-center gap-3"
              >
                <div className="w-10 h-10 rounded-full bg-blue-50 group-hover:bg-blue-100 flex items-center justify-center shrink-0 transition-colors">
                  <Upload className="w-5 h-5 text-blue-600" />
                </div>
                <div className="text-center sm:text-left">
                  <p className="text-xs font-semibold text-slate-700 group-hover:text-blue-600 transition-colors">
                    Click to attach or drag & drop news screenshot/image
                  </p>
                  <p className="text-[11px] text-slate-400">
                    JPG, PNG, WebP • EasyOCR will automatically extract text from image
                  </p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/jpeg,image/png,image/webp,image/gif"
                  onChange={handleImageSelect}
                  className="hidden"
                />
              </div>
            ) : (
              <div className="relative border border-slate-200 rounded-xl overflow-hidden bg-slate-50 flex items-center gap-4 p-3">
                <img
                  src={imagePreview}
                  alt="Preview"
                  className="w-16 h-16 object-cover rounded-lg border border-slate-200 shrink-0"
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 truncate">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span className="truncate">{imageFile?.name}</span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    {imageFile ? (imageFile.size / 1024 / 1024).toFixed(2) : 0} MB • OCR Ready
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleRemoveImage}
                  className="p-1.5 rounded-lg hover:bg-rose-50 text-slate-400 hover:text-rose-600 transition-colors shrink-0"
                  title="Remove image"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>

          {/* Optional URL Link Input */}
          {showUrlInput && (
            <div className="space-y-1.5 p-3.5 rounded-xl bg-slate-50 border border-slate-200 transition-all">
              <div className="flex items-center justify-between text-xs">
                <label className="font-semibold text-slate-700 flex items-center gap-1.5">
                  <LinkIcon className="w-3.5 h-3.5 text-blue-600" />
                  <span>Web Article / Image URL</span>
                </label>
                <button
                  type="button"
                  onClick={() => { setShowUrlInput(false); setImageUrl(''); }}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
              <input
                type="url"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                placeholder="https://example.com/news-story or image URL..."
                className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-400/40 focus:border-blue-500 font-mono"
              />
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {/* Submit / Loading Button */}
          <div className="pt-2">
            {loading ? (
              <div className="p-4 rounded-xl bg-slate-50 border border-amber-300 space-y-2.5 text-center">
                <div className="flex items-center justify-center gap-2 text-xs font-semibold text-amber-700">
                  <RefreshCw className="w-4 h-4 animate-spin text-amber-600" />
                  <span>Searching Live Internet & Fact-Checking...</span>
                </div>
                <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                  <div 
                    className="h-full rounded-full transition-all duration-500 bg-gradient-to-r from-amber-500 via-rose-500 to-emerald-500"
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
                className="w-full py-3.5 px-6 rounded-xl font-bold text-sm sm:text-base flex items-center justify-center gap-2 shadow-md hover:shadow-lg transition-all bg-gradient-to-r from-amber-500 via-rose-500 to-amber-500 bg-[length:200%_auto] hover:bg-right text-slate-950 font-sans"
              >
                <Search className="w-4 h-4" />
                <span>Verify Claim & Search Internet References</span>
              </button>
            )}
          </div>

        </form>

      </div>

    </div>
  );
};
