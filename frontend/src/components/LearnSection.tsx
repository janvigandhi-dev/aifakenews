import React from 'react';
import { ShieldAlert } from 'lucide-react';

export const LearnSection: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      
      {/* Header */}
      <div className="text-center space-y-2 pt-2">
        <h1 className="text-3xl font-extrabold text-slate-900">
          How TruthLens Works
        </h1>
        <p className="text-slate-600 text-sm max-w-lg mx-auto">
          Learn how AI identifies suspicious patterns and how you can protect yourself from online misinformation.
        </p>
      </div>

      {/* 3 Step Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        
        <div className="p-5 rounded-2xl bg-white border border-slate-200 space-y-3 shadow-sm">
          <div className="w-8 h-8 rounded-xl bg-amber-100 text-amber-800 font-bold flex items-center justify-center text-sm">
            1
          </div>
          <h3 className="font-bold text-slate-900 text-base">Language Scanning</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Scans for sensational words (e.g. <em>shocking, miracle, exposed, secret</em>), excessive punctuation (<code>!!!</code>), and all-caps shouting.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-200 space-y-3 shadow-sm">
          <div className="w-8 h-8 rounded-xl bg-rose-100 text-rose-800 font-bold flex items-center justify-center text-sm">
            2
          </div>
          <h3 className="font-bold text-slate-900 text-base">Pattern Matching</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Compares the text against thousands of verified news stories and known clickbait formats to detect misleading structures.
          </p>
        </div>

        <div className="p-5 rounded-2xl bg-white border border-slate-200 space-y-3 shadow-sm">
          <div className="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-800 font-bold flex items-center justify-center text-sm">
            3
          </div>
          <h3 className="font-bold text-slate-900 text-base">Fact & Claim Checking</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Extracts key claims from the article and checks whether they align with or contradict established facts and credible news wire agencies.
          </p>
        </div>

      </div>

      {/* Tips for Spotting Fake News */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-7 space-y-4 shadow-md">
        <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-amber-500" />
          <span>Top 4 Signs of Misleading News:</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
          
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-xs font-bold text-amber-700">1. Emotional Trigger Headlines</span>
            <p className="text-xs text-slate-600">
              Headlines created to make you angry, panicked, or outraged often prioritize clicks over factual accuracy.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-xs font-bold text-rose-700">2. Missing Sourced Quotes</span>
            <p className="text-xs text-slate-600">
              Legitimate news always names specific researchers, officials, or studies rather than vague "insiders" or "secret doctors".
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-xs font-bold text-purple-700">3. Miracle Cures or Instant Solutions</span>
            <p className="text-xs text-slate-600">
              Claims promising 100% cure in 48 hours or instant wealth are almost always fraudulent.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
            <span className="text-xs font-bold text-emerald-700">4. Check the Source URL</span>
            <p className="text-xs text-slate-600">
              Imitation websites often use modified domain names (e.g. <code>.co</code> or <code>.news-official.com</code>) to mimic real publishers.
            </p>
          </div>

        </div>
      </div>

    </div>
  );
};
