'use client';

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import zoomPlugin from 'chartjs-plugin-zoom';
import { useRef, useState } from 'react';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  zoomPlugin
);

interface ChartProps {
  data: any;
  title?: string;
}

export default function PollTrendChart({ data, title }: ChartProps) {
  const [hoverX, setHoverX] = useState<number | null>(null);
  
  // Dynamically detect keys from the data object
  const keys = data ? Object.keys(data) : [];
  
  if (keys.length === 0 || !data[keys[0]] || data[keys[0]].length === 0) {
    return <div className="p-12 text-center text-slate-400">트렌드 분석을 위한 데이터가 부족합니다</div>;
  }

  const labels = data[keys[0]].map((p: any) => p.date);
  
  const colors = [
    { border: 'rgb(79, 70, 229)', bg: 'rgba(79, 70, 229, 0.1)' },
    { border: 'rgb(244, 63, 94)', bg: 'rgba(244, 63, 94, 0.1)' },
    { border: 'rgb(16, 185, 129)', bg: 'rgba(16, 185, 129, 0.1)' },
    { border: 'rgb(245, 158, 11)', bg: 'rgba(245, 158, 11, 0.1)' },
  ];

  const datasets = keys.map((key, index) => ({
    label: key.replace(/_/g, ' ').toUpperCase(),
    data: data[key].map((p: any) => p.smoothed_value),
    borderColor: colors[index % colors.length].border,
    backgroundColor: colors[index % colors.length].bg,
    tension: 0.4,
    fill: true,
  }));
  
  const chartData = {
    labels,
    datasets,
  };

  // Custom Plugin for Hierarchical Colored Labels (Row-based)
  const hierarchicalLabelsPlugin = {
    id: 'hierarchicalLabels',
    afterDraw: (chart: any) => {
      const { ctx, scales: { x } } = chart;
      if (!x) return;

      const ticks = x.ticks;
      const area = chart.chartArea;

      ctx.save();
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';

      ticks.forEach((tick: any, index: number) => {
        const xPos = x.getPixelForTick(index);
        const label = x.getLabelForValue(tick.value);
        const date = new Date(label);
        if (isNaN(date.getTime())) return;

        const prevTick = index > 0 ? ticks[index - 1] : null;
        const prevDate = prevTick ? new Date(x.getLabelForValue(prevTick.value)) : null;

        const year = date.getFullYear().toString();
        const month = (date.getMonth() + 1).toString().padStart(2, '0');
        const day = date.getDate().toString().padStart(2, '0');

        const isMouseNear = hoverX !== null && Math.abs(xPos - hoverX) < 20;
        const fontSize = isMouseNear ? 16 : 12;
        const rowHeight = fontSize + 6;
        const startY = area.bottom + 8;

        ctx.font = `${isMouseNear ? 'bold' : 'normal'} ${fontSize}px sans-serif`;

        // Row 1: Year (Orange) - Only show when it changes
        if (!prevDate || date.getFullYear() !== prevDate.getFullYear()) {
          ctx.fillStyle = '#f97316';
          ctx.fillText(year, xPos, startY);
        }

        // Row 2: Month (Yellow) - Only show when it changes
        if (!prevDate || date.getMonth() !== prevDate.getMonth()) {
          ctx.fillStyle = '#eab308';
          ctx.fillText(month, xPos, startY + rowHeight);
        }

        // Row 3: Day (Red) - Always show
        ctx.fillStyle = '#ef4444';
        ctx.fillText(day, xPos, startY + rowHeight * 2);
      });
      ctx.restore();
    }
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    onHover: (event: any) => {
      const { x, y } = event;
      // Trigger hover effect only when mouse is near the bottom axis area
      if (chartRef.current && y > chartRef.current.chartArea.bottom - 20) {
        setHoverX(x);
      } else {
        setHoverX(null);
      }
    },
    plugins: {
      legend: {
        position: 'top' as const,
        labels: { color: '#94a3b8', font: { size: 12 } }
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleColor: '#94a3b8',
        bodyColor: '#f1f5f9',
        borderColor: 'rgba(255,255,255,0.1)',
        borderWidth: 1,
        padding: 10,
        callbacks: {
          title: (context: any) => context[0].label,
          afterBody: (context: any) => {
            if (context.length >= 2) {
              const val1 = context[0].raw;
              const val2 = context[1].raw;
              const diff = (val1 - val2).toFixed(2);
              const absDiff = Math.abs(parseFloat(diff));
              const lead = val1 > val2 ? context[0].dataset.label : context[1].dataset.label;
              return `\n격차: ${absDiff}%p (${lead} 우세)`;
            }
            return '';
          }
        }
      },
      zoom: {
        zoom: {
          wheel: { enabled: true, speed: 0.1 },
          pinch: { enabled: true },
          drag: {
            enabled: true,
            backgroundColor: 'rgba(79, 70, 229, 0.1)',
            borderColor: 'rgb(79, 70, 229)',
            borderWidth: 1,
          },
          mode: 'x' as const,
        },
        pan: { enabled: true, mode: 'x' as const, threshold: 10 }
      }
    },
    scales: {
      y: {
        grid: { color: 'rgba(255,255,255,0.05)' },
        ticks: { color: '#64748b' }
      },
      x: {
        grid: { display: false },
        ticks: { display: false } // Disable default ticks to use our plugin
      }
    },
    layout: {
      padding: {
        bottom: 45 // Reserve space for 3 rows of labels
      }
    }
  };

  const chartRef = useRef<any>(null);

  const resetZoom = () => chartRef.current?.resetZoom();
  const zoomIn = () => chartRef.current?.zoom(1.2);
  const zoomOut = () => chartRef.current?.zoom(0.8);

  return (
    <div className="relative h-full w-full flex flex-col">
      <div className="flex justify-between items-center mb-2 px-2">
        <div className="text-[10px] text-slate-500 flex items-center gap-3">
          <span className="flex items-center gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5" />
            </svg>
            드래그하여 영역 확대
          </span>
          <span className="flex items-center gap-1">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11.5V14m0-2.5v-6a1.5 1.5 0 113 0m-3 6a1.5 1.5 0 00-3 0v2a7.5 7.5 0 0015 0v-5a1.5 1.5 0 00-3 0m-6-3V11m0-5.5v-1a1.5 1.5 0 013 0v1m0 0V11" />
            </svg>
            휠로 확대/축소
          </span>
        </div>
        <div className="flex gap-1">
          <button onClick={zoomIn} className="bg-slate-800 hover:bg-slate-700 text-slate-300 p-1.5 rounded border border-slate-700 transition-colors" title="확대">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
            </svg>
          </button>
          <button onClick={zoomOut} className="bg-slate-800 hover:bg-slate-700 text-slate-300 p-1.5 rounded border border-slate-700 transition-colors" title="축소">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM13 10H7" />
            </svg>
          </button>
          <button onClick={resetZoom} className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-1 rounded border border-slate-700 text-[10px] font-medium transition-colors ml-1">
            초기화
          </button>
        </div>
      </div>
      <div className="flex-1 min-h-0">
        <Line ref={chartRef} options={options} data={chartData} plugins={[hierarchicalLabelsPlugin]} />
      </div>
    </div>
  );
}
