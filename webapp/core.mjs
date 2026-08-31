// Browser timing is an estimate, never an evaluated end-to-end accuracy bound.
export const frac = x => ((x % 1) + 1) % 1;
const finite = x => typeof x === 'number' && Number.isFinite(x);
function quality(q) {
  if (!q || ![1, 2, 3].includes(q.state) || !Number.isInteger(q.stratum) || q.stratum < 0 || q.stratum > 15) throw Error('quality');
  if (q.validity_seconds !== null && (!finite(q.validity_seconds) || q.validity_seconds < 0 || q.validity_seconds > 3600)) throw Error('validity');
}
export function accept(data, nonce, sent, received, wall) {
  const rtt = (received - sent) / 1000;
  if (data.schema !== 'nepp-web-1' || data.protocol_version !== 2 || data.nonce !== nonce || !finite(rtt) || rtt < 0 || rtt > 3) throw Error('exchange');
  if (!finite(data.processing_seconds) || data.processing_seconds < 0 || data.processing_seconds > rtt) throw Error('timing');
  const e = data.ed;
  if (!e || !Number.isInteger(e.year) || e.year < -2147483648 || e.year > 2147483647 || typeof e.fraction !== 'string' || !/^0(?:\.\d+)?$/.test(e.fraction) || !finite(Number(e.fraction)) || Number(e.fraction) >= 1 || !finite(e.rate) || e.rate <= 0 || e.model_id !== 1) throw Error('ED');
  quality(e.quality);
  if (e.quality.stratum === 0) throw Error('stratum');
  if (!finite(data.max_extrapolation_seconds) || data.max_extrapolation_seconds < 0 || data.max_extrapolation_seconds > 300) throw Error('age');
  let solar = data.solar;
  try {
    if (!solar || !finite(solar.phase) || solar.phase < 0 || solar.phase >= 1 || !finite(solar.rate) || solar.rate <= 0 || solar.model_id !== 1) throw Error('SP');
    quality(solar.quality);
  } catch { solar = null; }
  return {...data, solar, received, wall, rtt, oneWay: (rtt - data.processing_seconds) / 2};
}
export function display(sample, now, wall, longitude) {
  if (!sample) return null;
  const elapsed = (now - sample.received) / 1000;
  const age = elapsed + sample.oneWay;
  if (elapsed < 0 || Math.abs((wall - sample.wall) / 1000 - elapsed) > 1 || age > sample.max_extrapolation_seconds) return null;
  const f = Number(sample.ed.fraction) + sample.ed.rate * age;
  // Keep year and fraction separate; adding a large year loses sub-second digits.
  let year = sample.ed.year + Math.floor(f);
  let digits = (f - Math.floor(f)).toFixed(10).slice(2);
  if ((f - Math.floor(f)).toFixed(10) === '1.0000000000') { year++; digits = '0000000000'; }
  const s = sample.solar;
  const phase = s && finite(longitude) ? frac(s.phase + s.rate * age + longitude / 360) : null;
  const stale = q => q.state === 2 || (q.validity_seconds !== null && age > q.validity_seconds);
  return {ed: `${year}.${digits}`, phase, sp: phase === null ? '—' : (Math.floor(phase * 1e6) / 1e6).toFixed(6), stale: stale(sample.ed.quality) || !!(s && stale(s.quality)), age};
}
export const retryDelay = failures => Math.min(60000, 2000 * 2 ** Math.min(5, failures - 1));

// Observed on macOS Safari: GeolocationPosition.timestamp uses the 2001 epoch.
// This is a narrowly gated compatibility heuristic, not a change to the API's
// Unix-ms contract. Never replace a timestamp with "now" or alter ED timing.
export function normalizeLocationTimestamp(timestamp, now) {
  if (!Number.isFinite(timestamp) || !Number.isFinite(now)) return null;
  const age = now - timestamp;
  if (Math.abs(age) <= 300000) return {timestamp, epochCorrected:false};
  const corrected = timestamp + 978307200000;
  const correctedAge = now - corrected;
  if (timestamp >= 0 && age > 300000 && correctedAge >= 0 && correctedAge <= 300000)
    return {timestamp:corrected, epochCorrected:true};
  return null;
}

// The browser timeout may exclude permission waiting. Bound the whole request
// separately; ignore callbacks from timed-out, cancelled or replaced requests.
export function requestLocation(geo, report, {secure = true, schedule = setTimeout,
  unschedule = clearTimeout, now = Date.now} = {}) {
  let active = true, timer;
  const cancel = () => { active = false; unschedule(timer); };
  const finish = (state, fix = null, diagnostic = null) => {
    if (!active) return;
    cancel(); report(state, fix, diagnostic);
  };
  if (!secure) { finish('geoInsecure'); return cancel; }
  if (!geo) { finish('geoUnsupported'); return cancel; }
  report('locating', null);
  timer = schedule(() => finish('geoNoReply'), 20000);
  try {
    geo.getCurrentPosition(position => {
      const c = position?.coords;
      if (!c || !Number.isFinite(c.longitude) || c.longitude < -180 || c.longitude > 180 ||
          !Number.isFinite(c.latitude) || Math.abs(c.latitude) > 90) {
        finish('geoInvalidCoordinates'); return;
      }
      if (!Number.isFinite(position.timestamp)) { finish('geoInvalidTimestamp'); return; }
      const received = now();
      const ageMs = received - position.timestamp;
      if (!Number.isFinite(ageMs)) { finish('geoInvalidTimestamp'); return; }
      const normalized = normalizeLocationTimestamp(position.timestamp, received);
      if (!normalized) {
        finish(ageMs > 0 ? 'geoOld' : 'geoFuture', null,
          {seconds:Math.round(Math.abs(ageMs) / 1000)}); return;
      }
      if (Math.abs(c.latitude) >= 89.9) { finish('geoPole'); return; }
      const fix = {longitude:c.longitude, timestamp:normalized.timestamp};
      if (normalized.epochCorrected) fix.epochCorrected = true;
      finish('current', fix);
    }, error => finish(({1:'geoDenied',2:'geoUnavailable',3:'geoTimeout'})[error?.code] ?? 'geoUnknown'),
    {enableHighAccuracy:false,maximumAge:60000,timeout:15000});
  } catch { finish('geoUnknown'); }
  return cancel;
}
