/**
 * Role-based Authentication and Session Management for KEMSA Platform
 */

export type UserRole = 'national' | 'county' | 'facility';

export interface UserSession {
  role: UserRole;
  scopeId?: string;    // e.g. 'Kiambu' for county, 'FAC0001' for facility
  scopeName?: string;  // e.g. 'Kiambu County', 'Nairobi National Referral Hospital'
  scopeBadge?: string; // e.g. 'All 47 Counties'
  userName?: string;   // e.g. 'Dr. Alice Wanjiku'
  loginTime?: string;
}

export const SESSION_COOKIE_NAME = 'kemsa_session';

/**
 * Parses session from cookie header or raw string (safe for both browser & server/middleware)
 */
export function parseSession(cookieValue?: string | null): UserSession | null {
  if (!cookieValue) return null;
  try {
    const decoded = decodeURIComponent(cookieValue);
    const session = JSON.parse(decoded) as UserSession;
    if (session && session.role && ['national', 'county', 'facility'].includes(session.role)) {
      return session;
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Client-side: Read current active session from document.cookie
 */
export function getClientSession(): UserSession | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie
    .split('; ')
    .find((row) => row.startsWith(`${SESSION_COOKIE_NAME}=`));
  if (!match) return null;
  const val = match.split('=')[1];
  return parseSession(val);
}

/**
 * Client-side: Save session to document.cookie (24 hour expiration)
 */
export function setClientSession(session: UserSession): void {
  if (typeof document === 'undefined') return;
  const jsonStr = JSON.stringify(session);
  const encoded = encodeURIComponent(jsonStr);
  const maxAge = 60 * 60 * 24; // 24 hours
  document.cookie = `${SESSION_COOKIE_NAME}=${encoded}; path=/; max-age=${maxAge}; SameSite=Lax`;
}

/**
 * Client-side: Delete session cookie
 */
export function clearClientSession(): void {
  if (typeof document === 'undefined') return;
  document.cookie = `${SESSION_COOKIE_NAME}=; path=/; max-age=0; SameSite=Lax`;
}

/**
 * Format user role and scope for UI display
 */
export function formatSessionDisplay(session: UserSession | null): { roleTitle: string; scopeBadge: string } {
  if (!session) {
    return { roleTitle: 'Guest', scopeBadge: 'Not Authenticated' };
  }

  switch (session.role) {
    case 'national':
      return {
        roleTitle: 'National Leadership',
        scopeBadge: 'All 47 Counties (Country-wide)',
      };
    case 'county':
      return {
        roleTitle: 'County Health Department',
        scopeBadge: session.scopeName || `${session.scopeId || 'Unknown'} County`,
      };
    case 'facility':
      return {
        roleTitle: 'Facility Management',
        scopeBadge: session.scopeName || session.scopeId || 'Facility',
      };
    default:
      return { roleTitle: 'Unknown Role', scopeBadge: 'None' };
  }
}
