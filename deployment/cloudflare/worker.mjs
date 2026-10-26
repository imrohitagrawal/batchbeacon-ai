/** Fixed-host edge adapter. Backend still owns CSRF, sessions and authorization. */
function configuration(env) {
  const origin = (value) => {
    if (typeof value !== 'string') throw new Error('Missing origin');
    const url = new URL(value);
    if (url.protocol !== 'https:' || url.origin !== value || url.username || url.password)
      throw new Error('Invalid origin');
    return url;
  };
  const publicUrl = origin(env.PUBLIC_ORIGIN);
  const upstream = origin(env.UPSTREAM_ORIGIN);
  const timeout = Number(env.UPSTREAM_TIMEOUT_MS);
  if (!/^[1-9][0-9]*$/.test(String(env.UPSTREAM_TIMEOUT_MS)) || !Number.isSafeInteger(timeout) || timeout > 2147483647 || publicUrl.origin === upstream.origin)
    throw new Error('Invalid timeout or destination');
  return {publicUrl, upstream, timeout};
}
const failure = (status) => new Response('Request unavailable.', {
  status, headers: {'Cache-Control': 'private, no-store', 'Content-Type': 'text/plain', 'X-Content-Type-Options': 'nosniff'},
});
export default {
  async fetch(request, env) {
    let config;
    try { config = configuration(env); } catch { return failure(503); }
    const incoming = new URL(request.url);
    const host = request.headers.get('host');
    if (incoming.origin !== config.publicUrl.origin || (host !== null && host !== config.publicUrl.host)) return failure(403);
    if (!['GET', 'HEAD', 'POST'].includes(request.method)) return failure(405);
    const origin = request.headers.get('origin');
    if ((request.method === 'POST' && origin === null) || (origin !== null && origin !== config.publicUrl.origin)) return failure(403);
    const cookies = (request.headers.get('cookie') || '').split(';').map(v => v.trim()).filter(v => v.split('=')[0] === '__Host-bb_guest');
    if (cookies.length > 1) return failure(403);
    const headers = new Headers(request.headers);
    for (const name of [...headers.keys()]) {
      if (['host', 'authorization', 'proxy-authorization', 'x-serverless-authorization', 'forwarded', 'cookie'].includes(name) || name.startsWith('x-forwarded-')) headers.delete(name);
    }
    if (cookies.length) headers.set('cookie', cookies[0]);
    if (origin !== null) headers.set('origin', config.upstream.origin);
    const destination = new URL(config.upstream);
    destination.pathname = incoming.pathname;
    destination.search = incoming.search;
    const abort = new AbortController();
    const timer = setTimeout(() => abort.abort(), config.timeout);
    try {
      const upstream = await fetch(destination, {
        method: request.method, headers,
        body: request.method === 'POST' ? request.body : undefined,
        duplex: 'half', redirect: 'manual', signal: abort.signal,
        cache: 'no-store',
      });
      if (upstream.status >= 300 && upstream.status < 400) return failure(502);
      const output = new Headers(upstream.headers);
      const setCookies = typeof output.getSetCookie === 'function' ? output.getSetCookie() : (output.get('set-cookie') ? [output.get('set-cookie')] : []);
      for (const cookie of setCookies) {
        if (!cookie.startsWith('__Host-bb_guest=') || /;\s*domain\s*=/i.test(cookie) || !/;\s*secure(?:;|$)/i.test(cookie) || !/;\s*httponly(?:;|$)/i.test(cookie) || !/;\s*samesite=strict(?:;|$)/i.test(cookie) || !/;\s*path=\/(?:;|$)/i.test(cookie)) return failure(502);
      }
      const noTransform=(output.get('Cache-Control') || '').split(',').some(v=>v.trim()==='no-transform');
      output.set('Cache-Control', 'private, no-store'+(noTransform?', no-transform':''));
      output.delete('CDN-Cache-Control');
      output.delete('Cloudflare-CDN-Cache-Control');
      for (const name of [...output.keys()]) if (name.startsWith('access-control-')) output.delete(name);
      return new Response(upstream.body, {status: upstream.status, statusText: upstream.statusText, headers: output});
    } catch { return failure(502); }
    finally { clearTimeout(timer); }
  },
};
