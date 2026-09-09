'use client';

import React, { useEffect, useState, useMemo, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import ShellLayout from '@/components/ShellLayout';
import { getClientSession, UserSession } from '@/lib/auth';
import {
  getFacilityForecast,
  getNearbySurplusMatches,
  createTransferRequest,
  FacilityForecastResponse,
  SurplusMatchesResponse,
  SurplusMatchItem,
  TransferRequestRecord,
} from '@/lib/api';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  ShieldAlert,
  RefreshCw,
  ArrowLeftRight,
  X,
  Send,
  Search,
  CheckCircle,
  ArrowDown,
  Filter,
} from 'lucide-react';

function FacilityDashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [session, setSession] = useState<UserSession | null>(null);
  const [forecast, setForecast] = useState<FacilityForecastResponse | null>(null);
  const [matches, setMatches] = useState<SurplusMatchesResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filter for stock list
  const [stockFilter, setStockFilter] = useState<'ALL' | 'Critical' | 'Warning' | 'Healthy'>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Auto-filter for nearby surplus finder when countdown card is clicked
  const [selectedCommodityFilter, setSelectedCommodityFilter] = useState<{ id: string; name: string } | null>(null);
  const [healthyNotice, setHealthyNotice] = useState<string | null>(null);

  // Transfer Request Modal state
  const [selectedMatch, setSelectedMatch] = useState<SurplusMatchItem | null>(null);
  const [requestQty, setRequestQty] = useState<number>(50);
  const [requestOfficer, setRequestOfficer] = useState<string>('');
  const [requestReason, setRequestReason] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submittedTransfer, setSubmittedTransfer] = useState<TransferRequestRecord | null>(null);

  const activeFacilityId = session?.scopeId || 'FAC0001';
  const activeFacilityName = session?.scopeName || forecast?.facility_name || 'Nairobi National Referral Hospital';

  const loadData = async (facilityId: string) => {
    try {
      setLoading(true);
      setError(null);
      const [forecastData, matchesData] = await Promise.all([
        getFacilityForecast(facilityId),
        getNearbySurplusMatches(facilityId).catch((err) => {
          console.warn('Matches query warning:', err.message);
          return null;
        }),
      ]);
      setForecast(forecastData);
      setMatches(matchesData);
    } catch (err: unknown) {
      console.error('Error fetching facility data:', err);
      const msg = err instanceof Error ? err.message : 'Failed to connect to FastAPI backend';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const currentSession = getClientSession();
    setSession(currentSession);

    // Verify scope integrity
    const urlFacId = searchParams.get('facility_id') || searchParams.get('id');
    if (urlFacId && currentSession?.scopeId && urlFacId.toLowerCase() !== currentSession.scopeId.toLowerCase()) {
      router.replace(
        `/access-denied?reason=facility_scope_violation&attempted=${encodeURIComponent(
          urlFacId
        )}&authorized=${encodeURIComponent(currentSession.scopeId)}`
      );
      return;
    }

    const facilityToQuery = currentSession?.scopeId || 'FAC0001';
    loadData(facilityToQuery);
  }, [searchParams, router]);

  // Determine overall facility risk level for top banner
  const overallRisk = useMemo(() => {
    if (!forecast) return 'Healthy';
    if (forecast.risk_counts.critical > 0) return 'Critical';
    if (forecast.risk_counts.warning > 0) return 'Warning';
    if (forecast.risk_counts.watch > 0) return 'Watch';
    return 'Healthy';
  }, [forecast]);

  // Filtered commodities list
  const displayedForecasts = useMemo(() => {
    if (!forecast?.forecasts) return [];
    return forecast.forecasts
      .filter((item) => {
        if (stockFilter === 'Critical') return item.risk_flag.toLowerCase() === 'critical';
        if (stockFilter === 'Warning') return ['warning', 'watch'].includes(item.risk_flag.toLowerCase());
        if (stockFilter === 'Healthy') return item.risk_flag.toLowerCase() === 'healthy';
        return true;
      })
      .filter((item) => {
        if (!searchQuery.trim()) return true;
        const q = searchQuery.toLowerCase();
        return (
          item.commodity_name.toLowerCase().includes(q) ||
          item.category.toLowerCase().includes(q)
        );
      });
  }, [forecast, stockFilter, searchQuery]);

  // Filtered surplus donor matches based on selected countdown commodity
  const filteredSurplusMatches = useMemo(() => {
    if (!matches?.matches) return [];
    if (!selectedCommodityFilter) return matches.matches;
    return matches.matches.filter((m) => m.commodity_id === selectedCommodityFilter.id);
  }, [matches, selectedCommodityFilter]);

  // Handle click on medicine countdown card
  const handleCountdownCardClick = (item: {
    commodity_id: string;
    commodity_name: string;
    risk_flag: string;
    days_until_stockout: number | null;
  }) => {
    const isHealthy = item.risk_flag.toLowerCase() === 'healthy';
    if (isHealthy) {
      setHealthyNotice(
        `"${item.commodity_name}" buffer is healthy (${
          item.days_until_stockout !== null ? `${item.days_until_stockout} days` : '>90 days'
        }). No surplus transfer required.`
      );
      setTimeout(() => {
        setHealthyNotice((prev) => (prev?.includes(item.commodity_name) ? null : prev));
      }, 4500);
      return;
    }

    setSelectedCommodityFilter({ id: item.commodity_id, name: item.commodity_name });
    const el = document.getElementById('nearby-surplus-finder');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Open modal with pre-filled match data
  const handleOpenTransferModal = (match: SurplusMatchItem) => {
    setSelectedMatch(match);
    setRequestQty(match.recommended_quantity || match.available_surplus_units || 50);
    setRequestOfficer(session?.userName || `Pharmacy Officer (${activeFacilityName})`);
    setRequestReason(
      `Emergency stockout prevention: ${activeFacilityName} urgently requires ${match.commodity_name}.`
    );
    setSubmittedTransfer(null);
  };

  // Submit transfer request to backend
  const handleSubmitTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMatch || !forecast) return;

    try {
      setIsSubmitting(true);
      const record = await createTransferRequest({
        source_facility_id: selectedMatch.source_facility_id,
        destination_facility_id: forecast.facility_id,
        commodity_id: selectedMatch.commodity_id,
        requested_quantity: requestQty,
        recommended_quantity: selectedMatch.recommended_quantity,
        requested_by: requestOfficer,
        reason: requestReason,
      });

      setSubmittedTransfer(record);
      // Refresh surplus matches in background
      getNearbySurplusMatches(forecast.facility_id).then(setMatches).catch(() => {});
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to submit transfer request';
      alert(`Transfer submission error: ${msg}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <ShellLayout session={session}>
      <div className="space-y-6">
        {/* 1. DYNAMIC TOP ALERT BANNER (Unmissable Status Check) */}
        {!loading && !error && forecast && (
          <div
            className={`p-4 sm:p-5 rounded-2xl border shadow-sm flex items-start space-x-3.5 transition-all ${
              overallRisk === 'Critical'
                ? 'bg-red-50 border-red-300 text-red-950'
                : overallRisk === 'Warning'
                ? 'bg-amber-50 border-amber-300 text-amber-950'
                : 'bg-emerald-50 border-emerald-300 text-emerald-950'
            }`}
          >
            <div className="flex-shrink-0 mt-0.5">
              {overallRisk === 'Critical' && (
                <div className="p-2 rounded-xl bg-red-100 text-red-700">
                  <AlertTriangle className="w-6 h-6" />
                </div>
              )}
              {overallRisk === 'Warning' && (
                <div className="p-2 rounded-xl bg-amber-100 text-amber-700">
                  <Clock className="w-6 h-6" />
                </div>
              )}
              {overallRisk === 'Healthy' && (
                <div className="p-2 rounded-xl bg-emerald-100 text-emerald-700">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
              )}
            </div>

            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <span
                  className={`px-2 py-0.5 rounded text-[11px] font-black uppercase tracking-wider ${
                    overallRisk === 'Critical'
                      ? 'bg-red-200 text-red-900'
                      : overallRisk === 'Warning'
                      ? 'bg-amber-200 text-amber-900'
                      : 'bg-emerald-200 text-emerald-900'
                  }`}
                >
                  Facility Status: {overallRisk.toUpperCase()}
                </span>
                <span className="text-xs font-semibold text-slate-500">
                  Updated: {forecast.inventory_date}
                </span>
              </div>

              <h2 className="text-base sm:text-lg font-black mt-1">
                {overallRisk === 'Critical' &&
                  `CRITICAL STOCKOUT WARNING: ${forecast.risk_counts.critical} essential medicines will run out within 30 days.`}
                {overallRisk === 'Warning' &&
                  `ATTENTION: ${forecast.risk_counts.warning} medicines have declining safety buffers (31 to 60 days).`}
                {overallRisk === 'Healthy' &&
                  'ALL ESSENTIAL MEDICINES HEALTHY: Adequate safety buffer across all monitored commodities.'}
              </h2>

              <p className="text-xs sm:text-sm mt-0.5 leading-relaxed opacity-90">
                {overallRisk === 'Critical' &&
                  'Immediate clinical action recommended. Use the Nearby Surplus Finder below to request stock from neighboring facilities before local stocks deplete completely.'}
                {overallRisk === 'Warning' &&
                  'Monitor daily burn rates and verify impending delivery schedules with the County Pharmacist.'}
                {overallRisk === 'Healthy' &&
                  'No immediate stockout danger detected over the 90-day predictive horizon.'}
              </p>
            </div>
          </div>
        )}

        {/* Facility Header & Quick Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-2 border-b border-slate-200">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-100 text-purple-800 uppercase tracking-wide">
                Facility Operational Workspace
              </span>
              <span className="text-xs text-slate-500 font-medium">
                ID: <strong className="font-mono text-slate-800">{activeFacilityId}</strong>
              </span>
            </div>
            <h1 className="text-2xl font-black text-slate-900 mt-1">
              {activeFacilityName}
            </h1>
            <p className="text-xs text-slate-500">
              County: <strong className="text-slate-700">{forecast?.county || 'Nairobi'}</strong> &bull; Non-technical operational status check
            </p>
          </div>

          <div className="mt-3 sm:mt-0 flex items-center space-x-2">
            <button
              onClick={() => loadData(activeFacilityId)}
              disabled={loading}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-bold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 shadow-xs transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh Status</span>
            </button>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="py-20 text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-purple-600 border-t-transparent mb-3"></div>
            <p className="text-sm font-bold text-slate-700">Checking Pharmacy Stock Levels...</p>
            <p className="text-xs text-slate-500">Simulating 30/60/90-day depletion rates and searching nearby donors</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-center space-y-3">
            <ShieldAlert className="w-8 h-8 text-red-600 mx-auto" />
            <h3 className="text-base font-bold text-red-900">Unable to Load Facility Stock</h3>
            <p className="text-xs text-red-700 max-w-md mx-auto">{error}</p>
            <button
              onClick={() => loadData(activeFacilityId)}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-lg shadow"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && forecast && (
          <div className="space-y-8">
            {/* 2. STOCK STATUS & DAYS-OF-STOCK PROGRESS BARS */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-5">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 pb-3 border-b border-slate-100">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">
                    Medicine Stock Status &amp; Days-of-Stock Countdown
                  </h2>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Visual countdown buffers before runout &bull; No complex chart axes to interpret
                  </p>
                </div>

                {/* Filter and Search Controls */}
                <div className="flex flex-wrap items-center gap-2">
                  <div className="relative">
                    <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                    <input
                      type="text"
                      placeholder="Search medicine..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-purple-500 w-36 sm:w-44"
                    />
                  </div>

                  <div className="flex items-center bg-slate-100 p-1 rounded-lg text-xs font-semibold">
                    <button
                      onClick={() => setStockFilter('ALL')}
                      className={`px-2.5 py-1 rounded-md transition ${
                        stockFilter === 'ALL'
                          ? 'bg-white text-slate-900 shadow-xs font-bold'
                          : 'text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      All ({forecast.risk_counts.total})
                    </button>
                    <button
                      onClick={() => setStockFilter('Critical')}
                      className={`px-2.5 py-1 rounded-md transition ${
                        stockFilter === 'Critical'
                          ? 'bg-red-600 text-white shadow-xs font-bold'
                          : 'text-red-700 hover:bg-red-50'
                      }`}
                    >
                      Critical ({forecast.risk_counts.critical})
                    </button>
                    <button
                      onClick={() => setStockFilter('Warning')}
                      className={`px-2.5 py-1 rounded-md transition ${
                        stockFilter === 'Warning'
                          ? 'bg-amber-600 text-white shadow-xs font-bold'
                          : 'text-amber-700 hover:bg-amber-50'
                      }`}
                    >
                      Warning ({forecast.risk_counts.warning + forecast.risk_counts.watch})
                    </button>
                    <button
                      onClick={() => setStockFilter('Healthy')}
                      className={`px-2.5 py-1 rounded-md transition ${
                        stockFilter === 'Healthy'
                          ? 'bg-emerald-600 text-white shadow-xs font-bold'
                          : 'text-emerald-700 hover:bg-emerald-50'
                      }`}
                    >
                      Healthy ({forecast.risk_counts.healthy})
                    </button>
                  </div>
                </div>
              </div>

              {/* Healthy Feedback Notice */}
              {healthyNotice && (
                <div className="p-3 bg-emerald-50 border border-emerald-300 rounded-xl text-xs text-emerald-900 flex items-center justify-between shadow-xs animate-fadeIn">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    <span className="font-medium">{healthyNotice}</span>
                  </div>
                  <button
                    onClick={() => setHealthyNotice(null)}
                    className="text-emerald-700 hover:text-emerald-900 ml-2"
                    title="Dismiss"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}

              {/* Grid of Medicine Countdown Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                {displayedForecasts.map((item) => {
                  const days = item.days_until_stockout;
                  const isCritical = item.risk_flag.toLowerCase() === 'critical';
                  const isWarning = item.risk_flag.toLowerCase() === 'warning';
                  const isWatch = item.risk_flag.toLowerCase() === 'watch';
                  const isHealthy = item.risk_flag.toLowerCase() === 'healthy';
                  const isSelected = selectedCommodityFilter?.id === item.commodity_id;

                  // Calculate countdown bar percentage (max 90 days)
                  const barPct = days !== null ? Math.min(100, Math.max(5, (days / 90) * 100)) : 100;
                  const barColor = isCritical
                    ? 'bg-red-500'
                    : isWarning
                    ? 'bg-amber-500'
                    : isWatch
                    ? 'bg-blue-500'
                    : 'bg-emerald-500';

                  const badgeClass = isCritical
                    ? 'bg-red-100 text-red-800 border-red-300'
                    : isWarning
                    ? 'bg-amber-100 text-amber-800 border-amber-300'
                    : isWatch
                    ? 'bg-blue-100 text-blue-800 border-blue-300'
                    : 'bg-emerald-100 text-emerald-800 border-emerald-300';

                  return (
                    <div
                      key={item.commodity_id}
                      onClick={() => handleCountdownCardClick(item)}
                      className={`p-4 rounded-xl border transition-all cursor-pointer group ${
                        isSelected
                          ? 'ring-2 ring-purple-600 border-purple-600 bg-purple-50/30 shadow-sm'
                          : isCritical
                          ? 'border-red-200 bg-red-50/20 hover:border-red-400 hover:shadow-xs'
                          : isWarning
                          ? 'border-amber-200 bg-amber-50/20 hover:border-amber-400 hover:shadow-xs'
                          : 'border-slate-200 bg-white hover:border-slate-400 hover:shadow-xs'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h3 className="text-sm font-bold text-slate-900 leading-snug group-hover:text-purple-900 transition">
                            {item.commodity_name}
                          </h3>
                          <p className="text-xs text-slate-500 font-medium mt-0.5">
                            Category: {item.category}
                          </p>
                        </div>

                        <span className={`px-2 py-0.5 rounded text-[11px] font-black border uppercase tracking-wider flex-shrink-0 ${badgeClass}`}>
                          {item.risk_flag}
                        </span>
                      </div>

                      {/* Visual Days-of-Stock Countdown Progress Bar */}
                      <div className="mt-3.5 space-y-1">
                        <div className="flex items-baseline justify-between text-xs">
                          <span className="font-extrabold text-slate-800">
                            {days !== null ? `${days} Days of Stock Remaining` : 'Safe Buffer (>90 Days)'}
                          </span>
                          <span className="text-slate-500 font-mono text-[11px]">
                            {item.predicted_stockout_date ? `Runs out: ${item.predicted_stockout_date}` : 'No stockout'}
                          </span>
                        </div>

                        {/* The countdown bar */}
                        <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden border border-slate-200/60">
                          <div
                            style={{ width: `${barPct}%` }}
                            className={`h-full ${barColor} transition-all duration-300 rounded-full`}
                          />
                        </div>
                      </div>

                      {/* Stock units and daily burn rate */}
                      <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
                        <span>
                          Current Stock: <strong className="text-slate-900 font-mono">{item.current_stock_level.toLocaleString()} units</strong>
                        </span>
                        <span>
                          Burn Rate: <strong className="text-slate-700 font-mono">{item.recent_daily_consumption.toFixed(1)}/day</strong>
                        </span>
                      </div>

                      {/* Action Hint */}
                      <div className="mt-2 pt-1.5 border-t border-slate-100/70 flex items-center justify-end text-[11px]">
                        {!isHealthy ? (
                          <span className={`inline-flex items-center space-x-1 font-bold ${
                            isSelected ? 'text-purple-700' : 'text-slate-500 group-hover:text-purple-700'
                          } transition`}>
                            <span>{isSelected ? 'Filtered in Surplus Finder below' : 'Find nearby donors'}</span>
                            <ArrowDown className="w-3 h-3" />
                          </span>
                        ) : (
                          <span className="text-emerald-700 font-medium inline-flex items-center space-x-1">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Buffer safe (&gt;90 days)</span>
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* 3. NEARBY SURPLUS FINDER (Plain-Language Conversational Sentences) */}
            <div id="nearby-surplus-finder" className="bg-white rounded-2xl border-2 border-purple-200 shadow-xs p-6 space-y-5 scroll-mt-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-slate-100 gap-2">
                <div>
                  <div className="flex items-center space-x-2">
                    <h2 className="text-lg font-bold text-slate-900">
                      Nearby Surplus Finder
                    </h2>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-100 text-purple-800">
                      {selectedCommodityFilter
                        ? `${filteredSurplusMatches.length} Donor${filteredSurplusMatches.length === 1 ? '' : 's'} for ${selectedCommodityFilter.name}`
                        : `${matches?.matches_found ?? 0} Donors Available`}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Neighboring healthcare facilities with confirmed excess inventory (&ge;45 days buffer) calculated via real geodesic distance.
                  </p>
                </div>
              </div>

              {/* Active Commodity Filter Banner */}
              {selectedCommodityFilter && (
                <div className="p-3 bg-purple-50 border border-purple-200 rounded-xl flex items-center justify-between text-xs animate-fadeIn">
                  <div className="flex items-center space-x-2">
                    <Filter className="w-3.5 h-3.5 text-purple-700" />
                    <span className="font-bold text-purple-900">Filtered for:</span>
                    <span className="font-black bg-purple-200 text-purple-950 px-2 py-0.5 rounded font-mono">
                      {selectedCommodityFilter.name}
                    </span>
                    <span className="text-purple-700 font-medium">
                      ({filteredSurplusMatches.length} candidate{filteredSurplusMatches.length === 1 ? '' : 's'})
                    </span>
                  </div>
                  <button
                    onClick={() => setSelectedCommodityFilter(null)}
                    className="inline-flex items-center space-x-1 text-xs font-bold text-purple-700 hover:text-purple-950 bg-white border border-purple-200 hover:border-purple-300 px-2.5 py-1 rounded-lg shadow-2xs transition"
                  >
                    <X className="w-3.5 h-3.5" />
                    <span>Show All Donors</span>
                  </button>
                </div>
              )}

              {/* Conversational Match List */}
              {filteredSurplusMatches.length > 0 ? (
                <div className="space-y-3">
                  {filteredSurplusMatches.slice(0, 8).map((m, idx) => (
                    <div
                      key={`${m.source_facility_id}-${m.commodity_id}-${idx}`}
                      className="p-4 bg-slate-50 border border-slate-200 hover:border-purple-300 rounded-xl transition-all flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3"
                    >
                      {/* Plain Language Sentence */}
                      <div className="space-y-1 flex-1">
                        <p className="text-sm font-bold text-slate-900 leading-snug">
                          <span className="text-purple-900 underline decoration-purple-300 font-black">{m.source_facility_name}</span>
                          , located <span className="text-blue-700 font-black">{m.distance_km} km</span> away in {m.source_county} County, has <span className="text-emerald-700 font-black">{m.available_surplus_units} units</span> of {m.commodity_name} to spare.
                        </p>
                        <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-500 pt-0.5">
                          <span className="bg-white px-2 py-0.5 rounded border border-slate-200 font-mono">
                            Donor Stock Buffer: {m.source_days_of_stock.toFixed(0)} days
                          </span>
                          <span className="bg-white px-2 py-0.5 rounded border border-slate-200 font-mono">
                            Rec. Batch: {m.recommended_quantity} units
                          </span>
                          <span className="bg-white px-2 py-0.5 rounded border border-slate-200 text-emerald-800 font-semibold">
                            Est. Value: KES {m.transfer_value_kes.toLocaleString()}
                          </span>
                        </div>
                      </div>

                      {/* Request Transfer Action Button */}
                      <div className="flex-shrink-0">
                        <button
                          onClick={() => handleOpenTransferModal(m)}
                          className="w-full sm:w-auto inline-flex items-center justify-center space-x-1.5 px-4 py-2 bg-purple-700 hover:bg-purple-800 text-white text-xs font-bold rounded-lg shadow-xs transition active:scale-95"
                        >
                          <ArrowLeftRight className="w-3.5 h-3.5" />
                          <span>Request Transfer</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center text-xs text-slate-500 bg-slate-50 rounded-xl border border-dashed border-slate-200 space-y-2">
                  <p className="font-semibold text-slate-700">
                    {selectedCommodityFilter
                      ? `No nearby surplus donors currently found for "${selectedCommodityFilter.name}".`
                      : 'No neighboring surplus matches found within 400 km transport radius.'}
                  </p>
                  {selectedCommodityFilter && (
                    <div>
                      <p className="text-slate-500 text-[11px] mb-2">
                        Other facilities in this network are maintaining essential reserves for this medicine.
                      </p>
                      <button
                        onClick={() => setSelectedCommodityFilter(null)}
                        className="px-3 py-1.5 bg-white border border-slate-300 text-slate-700 hover:text-slate-900 text-xs font-bold rounded-lg hover:bg-slate-100 shadow-2xs transition"
                      >
                        View All Donors ({matches?.matches_found ?? 0})
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}

        {/* 4. REQUEST TRANSFER MODAL & CONFIRMATION STATE */}
        {selectedMatch && (
          <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-lg w-full p-6 space-y-5 animate-fadeIn">
              {!submittedTransfer ? (
                // Form View
                <form onSubmit={handleSubmitTransfer} className="space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                    <div>
                      <h3 className="text-base font-bold text-slate-900">
                        Request Inter-Facility Transfer
                      </h3>
                      <p className="text-xs text-slate-500">
                        Submits request to County Health Department for authorization
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setSelectedMatch(null)}
                      className="text-slate-400 hover:text-slate-700"
                    >
                      <X className="w-5 h-5" />
                    </button>
                  </div>

                  {/* Transfer Summary Header */}
                  <div className="p-3 bg-purple-50 rounded-xl border border-purple-200 text-xs space-y-1">
                    <div className="font-bold text-purple-950">
                      Medicine: {selectedMatch.commodity_name}
                    </div>
                    <div className="text-purple-800">
                      Donor: <strong>{selectedMatch.source_facility_name}</strong> ({selectedMatch.source_county}) &bull; {selectedMatch.distance_km} km away
                    </div>
                    <div className="text-purple-700">
                      Recipient: <strong>{activeFacilityName}</strong>
                    </div>
                  </div>

                  {/* Quantity Input */}
                  <div className="space-y-1">
                    <label className="block text-xs font-bold uppercase text-slate-700">
                      Requested Transfer Units
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={selectedMatch.available_surplus_units}
                      value={requestQty}
                      onChange={(e) => setRequestQty(Number(e.target.value))}
                      required
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                    <p className="text-[11px] text-slate-500">
                      Max available donor surplus: {selectedMatch.available_surplus_units} units (Recommended: {selectedMatch.recommended_quantity} units)
                    </p>
                  </div>

                  {/* Officer Name */}
                  <div className="space-y-1">
                    <label className="block text-xs font-bold uppercase text-slate-700">
                      Requesting Officer
                    </label>
                    <input
                      type="text"
                      value={requestOfficer}
                      onChange={(e) => setRequestOfficer(e.target.value)}
                      required
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>

                  {/* Reason Note */}
                  <div className="space-y-1">
                    <label className="block text-xs font-bold uppercase text-slate-700">
                      Clinical Rationale / Notes
                    </label>
                    <textarea
                      rows={2}
                      value={requestReason}
                      onChange={(e) => setRequestReason(e.target.value)}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs focus:ring-2 focus:ring-purple-500 focus:outline-none"
                    />
                  </div>

                  {/* Buttons */}
                  <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100">
                    <button
                      type="button"
                      onClick={() => setSelectedMatch(null)}
                      className="px-3.5 py-2 rounded-lg text-xs font-bold text-slate-600 hover:bg-slate-100 transition"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="inline-flex items-center space-x-1.5 px-4 py-2 bg-purple-700 hover:bg-purple-800 text-white text-xs font-bold rounded-lg shadow-xs transition active:scale-95 disabled:opacity-50"
                    >
                      <Send className="w-3.5 h-3.5" />
                      <span>{isSubmitting ? 'Submitting...' : 'Submit Transfer Request'}</span>
                    </button>
                  </div>
                </form>
              ) : (
                // Success Confirmation View
                <div className="text-center py-4 space-y-4">
                  <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
                    <CheckCircle className="w-7 h-7" />
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-slate-900">
                      Transfer Request Successfully Dispatched!
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Request ID: <strong className="font-mono text-purple-700">{submittedTransfer.request_id}</strong>
                    </p>
                  </div>

                  <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl text-left text-xs space-y-1.5">
                    <div>
                      Medicine: <strong className="text-slate-900">{submittedTransfer.commodity_name}</strong>
                    </div>
                    <div>
                      Quantity: <strong className="text-slate-900">{submittedTransfer.requested_quantity} units</strong>
                    </div>
                    <div>
                      Donor Facility: <strong className="text-slate-900">{submittedTransfer.source_facility_name}</strong> ({submittedTransfer.source_county})
                    </div>
                    <div className="pt-1 border-t border-slate-200 text-slate-600 italic">
                      Status: <strong className="text-amber-700 uppercase">{submittedTransfer.status}</strong> &bull; Dispatched to County Health Department approval queue.
                    </div>
                  </div>

                  <button
                    onClick={() => setSelectedMatch(null)}
                    className="w-full py-2.5 px-4 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs rounded-xl shadow-xs transition"
                  >
                    Done
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </ShellLayout>
  );
}

export default function FacilityDashboardPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-slate-500">Loading Facility Operational View...</div>}>
      <FacilityDashboardContent />
    </Suspense>
  );
}
