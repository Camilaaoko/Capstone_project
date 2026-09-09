'use client';

import React from 'react';
import Navbar from './Navbar';
import { UserSession } from '@/lib/auth';

interface ShellLayoutProps {
  children: React.ReactNode;
  session?: UserSession | null;
}

export default function ShellLayout({ children, session }: ShellLayoutProps) {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
      <Navbar currentSession={session} />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {children}
      </main>
      <footer className="bg-white border-t border-slate-200 py-3 text-center text-xs text-slate-500">
        KEMSA Healthcare Supply Chain Intelligence Platform &bull; Diagnostic &bull; Predictive &bull; Prescriptive
      </footer>
    </div>
  );
}
