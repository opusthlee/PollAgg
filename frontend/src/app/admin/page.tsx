'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface SurveyData {
  id: number;
  category: string;
  agency: string;
  date: string;
  results: Record<string, number>;
  sample_size: number;
  method: string | null;
  is_manual_override: boolean;
}

export default function Home() {
  const [dataPoints, setDataPoints] = useState<SurveyData[]>([]);
  const [loading, setLoading] = useState(true);
  const [newEntry, setNewEntry] = useState({
    category: 'election',
    agency: '',
    date: new Date().toISOString().split('T')[0],
    results: '{"party_democratic": 40, "party_republican": 40}',
    sample_size: 1000,
    method: 'CATI',
    is_manual_override: true,
  });

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002/api';

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${apiUrl}/data`);
      const data = await res.json();
      setDataPoints(data);
    } catch (err) {
      console.error('Failed to fetch data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await fetch(`${apiUrl}/data`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...newEntry,
          results: JSON.parse(newEntry.results),
        }),
      });
      if (res.ok) {
        fetchData();
        setNewEntry({ ...newEntry, agency: '', results: '{"target_a": 50, "target_b": 50}' });
      }
    } catch (err) {
      alert('Error adding data. Check JSON format.');
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-6xl mx-auto">
        <header className="mb-12 flex justify-between items-end">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="bg-amber-100 text-amber-800 text-xs font-bold px-2.5 py-1 rounded-full uppercase tracking-wider">🔒 ADMIN</span>
              <span className="text-xs text-slate-500">관리자 전용 영역</span>
            </div>
            <h1 className="text-4xl font-bold text-slate-900">PollAgg 관리 제어 센터</h1>
            <p className="text-slate-600">데이터 수집·수식 보정·DB 관리 시스템</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/dashboard"
              className="bg-indigo-600 text-white px-6 py-2.5 rounded-xl font-bold shadow-lg shadow-indigo-200 hover:bg-indigo-700 transition-all"
            >
              공개 대시보드 보기
            </Link>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Data Entry Section */}
          <section className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-6">
              <h2 className="text-xl font-semibold text-slate-800 mb-6">새 데이터 추가</h2>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">도메인 카테고리</label>
                  <select 
                    value={newEntry.category}
                    onChange={(e) => setNewEntry({...newEntry, category: e.target.value})}
                    className="w-full rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                  >
                    <option value="election">정치 & 선거</option>
                    <option value="marketing">시장 조사</option>
                    <option value="social">사회 통계</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">조사 기관 / 출처</label>
                  <input
                    type="text"
                    required
                    placeholder="예: 갤럽, 리얼미터, 미디어토마토"
                    value={newEntry.agency}
                    onChange={(e) => setNewEntry({ ...newEntry, agency: e.target.value })}
                    className="w-full rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">조사 일자</label>
                    <input
                      type="date"
                      required
                      value={newEntry.date}
                      onChange={(e) => setNewEntry({ ...newEntry, date: e.target.value })}
                      className="w-full rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">표본 크기</label>
                    <input
                      type="number"
                      required
                      value={newEntry.sample_size}
                      onChange={(e) => setNewEntry({ ...newEntry, sample_size: parseInt(e.target.value) })}
                      className="w-full rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">측정 데이터 (JSON)</label>
                  <textarea
                    required
                    rows={3}
                    value={newEntry.results}
                    onChange={(e) => setNewEntry({ ...newEntry, results: e.target.value })}
                    className="w-full rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border font-mono"
                  />
                  <p className="text-[10px] text-slate-400 mt-1">예시: {"{\"더불어민주당\": 45, \"국민의힘\": 40}"}</p>
                </div>
                <button
                  type="submit"
                  className="w-full bg-slate-900 text-white py-3 px-4 rounded-xl hover:bg-black transition-colors font-bold shadow-md"
                >
                  저장소에 추가
                </button>
              </form>
            </div>
          </section>

          {/* Table Section */}
          <section className="lg:col-span-2">
            <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
              <div className="p-6 border-b border-slate-200 flex justify-between items-center">
                <h2 className="text-xl font-semibold text-slate-800">마스터 데이터 저장소</h2>
                <button 
                  onClick={fetchData}
                  className="text-indigo-600 hover:text-indigo-700 text-sm font-medium"
                >
                  새로고침
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">카테고리</th>
                      <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">조사기관</th>
                      <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">일자</th>
                      <th className="px-6 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">결과</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-slate-200">
                    {loading ? (
                      <tr>
                        <td colSpan={4} className="px-6 py-12 text-center text-slate-500 italic">데이터베이스 연결 중...</td>
                      </tr>
                    ) : dataPoints.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="px-6 py-12 text-center text-slate-500">저장소가 비어 있습니다.</td>
                      </tr>
                    ) : (
                      dataPoints.map((point) => (
                        <tr key={point.id} className="hover:bg-slate-50 transition-colors">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="bg-slate-100 text-slate-600 text-[10px] font-bold px-2 py-1 rounded uppercase tracking-tighter">
                              {point.category}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap font-medium text-slate-900">{point.agency}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-slate-600 text-sm">{point.date}</td>
                          <td className="px-6 py-4 text-slate-600 text-sm font-mono truncate max-w-[200px]">
                            {JSON.stringify(point.results)}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}
