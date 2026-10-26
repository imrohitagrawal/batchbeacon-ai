import test from 'node:test';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';
const { default: worker } = await import(pathToFileURL(resolve('deployment/cloudflare/worker.mjs')));
const PUBLIC='https://batchbeacon.example';
const UPSTREAM='https://batchbeacon-existing.a.run.app';
const env={PUBLIC_ORIGIN:PUBLIC,UPSTREAM_ORIGIN:UPSTREAM,UPSTREAM_TIMEOUT_MS:'60000'};
const originalFetch=globalThis.fetch;
async function exercise(request, upstream=()=>new Response('ok',{status:200}), config=env) {
 const calls=[];globalThis.fetch=async(input,init)=>{const q=new Request(input,init);calls.push({url:q.url,method:q.method,headers:Object.fromEntries(q.headers),body:Buffer.from(await q.arrayBuffer()),redirect:q.redirect,init});return upstream(q);};
 try{return {response:await worker.fetch(request,config),calls};}finally{globalThis.fetch=originalFetch;}
}
function request(options={}) {
 const {method='POST',host='batchbeacon.example',url=PUBLIC+'/api/guest',headers={},body}=options; const origin=Object.hasOwn(options,'origin')?options.origin:PUBLIC;
 const h=new Headers(headers);if(origin!==undefined)h.set('origin',origin);if(host!==undefined)h.set('host',host);
 return new Request(url,{method,headers:h,...(body!==undefined?{body,duplex:'half'}:{})});
}
for (const [label,options] of [
 ['missing Origin',{origin:undefined}],['null Origin',{origin:'null'}],['upstream Origin',{origin:UPSTREAM}],['foreign Origin',{origin:'https://evil.example'}],['suffix Origin',{origin:PUBLIC+'.evil.example'}],['explicit port Origin',{origin:PUBLIC+':443'}],['path Origin',{origin:PUBLIC+'/'}],['combined duplicate Origin',{origin:PUBLIC+', '+PUBLIC}],['two different Origins',{origin:PUBLIC+', https://evil.example'}],['Host spoof',{host:'evil.example'}],['Host with wrong port',{host:'batchbeacon.example:444'}],['foreign request URL',{url:'https://evil.example/api/guest',host:'evil.example'}],['HTTP request URL',{url:'http://batchbeacon.example/api/guest'}],['foreign GET Origin',{method:'GET',origin:'https://evil.example'}],['OPTIONS',{method:'OPTIONS'}],['PUT',{method:'PUT'}],['DELETE',{method:'DELETE'}],['duplicate app cookies',{headers:{cookie:'__Host-bb_guest=one; __Host-bb_guest=two'}}],
]) test(`rejects ${label} before upstream`,async()=>{const {response,calls}=await exercise(request(options));assert.ok(response.status>=400&&response.status<500,`status ${response.status}`);assert.equal(calls.length,0);});

test('exact binary body, fixed upstream URL, CSRF and key preserved; only app cookie forwarded',async()=>{
 const binary=Buffer.from([0,255,13,10,128,65,0,17]);const {response,calls}=await exercise(request({url:PUBLIC+'/api/incidents/i/captures?next=https%3A%2F%2Fevil.example',body:binary,headers:{'content-type':'application/octet-stream','idempotency-key':'same-original-key','x-csrf-token':'a'.repeat(64),cookie:'unrelated_parent_session=DO_NOT_FORWARD; __Host-bb_guest=keep-capability; analytics=private','authorization':'Bearer DO_NOT_FORWARD','proxy-authorization':'secret','x-serverless-authorization':'secret','forwarded':'host=evil.example;proto=http','x-forwarded-host':'evil.example','x-forwarded-proto':'http','x-forwarded-for':'1.2.3.4'}}));
 assert.equal(response.status,200);assert.equal(calls.length,1);const q=calls[0];assert.equal(q.url,UPSTREAM+'/api/incidents/i/captures?next=https%3A%2F%2Fevil.example');assert.equal(q.headers.origin,UPSTREAM);assert.equal(q.headers.cookie,'__Host-bb_guest=keep-capability');assert.equal(q.headers['x-csrf-token'],'a'.repeat(64));assert.equal(q.headers['idempotency-key'],'same-original-key');assert.deepEqual(q.body,binary);assert.equal(q.redirect,'manual');assert.equal(q.init.cache,'no-store');assert.equal(q.init.cf?.cacheTtl,undefined);for(const k of Object.keys(q.headers)) assert.ok(!['authorization','proxy-authorization','x-serverless-authorization','forwarded'].includes(k)&&!k.startsWith('x-forwarded-'),k);assert.match(response.headers.get('cache-control')||'',/no-store/);assert.equal(response.headers.get('access-control-allow-origin'),null);
});

test('guestless safe GET needs no fabricated Origin/cookie and remains fixed origin',async()=>{const {response,calls}=await exercise(request({method:'GET',origin:undefined,url:PUBLIC+'//evil.example/path'}));assert.equal(response.status,200);assert.equal(calls.length,1);assert.equal(new URL(calls[0].url).origin,UPSTREAM);assert.equal(calls[0].headers.origin,undefined);assert.equal(calls[0].headers.cookie,undefined);});

test('upstream network failure does not retry or report success',async()=>{const {response,calls}=await exercise(request(),()=>{throw new TypeError('synthetic upstream unavailable')});assert.ok(response.status>=500);assert.equal(calls.length,1);});

test('cross-host redirect is denied and never followed',async()=>{const {response,calls}=await exercise(request(),()=>new Response(null,{status:302,headers:{location:'https://evil.example/steal'}}));assert.ok(response.status>=400);assert.equal(calls.length,1);assert.notEqual(response.headers.get('location'),'https://evil.example/steal');});

test('unsafe Domain-bearing app cookie fails closed',async()=>{const {response}=await exercise(request(),()=>new Response('ok',{headers:{'set-cookie':'__Host-bb_guest=value; Domain=example; Path=/; Secure; HttpOnly; SameSite=Strict'}}));assert.ok(response.status>=500);assert.equal(response.headers.get('set-cookie'),null);});

test('exact secure host-only app cookie survives without sharing Domain',async()=>{const cookie='__Host-bb_guest=value; Path=/; Max-Age=100; Secure; HttpOnly; SameSite=Strict';const {response}=await exercise(request(),()=>new Response('ok',{headers:{'set-cookie':cookie}}));assert.equal(response.status,200);assert.equal(response.headers.get('set-cookie'),cookie);});

for(const config of [{...env,PUBLIC_ORIGIN:'http://batchbeacon.example'},{...env,UPSTREAM_ORIGIN:'https://user:secret@example.com'},{...env,UPSTREAM_ORIGIN:UPSTREAM+'/arbitrary'},{...env,PUBLIC_ORIGIN:UPSTREAM},{}]) test(`invalid config rejects before fetch ${JSON.stringify(config)}`,async()=>{const {response,calls}=await exercise(request(),undefined,config);assert.ok(response.status>=500);assert.equal(calls.length,0);});

test('acquisition heartbeat is forwarded before final body without transformation or retry',async()=>{
 let controller;const stream=new ReadableStream({start(c){controller=c;c.enqueue(new TextEncoder().encode('\n'));}});
 const {response,calls}=await exercise(request({url:PUBLIC+'/api/incidents/'+'a'.repeat(32)+'/acquisitions',headers:{'X-BatchBeacon-Progress':'acquisition-progress-v1'}}),()=>new Response(stream,{headers:{'Content-Type':'application/vnd.batchbeacon.acquisition+json','Cache-Control':'private, no-store, no-transform','X-Accel-Buffering':'no'}}));
 assert.equal(calls.length,1);assert.equal(calls[0].headers['x-batchbeacon-progress'],'acquisition-progress-v1');
 assert.match(response.headers.get('cache-control'),/no-transform/);assert.equal(response.headers.get('x-accel-buffering'),'no');
 const reader=response.body.getReader();const first=await reader.read();assert.equal(new TextDecoder().decode(first.value),'\n');assert.equal(first.done,false);
 const final=JSON.stringify({protocol:'acquisition-progress-v1',status:503,body:{error:'unavailable',outcome:'unknown'}});
 controller.enqueue(new TextEncoder().encode(final));controller.close();assert.equal(new TextDecoder().decode((await reader.read()).value),final);assert.equal((await reader.read()).done,true);
});
