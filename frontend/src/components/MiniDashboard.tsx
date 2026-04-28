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
    <div className="w-80 h-[147px] bg-slate-900/50 backdrop-blur-xl border border-white/10 rounded-[24px] flex items-center justify-center">
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
      className="w-80 h-[147px] bg-slate-950/40 backdrop-blur-2xl border border-white/10 rounded-[24px] overflow-hidden shadow-2xl relative group select-none transition-all duration-500 hover:scale-[1.03] hover:shadow-indigo-500/20 cursor-pointer"
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      onClick={() => window.open(`${dashboardUrl}/view`, '_blank')}
    >
      {/* Background Glow */}
      <div className="absolute -top-16 -left-16 w-32 h-32 bg-indigo-600/15 rounded-full blur-[60px]"></div>
      <div className="absolute -bottom-16 -right-16 w-32 h-32 bg-rose-600/15 rounded-full blur-[60px]"></div>

      <div className="relative h-full px-3 py-2.5 flex flex-col">
        {/* Header — title +50% larger, LIVE chip in yellow */}
        <div className="flex justify-between items-start mb-0.5">
          <span className="text-[15px] font-bold text-indigo-400 uppercase tracking-widest leading-tight">2026 지방선거</span>
          <div className="bg-yellow-400/15 px-1.5 py-0.5 rounded border border-yellow-400/40 text-[8px] text-yellow-300 font-mono font-bold">
            LIVE
          </div>
        </div>
        <div className="text-white text-xs font-black uppercase tracking-tight text-center mb-1.5">
          {activeRegion === 'National' ? '전국 통합' : activeRegion}
        </div>

        {/* Stacked Progress Bar */}
        <div className="w-full h-1.5 bg-white/5 rounded-full overflow-hidden flex">
          {parties.map((p, i) => (
            <div
              key={p.name}
              style={{ width: `${(p.value / totalValue) * 100}%`, backgroundColor: p.color }}
              className="h-full transition-all duration-1000 ease-out"
            />
          ))}
        </div>

        {/* Stats row: Certainty (left) | Win Probability (center, +10% larger) | Gap (right) */}
        <div className="flex-1 flex items-center justify-between gap-1.5 px-1">
          <div className="flex flex-col items-center flex-1 min-w-0">
            <span className="text-[8px] font-bold text-slate-500 uppercase tracking-[0.15em] whitespace-nowrap">Certainty</span>
            <span className="text-lg font-black text-white tracking-tighter leading-none mt-0.5">
              ±{prediction.calculated_uncertainty.toFixed(1)}<span className="text-[9px] opacity-50 ml-0.5">%</span>
            </span>
          </div>
          <div className="w-px h-8 bg-white/10 flex-shrink-0" />
          <div className="flex flex-col items-center flex-1 min-w-0">
            <span className="text-[9px] font-bold text-indigo-400 uppercase tracking-[0.15em] whitespace-nowrap">Win Prob</span>
            <span className="text-xl font-black text-white tracking-tighter leading-none mt-0.5 drop-shadow-2xl">
              {prediction.target_1_lead_prob.toFixed(1)}<span className="text-[11px] opacity-50 ml-0.5">%</span>
            </span>
          </div>
          <div className="w-px h-8 bg-white/10 flex-shrink-0" />
          <div className="flex flex-col items-center flex-1 min-w-0">
            <span className="text-[8px] font-bold text-slate-500 uppercase tracking-[0.15em] whitespace-nowrap">Gap</span>
            <span className="text-lg font-black text-emerald-400 tracking-tighter leading-none mt-0.5">
              +{Math.abs(prediction.expected_gap).toFixed(1)}<span className="text-[9px] opacity-70 ml-0.5">%p</span>
            </span>
          </div>
        </div>

        {/* Region dots — bottom strip (no extra margin; flex-1 above pushes content evenly) */}
        <div className="flex gap-1 justify-center">
          {regions.map((_, i) => (
            <div
              key={i}
              className={`h-0.5 rounded-full transition-all duration-500 ${i === currentIndex ? 'w-3 bg-indigo-500' : 'w-0.5 bg-white/20'}`}
            />
          ))}
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
