'use client';

import React from 'react';
import { CategoryForecastResponse } from '@/lib/api';
import { Activity, Pill } from 'lucide-react';

interface TherapeuticCategoryDeficitProps {
  data: CategoryForecastResponse | null;
  loading?: boolean;
}

const CATEGORY_STYLES: Record<string, { bar: string; badge: string; text: string; dot: string }> = {
  Analgesics: {
    bar: 'bg-indigo-600',
    badge: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    text: 'text-indigo-700',
    dot: 'bg-indigo-500',
  },
  Antimalarials: {
    bar: 'bg-sky-600',
    badge: 'bg-sky-50 text-sky-700 border-sky-200',
    text: 'text-sky-700',
    dot: 'bg-sky-500',
  },
  Antibiotics: {
    bar: 'bg-amber-500',
    badge: 'bg-amber-50 text-amber-800 border-amber-200',
    text: 'text-amber-700',
    dot: 'bg-amber-500',
  },
  General: {
    bar: 'bg-emerald-600',
    badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    text: 'text-emerald-700',
    dot: 'bg-emerald-500',
  },
};

export default function TherapeuticCategoryDeficit({
  data,
  loading = false,
}: TherapeuticCategoryDeficitProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div className="space-y-2">
            <div className="h-5 w-64 bg-slate-200 rounded animate-pulse" />
            <div className="h-3 w-80 bg-slate-100 rounded animate-pulse" />
          </div>
        </div>
        <div className="space-y-3 pt-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="p-4 rounded-xl border border-slate-100 bg-slate-50/50 space-y-2">
              <div className="flex justify-between">
                <div className="h-4 w-32 bg-slate-200 rounded animate-pulse" />
                <div className="h-4 w-24 bg-slate-200 rounded animate-pulse" />
              </div>
              <div className="h-3 w-full bg-slate-200 rounded-full animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!data || !data.categories || data.categories.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 text-center py-12 space-y-2">
        <Pill className="w-8 h-8 text-slate-400 mx-auto" />
        <h3 className="text-sm font-bold text-slate-700">No Category Deficit Data Available</h3>
        <p className="text-xs text-slate-500">Forward consumption forecast models did not identify any 30-day stockouts.</p>
      </div>
    );
  }

  const maxDeficitValue = Math.max(...data.categories.map((c) => c.estimated_deficit_value_kes), 1);

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-slate-100 gap-2">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-bold text-slate-900">
              Predicted 30-Day Deficit by Therapeutic Program
            </h2>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-red-100 text-red-800 border border-red-200">
              30-Day Horizon
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Forward clinical demand gap &amp; estimated replenishment capital required by disease program
          </p>
        </div>

        {/* Aggregate Headline Pill */}
        <div className="flex items-center space-x-2 text-xs font-semibold px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-700">
          <Activity className="w-3.5 h-3.5 text-emerald-600" />
          <span>
            Total: <strong className="text-slate-900">KES {data.total_deficit_value_kes.toLocaleString()}</strong> ({data.total_unmet_demand_units.toLocaleString()} units)
          </span>
        </div>
      </div>

      {/* Horizontal Bar Breakdown Cards */}
      <div className="space-y-4">
        {data.categories.map((cat) => {
          const style = CATEGORY_STYLES[cat.category] || CATEGORY_STYLES.General;
          const relativeWidthPct = Math.min(100, Math.max(8, Math.round((cat.estimated_deficit_value_kes / maxDeficitValue) * 100)));

          return (
            <div
              key={cat.category}
              className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/40 hover:bg-slate-50 transition space-y-3"
            >
              {/* Category Title + Metric Badges */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1.5">
                <div className="flex items-center space-x-2">
                  <span className={`w-2.5 h-2.5 rounded-full ${style.dot}`} />
                  <h3 className="text-sm font-extrabold text-slate-900">
                    {cat.category}
                  </h3>
                  <span className={`px-2 py-0.5 rounded text-[11px] font-bold border ${style.badge}`}>
                    {cat.critical_pairs} critical pairs
                  </span>
                  <span className="text-[11px] text-slate-500 font-medium hidden sm:inline">
                    &bull; across {cat.affected_facilities_count} facilities
                  </span>
                </div>

                <div className="flex items-baseline space-x-3 text-xs">
                  <span className="text-slate-600 font-mono">
                    <strong className="text-slate-900">{cat.unmet_demand_units.toLocaleString()}</strong> units
                  </span>
                  <span className="font-mono font-black text-slate-900">
                    KES {cat.estimated_deficit_value_kes.toLocaleString()}
                  </span>
                  <span className="text-[11px] font-bold text-slate-500">
                    ({cat.percentage_of_value}%)
                  </span>
                </div>
              </div>

              {/* Proportional Horizontal Visual Bar */}
              <div className="space-y-1">
                <div className="h-3.5 w-full bg-slate-200/80 rounded-full overflow-hidden p-0.5">
                  <div
                    style={{ width: `${relativeWidthPct}%` }}
                    className={`h-full rounded-full transition-all duration-500 ${style.bar}`}
                    title={`${cat.category}: KES ${cat.estimated_deficit_value_kes.toLocaleString()} (${cat.percentage_of_value}%)`}
                  />
                </div>
              </div>

              {/* Key Contributing Commodities */}
              {cat.top_commodities && cat.top_commodities.length > 0 && (
                <div className="flex flex-wrap items-center gap-1.5 pt-1 text-[11px]">
                  <span className="text-slate-400 font-medium">Primary drivers:</span>
                  {cat.top_commodities.map((comm) => (
                    <span
                      key={comm.commodity_name}
                      className="inline-flex items-center px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700 font-medium"
                    >
                      <span>{comm.commodity_name}</span>
                      <span className="ml-1 text-slate-400">({comm.unmet_units.toLocaleString()} u &bull; KES {comm.deficit_value_kes.toLocaleString()})</span>
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
