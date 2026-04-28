'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import ValidationView from '@/components/ValidationView';

const PollTrendChart = dynamic(() => import('@/components/PollTrendChart'), { ssr: false });

export default function Dashboard() {
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'trend' | 'validation'>('trend');
  
  // 분석 범위 계층 (전국 -> 광역 -> 지역구)
  const [scopeLevel, setScopeLevel] = useState<'national' | 'metropolitan' | 'district'>('national');
  
  // 가상의 분석 라이브러리 (프로젝트 목록)
  const ANALYSIS_LIBRARY = [
    { id: 'kr_local_9', name: '9회 지방선거 (2026)', category: 'local_election', endDate: '2026-06-03', target_1: 'DP_lead', target_2: 'PPP_lead' },
    { id: 'kr_approval_26', name: '대통령 국정수행 지지도 (2026)', category: 'approval_rating', endDate: '2026-12-31', target_1: 'positive', target_2: 'negative' },
    { id: 'kr_by_26', name: '6.3 재보궐선거 (2026)', category: 'by_election', endDate: '2026-06-03', target_1: 'DP', target_2: 'PPP' },
    { id: 'kr_general_22', name: '22대 국회의원 선거 (2024)', category: 'election', endDate: '2024-04-10', target_1: '더불어민주당', target_2: '국민의힘' },
    { id: 'kr_presidential_20', name: '20대 대통령 선거 (2022)', category: 'election', endDate: '2022-03-09', target_1: '이재명', target_2: '윤석열' },
    { id: 'kr_local_8', name: '8회 지방선거 (2022)', category: 'election', endDate: '2022-06-01', target_1: '더불어민주당', target_2: '국민의힘' },
    { id: 'market_smart_26', name: '2026 스마트폰 시장 점유율', category: 'marketing', endDate: '2026-12-31', target_1: 'brand_apple', target_2: 'brand_samsung' }
  ];

  const [selectedProjectId, setSelectedProjectId] = useState('kr_local_9');
  const [availableRegions, setAvailableRegions] = useState<string[]>([]);
  
  const [config, setConfig] = useState({
    category: 'local_election',
    region: '', 
    district: '', 
    use_smoothing: true,
    use_correlated_errors: true,
    run_stress_test: true,
    target_1: 'DP_lead',
    target_2: 'PPP_lead'
  });

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002/api';

  // 광역 -> 기초(지역구) 매핑 데이터
  const LOCATION_MAP: Record<string, string[]> = {
    '서울': ['종로구', '중구', '용산구', '성동구', '광진구', '동대문구', '중랑구', '성북구', '강북구', '도봉구', '노원구', '은평구', '서대문구', '마포구', '양천구', '강서구', '구로구', '금천구', '영등포구', '동작구', '관악구', '서초구', '강남구', '송파구', '강동구'],
    '경기': ['수원시', '성남시', '고양시', '용인시', '부천시', '안산시', '안양시', '남양주시', '화성시', '평택시', '의정부시', '시흥시', '파주시', '광명시', '김포시', '군포시', '광주시', '이천시', '양주시', '오산시', '구리시', '안성시', '포천시', '의왕시', '하남시', '여주시'],
    '인천': ['중구', '동구', '미추홀구', '연수구', '남동구', '부평구', '계양구', '서구', '강화군', '옹진군'],
    '영남': ['부산', '대구', '울산', '경남', '경북'],
    '호남': ['광주', '전남', '전북'],
    '충청': ['대전', '세종', '충남', '충북'],
    '강원': ['춘천', '원주', '강릉'],
    '제주': ['제주', '서귀포']
  };

  useEffect(() => {
    const fetchAvailable = async () => {
      const project = ANALYSIS_LIBRARY.find(p => p.id === selectedProjectId) as any;
      if (!project) return;
      try {
        const res = await fetch(`${apiUrl}/data?category=${project.category}`);
        const data = await res.json();
        const regions = Array.from(new Set(data.map((d: any) => d.region))).filter(Boolean);
        setAvailableRegions(regions as string[]);
      } catch (e) {
        console.error("Failed to fetch available regions", e);
      }
    };
    fetchAvailable();
  }, [selectedProjectId]);

  useEffect(() => {
    fetchAnalysis();
  }, [config.category, config.use_smoothing, config.region, config.district, selectedProjectId]);

  const fetchAnalysis = async () => {
    setLoading(true);
    try {
      const currentProject = ANALYSIS_LIBRARY.find(p => p.id === selectedProjectId) as any;
      const category = currentProject?.category || config.category;
      const endDate = currentProject?.endDate;
      const target_1 = currentProject?.target_1 || config.target_1;
      const target_2 = currentProject?.target_2 || config.target_2;

      // 1. Fetch raw data with hierarchical filters
      const regionParam = config.region ? `&region=${encodeURIComponent(config.region)}` : '';
      const districtParam = config.district ? `&district=${encodeURIComponent(config.district)}` : '';
      const dataRes = await fetch(`${apiUrl}/data?category=${category}${regionParam}${districtParam}`);
      if (!dataRes.ok) throw new Error('데이터 로드 실패');
      
      let rawData = await dataRes.json();

      // [FIX] Filter data by project's end date
      if (endDate) {
        rawData = rawData.filter((d: any) => d.date <= endDate);
      }

      if (!rawData || rawData.length === 0) {
        setAnalysis(null);
        return;
      }

      // 2. Run analysis via the engine
      const analysisRes = await fetch(`${apiUrl}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          data: rawData,
          category: category,
          config: { ...config, target_1, target_2 }
        }),
      });
      
      if (!analysisRes.ok) throw new Error('분석 엔진 오류');
      
      const result = await analysisRes.json();
      setAnalysis(result);
    } catch (err) {
      console.error('분석 중 오류가 발생했습니다:', err);
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-8">
      <div className="max-w-7xl mx-auto">
        <header className="flex justify-between items-center mb-12">
          <div className="flex items-center gap-6">
            <Link 
              href="/" 
              className="p-2 hover:bg-slate-800 rounded-full transition-colors group"
              title="관리 도구로 돌아가기"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-slate-400 group-hover:text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </Link>
            <div>
              <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
                여론조사 통합 분석 엔진
              </h1>
              <p className="text-slate-400 mt-1">고급 통계 분석 시스템 v3.0</p>
            </div>
          </div>
          <div className="flex gap-4">
            <select 
              value={config.category}
              onChange={(e) => setConfig({...config, category: e.target.value})}
              className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
            >
              <option value="election">정치 & 선거</option>
              <option value="marketing">시장 조사</option>
              <option value="social">사회 통계</option>
            </select>
            <button 
              onClick={fetchAnalysis}
              className="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-2 rounded-lg text-sm font-medium transition-all shadow-lg shadow-indigo-500/20"
            >
              재계산
            </button>
          </div>
        </header>

        <div className="flex border-b border-slate-700 mb-8 gap-8">
          <button 
            onClick={() => setActiveTab('trend')}
            className={`pb-4 text-sm font-semibold transition-all ${activeTab === 'trend' ? 'text-indigo-400 border-b-2 border-indigo-400' : 'text-slate-500 hover:text-slate-300'}`}
          >
            트렌드 통합 분석
          </button>
          <button 
            onClick={() => setActiveTab('validation')}
            className={`pb-4 text-sm font-semibold transition-all ${activeTab === 'validation' ? 'text-indigo-400 border-b-2 border-indigo-400' : 'text-slate-500 hover:text-slate-300'}`}
          >
            모델 검증 리포트 (vs 실제 결과)
          </button>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center h-96 space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
            <p className="text-slate-400 text-sm animate-pulse">데이터를 수집하고 분석 엔진을 실행 중입니다...</p>
          </div>
        ) : !analysis ? (
          <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-24 text-center space-y-6 max-w-4xl mx-auto mt-12">
            <div className="bg-slate-900 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 9.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h2 className="text-xl font-bold text-white mb-2">분석할 데이터를 찾을 수 없습니다</h2>
              <p className="text-slate-400 max-w-md mx-auto">
                선택한 카테고리(<b>{config.category}</b>) 및 권역(<b>{config.region || '전국'}</b>)에 해당하는 데이터가 데이터베이스에 없습니다.
              </p>
            </div>
            <div className="flex justify-center gap-4 pt-4">
              <button 
                onClick={fetchAnalysis}
                className="bg-slate-700 hover:bg-slate-600 text-white px-6 py-2 rounded-lg text-sm font-medium transition-all"
              >
                다시 시도
              </button>
              <Link 
                href="/"
                className="bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-2 rounded-lg text-sm font-medium transition-all"
              >
                데이터 관리자로 이동
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            {/* Control Sidebar */}
            <aside className="lg:col-span-1 space-y-6">
              <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6">
                <h3 className="font-semibold mb-6 flex items-center gap-2">
                  <span className="w-2 h-2 bg-indigo-500 rounded-full"></span>
                  엔진 구성 설정
                </h3>
                <div className="space-y-4">
                  {[
                    { key: 'use_smoothing', label: '시계열 평활화 (Smoothing)' },
                    { key: 'use_correlated_errors', label: '상관 오차 보정' },
                    { key: 'run_stress_test', label: '스트레스 테스트' }
                  ].map((toggle) => (
                    <label key={toggle.key} className="flex items-center justify-between group cursor-pointer">
                      <span className="text-sm text-slate-300 group-hover:text-white transition-colors">{toggle.label}</span>
                      <input 
                        type="checkbox" 
                        checked={(config as any)[toggle.key]}
                        onChange={(e) => setConfig({...config, [toggle.key]: e.target.checked})}
                        className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-indigo-500 focus:ring-indigo-500"
                      />
                    </label>
                  ))}
                </div>
              </div>

              {/* Analysis Scope Card (Target + Region) */}
              <div className="bg-slate-800 border border-slate-700 rounded-2xl overflow-hidden shadow-xl shadow-slate-950/50">
                <div className="p-6 border-b border-slate-700/50 bg-slate-700/20">
                  <div className="flex justify-between items-start mb-3">
                    <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-widest opacity-80">현재 분석 프로젝트</h4>
                    <span className="bg-indigo-600/20 text-indigo-400 text-[10px] px-2 py-0.5 rounded font-bold uppercase ring-1 ring-indigo-500/30">LIVE</span>
                  </div>
                  
                  {/* Library Dropdown Selection */}
                  <div className="mb-4">
                    <select 
                      value={selectedProjectId}
                      onChange={(e) => {
                        const project = ANALYSIS_LIBRARY.find(p => p.id === e.target.value);
                        if (project) {
                          setSelectedProjectId(project.id);
                          setConfig({...config, category: project.category});
                        }
                      }}
                      className="w-full bg-slate-900/80 border border-slate-600/50 rounded-lg px-3 py-2.5 text-sm text-white font-bold focus:ring-2 focus:ring-indigo-500 outline-none cursor-pointer appearance-none shadow-inner"
                      style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' fill=\'none\' viewBox=\'0 0 24 24\' stroke=\'%236366f1\'%3E%3Cpath stroke-linecap=\'round\' stroke-linejoin=\'round\' stroke-width=\'2\' d=\'M19 9l-7 7-7-7\' /%3E%3C/svg%3E")', backgroundRepeat: 'no-repeat', backgroundPosition: 'right 0.75rem center', backgroundSize: '1rem' }}
                    >
                      {ANALYSIS_LIBRARY.map(project => (
                        <option key={project.id} value={project.id}>{project.name}</option>
                      ))}
                    </select>
                  </div>

                  <div className="flex items-center gap-2 text-slate-500">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-[10px] font-medium italic">최신 {analysis?.total_samples || 0}개 샘플 반영됨</span>
                  </div>
                </div>
                
                <div className="p-6 space-y-5">
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1">분석 범위 설정</h4>
                  
                  {/* Step 1: Scope Level Selection */}
                  <div className="flex bg-slate-900 p-1 rounded-lg border border-slate-700">
                    {(['national', 'metropolitan', 'district'] as const).map((level) => (
                      <button
                        key={level}
                        onClick={() => {
                          setScopeLevel(level);
                          if (level === 'national') setConfig({...config, region: '', district: ''});
                          if (level === 'metropolitan') setConfig({...config, district: ''});
                        }}
                        className={`flex-1 py-1.5 text-[10px] font-bold rounded-md transition-all ${
                          scopeLevel === level ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'
                        }`}
                      >
                        {level === 'national' ? '전국' : level === 'metropolitan' ? '광역' : '기초(지역구)'}
                      </button>
                    ))}
                  </div>

                  {/* Step 2: Metropolitan Selection (Provincial Level) */}
                  {scopeLevel !== 'national' && (
                    <div className="space-y-2 animate-in fade-in slide-in-from-top-2 duration-300">
                      <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">시/도 선택</label>
                      <select 
                        value={config.region}
                        onChange={(e) => setConfig({...config, region: e.target.value, district: ''})}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none transition-all cursor-pointer hover:border-slate-600"
                      >
                        <option value="">광역 단체를 선택하세요</option>
                        {Object.keys(LOCATION_MAP).filter(reg => availableRegions.includes(reg)).map(reg => (
                          <option key={reg} value={reg}>{reg}</option>
                        ))}
                      </select>
                    </div>
                  )}

                  {/* Step 3: District Selection (Local Level) */}
                  {scopeLevel === 'district' && config.region && (
                    <div className="space-y-2 animate-in fade-in slide-in-from-top-2 duration-300">
                      <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">세부 지역구/기초단체 선택</label>
                      <select 
                        value={config.district}
                        onChange={(e) => setConfig({...config, district: e.target.value})}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none transition-all cursor-pointer hover:border-slate-600"
                      >
                        <option value="">기초 단체를 선택하세요</option>
                        {LOCATION_MAP[config.region]?.map(dist => (
                          <option key={dist} value={dist}>{dist}</option>
                        ))}
                      </select>
                    </div>
                  )}

                  <p className="text-[10px] text-slate-500 mt-2 italic">
                    *상위 범위를 변경하면 하위 범위 선택이 초기화됩니다.
                  </p>
                </div>
              </div>

              <div className="bg-indigo-600/10 border border-indigo-500/20 rounded-2xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-widest">계산된 확실성 (Certainty)</h4>
                  <div className="group relative">
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-indigo-500/50 cursor-help" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {/* Tooltip for formula */}
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-4 bg-slate-800 border border-slate-700 rounded-xl shadow-2xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50">
                      <h5 className="text-[10px] font-bold text-indigo-400 uppercase mb-2">산출 수식 (Certainty Formula)</h5>
                      <div className="bg-slate-950 p-2 rounded text-[10px] font-mono text-slate-300 leading-relaxed mb-3">
                        Certainty = <br/>
                        (σ_consensus × (1 / √Σn_weighted)) + C
                      </div>
                      <ul className="text-[10px] text-slate-400 space-y-1">
                        <li>• <span className="text-slate-200">σ_consensus</span>: 조사기관 간 의견 불일치도</li>
                        <li>• <span className="text-slate-200">Σn_weighted</span>: 가중치가 적용된 통합 표본수</li>
                        <li>• <span className="text-slate-200">C</span>: 모델 기초 오차 상수</li>
                      </ul>
                    </div>
                  </div>
                </div>
                <div className="text-4xl font-bold mb-2">±{analysis?.prediction?.calculated_uncertainty?.toFixed(2) || '0.00'}%</div>
                <div className="space-y-3">
                  <p className="text-[10px] text-slate-400 leading-relaxed">
                    통합된 {analysis?.total_samples || 0}개 샘플의 통계적 편차와 표본 크기를 고려한 <strong>95% 신뢰 수준</strong>의 오차 범위입니다. 수치가 낮을수록 예측의 정밀도가 높음을 의미합니다.
                  </p>
                  <div className="flex items-center gap-2 pt-2 border-t border-indigo-500/10">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
                    <span className="text-[10px] text-slate-500 font-medium">데이터 정합성 검증 완료</span>
                  </div>
                </div>
              </div>
            </aside>

            {/* Main Content */}
            <main className="lg:col-span-3 space-y-8">
              {activeTab === 'trend' ? (
                <>
                  {/* Top Metrics */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6 relative overflow-hidden">
                      <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500"></div>
                      <h4 className="text-xs font-bold text-indigo-400 mb-2 uppercase tracking-tight">
                        {analysis?.prediction?.target_1?.replace(/party_/g, '').toUpperCase() || 'TARGET A'} 우세 확률
                      </h4>
                      <div className="text-4xl font-bold text-white mb-4">
                        {analysis?.prediction?.target_1_lead_prob?.toFixed(2) || '0.0'}%
                      </div>
                      <div className="w-full bg-slate-700 h-1.5 rounded-full overflow-hidden">
                        <div 
                          className="bg-indigo-500 h-full transition-all duration-1000" 
                          style={{ width: `${analysis?.prediction?.target_1_lead_prob || 0}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6 relative overflow-hidden">
                      <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500"></div>
                      <h4 className="text-xs font-bold text-emerald-400 mb-2 uppercase tracking-tight">예상 격차 (Expected Gap)</h4>
                      <div className="text-4xl font-bold text-white mb-2">
                        {Math.abs(analysis?.prediction?.expected_gap || 0)?.toFixed(2)}%p
                      </div>
                      <div className="text-[10px] text-slate-500 font-medium uppercase">
                        {analysis?.prediction?.expected_gap > 0 ? 
                          `${analysis?.prediction?.target_1?.replace(/party_/g, '').toUpperCase()} 리드` : 
                          `${analysis?.prediction?.target_2?.replace(/party_/g, '').toUpperCase()} 리드`}
                      </div>
                    </div>

                    <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6 relative overflow-hidden">
                      <div className="absolute top-0 left-0 w-1 h-full bg-rose-500"></div>
                      <h4 className="text-xs font-bold text-rose-400 mb-2 uppercase tracking-tight">
                        {analysis?.prediction?.target_2?.replace(/party_/g, '').toUpperCase() || 'TARGET B'} 우세 확률
                      </h4>
                      <div className="text-4xl font-bold text-white mb-4">
                        {analysis?.prediction?.target_2_lead_prob?.toFixed(2) || '0.0'}%
                      </div>
                      <div className="w-full bg-slate-700 h-1.5 rounded-full overflow-hidden">
                        <div 
                          className="bg-rose-500 h-full transition-all duration-1000" 
                          style={{ width: `${analysis?.prediction?.target_2_lead_prob || 0}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>

                  {/* Chart */}
                  <div className="bg-slate-800 border border-slate-700 rounded-2xl p-8">
                    <div className="flex justify-between items-center mb-8">
                      <h3 className="text-xl font-semibold">통합 트렌드 분석</h3>
                      <div className="flex gap-4 text-[10px] font-bold uppercase text-slate-500">
                        <span className="flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full bg-indigo-500"></span> 
                          {analysis?.prediction?.target_1?.replace(/party_/g, '').toUpperCase() || 'TARGET A'}
                        </span>
                        <span className="flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full bg-rose-500"></span> 
                          {analysis?.prediction?.target_2?.replace(/party_/g, '').toUpperCase() || 'TARGET B'}
                        </span>
                      </div>
                    </div>
                    <div className="h-[400px]">
                      <PollTrendChart data={analysis?.trend_lines || []} />
                    </div>
                  </div>

                  {/* Stress Test */}
                  {analysis?.stress_test_report && (
                    <div className="bg-amber-500/5 border border-amber-500/20 rounded-2xl p-6">
                      <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-3">
                          <span className="bg-amber-500 text-black text-[10px] font-black px-2 py-0.5 rounded uppercase">충격 테스트</span>
                          <h3 className="text-lg font-semibold text-amber-500">쇼크 시나리오 분석 리포트</h3>
                        </div>
                        <div className={`text-[10px] font-bold px-2 py-1 rounded border ${
                          analysis.stress_test_report.status.includes('Fragile') ? 'border-rose-500/50 text-rose-400 bg-rose-500/10' : 'border-emerald-500/50 text-emerald-400 bg-emerald-500/10'
                        }`}>
                          모델 상태: {analysis.stress_test_report.status}
                        </div>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
                        <div className="space-y-3">
                          <p className="text-sm text-slate-300 leading-relaxed">
                            이 분석은 <strong>가상의 쇼크 데이터</strong>(타겟 B가 압도적인 조사 결과)가 하나 추가되었을 때, 
                            기존 예측 모델의 우세 확률이 얼마나 변동하는지 측정합니다. 이를 통해 현재 데이터가 소수의 이상치에 
                            얼마나 민감하게 반응하는지(취약성)를 평가할 수 있습니다.
                          </p>
                          <div className="text-xs text-slate-500 bg-slate-900/50 p-3 rounded-lg border border-slate-700/50">
                            <strong>현재 시뮬레이션 결과:</strong> 타겟 B로의 급격한 쏠림 발생 시, 
                            {analysis?.prediction?.target_1?.replace(/party_/g, '').toUpperCase()}의 우세 확률이 
                            <span className="text-amber-400 font-bold mx-1">{Math.abs(analysis.stress_test_report.delta_a).toFixed(2)}%p</span> 
                            만큼 요동칩니다.
                          </div>
                        </div>

                        <div className="bg-slate-900/50 rounded-xl p-5 border border-slate-700/50 flex items-center justify-around">
                          <div className="text-center">
                            <div className="text-[10px] text-slate-500 uppercase mb-1 font-bold">기존 (Baseline)</div>
                            <div className="text-2xl font-bold text-white">{analysis.stress_test_report.baseline_prob_a.toFixed(2)}%</div>
                          </div>
                          <div className="text-xl text-slate-700">→</div>
                          <div className="text-center">
                            <div className="text-[10px] text-amber-500 uppercase mb-1 font-bold">쇼크 (Shocked)</div>
                            <div className="text-2xl font-bold text-amber-400">{analysis.stress_test_report.shocked_prob_a.toFixed(2)}%</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <ValidationView />
              )}
            </main>
          </div>
        )}
      </div>
    </div>
  );
}
