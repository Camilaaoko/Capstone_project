'use client';

import React, { Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { ShieldAlert, ArrowLeft, LogOut } from 'lucide-react';
import { getClientSession, clearClientSession, UserSession } from '@/lib/auth';

function AccessDeniedContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [session, setSession] = React.useState<UserSession | null>(null);

  React.useEffect(() => {
    setSession(getClientSession());
  }, []);

  const reason = searchParams.get('reason') || 'unauthorized';
  const required = searchParams.get('required');
  const actual = searchParams.get('actual') || session?.role;
  const attempted = searchParams.get('attempted');
  const authorized = searchParams.get('authorized') || session?.scopeId;

  const handleReturnToDashboard = () => {
    if (session && session.role) {
      router.push(`/${session.role}`);
    } else {
      router.push('/login');
    }
  };

  const handleSwitchAccount = () => {
    clearClientSession();
    window.location.href = '/login';
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg border border-red-200 p-6 sm:p-8 text-center">
        <div className="mx-auto w-14 h-14 rounded-full bg-red-100 flex items-center justify-center text-red-600 mb-4">
          <ShieldAlert className="w-8 h-8" />
        </div>

        <h1 className="text-xl font-bold text-slate-900 mb-2">
          Access Denied
        </h1>

        {reason === 'role_mismatch' && (
          <div className="text-sm text-slate-600 space-y-2 mb-6 text-left bg-slate-50 p-3.5 rounded-lg border border-slate-200">
            <p>
              <span className="font-semibold text-slate-800">Permission Mismatch:</span> This section requires <span className="font-bold text-red-700 capitalize">{required}</span> privileges.
            </p>
            <p>
              Your active session is authenticated as <span className="font-bold text-slate-800 capitalize">{actual || 'Unknown'}</span>. Under the KEMSA platform access rules, users cannot view or navigate across role boundaries.
            </p>
          </div>
        )}

        {reason === 'county_scope_violation' && (
          <div className="text-sm text-slate-600 space-y-2 mb-6 text-left bg-slate-50 p-3.5 rounded-lg border border-slate-200">
            <p>
              <span className="font-semibold text-slate-800">County Scope Violation:</span> You attempted to access data for <span className="font-bold text-red-700">{attempted}</span>.
            </p>
            <p>
              Your account is strictly scoped to <span className="font-bold text-emerald-700">{authorized}</span>. You cannot modify URLs to inspect other counties.
            </p>
          </div>
        )}

        {reason === 'facility_scope_violation' && (
          <div className="text-sm text-slate-600 space-y-2 mb-6 text-left bg-slate-50 p-3.5 rounded-lg border border-slate-200">
            <p>
              <span className="font-semibold text-slate-800">Facility Scope Violation:</span> You attempted to access inventory records for <span className="font-bold text-red-700">{attempted}</span>.
            </p>
            <p>
              Your account is strictly scoped to <span className="font-bold text-emerald-700">{authorized}</span>. You cannot modify URLs to inspect other facilities.
            </p>
          </div>
        )}

        {reason !== 'role_mismatch' && reason !== 'county_scope_violation' && reason !== 'facility_scope_violation' && (
          <p className="text-sm text-slate-600 mb-6">
            You do not have the necessary permissions to view this resource.
          </p>
        )}

        <div className="space-y-2.5">
          {session && (
            <button
              onClick={handleReturnToDashboard}
              className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm transition-colors shadow-sm"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Return to My Authorized Dashboard ({session.role})</span>
            </button>
          )}

          <button
            onClick={handleSwitchAccount}
            className="w-full flex items-center justify-center space-x-2 py-2 px-4 rounded-lg border border-slate-300 hover:bg-slate-100 text-slate-700 font-medium text-sm transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Switch Role or Re-Login</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export default function AccessDeniedPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-slate-500">Loading access status...</div>}>
      <AccessDeniedContent />
    </Suspense>
  );
}
