'use client';

import React, { useState, useEffect } from 'react';
import { setClientSession, UserRole, UserSession } from '@/lib/auth';
import { getFacilities, FacilitySummary } from '@/lib/api';
import { Landmark, Building2, Hospital, ArrowRight, ShieldCheck, AlertCircle } from 'lucide-react';

const KENYA_COUNTIES = [
  'Baringo', 'Bomet', 'Bungoma', 'Busia', 'Elgeyo-Marakwet', 'Embu', 'Garissa',
  'Homa Bay', 'Isiolo', 'Kajiado', 'Kakamega', 'Kericho', 'Kiambu', 'Kilifi',
  'Kirinyaga', 'Kisii', 'Kisumu', 'Kitui', 'Kwale', 'Laikipia', 'Lamu',
  'Machakos', 'Makueni', 'Mandera', 'Marsabit', 'Meru', 'Migori', 'Mombasa',
  'Murang\'a', 'Nairobi', 'Nakuru', 'Nandi', 'Narok', 'Nyamira', 'Nyandarua',
  'Nyeri', 'Samburu', 'Siaya', 'Taita-Taveta', 'Tana River', 'Tharaka-Nithi',
  'Trans Nzoia', 'Turkana', 'Uasin Gishu', 'Vihiga', 'Wajir', 'West Pokot'
];

export default function LoginPage() {
  const [selectedRole, setSelectedRole] = useState<UserRole>('national');
  const [selectedCounty, setSelectedCounty] = useState<string>('Nairobi');
  const [selectedFacilityId, setSelectedFacilityId] = useState<string>('FAC0001');

  const [facilities, setFacilities] = useState<FacilitySummary[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load facilities from FastAPI backend
  useEffect(() => {
    async function loadFacilities() {
      try {
        const data = await getFacilities();
        if (data && data.length > 0) {
          setFacilities(data);
          // Default to first facility
          setSelectedFacilityId(data[0].facility_id);
        }
      } catch (err: unknown) {
        const errMsg = err instanceof Error ? err.message : String(err);
        console.warn('Could not load facilities dynamically from backend, using fallback list:', errMsg);
        // Fallback standard facilities if backend is initializing
        const fallbackFacilities: FacilitySummary[] = [
          { facility_id: 'FAC0001', facility_name: 'Nairobi National Referral Hospital', county: 'Nairobi' },
          { facility_id: 'FAC0002', facility_name: 'Mombasa County Referral Hospital', county: 'Mombasa' },
          { facility_id: 'FAC0023', facility_name: 'Kiambu County Referral Hospital', county: 'Kiambu' },
          { facility_id: 'FAC0032', facility_name: 'Nakuru Level 5 Hospital', county: 'Nakuru' },
          { facility_id: 'FAC0045', facility_name: 'Kisumu District Hospital', county: 'Kisumu' },
        ];
        setFacilities(fallbackFacilities);
        setSelectedFacilityId('FAC0001');
      }
    }

    loadFacilities();
  }, []);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    let session: UserSession;

    if (selectedRole === 'national') {
      session = {
        role: 'national',
        userName: 'Executive Director (KEMSA HQ)',
        scopeBadge: 'All 47 Counties',
        loginTime: new Date().toISOString(),
      };
      setClientSession(session);
      window.location.href = '/national';
    } else if (selectedRole === 'county') {
      if (!selectedCounty) {
        setErrorMessage('Please select a county to proceed.');
        return;
      }
      session = {
        role: 'county',
        scopeId: selectedCounty,
        scopeName: `${selectedCounty} County`,
        userName: `County Health Director (${selectedCounty})`,
        loginTime: new Date().toISOString(),
      };
      setClientSession(session);
      window.location.href = '/county';
    } else if (selectedRole === 'facility') {
      const fac = facilities.find((f) => f.facility_id === selectedFacilityId);
      if (!fac) {
        setErrorMessage('Please select a valid health facility.');
        return;
      }
      session = {
        role: 'facility',
        scopeId: fac.facility_id,
        scopeName: fac.facility_name,
        userName: `Pharmacy Head (${fac.facility_name})`,
        loginTime: new Date().toISOString(),
      };
      setClientSession(session);
      window.location.href = '/facility';
    }
  };

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="flex justify-center">
          <div className="bg-emerald-700 text-white font-black text-2xl px-4 py-2 rounded-lg shadow-md tracking-wider">
            KEMSA
          </div>
        </div>
        <h2 className="mt-4 text-center text-2xl font-extrabold text-slate-900 tracking-tight">
          Supply Chain Intelligence Platform
        </h2>
        <p className="mt-1 text-center text-xs font-semibold text-slate-500 uppercase tracking-widest">
          Ministry of Health &bull; Republic of Kenya
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-lg">
        <div className="bg-white py-8 px-6 shadow-xl rounded-2xl sm:px-10 border border-slate-200">
          <div className="mb-6 pb-4 border-b border-slate-100">
            <h3 className="text-base font-semibold text-slate-800">
              Role-Based Workspace Sign-In
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Select your administrative role to access your dedicated operational workspace.
            </p>
          </div>

          {errorMessage && (
            <div className="mb-5 p-3.5 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2 text-sm text-red-700">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-6">
            {/* Role Selection Cards */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-3">
                1. Select Administrative Role
              </label>
              <div className="grid grid-cols-1 gap-3">
                {/* National Role */}
                <div
                  onClick={() => setSelectedRole('national')}
                  className={`relative flex items-center p-3.5 rounded-xl border-2 cursor-pointer transition-all ${
                    selectedRole === 'national'
                      ? 'border-emerald-600 bg-emerald-50/50 shadow-sm'
                      : 'border-slate-200 hover:border-slate-300 bg-white'
                  }`}
                >
                  <div className="p-2 rounded-lg bg-emerald-100 text-emerald-700 mr-3">
                    <Landmark className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-bold text-slate-900">
                      National Leadership
                    </div>
                    <div className="text-xs text-slate-500">
                      Executive situational awareness, country-wide risk map, aggregate demand
                    </div>
                  </div>
                  {selectedRole === 'national' && (
                    <ShieldCheck className="w-5 h-5 text-emerald-600 ml-2" />
                  )}
                </div>

                {/* County Role */}
                <div
                  onClick={() => setSelectedRole('county')}
                  className={`relative flex items-center p-3.5 rounded-xl border-2 cursor-pointer transition-all ${
                    selectedRole === 'county'
                      ? 'border-blue-600 bg-blue-50/50 shadow-sm'
                      : 'border-slate-200 hover:border-slate-300 bg-white'
                  }`}
                >
                  <div className="p-2 rounded-lg bg-blue-100 text-blue-700 mr-3">
                    <Building2 className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-bold text-slate-900">
                      County Health Department
                    </div>
                    <div className="text-xs text-slate-500">
                      Financial risk scorecard, explainability diagnostics, inter-facility transfer approvals
                    </div>
                  </div>
                  {selectedRole === 'county' && (
                    <ShieldCheck className="w-5 h-5 text-blue-600 ml-2" />
                  )}
                </div>

                {/* Facility Role */}
                <div
                  onClick={() => setSelectedRole('facility')}
                  className={`relative flex items-center p-3.5 rounded-xl border-2 cursor-pointer transition-all ${
                    selectedRole === 'facility'
                      ? 'border-purple-600 bg-purple-50/50 shadow-sm'
                      : 'border-slate-200 hover:border-slate-300 bg-white'
                  }`}
                >
                  <div className="p-2 rounded-lg bg-purple-100 text-purple-700 mr-3">
                    <Hospital className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-bold text-slate-900">
                      Facility / Hospital Management
                    </div>
                    <div className="text-xs text-slate-500">
                      30/60/90-day stockout countdowns, nearby surplus finder, transfer request submissions
                    </div>
                  </div>
                  {selectedRole === 'facility' && (
                    <ShieldCheck className="w-5 h-5 text-purple-600 ml-2" />
                  )}
                </div>
              </div>
            </div>

            {/* Dynamic Scope Selector */}
            {selectedRole === 'county' && (
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2 animate-fadeIn">
                <label htmlFor="county-select" className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                  2. Select Your County
                </label>
                <select
                  id="county-select"
                  value={selectedCounty}
                  onChange={(e) => setSelectedCounty(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-sm text-slate-800 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                >
                  {KENYA_COUNTIES.map((c) => (
                    <option key={c} value={c}>
                      {c} County
                    </option>
                  ))}
                </select>
                <p className="text-xs text-slate-500">
                  Access will be strictly restricted to {selectedCounty} County data.
                </p>
              </div>
            )}

            {selectedRole === 'facility' && (
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-2 animate-fadeIn">
                <label htmlFor="facility-select" className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                  2. Select Health Facility
                </label>
                <select
                  id="facility-select"
                  value={selectedFacilityId}
                  onChange={(e) => setSelectedFacilityId(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-white border border-slate-300 rounded-lg text-sm text-slate-800 focus:ring-2 focus:ring-purple-500 focus:outline-none"
                >
                  {facilities.map((f) => (
                    <option key={f.facility_id} value={f.facility_id}>
                      {f.facility_name} ({f.county}) [{f.facility_id}]
                    </option>
                  ))}
                </select>
                <p className="text-xs text-slate-500">
                  Access will be strictly restricted to this facility&apos;s inventory records.
                </p>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              className="w-full flex items-center justify-center space-x-2 py-3 px-4 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-sm shadow-md hover:shadow-lg transition-all"
            >
              <span>Sign In to {selectedRole.toUpperCase()} Workspace</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
