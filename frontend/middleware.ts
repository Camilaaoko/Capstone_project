import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { parseSession, SESSION_COOKIE_NAME } from './lib/auth';

export function middleware(request: NextRequest) {
  const { pathname, searchParams } = request.nextUrl;
  const cookieValue = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  const session = parseSession(cookieValue);

  // 1. Root redirect
  if (pathname === '/') {
    if (!session) {
      return NextResponse.redirect(new URL('/login', request.url));
    }
    return NextResponse.redirect(new URL(`/${session.role}`, request.url));
  }

  // 2. Login route: if already authenticated, redirect to authorized dashboard
  if (pathname === '/login') {
    if (session) {
      return NextResponse.redirect(new URL(`/${session.role}`, request.url));
    }
    return NextResponse.next();
  }

  // 3. Protected Route: /national
  if (pathname === '/national' || pathname.startsWith('/national/')) {
    if (!session) {
      return NextResponse.redirect(new URL('/login?redirect=/national', request.url));
    }
    if (session.role !== 'national') {
      const deniedUrl = new URL('/access-denied', request.url);
      deniedUrl.searchParams.set('reason', 'role_mismatch');
      deniedUrl.searchParams.set('required', 'national');
      deniedUrl.searchParams.set('actual', session.role);
      deniedUrl.searchParams.set('target', pathname);
      return NextResponse.redirect(deniedUrl);
    }
    return NextResponse.next();
  }

  // 4. Protected Route: /county
  if (pathname === '/county' || pathname.startsWith('/county/')) {
    if (!session) {
      return NextResponse.redirect(new URL('/login?redirect=/county', request.url));
    }
    if (session.role !== 'county') {
      const deniedUrl = new URL('/access-denied', request.url);
      deniedUrl.searchParams.set('reason', 'role_mismatch');
      deniedUrl.searchParams.set('required', 'county');
      deniedUrl.searchParams.set('actual', session.role);
      deniedUrl.searchParams.set('target', pathname);
      return NextResponse.redirect(deniedUrl);
    }

    // Scope check: ensure county user cannot view another county via query params or path
    const requestedCounty = searchParams.get('county');
    if (requestedCounty && session.scopeId && requestedCounty.toLowerCase() !== session.scopeId.toLowerCase()) {
      const deniedUrl = new URL('/access-denied', request.url);
      deniedUrl.searchParams.set('reason', 'county_scope_violation');
      deniedUrl.searchParams.set('attempted', requestedCounty);
      deniedUrl.searchParams.set('authorized', session.scopeId);
      return NextResponse.redirect(deniedUrl);
    }

    const segments = pathname.split('/').filter(Boolean);
    if (segments.length > 1 && session.scopeId) {
      const pathCounty = decodeURIComponent(segments[1]);
      if (pathCounty.toLowerCase() !== session.scopeId.toLowerCase()) {
        const deniedUrl = new URL('/access-denied', request.url);
        deniedUrl.searchParams.set('reason', 'county_scope_violation');
        deniedUrl.searchParams.set('attempted', pathCounty);
        deniedUrl.searchParams.set('authorized', session.scopeId);
        return NextResponse.redirect(deniedUrl);
      }
    }

    return NextResponse.next();
  }

  // 5. Protected Route: /facility
  if (pathname === '/facility' || pathname.startsWith('/facility/')) {
    if (!session) {
      return NextResponse.redirect(new URL('/login?redirect=/facility', request.url));
    }
    if (session.role !== 'facility') {
      const deniedUrl = new URL('/access-denied', request.url);
      deniedUrl.searchParams.set('reason', 'role_mismatch');
      deniedUrl.searchParams.set('required', 'facility');
      deniedUrl.searchParams.set('actual', session.role);
      deniedUrl.searchParams.set('target', pathname);
      return NextResponse.redirect(deniedUrl);
    }

    // Scope check: ensure facility user cannot view another facility via query params or path
    const requestedFacility = searchParams.get('facility_id') || searchParams.get('id');
    if (requestedFacility && session.scopeId && requestedFacility.toLowerCase() !== session.scopeId.toLowerCase()) {
      const deniedUrl = new URL('/access-denied', request.url);
      deniedUrl.searchParams.set('reason', 'facility_scope_violation');
      deniedUrl.searchParams.set('attempted', requestedFacility);
      deniedUrl.searchParams.set('authorized', session.scopeId);
      return NextResponse.redirect(deniedUrl);
    }

    const segments = pathname.split('/').filter(Boolean);
    if (segments.length > 1 && session.scopeId) {
      const pathFacility = decodeURIComponent(segments[1]);
      if (pathFacility.toLowerCase() !== session.scopeId.toLowerCase()) {
        const deniedUrl = new URL('/access-denied', request.url);
        deniedUrl.searchParams.set('reason', 'facility_scope_violation');
        deniedUrl.searchParams.set('attempted', pathFacility);
        deniedUrl.searchParams.set('authorized', session.scopeId);
        return NextResponse.redirect(deniedUrl);
      }
    }

    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/',
    '/login',
    '/national/:path*',
    '/county/:path*',
    '/facility/:path*',
  ],
};
