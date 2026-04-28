'use client';

import MiniDashboard from '@/components/MiniDashboard';

export default function MiniPage() {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-8 space-y-12">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold text-white tracking-tight">Mini Dashboard Preview</h1>
        <p className="text-slate-400 max-w-md mx-auto">
          dailyprizm.com의 뉴스 기사 하단이나 사이드바에 삽입될 미니 대시보드 컴포넌트입니다. 
          전국 종합 데이터와 광역별 데이터를 5초 간격으로 슬라이딩하며 보여줍니다.
        </p>
      </div>
      
      <div className="flex flex-wrap gap-12 justify-center items-center">
        {/* Case 1: 2026 Local Election */}
        <div className="space-y-4">
          <h2 className="text-xs font-bold text-indigo-400 uppercase tracking-widest text-center">9회 지방선거 (자동 슬라이딩)</h2>
          <MiniDashboard category="local_election" />
        </div>

        {/* Case 2: Approval Rating */}
        <div className="space-y-4">
          <h2 className="text-xs font-bold text-emerald-400 uppercase tracking-widest text-center">대통령 국정수행 지지도</h2>
          <MiniDashboard category="approval_rating" regions={['National']} />
        </div>
      </div>

      <div className="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl max-w-2xl w-full">
        <h3 className="text-sm font-bold text-white mb-4">Embed Code (Example)</h3>
        <pre className="bg-black/50 p-4 rounded-xl text-[10px] text-indigo-300 overflow-x-auto font-mono leading-relaxed">
{`<iframe
  src="https://poll.dailyprizm.com/mini"
  width="320"
  height="420"
  frameBorder="0"
  scrolling="no"
></iframe>`}
        </pre>
      </div>
    </div>
  );
}
