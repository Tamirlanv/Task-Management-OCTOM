import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { onSessionExpired, request, setSession } from './client';

const old = { access_token: 'old', refresh_token: 'refresh-old', expires_in: 900 };
const next = { access_token: 'next', refresh_token: 'refresh-next', expires_in: 900 };
const ok = (value: unknown) => new Response(JSON.stringify(value), { status: 200 });
beforeEach(() => setSession(old));
afterEach(() => {
  setSession(null);
  onSessionExpired(() => {});
  vi.unstubAllGlobals();
});

describe('access token renewal', () => {
  it('serializes concurrent refreshes and retries each request with the new token', async () => {
    const calls: string[] = [];
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/auth/refresh')) {
        calls.push(url);
        await new Promise((resolve) => setTimeout(resolve, 10));
        return ok(next);
      }
      return new Headers(init?.headers).get('Authorization') === 'Bearer next'
        ? ok({ value: url })
        : new Response(null, { status: 401 });
    });
    vi.stubGlobal('fetch', fetchMock);
    const results = await Promise.all([request('/first'), request('/second'), request('/third')]);
    expect(calls).toHaveLength(1);
    expect(results).toEqual([
      { value: '/api/v1/first' },
      { value: '/api/v1/second' },
      { value: '/api/v1/third' },
    ]);
    expect(fetchMock).toHaveBeenCalledTimes(7);
  });

  it('does not replay a failed rotation and clears the session once', async () => {
    const expired = vi.fn();
    onSessionExpired(expired);
    const fetchMock = vi.fn(async () => new Response(null, { status: 401 }));
    vi.stubGlobal('fetch', fetchMock);
    await expect(request('/first')).rejects.toMatchObject({ status: 401 });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(expired).toHaveBeenCalledTimes(1);
  });

  it('never clears a newer login when an older request returns 401', async () => {
    let resolve!: (result: Response) => void;
    vi.stubGlobal(
      'fetch',
      vi.fn(
        () =>
          new Promise<Response>((done) => {
            resolve = done;
          }),
      ),
    );
    const expired = vi.fn();
    onSessionExpired(expired);
    const pending = request('/slow');
    setSession(next);
    resolve(new Response(null, { status: 401 }));
    await expect(pending).rejects.toMatchObject({ status: 401 });
    expect(expired).not.toHaveBeenCalled();
  });

  it('surfaces rate limits without automatic retries', async () => {
    const fetchMock = vi.fn(
      async () => new Response(null, { status: 429, headers: { 'Retry-After': '30' } }),
    );
    vi.stubGlobal('fetch', fetchMock);
    await expect(request('/tasks')).rejects.toThrow('30 сек.');
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('discards successful responses belonging to a previous account', async () => {
    let resolve!: (result: Response) => void;
    vi.stubGlobal(
      'fetch',
      vi.fn(
        () =>
          new Promise<Response>((done) => {
            resolve = done;
          }),
      ),
    );
    const pending = request('/users/me');
    setSession(next);
    resolve(ok({ id: 'previous-user' }));
    await expect(pending).rejects.toMatchObject({ status: 401 });
  });
});
