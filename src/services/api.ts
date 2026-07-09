/**
 * Centered and Resilient API Client for Mastra Sentinel.
 * Communicates with the FastAPI backend on port 8000 via Vite's proxy on port 3000.
 * Includes automatic background authentication and graceful local fallback.
 */

const API_BASE = ''; // Relative path because of Vite server proxying
const DEFAULT_EMAIL = 'sivapanyam1@gmail.com';
const DEFAULT_PASSWORD = 'SreSentinel2026!';

let cachedToken: string | null = localStorage.getItem('sentinel_jwt_token');

export async function getAuthToken(): Promise<string | null> {
  if (cachedToken) {
    return cachedToken;
  }

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: DEFAULT_EMAIL, password: DEFAULT_PASSWORD }),
    });

    if (res.ok) {
      const data = await res.json();
      if (data.access_token) {
        cachedToken = data.access_token;
        localStorage.setItem('sentinel_jwt_token', cachedToken!);
        return cachedToken;
      }
    }
  } catch (err) {
    console.warn('Backend authentication failed or offline. Operating in resilient standalone mode.', err);
  }

  return null;
}

export async function apiRequest<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<{ data: T | null; error: Error | null; isMock: boolean }> {
  try {
    const token = await getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    } as Record<string, string>;

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers,
    });

    if (!res.ok) {
      // If unauthorized, clear cached token to force re-login next time
      if (res.status === 401) {
        cachedToken = null;
        localStorage.removeItem('sentinel_jwt_token');
      }
      throw new Error(`API returned error code ${res.status}: ${res.statusText}`);
    }

    const data = await res.json();
    return { data, error: null, isMock: false };
  } catch (err: any) {
    return { data: null, error: err, isMock: true };
  }
}
