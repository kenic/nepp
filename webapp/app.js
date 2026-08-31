import {accept, display, retryDelay, requestLocation} from './core.mjs';
const $ = id => document.getElementById(id);
const words = {
  en: {tagline:'ONE EARTH. A SHARED NOW.',earth:'EARTH DATE',solar:'SOLAR PHASE',now:'now, on our planet',midnight:'0 · Midnight',noon:'0.5 · Solar noon',refresh:'Refresh',details:'Details ↗',experimental:'EXPERIMENTAL · WEB 0.0.2',about:'About NEPP ↗',settings:'Settings',done:'Done',location:'Use current location',private:'Your coordinates stay on this device. ED does not need location.',longitude:'Manual longitude (east positive)',apply:'Apply',greenwich:'Use Greenwich',install:'On iPhone: Share → Add to Home Screen. A network connection is required.',privacy:'Privacy',support:'Support',accuracy:'Digits are not an accuracy guarantee. HTTP delay is estimated assuming a symmetric path; browser timing and network asymmetry are unassessed.',connecting:'Connecting…',unavailable:'No response · retrying',live:'Receiving · accuracy unassessed',retry:'Reconnecting · estimated',stale:'Stale · estimated',current:'Current location',last:'Last known location',needed:'Location needed',manual:'Manual longitude',locating:'Finding your location…',denied:'Location unavailable. Allow access in browser settings, or choose a manual longitude / Greenwich.',invalid:'Enter a longitude between −180 and 180.',source:'Source stratum',quality:'Quality supplied by server',roundtrip:'HTTP round trip (seconds)',age:'Seconds since server snapshot',unknown:'Unknown',state:'Supply state',bound:'Source bound (not end-to-end)',validity:'Source validity (seconds)',tracking:'Tracking',holdover:'Holdover',unassessed:'Unknown / unassessed'},
  ja: {tagline:'ひとつの地球。共通の「今」。',earth:'EARTH DATE · 地球日付',solar:'SOLAR PHASE · 太陽位相',now:'この惑星の、いま',midnight:'0 · 太陽の真夜中',noon:'0.5 · 太陽の正午',refresh:'更新',details:'詳細 ↗',experimental:'実験版 · WEB 0.0.2',about:'NEPPについて ↗',settings:'設定',done:'完了',location:'現在地を使う',private:'座標はこの端末内だけで扱います。EDに位置情報は不要です。',longitude:'手動の経度（東経を正の値で入力）',apply:'適用',greenwich:'グリニッジを使う',install:'iPhoneでは「共有」→「ホーム画面に追加」で配置できます。通信接続が必要です。',privacy:'プライバシー',support:'サポート',accuracy:'桁数は精度の保証ではありません。HTTPの通信遅延は往復対称と仮定した推定です。ブラウザの計時誤差と通信の非対称性は未評価です。',connecting:'接続中…',unavailable:'応答なし · 再接続中',live:'受信中 · 精度未評価',retry:'再接続中 · 推定表示',stale:'有効期間外 · 推定表示',current:'現在地',last:'最後に取得した現在地',needed:'位置情報が必要です',manual:'手動の経度',locating:'現在地を取得中…',denied:'現在地を取得できません。ブラウザの設定で許可するか、手動経度・グリニッジを選んでください。',invalid:'−180〜180の経度を入力してください。',source:'基準源のStratum',quality:'サーバーが伝える品質',roundtrip:'HTTP往復時間（秒）',age:'サーバーの基準時点からの秒数',unknown:'不明',state:'供給状態',bound:'基準源の誤差上限（全経路の保証ではありません）',validity:'基準源の有効期間（秒）',tracking:'追従中',holdover:'保持・外挿中',unassessed:'不明・未評価'}
};
Object.assign(words.en, {
  geoDenied:'Location permission denied (code 1). Check both site and browser permissions.',
  geoUnavailable:'Your device could not determine its location (code 2).',
  geoTimeout:'Location acquisition timed out (code 3). Try again.',
  geoNoReply:'No location response after 20 seconds. Check any permission prompt, then try again.',
  geoUnsupported:'This browser does not provide location access.',
  geoInsecure:'Location requires HTTPS or a localhost page.',
  geoInvalidCoordinates:'The browser returned invalid coordinates.',
  geoInvalidTimestamp:'The browser returned a missing or invalid location timestamp.',
  geoOld:'The location timestamp is {seconds} seconds old (limit: 300 s). Try again.',
  geoFuture:'The location timestamp is {seconds} seconds in the future (limit: 300 s). Check the Mac clock.',
  geoPole:'Local solar phase is not supported this close to a pole.',
  geoUnknown:'An unexpected location error occurred. Try again.',
  retryLocation:'Retry location',
  locationEpoch:'Location timestamp',
  epochCorrected:'2001 → 1970 epoch workaround applied (inferred).',
  epochStandard:'Standard Unix timestamp; no correction.'
});
Object.assign(words.ja, {
  geoDenied:'位置情報が拒否されました（コード1）。サイトとブラウザ両方の許可を確認してください。',
  geoUnavailable:'端末が現在地を特定できませんでした（コード2）。',
  geoTimeout:'現在地の取得がタイムアウトしました（コード3）。再試行してください。',
  geoNoReply:'20秒間、位置情報の応答がありません。許可の確認画面がないか確認し、再試行してください。',
  geoUnsupported:'このブラウザは位置情報の取得に対応していません。',
  geoInsecure:'位置情報にはHTTPSまたはlocalhostのページが必要です。',
  geoInvalidCoordinates:'ブラウザが返した緯度・経度が無効です。',
  geoInvalidTimestamp:'位置情報の取得時刻が欠けているか、無効な値です。',
  geoOld:'位置情報の取得時刻が現在より{seconds}秒古くなっています（許容：300秒）。再試行してください。',
  geoFuture:'位置情報の取得時刻が現在より{seconds}秒未来になっています（許容：300秒）。Macの時計を確認してください。',
  geoPole:'極に近いため、この地点の太陽位相には対応していません。',
  geoUnknown:'位置情報の取得で予期しないエラーが発生しました。再試行してください。',
  retryLocation:'現在地を再取得',
  locationEpoch:'位置情報の取得時刻',
  epochCorrected:'2001年 → 1970年の起点補正を使用（推定による回避策）。',
  epochStandard:'通常のUNIX時刻。補正なし。'
});
const read = (key, fallback) => {try {return localStorage.getItem(key) ?? fallback;} catch {return fallback;}};
const save = (key, value) => {try {localStorage.setItem(key, value);} catch { /* Private browsing still works. */ }};
let lang = read('nepp.web.language', navigator.language.startsWith('ja') ? 'ja' : 'en');
if (!words[lang]) lang = 'en';
let mode = read('nepp.web.location', 'current');
if (!['current','greenwich'].includes(mode)) mode = 'current';
let fix = null, manual = null, geoPending = false, geoTimer, cancelGeo = () => {}, geoStatus = 'needed', inputError = false;
let geoDiagnostic = null;
function locationMessage() {
  return t(geoStatus).replace('{seconds}', geoDiagnostic?.seconds?.toLocaleString(lang) ?? '—');
}
let sample = null, failures = 0, timer, controller, generation = 0, statusKey = 'connecting';
const t = key => words[lang][key] ?? key;
function localize() {
  document.documentElement.lang = lang;
  document.querySelectorAll('[data-i18n]').forEach(e => e.textContent = t(e.dataset.i18n));
  $('language').textContent = lang === 'en' ? '日本語' : 'English';
  $('settingsButton').ariaLabel = t('settings');
  for (const [id, path] of [['aboutLink',''],['privacyLink','privacy/'],['supportLink','support/']]) $(id).href = (lang === 'en' ? '/en/' : '/') + path;
  $('location').checked = mode === 'current';
  render();
}
function longitude() {return mode === 'current' ? fix?.longitude ?? null : mode === 'manual' ? manual : 0;}
function place() {
  if (mode === 'current') return !fix ? locationMessage() : t(Date.now() - fix.timestamp > 300000 || geoStatus.startsWith('geo') ? 'last' : 'current');
  return mode === 'manual' ? `${t('manual')} · ${manual}°` : 'Greenwich';
}
function render() {
  const d = display(sample, performance.now(), Date.now(), longitude());
  $('edMajor').textContent = d ? d.ed.slice(0, -6) : '—';
  $('edMinor').textContent = d ? d.ed.slice(-6) : '';
  $('earthButton').setAttribute('aria-label', `${t('earth')} ${d?.ed ?? '—'}`);
  $('sp').textContent = d?.sp ?? '—';
  $('place').textContent = place();
  $('locationStatus').textContent = inputError ? t('invalid') : mode === 'current' ? locationMessage() : '';
  $('retryLocation').hidden = mode !== 'current';
  $('retryLocation').disabled = geoPending;
  $('sun').style.visibility = d?.phase != null ? 'visible' : 'hidden';
  if (d?.phase != null) $('sun').style.left = `${d.phase * 100}%`;
  $('status').textContent = t(d ? d.stale ? 'stale' : failures ? 'retry' : 'live' : statusKey === 'connecting' ? 'connecting' : 'unavailable');
  if ($('details').open) detail(d);
}
function detail(d) {
  const target = $('detailContent'); target.replaceChildren();
  const dl = document.createElement('dl'); target.append(dl);
  const row = (key, value) => {const dt=document.createElement('dt'), dd=document.createElement('dd'); dt.textContent=key;dd.textContent=value ?? t('unknown');dl.append(dt,dd);};
  row('API', '/api/v2/state · draft-03 V2');
  if (mode === 'current' && fix)
    row(t('locationEpoch'), t(fix.epochCorrected ? 'epochCorrected' : 'epochStandard'));
  if (!sample) {row(t('state'), t('unavailable')); return;}
  row(t('source'), sample.ed.quality.stratum);
  row(t('roundtrip'), sample.rtt.toFixed(4)); row(t('age'), d?.age.toFixed(1));
  for (const [name, coord] of [['ED',sample.ed],['SP',sample.solar]]) {
    if (!coord) {row(name,t('unavailable'));continue;}
    const q=coord.quality;
    row(`${name} · ${t('state')}`,t(({1:'tracking',2:'holdover',3:'unassessed'})[q.state]));
    row(`${name} · ${t('bound')}`,q.evaluated ? q.uncertainty : t('unassessed'));
    row(`${name} · ${t('validity')}`,q.validity_seconds);
  }
}
async function poll() {
  if (document.hidden) return;
  clearTimeout(timer); controller?.abort();
  const id=++generation, c=new AbortController();controller=c;
  const nonce=Array.from(crypto.getRandomValues(new Uint8Array(16)),x=>x.toString(16).padStart(2,'0')).join('');
  const sent=performance.now();const wallSent=Date.now();
  const timeout=setTimeout(()=>c.abort(),3000);
  try {
    const response=await fetch(`/api/v2/state?nonce=${nonce}`,{signal:c.signal,cache:'no-store',credentials:'omit',redirect:'error'});
    if (!response.ok) throw Error('HTTP');
    const data=await response.json(), received=performance.now(),wall=Date.now();
    if (id!==generation || document.hidden) return;
    if (Math.abs(wall-wallSent-(received-sent))>1000) throw Error('clock step');
    sample=accept(data,nonce,sent,received,wall);failures=0;statusKey='live';
  } catch {
    if (id!==generation || document.hidden) return;
    failures++;statusKey='unavailable';
  } finally {
    clearTimeout(timeout);
    if(id===generation && !document.hidden) {render();timer=setTimeout(poll,failures ? retryDelay(failures) : 60000);}
  }
}
function locate() {
  if (document.hidden || mode!=='current' || geoPending) return;
  cancelGeo();
  cancelGeo = requestLocation(navigator.geolocation, (state, acquired, diagnostic) => {
    geoDiagnostic=diagnostic;
    geoStatus=state;geoPending=state==='locating';
    if(acquired) fix=acquired;
    render();
  }, {secure:window.isSecureContext});
}
function setMode(next) {
  cancelGeo();mode=next;geoPending=false;fix=null;geoStatus='needed';inputError=false;
  // Do not persist coordinates, including manually entered longitude.
  save('nepp.web.location', next==='manual' ? 'greenwich' : next);
  $('location').checked=next==='current';$('locationStatus').textContent='';
  if(next==='current') locate();render();
}
$('language').onclick=()=>{lang=lang==='en'?'ja':'en';save('nepp.web.language',lang);localize();};
$('settingsButton').onclick=()=>$('settings').showModal();
for(const id of ['detailsButton','earthButton','solarButton']) $(id).onclick=()=>{detail(display(sample,performance.now(),Date.now(),longitude()));$('details').showModal();};
$('refresh').onclick=poll;
$('retryLocation').onclick=locate;
$('location').onchange=e=>setMode(e.target.checked?'current':'greenwich');
$('greenwich').onclick=()=>setMode('greenwich');
function applyLongitude() {
  const input=$('longitude'),value=Number(input.value);
  if(!input.value.trim() || !input.validity.valid || !Number.isFinite(value) || value < -180 || value > 180){inputError=true;render();return;}
  manual=value;setMode('manual');input.blur();
}
$('applyLongitude').onclick=applyLongitude;
$('longitude').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();applyLongitude();}};
let animation;
function animate(){render();animation=setTimeout(animate,50);}
function resume(){localize();poll();locate();geoTimer=setInterval(locate,60000);animate();}
function pause(){generation++;controller?.abort();clearTimeout(timer);clearTimeout(animation);clearInterval(geoTimer);cancelGeo();geoPending=false;geoStatus='needed';sample=null;statusKey='connecting';}
document.addEventListener('visibilitychange',()=>document.hidden?pause():resume());
if(!document.hidden) resume();else localize();
