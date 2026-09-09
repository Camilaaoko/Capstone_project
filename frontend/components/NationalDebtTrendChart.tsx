'use client';

import React, { useEffect, useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, AlertCircle } from 'lucide-react';
import { NationalDebtTrendItem } from '@/lib/api';

interface NationalDebtTrendChartProps {
  data: NationalDebtTrendItem[];
  loading?: boolean;
}

export default function NationalDebtTrendChart({
  data,
  loading = false,
}: NationalDebtTrendChartProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Format KES billions for axis
  const formatBillions = (val: number) => {
    return 'KES ' + (val / 1e9).toFixed(1) + 'B';
  };

  // Format month for axis (e.g. 2024-01 -> Jan '24)
  const formatMonthAxis = (monthStr: string) => {
    if (!monthStr || monthStr.length < 7) return monthStr;
    const [year, month] = monthStr.split('-');
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const idx = parseInt(month, 10) - 1;
    return `${months[idx] || month} '${year.slice(2)}`;
  };

  // Trajectory stats
  const first = data[0];
  const last = data[data.length - 1];
  const diffPct =
    first && last && first.total_debt > 0
      ? (((last.total_debt - first.total_debt) / first.total_debt) * 100).toFixed(1)
      : null;

  if (loading || !mounted) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4 animate-pulse">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="space-y-2">
            <div className="h-5 w-64 bg-slate-200 rounded"></div>
            <div className="h-3 w-96 bg-slate-100 rounded"></div>
          </div>
          <div className="h-7 w-36 bg-slate-200 rounded-full"></div>
        </div>
        <div className="h-[210px] w-full bg-slate-50 rounded-xl flex items-center justify-center">
          <div className="text-xs text-slate-400 font-medium">Loading 24-month debt exposure trajectory...</div>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 text-center space-y-2">
        <AlertCircle className="w-6 h-6 text-slate-400 mx-auto" />
        <h3 className="text-sm font-bold text-slate-700">No Historical Debt Data Available</h3>
        <p className="text-xs text-slate-500">24-month macro exposure records could not be loaded.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-slate-100">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-base font-bold text-slate-900 tracking-tight">
              24-Month Macro Debt Exposure Trajectory
            </h2>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
              National Arrears Velocity
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Total outstanding county arrears owed to KEMSA across all 47 counties ({data.length} monthly snapshots &bull; 2024–2025)
          </p>
        </div>

        {diffPct && (
          <div className="flex items-center space-x-2 text-xs font-semibold px-3 py-1.5 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg self-start sm:self-auto">
            <TrendingUp className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span>
              Net Exposure: <strong className="font-bold">+{diffPct}%</strong> (KES {(first.total_debt / 1e9).toFixed(2)}B &rarr; KES {(last.total_debt / 1e9).toFixed(2)}B)
            </span>
          </div>
        )}
      </div>

      {/* Chart */}
      <div className="w-full h-[220px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
            <defs>
              <linearGradient id="debtGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#E11D48" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#E11D48" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
            <XAxis
              dataKey="month"
              tickFormatter={formatMonthAxis}
              tick={{ fontSize: 11, fill: '#64748B' }}
              axisLine={{ stroke: '#CBD5E1' }}
              tickLine={false}
              minTickGap={25}
            />
            <YAxis
              tickFormatter={formatBillions}
              tick={{ fontSize: 11, fill: '#64748B' }}
              axisLine={false}
              tickLine={false}
              domain={['auto', 'auto']}
              width={75}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const item = payload[0].payload as NationalDebtTrendItem;
                  return (
                    <div className="bg-slate-900 text-white p-3 rounded-xl shadow-lg border border-slate-700 text-xs space-y-1">
                      <div className="font-bold text-slate-200 border-b border-slate-700 pb-1">
                        {formatMonthAxis(item.month)} ({item.month})
                      </div>
                      <div className="text-rose-400 font-mono font-bold text-sm">
                        KES {item.total_debt.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                      <div className="text-slate-400 text-[11px] flex items-center justify-between gap-4">
                        <span>Avg Delinquency:</span>
                        <span className="text-slate-200 font-semibold">{item.avg_days_overdue} days</span>
                      </div>
                      <div className="text-slate-400 text-[11px] flex items-center justify-between gap-4">
                        <span>Counties Monitored:</span>
                        <span className="text-slate-200 font-semibold">{item.counties_count}</span>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area
              type="monotone"
              dataKey="total_debt"
              stroke="#E11D48"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#debtGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Footer / Context Legend */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100 text-[11px] text-slate-500">
        <div className="flex items-center space-x-2">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-rose-500"></span>
          <span>Cumulative National Arrears (KES)</span>
          <span className="text-slate-300">&bull;</span>
          <span>Provides national leadership with acceleration velocity context alongside point-in-time scorecards.</span>
        </div>
        <div className="font-medium text-slate-600">
          Latest Average Arrears Age: <strong className="text-slate-900">{last?.avg_days_overdue ?? 0} days</strong>
        </div>
      </div>
    </div>
  );
}
