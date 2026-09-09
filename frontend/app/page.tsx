'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getClientSession } from '@/lib/auth';

export default function RootPage() {
  const router = useRouter();

  useEffect(() => {
    const session = getClientSession();
    if (session && session.role) {
      router.replace(`/${session.role}`);
    } else {
      router.replace('/login');
    }
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100">
      <div className="text-center p-6">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-emerald-600 border-t-transparent mb-4"></div>
        <p className="text-sm font-medium text-slate-600">
          Redirecting to KEMSA Healthcare Intelligence Platform...
        </p>
      </div>
    </div>
  );
}
