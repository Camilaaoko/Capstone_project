/**
 * Typed API Client for KEMSA Healthcare Supply Chain Intelligence Platform
 * Connects to the FastAPI backend service.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
    // Avoid stale caching during active updates in development
    cache: options?.cache || 'no-store',
  });

  if (!res.ok) {
    let errorDetail = res.statusText;
    try {
      const errJson = await res.json();
      if (errJson && errJson.detail) {
        errorDetail = errJson.detail;
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(`API Error (${res.status}): ${errorDetail}`);
  }

  return res.json();
}

// =============================================================================
// Type Definitions
// =============================================================================

export interface HealthCheckResponse {
  status: string;
  message: string;
}

export interface FacilitySummary {
  facility_id: string;
  facility_name: string;
  county: string;
  sub_county?: string | null;
  facility_type?: string | null;
  facility_level?: string | null;
  facility_size_tier?: string | null;
  bed_capacity?: number | null;
  average_daily_patient_visits?: number | null;
  latitude?: number | null;
  longitude?: number | null;
}

export interface RiskFactorDetail {
  factor: string;
  factor_name: string;
  value: number;
  formatted_value: string;
  weight_pct: number;
  contribution: string;
  score_contribution: number;
  description: string;
}

export interface CountyScorecardSummary {
  county: string;
  risk_score: number;
  risk_tier: 'Low' | 'Medium' | 'High' | string;
  tier_color: string;
  tier_badge: string;
  amount_owed_kes: number;
  days_overdue: number;
  payment_history_score: number;
  primary_driver: string;
  month: string;
}

export interface CountyScorecardDetail extends CountyScorecardSummary {
  factors: RiskFactorDetail[];
  plain_language_summary: string;
}

export interface NationalDebtTrendItem {
  month: string;
  total_debt: number;
  avg_days_overdue: number;
  counties_count: number;
}

export interface CountyHistoryItem {
  county: string;
  month: string;
  amount_owed_kes: number;
  days_overdue: number;
  payment_history_score: number;
  risk_score: number;
  risk_tier: string;
  tier_color: string;
  tier_badge: string;
  primary_driver: string;
}

export interface RiskCounts {
  critical: number;
  warning: number;
  watch: number;
  healthy: number;
  total: number;
}

export interface CommodityStockoutForecast {
  facility_id: string;
  facility_name: string;
  county: string;
  commodity_id: string;
  commodity_name: string;
  category: string;
  current_stock_level: number;
  recent_daily_consumption: number;
  days_until_stockout: number | null;
  predicted_stockout_date: string | null;
  stockout_date_display: string;
  risk_flag: 'Critical' | 'Warning' | 'Watch' | 'Healthy' | string;
  risk_color: string;
  urgency_score: number;
  explanation: string;
}

export interface FacilityForecastResponse {
  facility_id: string;
  facility_name: string;
  county: string;
  inventory_date: string;
  risk_counts: RiskCounts;
  forecasts: CommodityStockoutForecast[];
}

export interface CountyAlertItem {
  facility_id: string;
  facility_name: string;
  commodity_id: string;
  commodity_name: string;
  days_until_stockout: number;
  predicted_stockout_date: string;
  current_stock_level: number;
  risk_flag: string;
  alert_message: string;
}

export interface FacilityRiskSummary {
  facility_id: string;
  facility_name: string;
  sub_county?: string | null;
  critical_count: number;
  warning_count: number;
  watch_count: number;
  healthy_count: number;
  highest_risk_flag: string;
}

export interface CountyForecastResponse {
  county: string;
  inventory_date: string;
  facilities_monitored: number;
  total_pairs: number;
  risk_counts: RiskCounts;
  critical_alerts: CountyAlertItem[];
  facilities: FacilityRiskSummary[];
}

export interface UrgentStockoutPair {
  facility_id: string;
  facility_name: string;
  county: string;
  commodity_id: string;
  commodity_name: string;
  days_until_stockout: number;
  predicted_stockout_date: string;
  current_stock_level: number;
  recent_daily_consumption: number;
  risk_flag: string;
}

export interface HorizonDeficit {
  horizon_days: number;
  label: string;
  predicted_stockout_pairs: number;
  estimated_unmet_demand_units: number;
}

export interface NationalForecastResponse {
  inventory_date: string;
  total_facilities_monitored: number;
  total_counties_monitored: number;
  total_commodities_monitored: number;
  total_pairs_monitored: number;
  risk_counts: RiskCounts;
  horizon_projections: {
    horizon_days: number;
    label: string;
    predicted_stockout_pairs: number;
    estimated_unmet_demand_units: number;
  }[];
  most_urgent_pairs: UrgentStockoutPair[];
}

export interface SurplusMatchItem {
  source_facility_id: string;
  source_facility_name: string;
  source_county: string;
  destination_facility_id: string;
  destination_facility_name: string;
  destination_county: string;
  commodity_id: string;
  commodity_name: string;
  category: string;
  distance_km: number;
  available_surplus_units: number;
  required_deficit_units: number;
  recommended_quantity: number;
  unit_cost_kes: number;
  transfer_value_kes: number;
  source_days_of_stock: number;
  destination_days_of_stock: number;
  priority_score: number;
  reason: string;
}

export interface SurplusMatchesResponse {
  destination_facility_id: string;
  destination_facility_name: string;
  county: string;
  shortage_commodities_count: number;
  matches_found: number;
  matches: SurplusMatchItem[];
}

export interface CreateTransferRequestPayload {
  source_facility_id: string;
  destination_facility_id: string;
  commodity_id: string;
  requested_quantity: number;
  recommended_quantity?: number;
  requested_by?: string;
  reason?: string;
}

export interface TransferRequestRecord {
  request_id: string;
  source_facility_id: string;
  source_facility_name: string;
  source_county: string;
  destination_facility_id: string;
  destination_facility_name: string;
  destination_county: string;
  commodity_id: string;
  commodity_name: string;
  requested_quantity: number;
  recommended_quantity: number;
  distance_km: number;
  status: 'pending' | 'approved' | 'rejected' | 'completed' | string;
  requested_by: string;
  requested_at: string;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  reason: string;
}

export interface CountyPendingRequestsResponse {
  county: string;
  pending_count: number;
  requests: TransferRequestRecord[];
}

export interface ReviewRequestPayload {
  reviewed_by?: string;
  notes?: string;
}

export interface HistoricalBaselineMetrics {
  total_transfers: number;
  total_units: number;
  total_value_kes: number;
}

export interface LiveActivityMetrics {
  status_counts: Record<string, number>;
  approved_transfers_count: number;
  total_units_transferred: number;
  estimated_financial_value_kes: number;
  estimated_wastage_prevented_kes: number;
}

export interface CategoryTopCommodity {
  commodity_name: string;
  unmet_units: number;
  deficit_value_kes: number;
}

export interface CategoryDeficitItem {
  category: string;
  critical_pairs: number;
  affected_facilities_count: number;
  unmet_demand_units: number;
  estimated_deficit_value_kes: number;
  percentage_of_value: number;
  percentage_of_units: number;
  top_commodities: CategoryTopCommodity[];
}

export interface CategoryForecastResponse {
  inventory_date: string;
  total_critical_pairs: number;
  total_unmet_demand_units: number;
  total_deficit_value_kes: number;
  categories: CategoryDeficitItem[];
}

export interface TopReallocatedCommodity {
  commodity_id: string;
  commodity_name: string;
  category: string;
  transfer_count: number;
  total_units: number;
  total_value_kes: number;
}

export interface RedistributionActivityResponse {
  status_counts: Record<string, number>;
  approved_transfers_count: number;
  total_units_transferred: number;
  estimated_financial_value_kes: number;
  estimated_wastage_prevented_kes: number;
  historical_baseline?: HistoricalBaselineMetrics;
  live_activity?: LiveActivityMetrics;
  combined_total_savings_kes?: number;
  combined_total_transfers?: number;
  combined_total_units?: number;
  recent_activity: Record<string, unknown>[];
  top_reallocated_commodities?: TopReallocatedCommodity[];
}

// =============================================================================
// API Functions
// =============================================================================

/** Root healthcheck */
export async function getHealthCheck(): Promise<HealthCheckResponse> {
  return fetchJson<HealthCheckResponse>('/');
}

/** Fetch all registered facilities */
export async function getFacilities(): Promise<FacilitySummary[]> {
  return fetchJson<FacilitySummary[]>('/api/facilities');
}

// --- Financial Scorecard ---

/** Fetch financial scorecard for all 47 counties */
export async function getAllCountyScorecards(month?: string): Promise<CountyScorecardSummary[]> {
  const query = month ? `?month=${encodeURIComponent(month)}` : '';
  return fetchJson<CountyScorecardSummary[]>(`/api/financial/scorecard${query}`);
}

/** Fetch detailed financial scorecard with explainability factors for a specific county */
export async function getCountyScorecard(county: string, month?: string): Promise<CountyScorecardDetail> {
  const query = month ? `?month=${encodeURIComponent(month)}` : '';
  return fetchJson<CountyScorecardDetail>(`/api/financial/scorecard/${encodeURIComponent(county)}${query}`);
}

/** Fetch 24-month national debt exposure trend */
export async function getNationalDebtTrend(): Promise<NationalDebtTrendItem[]> {
  return fetchJson<NationalDebtTrendItem[]>('/api/financial/national-debt-trend');
}

/** Fetch 24-month financial risk and debt history for a specific county */
export async function getCountyScorecardHistory(county: string): Promise<CountyHistoryItem[]> {
  return fetchJson<CountyHistoryItem[]>(`/api/financial/scorecard/${encodeURIComponent(county)}/history`);
}

// --- Demand Forecasting ---

/** Fetch 30/60/90-day forward stockout forecast for a specific facility */
export async function getFacilityForecast(facilityId: string): Promise<FacilityForecastResponse> {
  return fetchJson<FacilityForecastResponse>(`/api/forecast/facility/${encodeURIComponent(facilityId)}`);
}

/** Fetch aggregated stockout forecast and alert feed for a specific county */
export async function getCountyForecast(county: string): Promise<CountyForecastResponse> {
  return fetchJson<CountyForecastResponse>(`/api/forecast/county/${encodeURIComponent(county)}`);
}

/** Fetch national stockout forecast summary and urgent stockout pairs */
export async function getNationalForecast(topN: number = 10): Promise<NationalForecastResponse> {
  return fetchJson<NationalForecastResponse>(`/api/forecast/national?top_n=${topN}`);
}

/** Fetch 30-day predicted stockout deficit by commodity category (therapeutic program) */
export async function getCategoryStockoutForecast(): Promise<CategoryForecastResponse> {
  return fetchJson<CategoryForecastResponse>('/api/forecast/categories');
}

// --- Smart Redistribution ---

/** Find geodesic surplus matches for a facility facing stockout */
export async function getNearbySurplusMatches(
  facilityId: string,
  commodityId?: string,
  maxDistanceKm: number = 400.0
): Promise<SurplusMatchesResponse> {
  const params = new URLSearchParams();
  if (commodityId) params.set('commodity_id', commodityId);
  if (maxDistanceKm) params.set('max_distance_km', maxDistanceKm.toString());
  const qs = params.toString() ? `?${params.toString()}` : '';
  return fetchJson<SurplusMatchesResponse>(`/api/redistribution/matches/${encodeURIComponent(facilityId)}${qs}`);
}

/** Submit a new inter-facility transfer request */
export async function createTransferRequest(payload: CreateTransferRequestPayload): Promise<TransferRequestRecord> {
  return fetchJson<TransferRequestRecord>('/api/redistribution/request', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

/** Fetch pending transfer requests for a county review queue */
export async function getPendingTransfers(county: string): Promise<CountyPendingRequestsResponse> {
  return fetchJson<CountyPendingRequestsResponse>(`/api/redistribution/pending/${encodeURIComponent(county)}`);
}

/** Approve a pending transfer request */
export async function approveTransfer(requestId: string, payload?: ReviewRequestPayload): Promise<TransferRequestRecord> {
  return fetchJson<TransferRequestRecord>(`/api/redistribution/request/${encodeURIComponent(requestId)}/approve`, {
    method: 'POST',
    body: JSON.stringify(payload || {}),
  });
}

/** Reject a pending transfer request */
export async function rejectTransfer(requestId: string, payload?: ReviewRequestPayload): Promise<TransferRequestRecord> {
  return fetchJson<TransferRequestRecord>(`/api/redistribution/request/${encodeURIComponent(requestId)}/reject`, {
    method: 'POST',
    body: JSON.stringify(payload || {}),
  });
}

/** Fetch national redistribution activity and prevented wastage metrics */
export async function getRedistributionActivity(): Promise<RedistributionActivityResponse> {
  return fetchJson<RedistributionActivityResponse>('/api/redistribution/activity');
}
