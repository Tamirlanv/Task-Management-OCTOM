import { ApiError } from './errors';
import type { Tokens } from './types';

// Credentials live only in memory. Reloading the page starts a new login session.
let tokens: Tokens | null = null;
let revision = 0;
let refreshFlight: Promise<void> | null = null;
let expired: () => void = () => {};

export function onSessionExpired(callback: () => void) {
  expired = callback;
}
export function setSession(value: Tokens | null) {
  revision += 1;
  tokens = value;
}

async function response<T>(result: Response): Promise<T> {
  if (!result.ok) throw new ApiError(result.status, result.headers.get('Retry-After'));
  return result.status === 204 ? (undefined as T) : (result.json() as Promise<T>);
}

export async function publicRequest<T>(path: string, body: unknown): Promise<T> {
  return response<T>(
    await fetch(`/api/v1${path}`, {
      method: 'POST',
      signal: AbortSignal.timeout(15_000),
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  );
}

async function refresh(): Promise<void> {
  if (refreshFlight) return refreshFlight;
  if (!tokens) throw new ApiError(401);
  const current = revision;
  const credential = tokens.refresh_token;
  refreshFlight = (async () => {
    try {
      const next = await publicRequest<Tokens>('/auth/refresh', { refresh_token: credential });
      if (revision === current) tokens = next;
    } catch (error) {
      // A lost rotation response cannot safely be replayed. Require a new login.
      if (revision === current) {
        setSession(null);
        expired();
      }
      throw error;
    } finally {
      refreshFlight = null;
    }
  })();
  return refreshFlight;
}

export async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const current = revision;
  const credential = tokens?.access_token;
  const send = () =>
    fetch(`/api/v1${path}`, {
      ...options,
      signal: options.signal
        ? AbortSignal.any([options.signal, AbortSignal.timeout(15_000)])
        : AbortSignal.timeout(15_000),
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
        ...(tokens ? { Authorization: `Bearer ${tokens.access_token}` } : {}),
      },
    });
  let result = await send();
  if (result.status === 401 && tokens && current === revision) {
    if (credential === tokens.access_token) await refresh();
    if (current !== revision) throw new ApiError(401);
    result = await send();
  }
  if (result.status === 401 && current === revision) {
    setSession(null);
    expired();
  }
  if (current !== revision) throw new ApiError(401);
  return response<T>(result);
}

export function write<T>(path: string, method: 'POST' | 'PATCH' | 'DELETE', data?: unknown) {
  return request<T>(path, {
    method,
    ...(data === undefined ? {} : { body: JSON.stringify(data) }),
  });
}

export async function logout(): Promise<void> {
  await refreshFlight?.catch(() => {});
  const credential = tokens?.refresh_token;
  setSession(null);
  if (credential) await publicRequest<void>('/auth/logout', { refresh_token: credential });
}
