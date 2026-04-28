'use client';

import MiniDashboard from '@/components/MiniDashboard';
import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';

function WidgetContent() {
  const searchParams = useSearchParams();
  const category = searchParams.get('category') || 'local_election';
  
  return (
    <div className="flex items-center justify-center min-h-screen bg-transparent p-4 overflow-hidden">
      <MiniDashboard category={category} />
    </div>
  );
}

export default function WidgetPage() {
  return (
    <Suspense fallback={null}>
      <WidgetContent />
    </Suspense>
  );
}
