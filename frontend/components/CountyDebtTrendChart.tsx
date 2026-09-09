'use client';

import React, { useEffect, useState } from 'react';
import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { TrendingUp, AlertCircle, Activity } from 'lucide-react';
import { CountyHistoryItem } from '@/lib/api';

interface CountyDebtTrendChartProps {
  county: string;
  data: CountyHistoryItem[];
  loading?: boolean;
}

export default function CountyDebtTrendChart({
  county,
  data,
  loading = false,
}: CountyDebtTrendChartProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Format KES millions for left axis
  const formatMillions = (val: number) => {
    return 'KES ' + (val / 1e6).toFixed(0) + 'M';
  };

  // Format month for axis (e.g. 2024-01 -> Jan '24)
  const formatMonthAxis = (monthStr: string) => {
    if (!monthStr || monthStr.length < 7) return monthStr;
    const [year, month] = monthStr.split('-');
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const idx = parseInt(month, 10) - 1;
    return `${months[idx] || month} '${year.slice(2)}`;
  };

  const first = data[0];
  const last = data[data.length - 1];

  if (loading || !mounted) {
    return (
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-3 animate-pulse">
        <div className="flex items-center justify-between pb-2 border-b border-slate-200">
          <div className="h-4 w-52 bg-slate-200 rounded"></div>
          <div className="h-5 w-32 bg-slate-200 rounded-full"></div>
        </div>
        <div className="h-[170px] w-full bg-slate-100 rounded-lg flex items-center justify-center">
          <div className="text-xs text-slate-400 font-medium">Loading 24-month debt &amp; risk trajectory...</div>
        </div>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-center space-y-1.5">
        <AlertCircle className="w-5 h-5 text-slate-400 mx-auto" />
        <h4 className="text-xs font-bold text-slate-700">No History Available for {county}</h4>
        <p className="text-[11px] text-slate-500">24-month scorecard trend could not be compiled.</p>
      </div>
    );
  }

  return (
    <div className="bg-slate-50/80 border border-slate-200/90 rounded-xl p-4 space-y-3 transition-all duration-300">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-2.5 border-b border-slate-200">
        <div className="flex items-center space-x-2">
          <div className="p-1 rounded bg-blue-100 text-blue-700">
            <Activity className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900">
              24-Month Debt Exposure &amp; Risk Trajectory
            </h3>
            <p className="text-[11px] text-slate-500">
              Historical velocity diagnostic: tracking arrears growth and composite risk tier evolution (2024–2025)
            </p>
          </div>
        </div>

        {first && last && (
          <div className="flex items-center space-x-2 text-[11px] font-semibold text-slate-700 self-start sm:self-auto bg-white px-2.5 py-1 rounded-lg border border-slate-200 shadow-2xs">
            <TrendingUp className="w-3.5 h-3.5 text-blue-600" />
            <span>
              Risk Score: <strong className="text-slate-900">{first.risk_score}</strong> ({first.risk_tier}) &rarr;{' '}
              <strong className="text-amber-700">{last.risk_score}</strong> ({last.risk_tier})
            </span>
          </div>
        )}
      </div>

      {/* Chart: Inline & compact */}
      <div className="w-full h-[180px]">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 15, left: 5, bottom: 0 }}>
            <defs>
              <linearGradient id="countyDebtGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" vertical={false} />
            <XAxis
              dataKey="month"
              tickFormatter={formatMonthAxis}
              tick={{ fontSize: 10, fill: '#64748B' }}
              axisLine={{ stroke: '#CBD5E1' }}
              tickLine={false}
              minTickGap={20}
            />
            {/* Left Axis: Debt in Millions */}
            <YAxis
              yAxisId="debt"
              tickFormatter={formatMillions}
              tick={{ fontSize: 10, fill: '#3B82F6' }}
              axisLine={false}
              tickLine={false}
              domain={['auto', 'auto']}
              width={65}
            />
            {/* Right Axis: Risk Score (0-100) */}
            <YAxis
              yAxisId="score"
              orientation="right"
              domain={[0, 100]}
              tick={{ fontSize: 10, fill: '#D97706' }}
              axisLine={false}
              tickLine={false}
              width={35}
              ticks={[0, 35, 65, 100]}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const item = payload[0].payload as CountyHistoryItem;
                  const isHigh = item.risk_tier.toLowerCase() === 'high';
                  const isMed = item.risk_tier.toLowerCase() === 'medium';
                  return (
                    <div className="bg-slate-900 text-white p-2.5 rounded-xl shadow-lg border border-slate-700 text-xs space-y-1 min-w-[190px]">
                      <div className="flex items-center justify-between border-b border-slate-700 pb-1">
                        <span className="font-bold text-slate-200">{formatMonthAxis(item.month)}</span>
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-black ${
                            isHigh ? 'bg-red-900 text-red-200' : isMed ? 'bg-amber-900 text-amber-200' : 'bg-emerald-900 text-emerald-200'
                          }`}
                        >
                          {item.risk_tier} ({item.risk_score}/100)
                        </span>
                      </div>
                      <div className="text-blue-400 font-mono font-bold text-xs pt-0.5">
                        Debt: KES {item.amount_owed_kes.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </div>
                      <div className="text-slate-300 text-[11px] flex justify-between">
                        <span>Arrears Delinquency:</span>
                        <span className="font-semibold text-white">{item.days_overdue} days</span>
                      </div>
                      <div className="text-slate-400 text-[10px] pt-1 border-t border-slate-800">
                        Driver: {item.primary_driver}
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            {/* Outstanding Debt Area */}
            <Area
              yAxisId="debt"
              type="monotone"
              dataKey="amount_owed_kes"
              name="Outstanding Debt"
              stroke="#2563EB"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#countyDebtGrad)"
            />
            {/* Risk Score Line */}
            <Line
              yAxisId="score"
              type="monotone"
              dataKey="risk_score"
              name="Risk Score (0-100)"
              stroke="#D97706"
              strokeWidth={2.5}
              dot={{ r: 2, fill: '#D97706' }}
              activeDot={{ r: 4, stroke: '#F59E0B' }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Footer Legend */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-200/80 text-[11px] text-slate-500">
        <div className="flex items-center space-x-3">
          <span className="flex items-center space-x-1">
            <span className="inline-block w-2.5 h-2.5 rounded-full bg-blue-500"></span>
            <span>Outstanding Debt (Left Axis)</span>
          </span>
          <span className="flex items-center space-x-1">
            <span className="inline-block w-2.5 h-1 bg-amber-600 rounded"></span>
            <span>Composite Risk Score (Right Axis)</span>
          </span>
        </div>
        <div className="text-[10px] text-slate-400">
          Arrears threshold: &gt;65 High Risk | &gt;35 Medium Risk
        </div>
      </div>
    </div>
  );
}
