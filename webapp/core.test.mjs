import test from 'node:test';
import assert from 'node:assert/strict';
import {accept, display, frac, retryDelay, requestLocation, normalizeLocationTimestamp} from './core.mjs';
const q = {state:1,stratum:1,validity_seconds:100};
const data = () => ({schema:'nepp-web-1',protocol_version:2,nonce:'abc',processing_seconds:.01,max_extrapolation_seconds:300,ed:{year:2026,fraction:'0.4',rate:3.2e-8,model_id:1,quality:{...q}},solar:{phase:.999999,rate:1/86400,model_id:1,quality:{...q}}});
const receive = d => accept(d,'abc',1000,1100,100000);
test('ED split precision, delay and east longitude',()=>{
 const s=receive(data());const d=display(s,1100,100000,139.7);
 assert.equal(d.ed,'2026.4000000014');assert.ok(d.phase>0.38&&d.phase<0.4);
 assert.equal(s.oneWay,.045000000000000005);
 assert.ok(display(s,1100,100000,null).phase===null);
});
test('mismatched nonce, slow / inconsistent exchange rejected',()=>{
 assert.throws(()=>accept(data(),'wrong',1000,1100,0));
 assert.throws(()=>accept(data(),'abc',1000,5000,0));
 assert.throws(()=>receive({...data(),processing_seconds:.2}));
 assert.throws(()=>receive({...data(),protocol_version:1}));
 assert.throws(()=>receive({...data(),max_extrapolation_seconds:Infinity}));
});
test('independent SP failure and ED rejection',()=>{
 const bad=data();bad.solar.phase=NaN;assert.equal(receive(bad).solar,null);
 bad.ed.rate=0;assert.throws(()=>receive(bad));
});
test('validity, holdover, total expiry and suspend gaps',()=>{
 const s=receive(data());
 assert.equal(display(s,102100,201000,0).stale,true);
 assert.equal(display(s,302100,401000,0),null);
 assert.equal(display(s,1100,105000,0),null);
 assert.equal(display(s,1000,99900,0),null);
 const h=data();h.ed.quality.state=2;assert.equal(display(receive(h),1100,100000,0).stale,true);
});
test('fraction wraps without displaying solar 1.000000',()=>{
 assert.equal(frac(-.25),.75);
 const d=data();d.ed.fraction='0.999999999999';d.solar.phase=.99999999999;
 const s=accept({...d,processing_seconds:0},'abc',1000,1000,0);
 assert.equal(display(s,1000,0,0).ed,'2027.0000000000');
 assert.equal(display(s,1000,0,0).sp,'0.999999');
});
test('retry remains bounded',()=>{
 assert.deepEqual([1,2,3,4,5,6,7].map(retryDelay),[2000,4000,8000,16000,32000,60000,60000]);
});

function locationHarness(now = 1000000) {
 const events=[];let success,error,watchdog,cleared=false;
 const geo={getCurrentPosition(ok,fail){success=ok;error=fail;}};
 const cancel=requestLocation(geo,(state,fix,diagnostic)=>events.push({state,fix,diagnostic}),{
   schedule:(fn,ms)=>{assert.equal(ms,20000);watchdog=fn;return 1;},
   unschedule:()=>{cleared=true;},now:()=>now
 });
 return {events,cancel,success:p=>success(p),error:code=>error({code}),timeout:()=>watchdog(),cleared:()=>cleared};
}
const position={coords:{longitude:139.7,latitude:35.6},timestamp:1000000};
test('location distinguishes each browser error',()=>{
 for(const [code,state] of [[1,'geoDenied'],[2,'geoUnavailable'],[3,'geoTimeout'],[99,'geoUnknown']]) {
   const h=locationHarness();h.error(code);assert.equal(h.events.at(-1).state,state);assert.ok(h.cleared());
 }
});
test('permission wait has watchdog; late callbacks cannot overwrite timeout',()=>{
 const h=locationHarness();assert.equal(h.events[0].state,'locating');h.timeout();
 h.success(position);h.error(1);assert.deepEqual(h.events.map(x=>x.state),['locating','geoNoReply']);
});
test('cancelled location and replaced callbacks do not update UI',()=>{
 const h=locationHarness();h.cancel();h.success(position);h.timeout();assert.equal(h.events.length,1);
});
test('valid fix succeeds, stale / invalid / polar fixes are distinguished',()=>{
 const h=locationHarness();h.success(position);h.timeout();assert.equal(h.events.at(-1).state,'current');
 assert.deepEqual(h.events.at(-1).fix,{longitude:139.7,timestamp:1000000});
 for(const [p,state] of [[{...position,timestamp:1},'geoOld'],[{...position,coords:{longitude:NaN,latitude:0}},'geoInvalidCoordinates'],[{...position,coords:{longitude:0,latitude:90}},'geoPole']]){
   const f=locationHarness();f.success(p);assert.equal(f.events.at(-1).state,state);
 }
});
test('timestamp diagnostics distinguish invalid, old and future without coordinates',()=>{
 for(const timestamp of [undefined,null,NaN,Infinity,'1000000']) {
   const h=locationHarness();h.success({...position,timestamp});assert.equal(h.events.at(-1).state,'geoInvalidTimestamp');
 }
 for(const [timestamp,state] of [[600000,'geoOld'],[1400000,'geoFuture']]) {
   const h=locationHarness();h.success({...position,timestamp});
   assert.deepEqual(h.events.at(-1),{state,fix:null,diagnostic:{seconds:400}});
 }
 for(const timestamp of [700000,1300000]) {
   const h=locationHarness();h.success({...position,timestamp});assert.equal(h.events.at(-1).state,'current');
 }
});
test('unsupported, insecure and synchronous exceptions are reported',()=>{
 for(const [geo,options,want] of [[null,{},'geoUnsupported'],[{}, {secure:false},'geoInsecure'],[{getCurrentPosition(){throw Error('blocked');}}, {},'geoUnknown']]){
   const events=[];requestLocation(geo,s=>events.push(s),options);assert.equal(events.at(-1),want);
 }
});
test('reported Safari epoch case yields a 23 ms old fix and no double correction',()=>{
 const now=1788172452286, raw=809865252263;
 const normalized=normalizeLocationTimestamp(raw,now);
 assert.deepEqual(normalized,{timestamp:1788172452263,epochCorrected:true});
 assert.equal(now-normalized.timestamp,23);
 assert.deepEqual(normalizeLocationTimestamp(normalized.timestamp,now),{timestamp:normalized.timestamp,epochCorrected:false});
 const h=locationHarness(now);h.success({...position,timestamp:raw});
 assert.deepEqual(h.events.at(-1).fix,{longitude:139.7,timestamp:1788172452263,epochCorrected:true});
});
test('epoch workaround rejects stale, future, invalid and other-offset values',()=>{
 const now=1788172452286, offset=978307200000;
 for(const timestamp of [now-offset-300001,now-offset+1,now-300001,now+300001,
   now-2*offset,now/1000,null,NaN,Infinity,-1])
   assert.equal(normalizeLocationTimestamp(timestamp,now),null);
 for(const age of [0,300000])
   assert.deepEqual(normalizeLocationTimestamp(now-offset-age,now),{timestamp:now-age,epochCorrected:true});
});
