'use client';

import React, { useEffect, useState, useMemo } from 'react';
import ShellLayout from '@/components/ShellLayout';
import NationalDebtTrendChart from '@/components/NationalDebtTrendChart';
import TherapeuticCategoryDeficit from '@/components/TherapeuticCategoryDeficit';
import KenyaRiskMap from '@/components/KenyaRiskMap';
import { getClientSession, UserSession } from '@/lib/auth';
import {
  getAllCountyScorecards,
  getCountyScorecard,
  getCountyForecast,
  getNationalForecast,
  getRedistributionActivity,
  getNationalDebtTrend,
  getCategoryStockoutForecast,
  CountyScorecardSummary,
  CountyScorecardDetail,
  CountyForecastResponse,
  NationalForecastResponse,
  RedistributionActivityResponse,
  NationalDebtTrendItem,
  CategoryForecastResponse,
} from '@/lib/api';
import {
  TrendingUp,
  AlertTriangle,
  ShieldAlert,
  RefreshCw,
  Download,
  Search,
  Layers,
  CheckCircle2,
  LayoutGrid,
  Map as MapIcon,
  Package,
  X,
  ArrowDown,
  Building2,
  Clock,
  ExternalLink,
} from 'lucide-react';

interface RecentTransferLog {
  request_id: string;
  source_county: string;
  destination_county: string;
  commodity_name: string;
  requested_quantity: number;
  distance_km: number;
  status: string;
  requested_at: string;
}

export default function NationalDashboardPage() {
  const [session, setSession] = useState<UserSession | null>(null);
  const [scorecards, setScorecards] = useState<CountyScorecardSummary[]>([]);
  const [forecast, setForecast] = useState<NationalForecastResponse | null>(null);
  const [activity, setActivity] = useState<RedistributionActivityResponse | null>(null);
  const [debtTrend, setDebtTrend] = useState<NationalDebtTrendItem[]>([]);
  const [categoryForecast, setCategoryForecast] = useState<CategoryForecastResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // View mode toggle: 'grid' (default) vs 'map'
  const [viewMode, setViewMode] = useState<'grid' | 'map'>('grid');

  // Filter and search state for the National Risk Visual
  const [filterTier, setFilterTier] = useState<'ALL' | 'High' | 'Medium' | 'Low'>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Drawer state for County Risk Brief (Task 1)
  const [selectedCountyForDrawer, setSelectedCountyForDrawer] = useState<string | null>(null);
  const [drawerScorecard, setDrawerScorecard] = useState<CountyScorecardDetail | null>(null);
  const [drawerForecast, setDrawerForecast] = useState<CountyForecastResponse | null>(null);
  const [drawerLoading, setDrawerLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!selectedCountyForDrawer) {
      setDrawerScorecard(null);
      setDrawerForecast(null);
      return;
    }
    let isMounted = true;
    setDrawerLoading(true);
    Promise.all([
      getCountyScorecard(selectedCountyForDrawer),
      getCountyForecast(selectedCountyForDrawer),
    ])
      .then(([sc, fc]) => {
        if (isMounted) {
          setDrawerScorecard(sc);
          setDrawerForecast(fc);
        }
      })
      .catch((err) => {
        console.error('Error loading county drawer data:', err);
      })
      .finally(() => {
        if (isMounted) setDrawerLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedCountyForDrawer]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [scorecardsData, forecastData, activityData, debtTrendData, categoryData] = await Promise.all([
        getAllCountyScorecards(),
        getNationalForecast(5),
        getRedistributionActivity(),
        getNationalDebtTrend(),
        getCategoryStockoutForecast(),
      ]);
      setScorecards(scorecardsData);
      setForecast(forecastData);
      setActivity(activityData);
      setDebtTrend(debtTrendData);
      setCategoryForecast(categoryData);
    } catch (err: unknown) {
      console.error('Error fetching national data:', err);
      const msg = err instanceof Error ? err.message : 'Failed to connect to FastAPI backend';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    setSession(getClientSession());
    loadData();
  }, []);

  // Summary counts
  const highRiskCount = useMemo(
    () => scorecards.filter((s) => s.risk_tier.toLowerCase() === 'high').length,
    [scorecards]
  );
  const medRiskCount = useMemo(
    () => scorecards.filter((s) => s.risk_tier.toLowerCase() === 'medium').length,
    [scorecards]
  );
  const lowRiskCount = useMemo(
    () => scorecards.filter((s) => s.risk_tier.toLowerCase() === 'low').length,
    [scorecards]
  );

  // Filtered and sorted counties: High Risk first, then Medium, then Low, sorted by risk_score DESC
  const displayedCounties = useMemo(() => {
    const tierPriority: Record<string, number> = { high: 3, medium: 2, low: 1 };

    return scorecards
      .filter((c) => {
        if (filterTier !== 'ALL' && c.risk_tier.toLowerCase() !== filterTier.toLowerCase()) {
          return false;
        }
        if (searchQuery.trim()) {
          const q = searchQuery.toLowerCase();
          return c.county.toLowerCase().includes(q) || c.primary_driver.toLowerCase().includes(q);
        }
        return true;
      })
      .sort((a, b) => {
        const pA = tierPriority[a.risk_tier.toLowerCase()] || 0;
        const pB = tierPriority[b.risk_tier.toLowerCase()] || 0;
        if (pA !== pB) return pB - pA;
        return b.risk_score - a.risk_score;
      });
  }, [scorecards, filterTier, searchQuery]);

  // One-click CSV Export of County Risk Scorecard
  const handleExportCsv = () => {
    if (!scorecards.length) return;
    const headers = [
      'County',
      'Risk Tier',
      'Composite Risk Score',
      'Outstanding Debt (KES)',
      'Days Overdue',
      'Payment History Score',
      'Primary Risk Driver',
      'Record Month',
    ];
    const rows = scorecards.map((s) => [
      `"${s.county}"`,
      `"${s.risk_tier}"`,
      s.risk_score.toFixed(1),
      s.amount_owed_kes,
      s.days_overdue,
      s.payment_history_score.toFixed(1),
      `"${s.primary_driver}"`,
      `"${s.month}"`,
    ]);
    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const filename = `kemsa_national_county_risk_scorecard_${new Date().toISOString().slice(0, 10)}.csv`;
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const criticalPairs = forecast?.horizon_projections?.[0]?.predicted_stockout_pairs ?? 535;

  return (
    <ShellLayout session={session}>
      <div className="space-y-8">
        {/* Executive Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between pb-4 border-b border-slate-200">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 uppercase tracking-wide">
                Executive Portal
              </span>
              <span className="text-xs text-slate-500 font-medium">
                National Situational Awareness &bull; 30-Second Scan Screen
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 mt-1.5 tracking-tight">
              KEMSA National Leadership Dashboard
            </h1>
            <p className="text-sm text-slate-600 mt-0.5">
              Country-wide financial risk exposure, aggregate 30/60/90-day demand forecast, and inter-county redistribution activity.
            </p>
          </div>

          <div className="mt-4 md:mt-0 flex items-center space-x-2.5">
            <button
              onClick={handleExportCsv}
              disabled={loading || !scorecards.length}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-bold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 shadow-xs transition"
              title="Export all county risk data as CSV"
            >
              <Download className="w-4 h-4 text-slate-600" />
              <span>Export CSV</span>
            </button>

            <button
              onClick={loadData}
              disabled={loading}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-bold text-white bg-slate-900 rounded-lg hover:bg-slate-800 shadow-xs transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh Metrics</span>
            </button>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="py-20 text-center">
            <div className="inline-block animate-spin rounded-full h-9 w-9 border-4 border-emerald-600 border-t-transparent mb-3"></div>
            <p className="text-sm font-bold text-slate-700">Connecting to KEMSA Intelligence Layer...</p>
            <p className="text-xs text-slate-500">Querying financial scores, national forecast models, and redistribution logs</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-center space-y-3">
            <ShieldAlert className="w-8 h-8 text-red-600 mx-auto" />
            <h3 className="text-base font-bold text-red-900">Backend Communication Error</h3>
            <p className="text-xs text-red-700 max-w-md mx-auto">{error}</p>
            <button
              onClick={loadData}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-lg shadow"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && (
          <>
            {/* 1. TOP KPI METRIC CARDS (High Risk Counties + Critical Stockout Pairs + Wastage Prevented) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Card 1: High Risk Counties (Interactive Filter Shortcut - Task 2) */}
              <div
                onClick={() => {
                  setFilterTier('High');
                  if (viewMode !== 'grid') setViewMode('grid');
                  document.getElementById('national-risk-visual')?.scrollIntoView({ behavior: 'smooth' });
                }}
                className="bg-white p-5 rounded-2xl border-2 border-red-200 shadow-xs flex flex-col justify-between cursor-pointer hover:border-red-400 hover:shadow-md transition-all group"
                title="Click to filter 47-county scanner to High Risk"
              >
                <div>
                  <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-red-700">
                    <span>Counties at High Risk</span>
                    <ShieldAlert className="w-4 h-4 text-red-600" />
                  </div>
                  <div className="mt-3 flex items-baseline space-x-2">
                    <span className="text-4xl font-black text-red-600">{highRiskCount}</span>
                    <span className="text-xs font-semibold text-slate-500">/ 47 counties</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-2">
                    Immediate credit freeze &amp; debt restructuring threshold exceeded.
                  </p>
                  <div className="mt-2.5 pt-2 border-t border-red-100 flex items-center justify-between text-[11px] font-bold text-red-700">
                    <span>Filter scanner to High Risk</span>
                    <ArrowDown className="w-3.5 h-3.5 group-hover:translate-y-0.5 transition-transform" />
                  </div>
                </div>
                <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] font-medium text-slate-500">
                  <span>Medium: <strong className="text-amber-700">{medRiskCount}</strong></span>
                  <span>Low: <strong className="text-emerald-700">{lowRiskCount}</strong></span>
                </div>
              </div>

              {/* Card 2: 30-Day Critical Stockout Pairs */}
              <div className="bg-white p-5 rounded-2xl border-2 border-amber-200 shadow-xs flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-amber-700">
                    <span>Critical Stockouts (&le;30 Days)</span>
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                  </div>
                  <div className="mt-3 flex items-baseline space-x-2">
                    <span className="text-4xl font-black text-amber-600">{criticalPairs.toLocaleString()}</span>
                    <span className="text-xs font-semibold text-slate-500">facility-drug pairs</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-2">
                    Predicted to run out within 30 days without inter-facility transfer or order.
                  </p>
                </div>
                <div className="mt-3 pt-3 border-t border-slate-100 text-[11px] font-medium text-slate-500">
                  Est. Unmet Units: <strong className="text-slate-800">{Math.round(forecast?.horizon_projections?.[0]?.estimated_unmet_demand_units ?? 0).toLocaleString()}</strong>
                </div>
              </div>

              {/* Card 3: Total Monitored Facilities */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-600">
                    <span>Monitored Network</span>
                    <Layers className="w-4 h-4 text-emerald-600" />
                  </div>
                  <div className="mt-3 flex items-baseline space-x-2">
                    <span className="text-4xl font-black text-slate-900">
                      {forecast?.total_facilities_monitored ?? 100}
                    </span>
                    <span className="text-xs font-semibold text-slate-500">facilities</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-2">
                    Active ingestion across all 47 counties ({forecast?.total_pairs_monitored?.toLocaleString() ?? '1,500'} pairs).
                  </p>
                </div>
                <div className="mt-3 pt-3 border-t border-slate-100 text-[11px] font-medium text-slate-500">
                  Total Commodities: <strong className="text-slate-800">{forecast?.total_commodities_monitored ?? 15} essential medicines</strong>
                </div>
              </div>

              {/* Card 4: Wastage Prevented */}
              <div className="bg-white p-5 rounded-2xl border-2 border-emerald-200 shadow-xs flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-emerald-800">
                    <span>Wastage Prevented</span>
                    <TrendingUp className="w-4 h-4 text-emerald-600" />
                  </div>
                  <div className="mt-3 flex items-baseline space-x-1">
                    <span className="text-xs font-bold text-emerald-700">KES</span>
                    <span className="text-3xl font-black text-emerald-700">
                      {(activity?.combined_total_savings_kes ?? activity?.estimated_wastage_prevented_kes ?? 0).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 mt-2">
                    Financial inventory saved from expiry through network-wide smart redistribution.
                  </p>
                </div>
                <div className="mt-3 pt-3 border-t border-slate-100 space-y-1.5 text-[11px] font-medium text-slate-500">
                  <div className="flex items-center justify-between">
                    <span>Total Reallocations:</span>
                    <strong className="text-slate-800">
                      {(activity?.combined_total_transfers ?? activity?.approved_transfers_count ?? 0).toLocaleString()} transfers
                    </strong>
                  </div>
                  {activity?.live_activity && (
                    <div className="text-[10px] text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 flex items-center justify-between font-semibold">
                      <span>Live Pilot Activity:</span>
                      <span>{activity.live_activity.approved_transfers_count} approved ({activity.live_activity.total_units_transferred.toLocaleString()} units)</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 1.5 24-MONTH MACRO DEBT EXPOSURE TRAJECTORY */}
            <NationalDebtTrendChart data={debtTrend} loading={loading} />

            {/* 2. NATIONAL RISK VISUAL: COLOR-CODED 47-COUNTY SCANNER */}
            <div id="national-risk-visual" className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-5">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-4 border-b border-slate-100">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">
                    National County Financial Risk Visual
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Scannable 47-county risk status matrix &bull; Prioritized by composite risk score (Overdue Days 40%, Debt 35%, Payment History 25%)
                  </p>
                </div>

                {/* Filter, Search, and View Mode Controls */}
                <div className="flex flex-wrap items-center gap-2.5">
                  {/* View Mode Toggle: Grid View (Default) vs Map View */}
                  <div className="flex items-center bg-slate-100 p-1 rounded-lg text-xs font-bold">
                    <button
                      onClick={() => setViewMode('grid')}
                      className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-md transition ${
                        viewMode === 'grid'
                          ? 'bg-white text-slate-900 shadow-xs'
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                      title="Scannable 47-county risk card grid"
                    >
                      <LayoutGrid className="w-3.5 h-3.5" />
                      <span>Grid View</span>
                    </button>
                    <button
                      onClick={() => setViewMode('map')}
                      className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-md transition ${
                        viewMode === 'map'
                          ? 'bg-white text-slate-900 shadow-xs'
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                      title="Interactive geographic map of Kenya"
                    >
                      <MapIcon className="w-3.5 h-3.5" />
                      <span>Map View</span>
                    </button>
                  </div>

                  {/* Search */}
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type="text"
                      placeholder="Search county..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500 w-36 sm:w-44"
                    />
                  </div>

                  {/* Filter Pills */}
                  <div className="flex items-center bg-slate-100 p-1 rounded-lg text-xs font-semibold">
                    <button
                      onClick={() => setFilterTier('ALL')}
                      className={`px-2.5 py-1 rounded-md transition ${
                        filterTier === 'ALL'
                          ? 'bg-white text-slate-900 shadow-xs font-bold'
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      All ({scorecards.length})
                    </button>
                    <button
                      onClick={() => setFilterTier('High')}
                      className={`px-2.5 py-1 rounded-md transition flex items-center space-x-1 ${
                        filterTier === 'High'
                          ? 'bg-red-600 text-white shadow-xs font-bold'
                          : 'text-red-700 hover:bg-red-50'
                      }`}
                    >
                      <span>High ({highRiskCount})</span>
                    </button>
                    <button
                      onClick={() => setFilterTier('Medium')}
                      className={`px-2.5 py-1 rounded-md transition flex items-center space-x-1 ${
                        filterTier === 'Medium'
                          ? 'bg-amber-600 text-white shadow-xs font-bold'
                          : 'text-amber-700 hover:bg-amber-50'
                      }`}
                    >
                      <span>Med ({medRiskCount})</span>
                    </button>
                    <button
                      onClick={() => setFilterTier('Low')}
                      className={`px-2.5 py-1 rounded-md transition flex items-center space-x-1 ${
                        filterTier === 'Low'
                          ? 'bg-emerald-600 text-white shadow-xs font-bold'
                          : 'text-emerald-700 hover:bg-emerald-50'
                      }`}
                    >
                      <span>Low ({lowRiskCount})</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Proportional National Exposure Bar */}
              <div className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold text-slate-600">
                  <span>National Risk Distribution</span>
                  <div className="flex items-center space-x-3 text-[11px]">
                    <span className="text-red-600 font-bold">&bull; High ({Math.round((highRiskCount / 47) * 100)}%)</span>
                    <span className="text-amber-600 font-bold">&bull; Medium ({Math.round((medRiskCount / 47) * 100)}%)</span>
                    <span className="text-emerald-600 font-bold">&bull; Low ({Math.round((lowRiskCount / 47) * 100)}%)</span>
                  </div>
                </div>
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden flex">
                  <div
                    style={{ width: `${(highRiskCount / 47) * 100}%` }}
                    className="bg-red-500 h-full transition-all"
                    title={`High Risk: ${highRiskCount} counties`}
                  />
                  <div
                    style={{ width: `${(medRiskCount / 47) * 100}%` }}
                    className="bg-amber-400 h-full transition-all"
                    title={`Medium Risk: ${medRiskCount} counties`}
                  />
                  <div
                    style={{ width: `${(lowRiskCount / 47) * 100}%` }}
                    className="bg-emerald-500 h-full transition-all"
                    title={`Low Risk: ${lowRiskCount} counties`}
                  />
                </div>
              </div>

              {/* Conditional View: 47-County Scannable Grid (Default) or Kenya Interactive Geo-Risk Map */}
              {viewMode === 'grid' ? (
                <>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                    {displayedCounties.map((c) => {
                      const isHigh = c.risk_tier.toLowerCase() === 'high';
                      const isMed = c.risk_tier.toLowerCase() === 'medium';
                      const borderClass = isHigh
                        ? 'border-red-300 bg-red-50/40 hover:border-red-500'
                        : isMed
                        ? 'border-amber-300 bg-amber-50/30 hover:border-amber-500'
                        : 'border-emerald-200 bg-emerald-50/20 hover:border-emerald-500';

                      const badgeClass = isHigh
                        ? 'bg-red-100 text-red-800 border-red-300'
                        : isMed
                        ? 'bg-amber-100 text-amber-800 border-amber-300'
                        : 'bg-emerald-100 text-emerald-800 border-emerald-300';

                      return (
                        <div
                          key={c.county}
                          onClick={() => setSelectedCountyForDrawer(c.county)}
                          className={`p-3 rounded-xl border transition-all duration-150 shadow-2xs hover:shadow-md hover:scale-[1.01] cursor-pointer flex flex-col justify-between ${borderClass}`}
                          title={`Click to open ${c.county} County Executive Brief`}
                        >
                          <div>
                            <div className="flex items-center justify-between">
                              <h3 className="text-xs font-extrabold text-slate-900 truncate" title={c.county}>
                                {c.county}
                              </h3>
                              <ExternalLink className="w-3 h-3 text-slate-400 opacity-60" />
                            </div>
                            <div className="mt-1.5 flex items-center justify-between">
                              <span className={`px-1.5 py-0.5 rounded text-[10px] font-black border uppercase tracking-wider ${badgeClass}`}>
                                {c.risk_tier}
                              </span>
                              <span className="text-xs font-black text-slate-800">
                                {c.risk_score.toFixed(0)}<span className="text-[10px] text-slate-400 font-normal">/100</span>
                              </span>
                            </div>
                          </div>

                          <div className="mt-2 pt-2 border-t border-slate-200/60 text-[10px] text-slate-600 space-y-0.5">
                            <div className="truncate font-mono font-medium" title={`KES ${c.amount_owed_kes.toLocaleString()}`}>
                              KES {(c.amount_owed_kes / 1_000_000).toFixed(1)}M
                            </div>
                            <div className="text-slate-500">
                              {c.days_overdue} days overdue
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {displayedCounties.length === 0 && (
                    <div className="py-8 text-center text-xs text-slate-500">
                      No counties match the current filter or search criteria.
                    </div>
                  )}
                </>
              ) : (
                <KenyaRiskMap
                  scorecards={scorecards}
                  filterTier={filterTier}
                  searchQuery={searchQuery}
                />
              )}
            </div>

            {/* 3. AGGREGATE STOCKOUT FORECAST (30/60/90-DAY HORIZON VISUAL) */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Horizon Progression Column */}
              <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-5">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div>
                    <h2 className="text-lg font-bold text-slate-900">
                      Forward Stockout Horizon Projections (30 / 60 / 90 Days)
                    </h2>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Recursive multi-step forward demand depletion across all 1,500 facility-drug pairs nationwide
                    </p>
                  </div>
                  <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-800 border border-blue-200">
                    Predictive Model Active
                  </span>
                </div>

                {/* 3 Horizon Bar Cards */}
                <div className="space-y-4">
                  {forecast?.horizon_projections?.map((h) => {
                    const totalPairs = forecast?.total_pairs_monitored || 1500;
                    const pct = Math.round((h.predicted_stockout_pairs / totalPairs) * 100);
                    const isCritical = h.horizon_days === 30;
                    const isWarning = h.horizon_days === 60;
                    const barColor = isCritical
                      ? 'bg-red-600'
                      : isWarning
                      ? 'bg-amber-500'
                      : 'bg-indigo-600';
                    const badgeColor = isCritical
                      ? 'bg-red-100 text-red-800'
                      : isWarning
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-indigo-100 text-indigo-800';

                    return (
                      <div key={h.horizon_days} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-0.5 rounded text-xs font-extrabold uppercase ${badgeColor}`}>
                              {h.label}
                            </span>
                            <span className="text-xs text-slate-500 font-medium">
                              ({h.horizon_days} days forward)
                            </span>
                          </div>
                          <div className="text-right">
                            <span className="text-base font-black text-slate-900">
                              {h.predicted_stockout_pairs.toLocaleString()} pairs
                            </span>
                            <span className="text-xs text-slate-500 ml-1.5 font-medium">
                              ({pct}% of national inventory)
                            </span>
                          </div>
                        </div>

                        {/* Visual Progress Bar */}
                        <div className="h-3 w-full bg-slate-200 rounded-full overflow-hidden">
                          <div
                            style={{ width: `${pct}%` }}
                            className={`h-full ${barColor} transition-all duration-300 rounded-full`}
                          />
                        </div>

                        <div className="flex items-center justify-between text-xs text-slate-600 pt-0.5">
                          <span>
                            {isCritical
                              ? 'Immediate depletion risk — emergency redistribution required'
                              : isWarning
                              ? 'Medium-term exhaustion — order replenishment window'
                              : 'Full quarterly exposure without procurement'}
                          </span>
                          <span className="font-semibold text-slate-800">
                            Est. Unmet: {Math.round(h.estimated_unmet_demand_units).toLocaleString()} units
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Plain-Language Executive Insight Box */}
                <div className="p-3.5 bg-blue-50 border border-blue-200 rounded-xl text-xs text-blue-900 flex items-start space-x-2.5">
                  <CheckCircle2 className="w-4 h-4 text-blue-700 flex-shrink-0 mt-0.5" />
                  <p className="leading-relaxed">
                    <strong className="font-bold">Executive Forecast Summary:</strong> Nationally, <strong>{criticalPairs} facility-drug pairs</strong> face critical stockout within 30 days. Unmet demand will scale to <strong>{Math.round(forecast?.horizon_projections?.[2]?.estimated_unmet_demand_units ?? 0).toLocaleString()} units</strong> by day 90 if county debts freeze procurement restocks.
                  </p>
                </div>
              </div>

              {/* Urgent National Need Column (Generalized to County/Commodity — NO facility names leak) */}
              <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4 flex flex-col justify-between">
                <div>
                  <div className="pb-3 border-b border-slate-100">
                    <h3 className="text-base font-bold text-slate-900">
                      Most Urgent Stockout Clusters
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Abstracted by County &bull; Strictly compliant with non-leaking executive view rule
                    </p>
                  </div>

                  <div className="divide-y divide-slate-100 mt-2">
                    {forecast?.most_urgent_pairs?.slice(0, 5).map((p, idx) => (
                      <div key={`${p.county}-${p.commodity_id}-${idx}`} className="py-2.5 space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-slate-900 truncate max-w-[160px]" title={p.commodity_name}>
                            {p.commodity_name}
                          </span>
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-black bg-red-100 text-red-800 border border-red-200">
                            {p.days_until_stockout === 0 ? 'Stocked Out' : `${p.days_until_stockout}d remaining`}
                          </span>
                        </div>
                        <div className="flex items-center justify-between text-[11px] text-slate-500">
                          <span className="font-semibold text-emerald-800">{p.county} County Cluster</span>
                          <span>Stock: {p.current_stock_level.toLocaleString()} units</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-[11px] text-slate-500">
                  Per executive design specification, granular health facility identities are abstracted into county clusters.
                </div>
              </div>
            </div>

            {/* 3.5 PREDICTED 30-DAY DEFICIT BY THERAPEUTIC PROGRAM */}
            <TherapeuticCategoryDeficit data={categoryForecast} loading={loading} />

            {/* 4. REDISTRIBUTION ACTIVITY LOG & WASTAGE PREVENTED (County-to-County level summary) */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-slate-100">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">
                    Inter-County Redistribution Manifest &amp; Savings Log
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    High-level national reallocation summary &bull; Generalized routes preserving executive view isolation
                  </p>
                </div>
                <div className="mt-2 sm:mt-0 flex items-center space-x-2 text-xs font-semibold text-emerald-800 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
                  <span>KES {(activity?.combined_total_savings_kes ?? activity?.estimated_wastage_prevented_kes ?? 0).toLocaleString()} Wastage Prevented</span>
                </div>
              </div>

              {/* Stats Bar */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-center">
                  <div className="text-xs text-slate-500 uppercase font-bold tracking-wider">Total Reallocations</div>
                  <div className="text-xl font-black text-slate-900 mt-1">{(activity?.combined_total_transfers ?? activity?.approved_transfers_count ?? 0).toLocaleString()}</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">85,115 baseline + {activity?.live_activity?.approved_transfers_count ?? 0} live</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-center">
                  <div className="text-xs text-slate-500 uppercase font-bold tracking-wider">Total Units Reallocated</div>
                  <div className="text-xl font-black text-slate-900 mt-1">{(activity?.combined_total_units ?? activity?.total_units_transferred ?? 0).toLocaleString()} units</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Diverted from expiry to clinical need</div>
                </div>
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-center">
                  <div className="text-xs text-slate-500 uppercase font-bold tracking-wider">Total Financial Value Saved</div>
                  <div className="text-xl font-black text-emerald-700 mt-1">KES {(activity?.combined_total_savings_kes ?? activity?.estimated_financial_value_kes ?? 0).toLocaleString()}</div>
                  <div className="text-[10px] text-emerald-600 font-semibold mt-0.5">Preserved public health capital</div>
                </div>
              </div>

              {/* Top Reallocated Essential Medicines Panel */}
              {activity?.top_reallocated_commodities && activity.top_reallocated_commodities.length > 0 && (
                <div className="p-4 bg-slate-50/80 rounded-xl border border-slate-200/90 space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1">
                    <div className="flex items-center space-x-2">
                      <Package className="w-4 h-4 text-emerald-600" />
                      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                        Top Reallocated Essential Medicines (Highest Network Mobility)
                      </h3>
                    </div>
                    <span className="text-[11px] text-slate-500 font-medium">
                      Top 5 commodities prevented from expiry and stockout
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                    {activity.top_reallocated_commodities.map((item, idx) => (
                      <div
                        key={item.commodity_id}
                        className="bg-white p-3.5 rounded-lg border border-slate-200 shadow-2xs space-y-2 flex flex-col justify-between hover:border-slate-300 transition"
                      >
                        <div>
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-black text-slate-400">#{idx + 1}</span>
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-bold capitalize bg-slate-100 text-slate-700">
                              {item.category}
                            </span>
                          </div>
                          <h4 className="text-xs font-bold text-slate-900 mt-1.5 line-clamp-2" title={item.commodity_name}>
                            {item.commodity_name}
                          </h4>
                        </div>

                        <div className="pt-2 border-t border-slate-100 text-[11px] space-y-1">
                          <div className="flex justify-between items-baseline font-mono">
                            <span className="text-slate-500">Volume:</span>
                            <strong className="text-slate-900 font-black">{item.total_units.toLocaleString()} u</strong>
                          </div>
                          <div className="flex justify-between items-baseline font-mono text-[10px]">
                            <span className="text-slate-400">Transfers:</span>
                            <span className="text-slate-600 font-semibold">{item.transfer_count.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between items-baseline font-mono text-[10px] text-emerald-700 font-bold">
                            <span>Value:</span>
                            <span>KES {(item.total_value_kes / 1_000_000).toFixed(2)}M</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Activity Feed Table (Generalizing facilities to County -> County) */}
              <div className="overflow-x-auto border border-slate-200 rounded-xl">
                <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
                  <thead className="bg-slate-50 text-slate-600 font-bold uppercase tracking-wider">
                    <tr>
                      <th className="px-4 py-3">Transfer Route (County Scope)</th>
                      <th className="px-4 py-3">Commodity</th>
                      <th className="px-4 py-3">Quantity</th>
                      <th className="px-4 py-3">Haversine Distance</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 bg-white">
                    {activity?.recent_activity && activity.recent_activity.length > 0 ? (
                      (activity.recent_activity as unknown as RecentTransferLog[]).map((r) => (
                        <tr key={r.request_id} className="hover:bg-slate-50 transition">
                          <td className="px-4 py-3 font-semibold text-slate-900">
                            <span className="text-blue-700 font-bold">{r.source_county} County</span>
                            <span className="text-slate-400 mx-1.5">&rarr;</span>
                            <span className="text-emerald-700 font-bold">{r.destination_county} County</span>
                          </td>
                          <td className="px-4 py-3 text-slate-800 font-medium">{r.commodity_name}</td>
                          <td className="px-4 py-3 font-mono font-bold text-slate-900">{r.requested_quantity} units</td>
                          <td className="px-4 py-3 text-slate-600 font-mono">{r.distance_km} km</td>
                          <td className="px-4 py-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[11px] font-bold capitalize ${
                                r.status === 'approved'
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : r.status === 'rejected'
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-amber-100 text-amber-800'
                              }`}
                            >
                              {r.status}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-slate-500">{r.requested_at?.slice(0, 16) || 'Recent'}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={6} className="px-4 py-6 text-center text-xs text-slate-500">
                          No inter-county redistribution activity logged yet.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        {/* 5. COUNTY EXECUTIVE RISK BRIEF SLIDE-OVER DRAWER (Task 1) */}
        {selectedCountyForDrawer && (
          <div className="fixed inset-0 z-50 overflow-hidden">
            {/* Backdrop */}
            <div
              className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity duration-300"
              onClick={() => setSelectedCountyForDrawer(null)}
            />

            {/* Slide-over panel */}
            <div className="fixed inset-y-0 right-0 max-w-lg w-full bg-white shadow-2xl z-50 flex flex-col justify-between border-l border-slate-200 animate-slideLeft">
              {/* Drawer Header */}
              <div className="p-6 border-b border-slate-100 flex items-start justify-between bg-slate-50/70">
                <div>
                  <div className="flex items-center space-x-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-black uppercase tracking-wider border ${
                        drawerScorecard?.risk_tier.toLowerCase() === 'high'
                          ? 'bg-red-100 text-red-800 border-red-300'
                          : drawerScorecard?.risk_tier.toLowerCase() === 'medium'
                          ? 'bg-amber-100 text-amber-800 border-amber-300'
                          : 'bg-emerald-100 text-emerald-800 border-emerald-300'
                      }`}
                    >
                      {drawerScorecard?.risk_tier || 'County'} Risk Profile
                    </span>
                    <span className="text-xs text-slate-500 font-mono">
                      {selectedCountyForDrawer} County
                    </span>
                  </div>
                  <h2 className="text-2xl font-black text-slate-900 mt-1.5 tracking-tight">
                    {selectedCountyForDrawer} Executive Brief
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    High-level situational diagnostic &bull; Abstracted county perspective
                  </p>
                </div>

                <button
                  onClick={() => setSelectedCountyForDrawer(null)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200/60 transition"
                  title="Close brief"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Drawer Content */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {drawerLoading ? (
                  <div className="py-20 text-center space-y-3">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-emerald-600 border-t-transparent" />
                    <p className="text-xs font-bold text-slate-600">
                      Querying {selectedCountyForDrawer} County risk &amp; supply metrics...
                    </p>
                  </div>
                ) : drawerScorecard ? (
                  <>
                    {/* Scorecard Hero Tile */}
                    <div className="p-4 bg-slate-50 rounded-2xl border border-slate-200 flex items-center justify-between">
                      <div>
                        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                          Composite Risk Score
                        </div>
                        <div className="text-3xl font-black text-slate-900 mt-0.5">
                          {drawerScorecard.risk_score.toFixed(1)}
                          <span className="text-xs text-slate-400 font-normal"> / 100</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                          Primary Risk Driver
                        </div>
                        <div className="text-sm font-black text-slate-800 mt-0.5">
                          {drawerScorecard.primary_driver}
                        </div>
                      </div>
                    </div>

                    {/* Plain-Language 'Why' Explanation */}
                    <div className="space-y-2">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center space-x-1.5">
                        <Building2 className="w-3.5 h-3.5 text-blue-600" />
                        <span>Plain-Language Diagnostic</span>
                      </h3>
                      <div className="p-4 bg-blue-50/60 border border-blue-200 rounded-xl text-xs text-slate-800 leading-relaxed font-medium">
                        {drawerScorecard.plain_language_summary}
                      </div>
                    </div>

                    {/* Financial Exposure Stats */}
                    <div className="space-y-2">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center space-x-1.5">
                        <Clock className="w-3.5 h-3.5 text-slate-600" />
                        <span>County Financial Exposure</span>
                      </h3>
                      <div className="grid grid-cols-2 gap-2.5">
                        <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                          <span className="text-[11px] text-slate-500 font-medium">Outstanding Debt</span>
                          <div className="font-mono font-bold text-slate-900 text-sm mt-0.5">
                            KES {(drawerScorecard.amount_owed_kes / 1_000_000).toFixed(2)}M
                          </div>
                        </div>
                        <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                          <span className="text-[11px] text-slate-500 font-medium">Delinquency</span>
                          <div className="font-mono font-bold text-slate-900 text-sm mt-0.5">
                            {drawerScorecard.days_overdue} days overdue
                          </div>
                        </div>
                        <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                          <span className="text-[11px] text-slate-500 font-medium">Payment History</span>
                          <div className="font-mono font-bold text-slate-900 text-sm mt-0.5">
                            {drawerScorecard.payment_history_score.toFixed(0)} / 100
                          </div>
                        </div>
                        <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                          <span className="text-[11px] text-slate-500 font-medium">Restock Status</span>
                          <div className="font-bold text-sm mt-0.5">
                            {drawerScorecard.risk_tier.toLowerCase() === 'high' ? (
                              <span className="text-red-600">Order Frozen</span>
                            ) : drawerScorecard.risk_tier.toLowerCase() === 'medium' ? (
                              <span className="text-amber-600">Conditional Restock</span>
                            ) : (
                              <span className="text-emerald-600">Auto-Approved</span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* High-Level Stockout Situation (Aggregate Counts Only — NO Facility Names) */}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center space-x-1.5">
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                          <span>County Supply Health &bull; Abstracted Totals</span>
                        </h3>
                        <span className="text-[11px] text-slate-500 font-medium">
                          {drawerForecast?.facilities_monitored ?? 2} facilities monitored
                        </span>
                      </div>

                      <div className="grid grid-cols-4 gap-2 text-center">
                        <div className="p-2.5 bg-red-50 border border-red-200 rounded-xl">
                          <div className="text-lg font-black text-red-600">
                            {drawerForecast?.risk_counts.critical ?? 0}
                          </div>
                          <div className="text-[10px] font-bold text-red-700 uppercase">Critical</div>
                          <div className="text-[9px] text-slate-500">&le;30 days</div>
                        </div>
                        <div className="p-2.5 bg-amber-50 border border-amber-200 rounded-xl">
                          <div className="text-lg font-black text-amber-600">
                            {drawerForecast?.risk_counts.warning ?? 0}
                          </div>
                          <div className="text-[10px] font-bold text-amber-700 uppercase">Warning</div>
                          <div className="text-[9px] text-slate-500">31-60 days</div>
                        </div>
                        <div className="p-2.5 bg-blue-50 border border-blue-200 rounded-xl">
                          <div className="text-lg font-black text-blue-600">
                            {drawerForecast?.risk_counts.watch ?? 0}
                          </div>
                          <div className="text-[10px] font-bold text-blue-700 uppercase">Watch</div>
                          <div className="text-[9px] text-slate-500">61-90 days</div>
                        </div>
                        <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-xl">
                          <div className="text-lg font-black text-emerald-600">
                            {drawerForecast?.risk_counts.healthy ?? 0}
                          </div>
                          <div className="text-[10px] font-bold text-emerald-700 uppercase">Healthy</div>
                          <div className="text-[9px] text-slate-500">&gt;90 days</div>
                        </div>
                      </div>

                      <p className="text-[11px] text-slate-400 italic pt-1">
                        Per executive design specification, granular health facility identities are strictly abstracted into county totals.
                      </p>
                    </div>
                  </>
                ) : (
                  <div className="py-12 text-center text-xs text-slate-500">
                    Unable to load detail scorecard for {selectedCountyForDrawer}.
                  </div>
                )}
              </div>

              {/* Drawer Footer */}
              <div className="p-4 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
                <span className="text-[11px] text-slate-500 font-mono">
                  Record Period: {drawerScorecard?.month || 'Current'}
                </span>
                <button
                  onClick={() => setSelectedCountyForDrawer(null)}
                  className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs rounded-xl shadow-xs transition"
                >
                  Close Executive Brief
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </ShellLayout>
  );
}
