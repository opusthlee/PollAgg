'use client';

import { useState, useEffect } from 'react';

interface MiniDashboardProps {
  category?: string;
  regions?: string[];
}

export default function MiniDashboard({ 
  category = 'local_election', 
  regions = ['National', '서울', '경기', '인천', '강원', '영남', '호남', '충청'] 
}: MiniDashboardProps) {
  const [data, setData] = useState<any>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);
  
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002/api';
  const dashboardUrl = process.env.NEXT_PUBLIC_DASHBOARD_URL || 'http://localhost:3000';

  useEffect(() => {
    fetchBatchData();
  }, [category]);

  const fetchBatchData = async () => {
    try {
      // 1. Fetch raw data first
      const rawRes = await fetch(`${apiUrl}/data?category=${category}`);
      const rawData = await rawRes.json();

      // 2. Run batch analysis
      const res = await fetch(`${apiUrl}/batch-analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data: rawData,
          category: category,
          config: {
            use_smoothing: true,
            use_correlated_errors: true
          },
          regions: regions
        })
      });
      const batchResult = await res.json();
      setData(batchResult);
    } catch (err) {
      console.error("Failed to fetch mini dashboard data", err);
    } finally {
      setLoading(false);
    }
  };

  const handleTouchStart = (e: React.TouchEvent) => setTouchStart(e.targetTouches[0].clientX);
  const handleTouchMove = (e: React.TouchEvent) => setTouchEnd(e.targetTouches[0].clientX);
  const handleTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > 50;
    const isRightSwipe = distance < -50;
    if (isLeftSwipe) setCurrentIndex((prev) => (prev + 1) % regions.length);
    if (isRightSwipe) setCurrentIndex((prev) => (prev - 1 + regions.length) % regions.length);
    setTouchStart(null);
    setTouchEnd(null);
  };

  if (loading || !data) return (
    <div className="w-80 h-96 bg-slate-900/50 backdrop-blur-xl border border-white/10 rounded-3xl flex items-center justify-center">
      <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
    </div>
  );

  const activeRegion = regions[currentIndex];
  const regionData = data[activeRegion];

  if (!regionData) {
    // Skip to next if no data for this region
    return null;
  }

  const prediction = regionData.prediction;
  const summary = regionData.summary;
  
  // Dynamic parties (Support for 3rd parties)
  const parties = Object.keys(summary).map(key => ({
    name: key.replace(/_lead/g, '').replace(/party_/g, '').toUpperCase(),
    value: summary[key].weighted_mean,
    color: key.includes('DP') ? '#4f46e5' : key.includes('PPP') ? '#f43f5e' : '#10b981'
  })).sort((a, b) => b.value - a.value);

  const totalValue = parties.reduce((sum, p) => sum + p.value, 0);

  return (
    <div 
      className="w-80 h-[300px] bg-slate-950/40 backdrop-blur-2xl border border-white/10 rounded-[28px] overflow-hidden shadow-2xl relative group select-none transition-all duration-500 hover:scale-[1.03] hover:shadow-indigo-500/20 cursor-pointer"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onClick={() => window.open(`${dashboardUrl}/view`, '_blank')}
    >
      {/* Background Glow */}
      <div className="absolute -top-16 -left-16 w-32 h-32 bg-indigo-600/15 rounded-full blur-[60px]"></div>
      <div className="absolute -bottom-16 -right-16 w-32 h-32 bg-rose-600/15 rounded-full blur-[60px]"></div>

      <div className="relative h-full p-5 flex flex-col">
        {/* Header - Compact */}
        <div className="text-center mb-4">
          <div className="flex justify-between items-start mb-1">
            <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest">2026 지방선거</span>
            <div className="bg-white/5 px-1.5 py-0.5 rounded border border-white/10 text-[8px] text-slate-400 font-mono">
              LIVE
            </div>
          </div>
          <div className="text-white text-base font-black uppercase tracking-tight">
            {activeRegion === 'National' ? '전국 종합' : activeRegion}
          </div>
        </div>

        {/* Stacked Progress Bar (Multi-party support) */}
        <div className="w-full h-3 bg-white/5 rounded-full overflow-hidden flex mb-8">
          {parties.map((p, i) => (
            <div 
              key={p.name}
              style={{ width: `${(p.value / totalValue) * 100}%`, backgroundColor: p.color }}
              className="h-full transition-all duration-1000 ease-out"
            />
          ))}
        </div>

        {/* Main Metric - Compact */}
        <div className="flex-1 flex flex-col items-center justify-center text-center">
          <div className="text-5xl font-black text-white tracking-tighter mb-0.5 drop-shadow-2xl">
            {prediction.target_1_lead_prob.toFixed(1)}<span className="text-xl ml-0.5 opacity-50">%</span>
          </div>
          <div className="text-[9px] font-bold text-slate-400 uppercase tracking-[0.2em] mb-4">
            Win Probability
          </div>

          <div className="bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-xl flex items-center gap-1.5 mb-2">
            <span className="text-emerald-400 text-xs font-bold">+{Math.abs(prediction.expected_gap).toFixed(1)}%p Gap</span>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 10l7-7m0 0l7 7m-7-7v18" />
            </svg>
          </div>
        </div>

        {/* Footer Info - Slimmer */}
        <div className="mt-auto pt-3 border-t border-white/5 flex justify-between items-center">
          <div className="flex flex-col">
            <span className="text-[8px] text-slate-500 uppercase font-bold tracking-widest">Certainty</span>
            <span className="text-[10px] text-white font-medium">±{prediction.calculated_uncertainty.toFixed(1)}%</span>
          </div>
          <div className="flex gap-1">
            {regions.map((_, i) => (
              <div 
                key={i} 
                className={`w-0.5 h-0.5 rounded-full transition-all duration-500 ${i === currentIndex ? 'w-3 bg-indigo-500' : 'bg-white/20'}`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Manual Controls - Faint Arrows */}
      <div className="absolute inset-y-0 left-0 w-12 flex items-center pointer-events-none">
        <button 
          onClick={(e) => {
            e.stopPropagation();
            setCurrentIndex((prev) => (prev - 1 + regions.length) % regions.length);
          }}
          className="w-full h-16 bg-white/5 hover:bg-white/10 backdrop-blur-sm rounded-r-2xl flex items-center justify-center text-white/20 hover:text-white transition-all pointer-events-auto"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
      </div>
      <div className="absolute inset-y-0 right-0 w-12 flex items-center pointer-events-none">
        <button 
          onClick={(e) => {
            e.stopPropagation();
            setCurrentIndex((prev) => (prev + 1) % regions.length);
          }}
          className="w-full h-16 bg-white/5 hover:bg-white/10 backdrop-blur-sm rounded-l-2xl flex items-center justify-center text-white/20 hover:text-white transition-all pointer-events-auto"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}
