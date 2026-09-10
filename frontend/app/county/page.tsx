'use client';

import React, { useEffect, useState, useMemo, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import ShellLayout from '@/components/ShellLayout';
import CountyDebtTrendChart from '@/components/CountyDebtTrendChart';
import { getClientSession, UserSession } from '@/lib/auth';
import {
  getCountyScorecard,
  getCountyScorecardHistory,
  getCountyForecast,
  getFacilityForecast,
  getNearbySurplusMatches,
  getPendingTransfers,
  getFacilities,
  approveTransfer,
  rejectTransfer,
  createTransferRequest,
  CountyScorecardDetail,
  CountyHistoryItem,
  CountyForecastResponse,
  FacilityForecastResponse,
  SurplusMatchesResponse,
  SurplusMatchItem,
  FacilitySummary,
  TransferRequestRecord,
} from '@/lib/api';
import {
  Building2,
  CheckCircle2,
  FileText,
  ShieldAlert,
  RefreshCw,
  Clock,
  Inbox,
  ChevronDown,
  ChevronUp,
  Check,
  X,
  Hospital,
  PlusCircle,
  Bell,
  CheckCircle,
  ArrowLeftRight,
  ArrowRight,
  AlertTriangle,
  Send,
} from 'lucide-react';

function CountyDashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [session, setSession] = useState<UserSession | null>(null);
  const [scorecard, setScorecard] = useState<CountyScorecardDetail | null>(null);
  const [scorecardHistory, setScorecardHistory] = useState<CountyHistoryItem[]>([]);
  const [forecast, setForecast] = useState<CountyForecastResponse | null>(null);
  const [pendingTransfers, setPendingTransfers] = useState<TransferRequestRecord[]>([]);
  const [facilities, setFacilities] = useState<FacilitySummary[]>([]);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // UI States
  const [showWhyFactors, setShowWhyFactors] = useState<boolean>(false);
  const [facilitySortBy, setFacilitySortBy] = useState<'risk' | 'name'>('risk');
  const [actionFeedback, setActionFeedback] = useState<{ id: string; message: string; type: 'success' | 'danger' } | null>(null);
  const [isProcessingAction, setIsProcessingAction] = useState<string | null>(null);

  // Task 3: Inline Accordion state for Facility Roster
  const [expandedFacilityId, setExpandedFacilityId] = useState<string | null>(null);
  const [facilityForecastCache, setFacilityForecastCache] = useState<Record<string, FacilityForecastResponse>>({});
  const [loadingFacilityId, setLoadingFacilityId] = useState<string | null>(null);

  // Task 4: Fast-Track Match Modal state for Critical Alerts
  const [fastTrackTarget, setFastTrackTarget] = useState<{
    facility_id: string;
    facility_name: string;
    commodity_id?: string;
    commodity_name?: string;
    alert_message?: string;
    days_until_stockout?: number;
  } | null>(null);
  const [fastTrackMatches, setFastTrackMatches] = useState<SurplusMatchesResponse | null>(null);
  const [fastTrackLoading, setFastTrackLoading] = useState<boolean>(false);
  const [isSubmittingFastTrack, setIsSubmittingFastTrack] = useState<boolean>(false);
  const [fastTrackQty, setFastTrackQty] = useState<number>(100);

  const activeCounty = session?.scopeId || 'Kiambu';

  const loadData = async (county: string) => {
    try {
      setLoading(true);
      setError(null);
      const [scorecardData, historyData, forecastData, transfersData, countyFacilities] = await Promise.all([
        getCountyScorecard(county),
        getCountyScorecardHistory(county),
        getCountyForecast(county),
        getPendingTransfers(county),
        getFacilities(county),
      ]);
      setScorecard(scorecardData);
      setScorecardHistory(historyData);
      setForecast(forecastData);
      setPendingTransfers(transfersData.requests || []);
      setFacilities(countyFacilities);
    } catch (err: unknown) {
      console.error('Error fetching county data:', err);
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
    const urlCounty = searchParams.get('county');
    if (urlCounty && currentSession?.scopeId && urlCounty.toLowerCase() !== currentSession.scopeId.toLowerCase()) {
      router.replace(
        `/access-denied?reason=county_scope_violation&attempted=${encodeURIComponent(
          urlCounty
        )}&authorized=${encodeURIComponent(currentSession.scopeId)}`
      );
      return;
    }

    const countyToQuery = currentSession?.scopeId || 'Kiambu';
    loadData(countyToQuery);
  }, [searchParams, router]);

  // Combined county facility list with forecast highest risk flags
  const facilitiesWithRisk = useMemo(() => {
    const forecastMap = new Map<string, { highest_risk_flag: string; critical_count: number; warning_count: number; healthy_count: number }>();
    if (forecast?.facilities) {
      for (const f of forecast.facilities) {
        forecastMap.set(f.facility_id, {
          highest_risk_flag: f.highest_risk_flag,
          critical_count: f.critical_count,
          warning_count: f.warning_count,
          healthy_count: f.healthy_count,
        });
      }
    }

    const priority: Record<string, number> = {
      Critical: 4,
      Warning: 3,
      Watch: 2,
      Healthy: 1,
    };

    return facilities.map((f) => {
      const riskInfo = forecastMap.get(f.facility_id) || {
        highest_risk_flag: 'Healthy',
        critical_count: 0,
        warning_count: 0,
        healthy_count: 0,
      };
      return {
        ...f,
        ...riskInfo,
      };
    }).sort((a, b) => {
      if (facilitySortBy === 'risk') {
        const pA = priority[a.highest_risk_flag] || 0;
        const pB = priority[b.highest_risk_flag] || 0;
        if (pA !== pB) return pB - pA;
        return a.facility_name.localeCompare(b.facility_name);
      }
      return a.facility_name.localeCompare(b.facility_name);
    });
  }, [facilities, forecast, facilitySortBy]);

  // Action: Approve Transfer Request
  const handleApprove = async (requestId: string) => {
    try {
      setIsProcessingAction(requestId);
      const reviewer = session?.userName || `County Health Director (${activeCounty})`;
      await approveTransfer(requestId, { reviewed_by: reviewer });
      // Remove from pending list immediately
      setPendingTransfers((prev) => prev.filter((r) => r.request_id !== requestId));
      setActionFeedback({
        id: requestId,
        message: `Transfer ${requestId} approved successfully and dispatched!`,
        type: 'success',
      });
      setTimeout(() => setActionFeedback(null), 5000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to approve transfer request';
      alert(`Approval error: ${msg}`);
    } finally {
      setIsProcessingAction(null);
    }
  };

  // Action: Reject Transfer Request
  const handleReject = async (requestId: string) => {
    try {
      setIsProcessingAction(requestId);
      const reviewer = session?.userName || `County Health Director (${activeCounty})`;
      await rejectTransfer(requestId, { reviewed_by: reviewer });
      // Remove from pending list immediately
      setPendingTransfers((prev) => prev.filter((r) => r.request_id !== requestId));
      setActionFeedback({
        id: requestId,
        message: `Transfer ${requestId} rejected.`,
        type: 'danger',
      });
      setTimeout(() => setActionFeedback(null), 5000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to reject transfer request';
      alert(`Rejection error: ${msg}`);
    } finally {
      setIsProcessingAction(null);
    }
  };

  // Action: Seed a test transfer request for interactive verification
  const handleCreateTestRequest = async () => {
    try {
      if (facilities.length === 0) {
        alert('No facilities found in this county to create a test transfer.');
        return;
      }
      const source = facilities[0];
      const dest = facilities.length > 1 ? facilities[1] : { facility_id: 'FAC0001', facility_name: 'Nairobi Referral' };

      const newReq = await createTransferRequest({
        source_facility_id: source.facility_id,
        destination_facility_id: dest.facility_id,
        commodity_id: 'COM001',
        requested_quantity: 100,
        recommended_quantity: 100,
        requested_by: `Pharmacist (${dest.facility_name})`,
        reason: `Urgent inter-facility stockout buffer rebalance for ${activeCounty} County.`,
      });

      setPendingTransfers((prev) => [newReq, ...prev]);
      setActionFeedback({
        id: newReq.request_id,
        message: `Created test request ${newReq.request_id}. Ready for Approve/Reject test.`,
        type: 'success',
      });
      setTimeout(() => setActionFeedback(null), 5000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create test request';
      alert(`Error creating test transfer: ${msg}`);
    }
  };

  // Task 3: Toggle Facility Roster Accordion
  const handleToggleFacility = async (facilityId: string) => {
    if (expandedFacilityId === facilityId) {
      setExpandedFacilityId(null);
      return;
    }
    setExpandedFacilityId(facilityId);
    if (!facilityForecastCache[facilityId]) {
      try {
        setLoadingFacilityId(facilityId);
        const res = await getFacilityForecast(facilityId);
        setFacilityForecastCache((prev) => ({ ...prev, [facilityId]: res }));
      } catch (err) {
        console.error('Error fetching facility forecast:', err);
      } finally {
        setLoadingFacilityId(null);
      }
    }
  };

  // Task 4: Open Fast-Track Match Modal for an alert or at-risk drug
  const handleOpenFastTrackModal = async (target: {
    facility_id: string;
    facility_name: string;
    commodity_id?: string;
    commodity_name?: string;
    alert_message?: string;
    days_until_stockout?: number;
  }) => {
    setFastTrackTarget(target);
    setFastTrackLoading(true);
    setFastTrackMatches(null);
    try {
      const res = await getNearbySurplusMatches(target.facility_id, target.commodity_id);
      setFastTrackMatches(res);
      if (res?.matches && res.matches.length > 0) {
        setFastTrackQty(res.matches[0].recommended_quantity || res.matches[0].available_surplus_units || 100);
      }
    } catch (err) {
      console.error('Error fetching surplus matches for alert:', err);
    } finally {
      setFastTrackLoading(false);
    }
  };

  // Task 4: Submit Fast-Track Transfer Request
  const handleConfirmFastTrackTransfer = async (match: SurplusMatchItem) => {
    if (!fastTrackTarget) return;
    try {
      setIsSubmittingFastTrack(true);
      const reviewer = session?.userName || `County Health Director (${activeCounty})`;
      const record = await createTransferRequest({
        source_facility_id: match.source_facility_id,
        destination_facility_id: fastTrackTarget.facility_id,
        commodity_id: match.commodity_id,
        requested_quantity: fastTrackQty,
        recommended_quantity: match.recommended_quantity,
        requested_by: reviewer,
        reason: fastTrackTarget.alert_message || `Fast-track redistribution to resolve critical stockout of ${match.commodity_name} at ${fastTrackTarget.facility_name}.`,
      });

      // Add to pending transfers queue
      setPendingTransfers((prev) => [record, ...prev]);
      setActionFeedback({
        id: record.request_id,
        message: `Fast-track transfer request ${record.request_id} created and dispatched to Decision Queue!`,
        type: 'success',
      });
      setFastTrackTarget(null);
      setTimeout(() => setActionFeedback(null), 6000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create fast-track transfer';
      alert(`Fast-track submission error: ${msg}`);
    } finally {
      setIsSubmittingFastTrack(false);
    }
  };

  const getTierColorClass = (tier?: string) => {
    switch (tier?.toLowerCase()) {
      case 'high':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'medium':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      default:
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
    }
  };

  const getRiskBadgeClass = (flag: string) => {
    switch (flag.toLowerCase()) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'warning':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'watch':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
    }
  };

  return (
    <ShellLayout session={session}>
      <div className="space-y-8">
        {/* County Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between pb-4 border-b border-slate-200">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800 uppercase tracking-wide">
                County Operations Workspace
              </span>
              <span className="text-xs text-slate-500 font-medium">
                Scope: <strong className="text-slate-900">{activeCounty} County</strong>
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-black text-slate-900 mt-1.5 tracking-tight">
              {activeCounty} County Health Department
            </h1>
            <p className="text-sm text-slate-600 mt-0.5">
              Financial risk diagnostics, inter-facility redistribution approvals, and stockout alert triage.
            </p>
          </div>

          <div className="mt-4 md:mt-0 flex items-center space-x-2.5">
            <button
              onClick={() => loadData(activeCounty)}
              disabled={loading}
              className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-bold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 shadow-xs transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh County Data</span>
            </button>
          </div>
        </div>

        {/* Action Feedback Toast Banner */}
        {actionFeedback && (
          <div
            className={`p-4 rounded-xl border flex items-center justify-between text-xs font-bold transition-all shadow-sm ${
              actionFeedback.type === 'success'
                ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
                : 'bg-red-50 border-red-300 text-red-900'
            }`}
          >
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span>{actionFeedback.message}</span>
            </div>
            <button
              onClick={() => setActionFeedback(null)}
              className="text-slate-400 hover:text-slate-700"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="py-20 text-center">
            <div className="inline-block animate-spin rounded-full h-9 w-9 border-4 border-blue-600 border-t-transparent mb-3"></div>
            <p className="text-sm font-bold text-slate-700">Loading {activeCounty} County Operational Feed...</p>
            <p className="text-xs text-slate-500">Querying financial risk scorecard, local facility roster, and pending transfer queue</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-center space-y-3">
            <ShieldAlert className="w-8 h-8 text-red-600 mx-auto" />
            <h3 className="text-base font-bold text-red-900">Backend Communication Error</h3>
            <p className="text-xs text-red-700 max-w-md mx-auto">{error}</p>
            <button
              onClick={() => loadData(activeCounty)}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-bold rounded-lg shadow"
            >
              Retry
            </button>
          </div>
        )}

        {!loading && !error && scorecard && (
          <>
            {/* 1. COUNTY RISK SCORECARD CARDS */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Card 1: Risk Tier */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-500">
                    <span>Financial Risk Tier</span>
                    <Building2 className="w-4 h-4 text-blue-600" />
                  </div>
                  <div className="mt-3 flex items-center space-x-3">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-black border uppercase tracking-wider ${getTierColorClass(
                        scorecard.risk_tier
                      )}`}
                    >
                      {scorecard.risk_tier} Risk
                    </span>
                    <span className="text-3xl font-black text-slate-900">
                      {scorecard.risk_score.toFixed(1)} <span className="text-xs text-slate-400 font-normal">/ 100</span>
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 mt-2">
                    Primary Driver: <strong className="text-slate-800">{scorecard.primary_driver}</strong>
                  </p>
                </div>
                <div className="mt-3 pt-3 border-t border-slate-100 text-[11px] text-slate-500">
                  Month: <strong className="text-slate-700">{scorecard.month}</strong>
                </div>
              </div>

              {/* Card 2: Outstanding Debt */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-500">
                    <span>Outstanding KEMSA Balance</span>
                    <Clock className="w-4 h-4 text-slate-600" />
                  </div>
                  <div className="mt-3 text-3xl font-black text-slate-900 font-mono">
                    KES {scorecard.amount_owed_kes.toLocaleString()}
                  </div>
                  <p className="text-xs text-slate-600 mt-2">
                    Delinquency: <span className="font-bold text-red-700">{scorecard.days_overdue} days overdue</span>
                  </p>
                </div>
                <div className="mt-3 pt-3 border-t border-slate-100 text-[11px] text-slate-500">
                  Payment History Score: <strong className="text-slate-700">{scorecard.payment_history_score.toFixed(1)} / 100</strong>
                </div>
              </div>

              {/* Card 3: County Facilities */}
              <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-slate-500">
                    <span>Monitored Facilities</span>
                    <Hospital className="w-4 h-4 text-purple-600" />
                  </div>
                  <div className="mt-3 flex items-baseline space-x-2">
                    <span className="text-3xl font-black text-slate-900">
                      {facilities.length}
                    </span>
                    <span className="text-xs font-semibold text-slate-500">hospitals in county</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-2">
                    Total Inventory Pairs: <strong className="text-slate-800">{forecast?.total_pairs ?? 0} pairs</strong>
                  </p>
                </div>
                <div className="mt-3 pt-3 border-t border-slate-100 text-[11px] text-slate-500">
                  Critical Stockouts: <strong className="text-red-600">{forecast?.risk_counts.critical ?? 0} drugs</strong>
                </div>
              </div>

              {/* Card 4: Pending Transfers Queue */}
              <div className="bg-white p-5 rounded-2xl border-2 border-blue-200 shadow-xs flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-blue-700">
                    <span>Pending Transfers Queue</span>
                    <Inbox className="w-4 h-4 text-blue-600" />
                  </div>
                  <div className="mt-3 flex items-baseline space-x-2">
                    <span className="text-3xl font-black text-blue-700">
                      {pendingTransfers.length}
                    </span>
                    <span className="text-xs font-semibold text-slate-500">awaiting decision</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-2">
                    Requires County Pharmacist / Health Director approval.
                  </p>
                </div>
                <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px]">
                  <span className="text-slate-500">Action Required</span>
                  <button
                    onClick={handleCreateTestRequest}
                    className="text-blue-600 font-bold hover:underline"
                  >
                    + Add Test Transfer
                  </button>
                </div>
              </div>
            </div>

            {/* 2. 'WHY' EXPLANATION PANEL (Collapsible & Plain-Language First) */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-3 border-b border-slate-100">
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 rounded-lg bg-blue-50 text-blue-700">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-900">
                      Financial Risk Diagnostic: Why was {scorecard.county} assigned {scorecard.risk_tier} Risk?
                    </h2>
                    <p className="text-xs text-slate-500">
                      Automated explainability decomposing debt volume, delinquency days, and historical payment velocity
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => setShowWhyFactors(!showWhyFactors)}
                  className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-bold text-blue-700 hover:bg-blue-50 transition border border-blue-200"
                >
                  <span>{showWhyFactors ? 'Hide Factor Breakdown' : 'Show Detailed Factors'}</span>
                  {showWhyFactors ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>
              </div>

              {/* Default Visible: Plain-Language Sentence */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-sm font-medium text-slate-800 leading-relaxed">
                {scorecard.plain_language_summary}
              </div>

              {/* Expandable: Factor-by-Factor Detailed Decomposition & 24-Month Velocity Trend */}
              {showWhyFactors && (
                <div className="space-y-4 pt-2 animate-fadeIn">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
                    {scorecard.factors?.map((factor) => (
                      <div
                        key={factor.factor}
                        className="p-4 bg-white border border-slate-200 rounded-xl shadow-2xs space-y-2"
                      >
                        <div className="flex items-center justify-between text-xs font-bold">
                          <span className="text-slate-900">{factor.factor_name}</span>
                          <span className="px-2 py-0.5 rounded text-[10px] bg-blue-50 text-blue-700 border border-blue-200">
                            {factor.weight_pct}% Weight
                          </span>
                        </div>

                        <div className="flex items-baseline justify-between pt-1">
                          <span className="text-lg font-black text-slate-900">{factor.formatted_value}</span>
                          <span
                            className={`text-xs font-bold ${
                              factor.contribution.toLowerCase() === 'high'
                                ? 'text-red-600'
                                : factor.contribution.toLowerCase() === 'medium'
                                ? 'text-amber-600'
                                : 'text-emerald-600'
                            }`}
                          >
                            {factor.contribution} Contribution
                          </span>
                        </div>

                        <p className="text-xs text-slate-500 leading-normal border-t border-slate-100 pt-2">
                          {factor.description}
                        </p>
                      </div>
                    ))}
                  </div>

                  {/* 24-Month Debt & Risk Velocity Diagnosis Chart */}
                  <CountyDebtTrendChart
                    county={activeCounty}
                    data={scorecardHistory}
                    loading={loading}
                  />
                </div>
              )}
            </div>

            {/* 3. REDISTRIBUTION DECISION QUEUE (Approve / Reject Action Cards) */}
            <div className="bg-white rounded-2xl border-2 border-blue-200 shadow-xs p-6 space-y-5">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-slate-100 gap-2">
                <div>
                  <div className="flex items-center space-x-2">
                    <h2 className="text-lg font-bold text-slate-900">
                      Redistribution Decision Queue
                    </h2>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-100 text-blue-800">
                      {pendingTransfers.length} Pending
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Review and authorize inter-facility stock transfers to balance inventory before stockouts occur.
                  </p>
                </div>

                <button
                  onClick={handleCreateTestRequest}
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-bold text-blue-700 bg-blue-50 hover:bg-blue-100 border border-blue-200 rounded-lg transition"
                >
                  <PlusCircle className="w-3.5 h-3.5" />
                  <span>Create Sample Transfer Request</span>
                </button>
              </div>

              {pendingTransfers.length === 0 ? (
                <div className="py-12 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200 space-y-3">
                  <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto" />
                  <h3 className="text-sm font-bold text-slate-800">All Transfers Reviewed</h3>
                  <p className="text-xs text-slate-500 max-w-md mx-auto">
                    There are currently no pending redistribution requests requiring review in {activeCounty} County.
                  </p>
                  <button
                    onClick={handleCreateTestRequest}
                    className="inline-flex items-center space-x-1 px-3 py-1.5 text-xs font-bold text-blue-700 bg-white border border-blue-300 rounded-lg hover:bg-blue-50 shadow-2xs"
                  >
                    <PlusCircle className="w-3.5 h-3.5" />
                    <span>Create Test Transfer to Exercise Workflow</span>
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {pendingTransfers.map((req) => (
                    <div
                      key={req.request_id}
                      className="p-5 bg-white border-2 border-slate-200 rounded-xl shadow-xs hover:border-blue-300 transition-all flex flex-col justify-between space-y-4"
                    >
                      <div className="space-y-3">
                        <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                          <div>
                            <span className="text-xs font-mono font-bold text-blue-700">
                              {req.request_id}
                            </span>
                            <h3 className="text-sm font-bold text-slate-900 mt-0.5">
                              {req.commodity_name}
                            </h3>
                          </div>
                          <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                            Awaiting Review
                          </span>
                        </div>

                        {/* Donor to Recipient Route */}
                        <div className="p-3 bg-slate-50 rounded-lg text-xs space-y-1.5 border border-slate-200">
                          <div className="flex items-center justify-between">
                            <span className="text-slate-500 font-semibold">Donor Facility:</span>
                            <span className="font-bold text-slate-900 truncate max-w-[200px]" title={req.source_facility_name}>
                              {req.source_facility_name} ({req.source_county})
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-slate-500 font-semibold">Recipient Facility:</span>
                            <span className="font-bold text-slate-900 truncate max-w-[200px]" title={req.destination_facility_name}>
                              {req.destination_facility_name} ({req.destination_county})
                            </span>
                          </div>
                          <div className="flex items-center justify-between pt-1 border-t border-slate-200/60 font-mono text-[11px]">
                            <span className="text-slate-500">Haversine Distance:</span>
                            <strong className="text-blue-700">{req.distance_km} km</strong>
                          </div>
                          <div className="flex items-center justify-between font-mono text-[11px]">
                            <span className="text-slate-500">Batch Volume:</span>
                            <strong className="text-emerald-700">{req.requested_quantity} units</strong>
                          </div>
                        </div>

                        {/* Plain Language Rationale */}
                        <div className="text-xs text-slate-600 bg-blue-50/50 p-2.5 rounded-lg border border-blue-100 leading-relaxed italic">
                          &ldquo;{req.reason}&rdquo;
                        </div>
                      </div>

                      {/* Approve / Reject Buttons */}
                      <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100">
                        <button
                          onClick={() => handleApprove(req.request_id)}
                          disabled={isProcessingAction === req.request_id}
                          className="flex items-center justify-center space-x-1.5 py-2.5 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-xs transition active:scale-95 disabled:opacity-50"
                        >
                          <Check className="w-4 h-4" />
                          <span>Approve Transfer</span>
                        </button>

                        <button
                          onClick={() => handleReject(req.request_id)}
                          disabled={isProcessingAction === req.request_id}
                          className="flex items-center justify-center space-x-1.5 py-2.5 px-3 rounded-lg bg-white border border-red-300 hover:bg-red-50 text-red-700 font-bold text-xs shadow-xs transition active:scale-95 disabled:opacity-50"
                        >
                          <X className="w-4 h-4" />
                          <span>Reject</span>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 4. FACILITY LIST & CRITICAL ALERT FEED */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* County Facility Roster */}
              <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-slate-100 gap-2">
                  <div>
                    <h2 className="text-base font-bold text-slate-900">
                      County Health Facility Inventory Roster
                    </h2>
                    <p className="text-xs text-slate-500">
                      Filtered strictly to {activeCounty} County &bull; Cross-referenced with real-time stockout flags
                    </p>
                  </div>

                  {/* Sort Controls */}
                  <div className="flex items-center space-x-1.5 text-xs">
                    <span className="text-slate-500 font-semibold">Sort by:</span>
                    <button
                      onClick={() => setFacilitySortBy('risk')}
                      className={`px-2.5 py-1 rounded-md text-xs font-bold transition ${
                        facilitySortBy === 'risk'
                          ? 'bg-blue-600 text-white shadow-xs'
                          : 'bg-slate-100 text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      Risk Flag
                    </button>
                    <button
                      onClick={() => setFacilitySortBy('name')}
                      className={`px-2.5 py-1 rounded-md text-xs font-bold transition ${
                        facilitySortBy === 'name'
                          ? 'bg-blue-600 text-white shadow-xs'
                          : 'bg-slate-100 text-slate-600 hover:text-slate-900'
                      }`}
                    >
                      Name
                    </button>
                  </div>
                </div>

                <div className="divide-y divide-slate-100">
                  {facilitiesWithRisk.map((f) => {
                    const isExpanded = expandedFacilityId === f.facility_id;
                    const cachedForecast = facilityForecastCache[f.facility_id];
                    const isLoadingThis = loadingFacilityId === f.facility_id;

                    const criticalAndWarning =
                      cachedForecast?.forecasts?.filter((item) =>
                        ['critical', 'warning'].includes(item.risk_flag.toLowerCase())
                      ) || [];

                    return (
                      <div key={f.facility_id} className="py-2.5">
                        <div
                          onClick={() => handleToggleFacility(f.facility_id)}
                          className={`p-2.5 rounded-xl cursor-pointer transition-all flex items-center justify-between gap-3 ${
                            isExpanded ? 'bg-blue-50/70 border border-blue-200' : 'hover:bg-slate-50'
                          }`}
                          title={isExpanded ? 'Click to collapse commodities' : 'Click to expand critical & warning commodities'}
                        >
                          <div className="flex items-center space-x-2.5">
                            <div className="p-1 rounded bg-white shadow-2xs border border-slate-200 text-slate-500">
                              {isExpanded ? <ChevronUp className="w-3.5 h-3.5 text-blue-700" /> : <ChevronDown className="w-3.5 h-3.5" />}
                            </div>
                            <div>
                              <div className="flex items-center space-x-2">
                                <h3 className="text-xs font-bold text-slate-900">{f.facility_name}</h3>
                                <span className="text-[10px] font-mono text-slate-400">[{f.facility_id}]</span>
                              </div>
                              <div className="text-[11px] text-slate-500 mt-0.5">
                                {f.sub_county || 'Central Sub-County'} &bull; Level: {f.facility_level || 'Level 4'}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-0.5 rounded text-[11px] font-black border uppercase ${getRiskBadgeClass(f.highest_risk_flag)}`}>
                              {f.highest_risk_flag}
                            </span>
                            <div className="hidden sm:block text-right text-[11px] text-slate-500">
                              <div>Critical: <strong className="text-red-600">{f.critical_count}</strong></div>
                              <div>Healthy: <strong className="text-emerald-600">{f.healthy_count}</strong></div>
                            </div>
                          </div>
                        </div>

                        {/* Task 3: Inline Accordion Expansion */}
                        {isExpanded && (
                          <div className="mt-2.5 p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-3 animate-fadeIn">
                            <div className="flex items-center justify-between border-b border-slate-200/80 pb-2">
                              <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                                At-Risk Commodities &bull; {f.facility_name}
                              </span>
                              <span className="text-[11px] text-slate-500 font-mono">
                                {criticalAndWarning.length} requiring buffer replenishment
                              </span>
                            </div>

                            {isLoadingThis ? (
                              <div className="py-6 text-center space-y-1">
                                <div className="inline-block animate-spin rounded-full h-5 w-5 border-2 border-blue-600 border-t-transparent" />
                                <p className="text-xs text-slate-500">Checking facility stockout countdowns...</p>
                              </div>
                            ) : criticalAndWarning.length > 0 ? (
                              <div className="space-y-2">
                                {criticalAndWarning.map((item) => (
                                  <div
                                    key={item.commodity_id}
                                    className="p-3 bg-white rounded-lg border border-slate-200 shadow-2xs flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2.5"
                                  >
                                    <div className="space-y-0.5 flex-1">
                                      <div className="flex items-center space-x-2">
                                        <span className="text-xs font-bold text-slate-900">{item.commodity_name}</span>
                                        <span className="text-[10px] text-slate-400 capitalize">({item.category})</span>
                                        <span
                                          className={`px-1.5 py-0.2 rounded text-[10px] font-black uppercase border ${
                                            item.risk_flag.toLowerCase() === 'critical'
                                              ? 'bg-red-100 text-red-800 border-red-200'
                                              : 'bg-amber-100 text-amber-800 border-amber-200'
                                          }`}
                                        >
                                          {item.risk_flag}
                                        </span>
                                      </div>
                                      <div className="text-[11px] text-slate-600">
                                        <strong className={item.risk_flag.toLowerCase() === 'critical' ? 'text-red-700' : 'text-amber-700'}>
                                          {item.days_until_stockout === 0 ? 'Stocked Out' : `${item.days_until_stockout} days remaining`}
                                        </strong>
                                        <span className="text-slate-400"> &bull; Current Stock: {item.current_stock_level} units &bull; Burn: {item.recent_daily_consumption.toFixed(1)}/day</span>
                                      </div>
                                    </div>

                                    {/* Action: Find Nearby Surplus Button */}
                                    <button
                                      onClick={() =>
                                        handleOpenFastTrackModal({
                                          facility_id: f.facility_id,
                                          facility_name: f.facility_name,
                                          commodity_id: item.commodity_id,
                                          commodity_name: item.commodity_name,
                                          alert_message: `${f.facility_name} is facing ${item.risk_flag.toLowerCase()} stockout of ${item.commodity_name} in ${item.days_until_stockout} days.`,
                                          days_until_stockout: item.days_until_stockout ?? 0,
                                        })
                                      }
                                      className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 rounded-lg text-xs font-bold transition flex-shrink-0"
                                    >
                                      <ArrowLeftRight className="w-3.5 h-3.5" />
                                      <span>Find Nearby Surplus</span>
                                    </button>
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="py-4 text-center text-xs text-slate-600 bg-white rounded-lg border border-slate-100">
                                All 15 essential medicines at {f.facility_name} have healthy stock buffers (&gt;60 days). No emergency redistribution required.
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Critical Alert Feed */}
              <div className="bg-white rounded-2xl border border-slate-200 shadow-xs p-6 space-y-4 flex flex-col justify-between">
                <div>
                  <div className="pb-3 border-b border-slate-100 flex items-center justify-between">
                    <div>
                      <h3 className="text-base font-bold text-slate-900 flex items-center space-x-1.5">
                        <Bell className="w-4 h-4 text-amber-600" />
                        <span>Critical Alert Feed</span>
                      </h3>
                      <p className="text-xs text-slate-500 mt-0.5">
                        Automated stockout warnings &bull; Click to fast-track transfer
                      </p>
                    </div>
                    <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-800">
                      {forecast?.critical_alerts?.length ?? 0} Alerts
                    </span>
                  </div>

                  <div className="divide-y divide-slate-100 max-h-[380px] overflow-y-auto pr-1">
                    {forecast?.critical_alerts && forecast.critical_alerts.length > 0 ? (
                      forecast.critical_alerts.map((a, idx) => (
                        <div
                          key={`${a.facility_id}-${a.commodity_id}-${idx}`}
                          onClick={() =>
                            handleOpenFastTrackModal({
                              facility_id: a.facility_id,
                              facility_name: a.facility_name,
                              commodity_id: a.commodity_id,
                              commodity_name: a.commodity_name,
                              alert_message: a.alert_message,
                              days_until_stockout: a.days_until_stockout,
                            })
                          }
                          className="p-3 space-y-1.5 rounded-xl cursor-pointer hover:bg-amber-50/80 transition-all border border-transparent hover:border-amber-200 group"
                          title="Click to fast-track nearest donor surplus match"
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-slate-900 truncate max-w-[170px]" title={a.facility_name}>
                              {a.facility_name}
                            </span>
                            <span className="px-1.5 py-0.5 rounded text-[10px] font-black bg-red-100 text-red-800 border border-red-200">
                              {a.days_until_stockout === 0 ? 'STOCKOUT' : `${a.days_until_stockout}d left`}
                            </span>
                          </div>
                          <p className="text-xs text-slate-600 leading-snug">
                            {a.alert_message}
                          </p>
                          <div className="flex items-center justify-between text-[10px] pt-1 text-slate-400 font-mono">
                            <span>Runs out: {a.predicted_stockout_date}</span>
                            <span className="text-blue-700 font-bold group-hover:underline flex items-center space-x-0.5 font-sans">
                              <span>Fast-track match</span>
                              <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                            </span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="py-12 text-center text-xs text-slate-500">
                        No critical stockout alerts for {activeCounty} County.
                      </div>
                    )}
                  </div>
                </div>

                <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-[11px] text-amber-900 font-medium">
                  Click any critical alert to immediately match with nearest surplus donor and dispatch a transfer request.
                </div>
              </div>
            </div>
          </>
        )}

        {/* Task 4: Fast-Track Match Modal */}
        {fastTrackTarget && (
          <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-lg w-full p-6 space-y-5 animate-fadeIn">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div>
                  <h3 className="text-base font-bold text-slate-900">
                    Fast-Track Surplus Match &amp; Transfer
                  </h3>
                  <p className="text-xs text-slate-500">
                    One-click resolution for critical stockout alert
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setFastTrackTarget(null)}
                  className="text-slate-400 hover:text-slate-700 p-1"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Deficit Alert Context */}
              <div className="p-3.5 bg-red-50 border border-red-200 rounded-xl space-y-1 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-red-950">
                    Recipient: {fastTrackTarget.facility_name}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-black bg-red-100 text-red-800 border border-red-300 uppercase">
                    Critical Alert
                  </span>
                </div>
                <div className="text-red-900">
                  Medicine: <strong>{fastTrackTarget.commodity_name}</strong> &bull; {fastTrackTarget.days_until_stockout} days buffer remaining
                </div>
                {fastTrackTarget.alert_message && (
                  <div className="text-[11px] text-red-700 italic pt-0.5">
                    &ldquo;{fastTrackTarget.alert_message}&rdquo;
                  </div>
                )}
              </div>

              {/* Matches Query Result */}
              {fastTrackLoading ? (
                <div className="py-10 text-center space-y-2">
                  <div className="inline-block animate-spin rounded-full h-7 w-7 border-3 border-purple-600 border-t-transparent" />
                  <p className="text-xs font-bold text-slate-700">Finding nearest donor facility with confirmed surplus...</p>
                  <p className="text-[11px] text-slate-400">Calculating Haversine geodesic distances</p>
                </div>
              ) : fastTrackMatches?.matches && fastTrackMatches.matches.length > 0 ? (
                (() => {
                  const m = fastTrackMatches.matches[0];
                  return (
                    <div className="space-y-4">
                      <div className="p-4 bg-purple-50 border border-purple-200 rounded-xl space-y-2.5 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] font-bold text-purple-700 uppercase tracking-wider">
                            Recommended Donor Facility
                          </span>
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white text-purple-900 border border-purple-200 font-mono">
                            {m.distance_km} km away
                          </span>
                        </div>
                        <div>
                          <h4 className="text-sm font-black text-slate-900">
                            {m.source_facility_name}
                          </h4>
                          <span className="text-slate-500 font-medium">{m.source_county} County</span>
                        </div>
                        <div className="grid grid-cols-2 gap-2 pt-2 border-t border-purple-200/70 font-mono text-[11px]">
                          <div>
                            <span className="text-slate-500">Available Surplus:</span>
                            <div className="font-bold text-slate-900">{m.available_surplus_units} units</div>
                          </div>
                          <div>
                            <span className="text-slate-500">Donor Buffer:</span>
                            <div className="font-bold text-emerald-700">{m.source_days_of_stock.toFixed(0)} days safe</div>
                          </div>
                        </div>
                      </div>

                      {/* Quantity Input */}
                      <div className="space-y-1">
                        <label className="block text-xs font-bold uppercase text-slate-700">
                          Transfer Quantity (Units)
                        </label>
                        <input
                          type="number"
                          min={1}
                          max={m.available_surplus_units}
                          value={fastTrackQty}
                          onChange={(e) => setFastTrackQty(Number(e.target.value))}
                          className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-purple-500 focus:outline-none"
                        />
                        <p className="text-[11px] text-slate-500">
                          Recommended batch: {m.recommended_quantity} units &bull; Est. Value: KES {(fastTrackQty * m.unit_cost_kes).toLocaleString()}
                        </p>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100">
                        <button
                          type="button"
                          onClick={() => setFastTrackTarget(null)}
                          className="px-3.5 py-2 rounded-lg text-xs font-bold text-slate-600 hover:bg-slate-100 transition"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          onClick={() => handleConfirmFastTrackTransfer(m)}
                          disabled={isSubmittingFastTrack}
                          className="inline-flex items-center space-x-1.5 px-4 py-2 bg-purple-700 hover:bg-purple-800 text-white text-xs font-bold rounded-lg shadow-xs transition active:scale-95 disabled:opacity-50"
                        >
                          <Send className="w-3.5 h-3.5" />
                          <span>{isSubmittingFastTrack ? 'Dispatching...' : 'Request Transfer & Add to Queue'}</span>
                        </button>
                      </div>
                    </div>
                  );
                })()
              ) : (
                <div className="py-8 text-center space-y-3 bg-slate-50 rounded-xl border border-dashed border-slate-200 p-4">
                  <AlertTriangle className="w-8 h-8 text-amber-500 mx-auto" />
                  <h4 className="text-xs font-bold text-slate-800">No Nearby Donor With Surplus Found</h4>
                  <p className="text-xs text-slate-500 max-w-sm mx-auto">
                    No neighboring healthcare facilities within 400 km currently hold excess stock of {fastTrackTarget.commodity_name}.
                  </p>
                  <button
                    onClick={() => setFastTrackTarget(null)}
                    className="px-4 py-2 bg-slate-200 hover:bg-slate-300 text-slate-800 text-xs font-bold rounded-lg transition"
                  >
                    Close
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

export default function CountyDashboardPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-slate-500">Loading County Operational View...</div>}>
      <CountyDashboardContent />
    </Suspense>
  );
}
