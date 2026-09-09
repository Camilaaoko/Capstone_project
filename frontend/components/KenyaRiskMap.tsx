'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { CountyScorecardSummary } from '@/lib/api';
import { MapPin, ArrowUpRight } from 'lucide-react';

export const COUNTY_COORDINATES: Record<string, { lat: number; lng: number; facilities: number }> = {
  "Baringo": { lat: 0.4153, lng: 36.0462, facilities: 2 },
  "Bomet": { lat: -0.8386, lng: 35.4081, facilities: 2 },
  "Bungoma": { lat: 0.5438, lng: 34.5616, facilities: 2 },
  "Busia": { lat: 0.5099, lng: 34.1067, facilities: 2 },
  "Elgeyo-Marakwet": { lat: 0.677, lng: 35.4105, facilities: 2 },
  "Embu": { lat: -0.5293, lng: 37.4656, facilities: 2 },
  "Garissa": { lat: -0.503, lng: 39.6406, facilities: 2 },
  "Homa Bay": { lat: -0.5701, lng: 34.3785, facilities: 2 },
  "Isiolo": { lat: 0.2988, lng: 37.5239, facilities: 2 },
  "Kajiado": { lat: -1.8744, lng: 36.8523, facilities: 2 },
  "Kakamega": { lat: 0.2421, lng: 34.6965, facilities: 2 },
  "Kericho": { lat: -0.3305, lng: 35.2697, facilities: 2 },
  "Kiambu": { lat: -1.143, lng: 36.7669, facilities: 2 },
  "Kilifi": { lat: -3.5244, lng: 39.9646, facilities: 3 },
  "Kirinyaga": { lat: -0.4232, lng: 37.2799, facilities: 2 },
  "Kisii": { lat: -0.7608, lng: 34.8223, facilities: 2 },
  "Kisumu": { lat: -0.1537, lng: 34.6792, facilities: 2 },
  "Kitui": { lat: -1.3453, lng: 37.9545, facilities: 2 },
  "Kwale": { lat: -4.15, lng: 39.4382, facilities: 3 },
  "Laikipia": { lat: 0.3983, lng: 36.7947, facilities: 2 },
  "Lamu": { lat: -2.2838, lng: 40.9401, facilities: 3 },
  "Machakos": { lat: -1.5243, lng: 37.2726, facilities: 2 },
  "Makueni": { lat: -1.9085, lng: 37.6945, facilities: 2 },
  "Mandera": { lat: 3.8606, lng: 41.8698, facilities: 2 },
  "Marsabit": { lat: 2.3645, lng: 38.0101, facilities: 2 },
  "Meru": { lat: 0.0618, lng: 37.6903, facilities: 2 },
  "Migori": { lat: -1.0427, lng: 34.4764, facilities: 2 },
  "Mombasa": { lat: -4.0365, lng: 39.581, facilities: 3 },
  "Murang'a": { lat: -0.7432, lng: 37.1337, facilities: 2 },
  "Nairobi": { lat: -1.292, lng: 36.832, facilities: 3 },
  "Nakuru": { lat: -0.2855, lng: 35.9727, facilities: 2 },
  "Nandi": { lat: 0.1948, lng: 35.0121, facilities: 2 },
  "Narok": { lat: -0.9883, lng: 35.9513, facilities: 2 },
  "Nyamira": { lat: -0.4872, lng: 34.8309, facilities: 2 },
  "Nyandarua": { lat: -0.1943, lng: 36.5686, facilities: 2 },
  "Nyeri": { lat: -0.4449, lng: 36.884, facilities: 2 },
  "Samburu": { lat: 1.1462, lng: 36.8634, facilities: 2 },
  "Siaya": { lat: 0.1011, lng: 34.1931, facilities: 2 },
  "Taita Taveta": { lat: -3.2451, lng: 38.3187, facilities: 2 },
  "Tana River": { lat: -1.4567, lng: 39.5267, facilities: 3 },
  "Tharaka-Nithi": { lat: -0.2292, lng: 37.7686, facilities: 2 },
  "Trans Nzoia": { lat: 1.0113, lng: 35.0102, facilities: 2 },
  "Turkana": { lat: 3.1324, lng: 35.5755, facilities: 2 },
  "Uasin Gishu": { lat: 0.5226, lng: 35.3622, facilities: 2 },
  "Vihiga": { lat: 0.074, lng: 34.7975, facilities: 2 },
  "Wajir": { lat: 1.765, lng: 40.0602, facilities: 2 },
  "West Pokot": { lat: 1.3122, lng: 35.1106, facilities: 2 },
};

// Map projection parameters
const MIN_LNG = 33.5;
const MAX_LNG = 42.2;
const MIN_LAT = -4.7;
const MAX_LAT = 4.5;
const SVG_WIDTH = 760;
const SVG_HEIGHT = 680;
const PADDING = 40;

function projectCoords(lat: number, lng: number): { x: number; y: number } {
  const x = PADDING + ((lng - MIN_LNG) / (MAX_LNG - MIN_LNG)) * (SVG_WIDTH - 2 * PADDING);
  const y = PADDING + ((MAX_LAT - lat) / (MAX_LAT - MIN_LAT)) * (SVG_HEIGHT - 2 * PADDING);
  return { x: Math.round(x * 10) / 10, y: Math.round(y * 10) / 10 };
}

const EQUATOR_Y = projectCoords(0, 37.5).y;

interface KenyaRiskMapProps {
  scorecards: CountyScorecardSummary[];
  filterTier: string;
  searchQuery: string;
}

export default function KenyaRiskMap({
  scorecards,
  filterTier,
  searchQuery,
}: KenyaRiskMapProps) {
  const [hoveredCounty, setHoveredCounty] = useState<string | null>(null);
  const [selectedCounty, setSelectedCounty] = useState<string | null>(null);

  // Scorecards map by county name
  const scorecardMap = React.useMemo(() => {
    const map = new Map<string, CountyScorecardSummary>();
    scorecards.forEach((s) => {
      map.set(s.county.toLowerCase(), s);
    });
    return map;
  }, [scorecards]);

  // Find all counties matching the current filter and search query
  const matchingCounties = React.useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return scorecards.filter((s) => {
      const matchesFilter =
        filterTier === 'ALL' || s.risk_tier.toLowerCase() === filterTier.toLowerCase();
      const matchesSearch = !q || s.county.toLowerCase().includes(q);
      return matchesFilter && matchesSearch;
    });
  }, [scorecards, filterTier, searchQuery]);

  // First matching county (prioritizing exact match, then prefix, then substring)
  const firstMatchingCounty = React.useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) {
      return matchingCounties[0]?.county || null;
    }
    const exact = matchingCounties.find((s) => s.county.toLowerCase() === q);
    if (exact) return exact.county;
    const prefix = matchingCounties.find((s) => s.county.toLowerCase().startsWith(q));
    if (prefix) return prefix.county;
    return matchingCounties[0]?.county || null;
  }, [matchingCounties, searchQuery]);

  // When search query or filter changes, auto-select the best matching county
  React.useEffect(() => {
    if (searchQuery.trim()) {
      if (firstMatchingCounty) {
        setSelectedCounty(firstMatchingCounty);
      }
    } else if (filterTier !== 'ALL') {
      if (selectedCounty) {
        const current = scorecardMap.get(selectedCounty.toLowerCase());
        if (current && current.risk_tier.toLowerCase() !== filterTier.toLowerCase()) {
          setSelectedCounty(firstMatchingCounty);
        }
      }
    }
  }, [searchQuery, filterTier, firstMatchingCounty, selectedCounty, scorecardMap]);

  // Check if search has zero matches
  const isSearchActive = Boolean(searchQuery.trim());
  const hasNoMatches = isSearchActive && matchingCounties.length === 0;

  // Current active county detail for sidebar or hover card
  const activeCountyName = hoveredCounty || selectedCounty || firstMatchingCounty || 'Nairobi';
  const activeScorecard = hasNoMatches
    ? null
    : scorecardMap.get(activeCountyName.toLowerCase()) || matchingCounties[0] || scorecards[0];
  const activeCoords = activeScorecard
    ? COUNTY_COORDINATES[activeScorecard.county] || { lat: -1.292, lng: 36.832, facilities: 3 }
    : { lat: -1.292, lng: 36.832, facilities: 3 };

  return (
    <div className="space-y-4">
      {/* Map + Detail Panel Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* SVG Interactive Map Canvas */}
        <div className="lg:col-span-8 bg-white rounded-2xl border border-slate-200 p-4 shadow-xs relative overflow-hidden">
          {/* Top Map Overlays */}
          <div className="absolute top-4 left-4 z-10 flex items-center space-x-2">
            <span className="px-2.5 py-1 rounded-md bg-white/95 backdrop-blur-xs border border-slate-200 text-[11px] font-mono font-bold text-slate-800 shadow-xs">
              KENYA GEODYNAMIC RISK MATRIX
            </span>
            <span className="text-[11px] text-slate-500 font-mono hidden sm:inline">
              EPSG:4326 Centroid Projections
            </span>
          </div>

          {/* Compass Rose */}
          <div className="absolute top-4 right-4 z-10 flex flex-col items-center bg-white/95 backdrop-blur-xs border border-slate-200 px-2.5 py-1 rounded-md text-[10px] font-mono text-slate-600 shadow-xs">
            <span className="text-emerald-600 font-bold">N &uarr;</span>
            <span className="text-[9px] text-slate-400">Turkana / Mandera</span>
          </div>

          {/* Map SVG */}
          <svg
            viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
            className="w-full h-auto select-none"
            style={{ maxHeight: '580px' }}
          >
            <defs>
              {/* Light canvas subtle gradient */}
              <radialGradient id="lightMapCanvas" cx="50%" cy="45%" r="75%">
                <stop offset="0%" stopColor="#FFFFFF" />
                <stop offset="100%" stopColor="#F8FAFC" />
              </radialGradient>
              {/* Water gradient */}
              <linearGradient id="waterGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#E0F2FE" />
                <stop offset="100%" stopColor="#BAE6FD" stopOpacity="0.75" />
              </linearGradient>
              {/* Ocean gradient */}
              <linearGradient id="oceanGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#F0F9FF" />
                <stop offset="100%" stopColor="#E0F2FE" />
              </linearGradient>
              {/* Drop shadow for nodes */}
              <filter id="nodeShadow" x="-30%" y="-30%" width="160%" height="160%">
                <feDropShadow dx="0" dy="1.5" stdDeviation="1.5" floodColor="#0F172A" floodOpacity="0.18" />
              </filter>
            </defs>

            {/* Canvas Background */}
            <rect width={SVG_WIDTH} height={SVG_HEIGHT} fill="url(#lightMapCanvas)" stroke="#E2E8F0" strokeWidth="1" rx="14" />

            {/* Water Bodies & Geographic Landmarks */}
            {/* Lake Victoria */}
            <g id="lake-victoria">
              <path
                d="M 40 314 L 71 314 L 95 327 L 118 346 L 102 373 L 102 405 L 71 425 L 40 425 Z"
                fill="url(#waterGradient)"
                stroke="#BAE6FD"
                strokeWidth="1.5"
                opacity="0.9"
              />
              <text
                x="60"
                y="370"
                fill="#0284C7"
                fontSize="10"
                fontWeight="700"
                fontFamily="sans-serif"
                opacity="0.75"
                transform="rotate(-45, 60, 370)"
              >
                L. Victoria
              </text>
            </g>

            {/* Lake Turkana */}
            <g id="lake-turkana">
              <path
                d="M 235 53 L 243 99 L 282 151 L 290 177 L 267 170 L 220 112 Z"
                fill="url(#waterGradient)"
                stroke="#BAE6FD"
                strokeWidth="1.5"
                opacity="0.85"
              />
              <text
                x="256"
                y="118"
                fill="#0284C7"
                fontSize="9"
                fontWeight="700"
                fontFamily="sans-serif"
                opacity="0.75"
                transform="rotate(65, 256, 118)"
              >
                L. Turkana
              </text>
            </g>

            {/* Indian Ocean (South-East Coastline) */}
            <g id="indian-ocean">
              <path
                d="M 650 464 L 618 490 L 556 542 L 532 575 L 501 607 L 485 640 L 485 666 L 746 666 L 746 464 Z"
                fill="url(#oceanGradient)"
                stroke="#BAE6FD"
                strokeWidth="1"
                opacity="0.85"
              />
              {/* Subtle wave ripple lines */}
              <path
                d="M 570 570 Q 600 560, 630 570 T 690 570"
                stroke="#BAE6FD"
                strokeWidth="1"
                fill="none"
                opacity="0.6"
              />
              <path
                d="M 530 620 Q 560 610, 590 620 T 650 620"
                stroke="#BAE6FD"
                strokeWidth="1"
                fill="none"
                opacity="0.6"
              />
              <text
                x="640"
                y="595"
                fill="#0369A1"
                fontSize="11"
                fontWeight="800"
                letterSpacing="2"
                fontFamily="sans-serif"
                opacity="0.5"
              >
                INDIAN OCEAN
              </text>
            </g>

            {/* Latitude & Longitude Reference Grid */}
            <g stroke="#CBD5E1" strokeWidth="0.75" strokeDasharray="4 4" opacity="0.6">
              {/* Meridians */}
              <line x1={projectCoords(0, 36.0).x} y1="20" x2={projectCoords(0, 36.0).x} y2={SVG_HEIGHT - 20} />
              <line x1={projectCoords(0, 38.0).x} y1="20" x2={projectCoords(0, 38.0).x} y2={SVG_HEIGHT - 20} />
              <line x1={projectCoords(0, 40.0).x} y1="20" x2={projectCoords(0, 40.0).x} y2={SVG_HEIGHT - 20} />
              {/* Parallels */}
              <line x1="20" y1={projectCoords(2.0, 37.0).y} x2={SVG_WIDTH - 20} y2={projectCoords(2.0, 37.0).y} />
              <line x1="20" y1={projectCoords(-2.0, 37.0).y} x2={SVG_WIDTH - 20} y2={projectCoords(-2.0, 37.0).y} />
            </g>

            {/* Grid Coordinate Callouts */}
            <g fill="#94A3B8" fontSize="9" fontFamily="monospace">
              <text x={projectCoords(0, 36.0).x} y="32" textAnchor="middle">36&deg;E</text>
              <text x={projectCoords(0, 38.0).x} y="32" textAnchor="middle">38&deg;E</text>
              <text x={projectCoords(0, 40.0).x} y="32" textAnchor="middle">40&deg;E</text>
              <text x="26" y={projectCoords(2.0, 37.0).y + 3} textAnchor="start">2&deg;N</text>
              <text x="26" y={projectCoords(-2.0, 37.0).y + 3} textAnchor="start">2&deg;S</text>
            </g>

            {/* Equator (Latitude 0°) Line */}
            <line
              x1="30"
              y1={EQUATOR_Y}
              x2={SVG_WIDTH - 30}
              y2={EQUATOR_Y}
              stroke="#10B981"
              strokeWidth="1.5"
              strokeDasharray="5 5"
              opacity="0.8"
            />
            <rect
              x={SVG_WIDTH - 128}
              y={EQUATOR_Y - 14}
              width="96"
              height="16"
              rx="4"
              fill="#ECFDF5"
              stroke="#A7F3D0"
              strokeWidth="1"
            />
            <text
              x={SVG_WIDTH - 80}
              y={EQUATOR_Y - 3}
              fill="#065F46"
              fontSize="9"
              fontWeight="bold"
              fontFamily="monospace"
              textAnchor="middle"
            >
              Equator (0.0&deg;)
            </text>

            {/* Regional Sector Labels */}
            <text x="140" y="75" fill="#94A3B8" fontSize="10" fontWeight="800" letterSpacing="1" fontFamily="sans-serif">
              NORTHERN KENYA
            </text>
            <text x="50" y="280" fill="#94A3B8" fontSize="10" fontWeight="800" letterSpacing="1" fontFamily="sans-serif">
              WESTERN / L.VICTORIA
            </text>
            <text x="310" y="520" fill="#94A3B8" fontSize="10" fontWeight="800" letterSpacing="1" fontFamily="sans-serif">
              SOUTHERN RIFT
            </text>
            <text x="520" y="440" fill="#94A3B8" fontSize="10" fontWeight="800" letterSpacing="1" fontFamily="sans-serif">
              EASTERN / COASTAL
            </text>

            {/* 47 County Nodes */}
            {Object.entries(COUNTY_COORDINATES).map(([countyName, coords]) => {
              const { x, y } = projectCoords(coords.lat, coords.lng);
              const card = scorecardMap.get(countyName.toLowerCase());
              const riskTier = card?.risk_tier || 'Low';
              const isHigh = riskTier.toLowerCase() === 'high';
              const isMed = riskTier.toLowerCase() === 'medium';
              const isHovered = hoveredCounty === countyName;
              const isSelected = selectedCounty === countyName;

              // Filter matching
              const matchesFilter =
                filterTier === 'ALL' || riskTier.toLowerCase() === filterTier.toLowerCase();
              const matchesSearch =
                !searchQuery || countyName.toLowerCase().includes(searchQuery.toLowerCase());
              const isDimmed = !matchesFilter || !matchesSearch;

              const fillColor = isHigh ? '#EF4444' : isMed ? '#F59E0B' : '#10B981';
              const strokeColor = '#FFFFFF';
              const radius = isHigh ? 10 : isMed ? 8.5 : 7.5;

              return (
                <g
                  key={countyName}
                  className="cursor-pointer transition-opacity duration-200"
                  opacity={isDimmed ? 0.2 : 1.0}
                  onMouseEnter={() => setHoveredCounty(countyName)}
                  onMouseLeave={() => setHoveredCounty(null)}
                  onClick={() => setSelectedCounty(countyName)}
                >
                  {/* High Risk Pulsing Ring */}
                  {isHigh && !isDimmed && (
                    <circle
                      cx={x}
                      cy={y}
                      r={radius + 5}
                      fill="none"
                      stroke="#EF4444"
                      strokeWidth="1.5"
                      opacity="0.4"
                    >
                      <animate
                        attributeName="r"
                        values={`${radius + 3};${radius + 10};${radius + 3}`}
                        dur="2.5s"
                        repeatCount="indefinite"
                      />
                      <animate
                        attributeName="opacity"
                        values="0.6;0.1;0.6"
                        dur="2.5s"
                        repeatCount="indefinite"
                      />
                    </circle>
                  )}

                  {/* Active Selection Glow Ring */}
                  {(isHovered || isSelected) && (
                    <circle
                      cx={x}
                      cy={y}
                      r={radius + 6}
                      fill="none"
                      stroke="#0F172A"
                      strokeWidth="2"
                      strokeDasharray="3 2"
                    />
                  )}

                  {/* Main Node Circle */}
                  <circle
                    cx={x}
                    cy={y}
                    r={radius}
                    fill={fillColor}
                    stroke={strokeColor}
                    strokeWidth={2}
                    filter="url(#nodeShadow)"
                  />

                  {/* Node Center Dot */}
                  <circle cx={x} cy={y} r="2" fill="#FFFFFF" opacity="0.9" />

                  {/* County Name Label */}
                  <text
                    x={x}
                    y={y + radius + 10}
                    textAnchor="middle"
                    fill={isHovered || isSelected ? '#0F172A' : isDimmed ? '#94A3B8' : '#1E293B'}
                    fontSize={isHovered || isSelected ? '11' : '8.5'}
                    fontWeight={isHovered || isSelected ? '800' : '700'}
                    fontFamily="sans-serif"
                    className="pointer-events-none"
                    paintOrder="stroke fill"
                    stroke="#FFFFFF"
                    strokeWidth={isHovered || isSelected ? '3.5' : '2.5'}
                    strokeLinejoin="round"
                  >
                    {countyName}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Map Legend Footer */}
          <div className="mt-3 pt-3 border-t border-slate-200 flex flex-wrap items-center justify-between text-xs text-slate-600 gap-2">
            <div className="flex items-center space-x-4">
              <span className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block shadow-xs" />
                <span className="text-slate-800 font-semibold">High Risk (Freeze Threshold)</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block shadow-xs" />
                <span className="text-slate-800 font-semibold">Medium Risk (Watchlist)</span>
              </span>
              <span className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block shadow-xs" />
                <span className="text-slate-800 font-semibold">Low Risk (Restock Healthy)</span>
              </span>
            </div>
            <div className="text-[11px] text-slate-500 font-mono">
              Click any node to focus county profile
            </div>
          </div>
        </div>

        {/* Focused County Profile Card (Right Column) */}
        <div className="lg:col-span-4 bg-white rounded-2xl border border-slate-200 shadow-xs p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center space-x-2">
              <MapPin className="w-4 h-4 text-emerald-600" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500">
                County Geo-Financial Focus
              </h3>
            </div>
            {activeScorecard ? (
              <span
                className={`px-2 py-0.5 rounded text-[11px] font-black uppercase tracking-wider border ${
                  activeScorecard.risk_tier.toLowerCase() === 'high'
                    ? 'bg-red-100 text-red-800 border-red-300'
                    : activeScorecard.risk_tier.toLowerCase() === 'medium'
                    ? 'bg-amber-100 text-amber-800 border-amber-300'
                    : 'bg-emerald-100 text-emerald-800 border-emerald-300'
                }`}
              >
                {activeScorecard.risk_tier} RISK
              </span>
            ) : (
              <span className="px-2 py-0.5 rounded text-[11px] font-bold text-slate-400 bg-slate-100 border border-slate-200">
                0 MATCHES
              </span>
            )}
          </div>

          {activeScorecard ? (
            <div className="space-y-4">
              <div>
                <h2 className="text-2xl font-black text-slate-900 tracking-tight">
                  {activeScorecard.county} County
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Centroid: {activeCoords.lat.toFixed(2)}&deg;N, {activeCoords.lng.toFixed(2)}&deg;E &bull; {activeCoords.facilities} Monitored Facilities
                </p>
              </div>

              {/* Composite Score Card */}
              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between">
                <div>
                  <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    Composite Risk Score
                  </div>
                  <div className="text-2xl font-black text-slate-900 mt-0.5">
                    {activeScorecard.risk_score.toFixed(0)}
                    <span className="text-xs text-slate-400 font-normal"> / 100</span>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    Primary Driver
                  </div>
                  <div className="text-xs font-bold text-slate-800 mt-0.5">
                    {activeScorecard.primary_driver}
                  </div>
                </div>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-2 gap-2.5 text-xs">
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
                  <span className="text-[11px] text-slate-500 font-medium">Outstanding Debt</span>
                  <div className="font-mono font-bold text-slate-900 truncate">
                    KES {(activeScorecard.amount_owed_kes / 1_000_000).toFixed(1)}M
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
                  <span className="text-[11px] text-slate-500 font-medium">Days Overdue</span>
                  <div className="font-mono font-bold text-slate-900">
                    {activeScorecard.days_overdue} days
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
                  <span className="text-[11px] text-slate-500 font-medium">Payment Score</span>
                  <div className="font-mono font-bold text-slate-900">
                    {activeScorecard.payment_history_score.toFixed(0)}/100
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
                  <span className="text-[11px] text-slate-500 font-medium">Restock Status</span>
                  <div className="font-bold text-slate-900">
                    {activeScorecard.risk_tier === 'High' ? (
                      <span className="text-red-600">Order Frozen</span>
                    ) : activeScorecard.risk_tier === 'Medium' ? (
                      <span className="text-amber-600">Conditional</span>
                    ) : (
                      <span className="text-emerald-600">Auto-Approved</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Button to County Portal */}
              <div className="pt-2">
                <Link
                  href={`/county?county=${encodeURIComponent(activeScorecard.county)}`}
                  className="w-full inline-flex items-center justify-center space-x-2 px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl shadow-xs transition"
                >
                  <span>Open {activeScorecard.county} County Workspace</span>
                  <ArrowUpRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-xs text-slate-500 space-y-2">
              <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
                <MapPin className="w-5 h-5" />
              </div>
              <p className="font-bold text-slate-700">No matching county found</p>
              <p className="text-slate-400 max-w-[220px] mx-auto leading-relaxed">
                No county matching &ldquo;{searchQuery}&rdquo; under {filterTier === 'ALL' ? 'the national network' : `${filterTier} Risk tier`}.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
