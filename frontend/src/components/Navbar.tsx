import React, { useState } from 'react';
import { ShieldCheck, History, BookOpen, Activity, X, ChevronRight } from 'lucide-react';

interface NavbarProps {
  activeTab: 'analyzer' | 'history' | 'learn';
  setActiveTab: (tab: 'analyzer' | 'history' | 'learn') => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
}) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const navItems = [
    {
      id: 'analyzer' as const,
      label: 'Analyze News',
      desc: 'Check headlines, articles, or web links',
      icon: <Activity className="w-5 h-5 text-amber-500" />
    },
    {
      id: 'history' as const,
      label: 'Past Analyses',
      desc: 'View previously checked news & download reports',
      icon: <History className="w-5 h-5 text-blue-500" />
    },
    {
      id: 'learn' as const,
      label: 'How It Works',
      desc: 'Learn how AI detects misleading patterns',
      icon: <BookOpen className="w-5 h-5 text-emerald-500" />
    }
  ];

  const handleSelectTab = (tabId: 'analyzer' | 'history' | 'learn') => {
    setActiveTab(tabId);
    setIsMenuOpen(false);
  };

  return (
    <>
      <header className="sticky top-0 z-50 backdrop-blur-md bg-white/90 border-b border-slate-200 shadow-sm">
        <div className="max-w-5xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-16">
            
            {/* Logo */}
            <div 
              className="flex items-center gap-3 cursor-pointer group"
              onClick={() => handleSelectTab('analyzer')}
            >
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-amber-500 to-rose-500 p-0.5 shadow-md shadow-amber-500/20 group-hover:scale-105 transition-transform duration-200">
                <div className="w-full h-full bg-white rounded-[10px] flex items-center justify-center">
                  <ShieldCheck className="w-5 h-5 text-amber-500" />
                </div>
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-xl tracking-tight text-slate-900">
                    Truth<span className="text-amber-500">Lens</span>
                  </span>
                  <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
                    Explainable AI
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 hidden sm:block">
                  AI Fake News & Misinformation Detector
                </p>
              </div>
            </div>

            {/* 3-Line Hamburger Menu Button */}
            <button
              type="button"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              aria-label="Toggle Navigation Menu"
              className={`p-2.5 rounded-xl border transition-all flex items-center gap-2 text-xs font-semibold ${
                isMenuOpen 
                  ? 'bg-amber-500 text-slate-950 border-amber-500 shadow-md' 
                  : 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-200 hover:border-amber-400'
              }`}
            >
              {isMenuOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <div className="flex flex-col justify-center items-center gap-1 w-5 h-5">
                  <span className="w-4 h-0.5 bg-slate-800 rounded-full"></span>
                  <span className="w-4 h-0.5 bg-slate-800 rounded-full"></span>
                  <span className="w-4 h-0.5 bg-slate-800 rounded-full"></span>
                </div>
              )}
              <span className="hidden sm:inline font-mono text-[11px] uppercase tracking-wider">
                {isMenuOpen ? 'Close' : 'Menu'}
              </span>
            </button>

          </div>
        </div>
      </header>

      {/* Slide-out Navigation Drawer */}
      {isMenuOpen && (
        <div className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm transition-opacity" onClick={() => setIsMenuOpen(false)}>
          <div 
            className="fixed top-16 right-0 sm:right-6 max-w-sm w-full bg-white border border-slate-200 sm:rounded-2xl shadow-2xl p-5 space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900 font-mono uppercase tracking-wider">
                  Navigation
                </h3>
                <p className="text-[11px] text-slate-500">Choose where you want to go</p>
              </div>
              <button 
                onClick={() => setIsMenuOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Navigation List */}
            <div className="space-y-2">
              {navItems.map((item) => {
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => handleSelectTab(item.id)}
                    className={`w-full text-left p-3.5 rounded-xl border transition-all flex items-center justify-between gap-3 group ${
                      isActive
                        ? 'bg-amber-50 border-amber-300 text-slate-900 shadow-sm'
                        : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-white border border-slate-200 shadow-sm group-hover:scale-105 transition-transform">
                        {item.icon}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className={`text-sm font-bold ${isActive ? 'text-amber-700' : 'text-slate-900'}`}>
                            {item.label}
                          </span>
                          {isActive && (
                            <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-amber-500 text-slate-950">
                              Active
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-500 mt-0.5">{item.desc}</p>
                      </div>
                    </div>
                    <ChevronRight className={`w-4 h-4 transition-transform ${isActive ? 'text-amber-600 translate-x-0.5' : 'text-slate-400 group-hover:text-slate-600'}`} />
                  </button>
                );
              })}
            </div>

          </div>
        </div>
      )}
    </>
  );
};
