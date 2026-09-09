'use client';

import React from 'react';
import { clearClientSession, getClientSession, formatSessionDisplay, UserSession } from '@/lib/auth';
import { LogOut, Building2, Landmark, Hospital, UserCheck } from 'lucide-react';

interface NavbarProps {
  currentSession?: UserSession | null;
}

export default function Navbar({ currentSession }: NavbarProps) {
  const [session, setSession] = React.useState<UserSession | null>(currentSession || null);

  React.useEffect(() => {
    if (!currentSession) {
      const active = getClientSession();
      setSession(active);
    }
  }, [currentSession]);

  const handleLogout = () => {
    clearClientSession();
    // Force a full refresh to ensure all cookies and cached middleware state are cleared
    window.location.href = '/login';
  };

  const { roleTitle, scopeBadge } = formatSessionDisplay(session);

  const getRoleIcon = () => {
    if (!session) return <UserCheck className="w-5 h-5 text-slate-400" />;
    switch (session.role) {
      case 'national':
        return <Landmark className="w-5 h-5 text-emerald-600" />;
      case 'county':
        return <Building2 className="w-5 h-5 text-blue-600" />;
      case 'facility':
        return <Hospital className="w-5 h-5 text-purple-600" />;
    }
  };

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
      {/* Top Republic Color Band */}
      <div className="h-1 w-full bg-gradient-to-r from-emerald-600 via-amber-500 to-sky-600" />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Brand & Institutional Title */}
          <div className="flex items-center space-x-3.5">
            {/* Official KEMSA Institutional Logotype with 3 Angled Capsule Pills */}
            <div className="flex items-center space-x-2.5 bg-slate-900 text-white px-3 py-1.5 rounded-lg shadow-sm">
              <div className="flex items-center space-x-1">
                <span
                  className="inline-block w-1.5 h-3.5 rounded-full bg-[#00A859] transform rotate-[32deg]"
                  title="Clinical Emerald"
                />
                <span
                  className="inline-block w-1.5 h-3.5 rounded-full bg-[#FF7A00] transform rotate-[32deg]"
                  title="Logistics Amber"
                />
                <span
                  className="inline-block w-1.5 h-3.5 rounded-full bg-[#0EA5E9] transform rotate-[32deg]"
                  title="Executive Cyan"
                />
              </div>
              <div className="h-4 w-px bg-slate-700" />
              <div className="flex items-baseline space-x-1">
                <span className="font-black text-base tracking-[0.16em] text-white">
                  KEMSA
                </span>
                <span className="font-extrabold text-xs tracking-wider text-emerald-400">
                  INTELLIGENCE
                </span>
              </div>
            </div>

            {/* Official Subtitle */}
            <div className="hidden sm:block">
              <h1 className="text-sm font-bold text-slate-900 leading-tight">
                Healthcare Supply Chain Intelligence Platform
              </h1>
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">
                KENYA MEDICAL SUPPLIES AUTHORITY &bull; REPUBLIC OF KENYA
              </p>
            </div>
          </div>

          {/* Live Network Status & User Session */}
          <div className="flex items-center space-x-3 sm:space-x-4">
            {/* Live Operational Network Status Badge */}
            <div className="hidden lg:inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold shadow-2xs">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-600"></span>
              </span>
              <span>Supply Chain Network Active</span>
            </div>

            {session && (
              <div className="hidden sm:flex items-center bg-slate-50 border border-slate-200 rounded-lg px-3 py-1.5 space-x-2.5">
                <div className="p-1 rounded-md bg-white shadow-xs border border-slate-200">
                  {getRoleIcon()}
                </div>
                <div className="text-left text-xs">
                  <div className="font-semibold text-slate-800">
                    Logged in as: <span className="text-emerald-700 font-bold">{roleTitle}</span>
                  </div>
                  <div className="text-slate-600 font-medium truncate max-w-[220px]" title={scopeBadge}>
                    Scope: {scopeBadge}
                  </div>
                </div>
              </div>
            )}

            <button
              onClick={handleLogout}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 border border-slate-300 rounded-md text-xs font-semibold text-slate-700 bg-white hover:bg-slate-100 hover:text-red-700 hover:border-red-300 transition-colors shadow-xs"
              title="End session and return to login"
            >
              <LogOut className="w-4 h-4" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
