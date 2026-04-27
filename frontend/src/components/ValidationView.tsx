'use client';

import { useState, useEffect } from 'react';

export default function ValidationView() {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [scope, setScope] = useState({ level: 'national', region: '', district: '' });
  const [optimizing, setOptimizing] = useState(false);
  const [optMessage, setOptMessage] = useState('');
  
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002/api';

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
    fetchReport();
  }, [scope.region, scope.district]);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('date', '2024-04-10');
      if (scope.region) params.append('region', scope.region);
      if (scope.district) params.append('district', scope.district);
      
      const res = await fetch(`${apiUrl}/validate?${params.toString()}`);
      const data = await res.json();
      setReport(data);
    } catch (err) {
      console.error('Validation fetch failed:', err);
      setReport({ status: 'error' });
    }
    setLoading(false);
  };

  const handleOptimize = async () => {
    setOptimizing(true);
    try {
      const params = new URLSearchParams();
      if (scope.region) params.append('region', scope.region);
      if (scope.district) params.append('district', scope.district);

      const res = await fetch(`${apiUrl}/optimize?${params.toString()}`, { method: 'POST' });
      const data = await res.json();
      setOptMessage(data.message || '최적화가 완료되었습니다.');
    } catch (err) {
      setOptMessage('최적화 중 오류가 발생했습니다.');
    }
    setOptimizing(false);
    setTimeout(() => setOptMessage(''), 3000);
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Scope Selection for Validation */}
      <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6">
        <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">검증 데이터 범위 설정</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="flex bg-slate-900 p-1 rounded-xl w-fit h-fit border border-slate-700">
            {[
              { id: 'national', label: '전국' },
              { id: 'metropolitan', label: '광역' },
              { id: 'district', label: '기초(지역구)' }
            ].map((lvl) => (
              <button
                key={lvl.id}
                onClick={() => setScope({ ...scope, level: lvl.id as any, region: lvl.id === 'national' ? '' : scope.region, district: '' })}
                className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${
                  scope.level === lvl.id ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'
                }`}
              >
                {lvl.label}
              </button>
            ))}
          </div>

          <div className="flex gap-4">
            {scope.level !== 'national' && (
              <select 
                value={scope.region}
                onChange={(e) => setScope({...scope, region: e.target.value, district: ''})}
                className="bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm text-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none flex-1"
              >
                <option value="">광역 선택</option>
                {Object.keys(LOCATION_MAP).map(reg => (
                  <option key={reg} value={reg}>{reg}</option>
                ))}
              </select>
            )}
            {scope.level === 'district' && scope.region && (
              <select 
                value={scope.district}
                onChange={(e) => setScope({...scope, district: e.target.value})}
                className="bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm text-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none flex-1"
              >
                <option value="">기초/지역구 선택</option>
                {LOCATION_MAP[scope.region]?.map(dist => (
                  <option key={dist} value={dist}>{dist}</option>
                ))}
              </select>
            )}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="animate-pulse p-12 text-center text-slate-500">검증 데이터 분석 중...</div>
      ) : !report || report.status === 'error' ? (
        <div className="p-12 text-center text-slate-500 bg-slate-800/30 border border-slate-700 rounded-2xl">
          선택한 범위({scope.region || '전국'} {scope.district})에 대한 검증 데이터(실제 결과)가 없습니다.
        </div>
      ) : (
        <>
          {/* Overview Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6">
              <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-widest mb-2">전체 평균 절대 오차 (MAE)</h4>
              <div className="text-4xl font-bold">±{report.overall_mae.toFixed(2)}%</div>
              <p className="text-xs text-slate-400 mt-2">{report.total_polls_analyzed}개의 여론조사 분석 결과</p>
            </div>
            {Object.entries(report.method_analysis).map(([method, error]: any) => (
              <div key={method} className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6">
                <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-widest mb-2">{method} 정확도</h4>
                <div className="text-4xl font-bold">±{error.toFixed(2)}%</div>
                <p className="text-xs text-slate-400 mt-2">평균 오차율</p>
              </div>
            ))}
          </div>

          {/* Agency Bias Table */}
          <div className="bg-slate-800 border border-slate-700 rounded-2xl overflow-hidden">
            <div className="p-6 border-b border-slate-700 flex justify-between items-center">
              <div>
                <h3 className="font-semibold text-lg">조사 기관별 편향성 (Bias) 분석</h3>
                <span className="text-xs text-slate-500">*수치가 0에 가까울수록 실제 결과와 일치</span>
              </div>
              <div className="flex items-center gap-3">
                {optMessage && <span className="text-xs text-indigo-400 animate-bounce">{optMessage}</span>}
                <button 
                  onClick={handleOptimize}
                  disabled={optimizing}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg text-sm font-bold transition-all disabled:opacity-50"
                >
                  {optimizing ? '최적화 중...' : '분석 모델 최적화 (Bias 반영)'}
                </button>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-900/50 text-slate-400 uppercase text-[10px] tracking-wider">
                  <tr>
                    <th className="px-6 py-4">조사 기관</th>
                    <th className="px-6 py-4">평균 오차</th>
                    {report.agency_analysis.length > 0 && Object.keys(report.agency_analysis[0].bias_by_target).map(target => (
                      <th key={target} className="px-6 py-4">{target} 편향</th>
                    ))}
                    <th className="px-6 py-4">조사 건수</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700">
                  {report.agency_analysis.map((agency: any) => (
                    <tr key={agency.agency} className="hover:bg-slate-700/30 transition-colors">
                      <td className="px-6 py-4 font-medium">{agency.agency}</td>
                      <td className="px-6 py-4 text-indigo-400 font-bold">±{agency.avg_error.toFixed(2)}%</td>
                      {Object.keys(agency.bias_by_target).map(target => {
                        const val = agency.bias_by_target[target];
                        return (
                          <td key={target} className={`px-6 py-4 ${val > 0 ? 'text-rose-400' : val < 0 ? 'text-blue-400' : 'text-slate-400'}`}>
                            {val > 0 ? '+' : ''}{val.toFixed(2)}%
                          </td>
                        );
                      })}
                      <td className="px-6 py-4 text-slate-500">{agency.poll_count}건</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
