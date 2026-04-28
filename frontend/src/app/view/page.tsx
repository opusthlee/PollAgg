'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';

const PollTrendChart = dynamic(() => import('@/components/PollTrendChart'), { ssr: false });

export default function DashboardView() {
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002/api';

  useEffect(() => {
    fetchAnalysis();
  }, []);

  const fetchAnalysis = async () => {
    setLoading(true);
    try {
      // Fetch default 2026 local election data
      const dataRes = await fetch(`${apiUrl}/data?category=local_election`);
      const rawData = await dataRes.json();
      
      const res = await fetch(`${apiUrl}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data: rawData,
          category: 'local_election',
          config: {
            use_smoothing: true,
            use_correlated_errors: true,
            run_stress_test: true
          }
        })
      });
      const result = await res.json();
      setAnalysis(result);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center text-white font-bold tracking-widest uppercase">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        <span>분석 엔진 가동 중...</span>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-8 lg:p-12">
      <header className="max-w-7xl mx-auto mb-12 flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-black text-white tracking-tighter mb-2 italic">POLL<span className="text-indigo-500">AGG</span> DASHBOARD</h1>
          <p className="text-slate-500 text-sm font-medium uppercase tracking-[0.3em]">9회 전국 동시 지방선거 실시간 데이터 시각화</p>
        </div>
        <div className="text-right">
          <span className="bg-indigo-600/20 text-indigo-400 text-[10px] px-3 py-1 rounded-full font-bold border border-indigo-500/30 uppercase tracking-widest">Live Analysis</span>
        </div>
      </header>

      <main className="max-w-7xl mx-auto space-y-8">
        {/* Top Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-slate-900/50 backdrop-blur-xl border border-white/5 rounded-[32px] p-8">
            <h4 className="text-xs font-bold text-indigo-400 mb-4 uppercase tracking-widest">{analysis?.prediction?.target_1?.toUpperCase()} 우세 확률</h4>
            <div className="text-6xl font-black text-white mb-6 tracking-tighter">{analysis?.prediction?.target_1_lead_prob?.toFixed(1)}%</div>
            <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
              <div className="bg-indigo-500 h-full transition-all duration-1000" style={{ width: `${analysis?.prediction?.target_1_lead_prob}%` }}></div>
            </div>
          </div>

          <div className="bg-slate-900/50 backdrop-blur-xl border border-white/5 rounded-[32px] p-8 flex flex-col justify-center text-center relative overflow-hidden">
             <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-32 bg-emerald-500/10 blur-3xl rounded-full"></div>
             <h4 className="text-xs font-bold text-emerald-400 mb-2 uppercase tracking-widest">통합 격차 (Gap)</h4>
             <div className="text-6xl font-black text-white tracking-tighter">±{Math.abs(analysis?.prediction?.expected_gap).toFixed(1)}%p</div>
          </div>

          <div className="bg-slate-900/50 backdrop-blur-xl border border-white/5 rounded-[32px] p-8">
            <h4 className="text-xs font-bold text-rose-400 mb-4 uppercase tracking-widest">{analysis?.prediction?.target_2?.toUpperCase()} 우세 확률</h4>
            <div className="text-6xl font-black text-white mb-6 tracking-tighter">{analysis?.prediction?.target_2_lead_prob?.toFixed(1)}%</div>
            <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
              <div className="bg-rose-500 h-full transition-all duration-1000" style={{ width: `${analysis?.prediction?.target_2_lead_prob}%` }}></div>
            </div>
          </div>
        </div>

        {/* Big Trend Chart */}
        <div className="bg-slate-900/50 backdrop-blur-xl border border-white/5 rounded-[40px] p-10">
          <div className="flex justify-between items-center mb-10">
            <h3 className="text-2xl font-bold text-white tracking-tight">지지도 통합 트렌드 (Time-series)</h3>
            <div className="flex gap-6 text-[10px] font-black uppercase text-slate-500">
              <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-indigo-500"></span> {analysis?.prediction?.target_1?.toUpperCase()}</span>
              <span className="flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-rose-500"></span> {analysis?.prediction?.target_2?.toUpperCase()}</span>
            </div>
          </div>
          <div className="h-[500px]">
            <PollTrendChart data={analysis?.trend_lines || []} />
          </div>
        </div>

        {/* Bottom Details */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="bg-slate-900/50 backdrop-blur-xl border border-white/5 rounded-[32px] p-8">
             <h4 className="text-xs font-bold text-slate-500 mb-4 uppercase tracking-widest">통계적 유의성 (Certainty)</h4>
             <div className="text-3xl font-bold text-white mb-2">±{analysis?.prediction?.calculated_uncertainty.toFixed(2)}%</div>
             <p className="text-xs text-slate-500 leading-relaxed">
               전국 {analysis?.total_samples}개 샘플의 가중 평균과 기관별 편차를 고려한 95% 신뢰 수준의 오차 범위입니다. 
               엔진은 결정론적 산출 방식을 사용하여 데이터 무결성을 보장합니다.
             </p>
          </div>
          <div className="bg-amber-500/5 border border-amber-500/20 rounded-[32px] p-8 flex items-center gap-6">
             <div className="w-16 h-16 bg-amber-500/20 rounded-2xl flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
             </div>
             <div>
                <h4 className="text-xs font-bold text-amber-500 mb-1 uppercase tracking-widest">모델 상태 리포트</h4>
                <p className="text-sm text-slate-300 font-medium">현재 분석 엔진은 {analysis?.stress_test_report?.status} 상태입니다.</p>
             </div>
          </div>
        </div>
      </main>

      <footer className="max-w-7xl mx-auto mt-20 pt-8 border-t border-white/5 text-center">
        <p className="text-[10px] text-slate-600 font-bold uppercase tracking-widest">© 2026 PollAgg Statistical Engine. All data provided for simulation purposes.</p>
      </footer>
    </div>
  );
}
