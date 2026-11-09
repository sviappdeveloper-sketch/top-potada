// =====================================================================
// Top Potada — sunucu katmanı
// Oyun kodu window.claude.use('db' | 'user' | 'room') ile konuşur. Bu dosya o
// arayüzü Firebase (Auth + Firestore) üzerinde sağlar. firebase-config.js
// doldurulmamışsa aynı arayüzü tarayıcı içinde (DEMO) sağlar.
// Hesap işlemleri: window.TP
// =====================================================================
import { firebaseConfig, FIREBASE_SDK } from './firebase-config.js';

const listeners = new Set();
const TP = window.TP = {
  mode: 'loading',          // 'firebase' | 'demo' | 'error'
  user: null,               // { uid, anon, member, name, email, photo }
  error: '',
  onAuth(fn){ listeners.add(fn); if(TP.user) setTimeout(()=>fn(TP.user)); return ()=>listeners.delete(fn); },
  signInGoogle: async()=>{}, signOut: async()=>{}, deleteAuthUser: async()=>{},
};
let readyResolve; const ready = new Promise(r=>readyResolve=r);
TP.ready = ready;
function setUser(u){ TP.user = u; listeners.forEach(f=>{ try{ f(u); }catch(e){ console.error(e); } }); if(u) readyResolve(u); }

const configured = firebaseConfig && firebaseConfig.apiKey && firebaseConfig.apiKey !== 'BURAYA';
if(configured) initFirebase().catch(e=>{ console.error(e); TP.mode='error'; TP.error='Sunucuya bağlanılamadı.'; initDemo(); });
else initDemo();

// ---------------------------------------------------------------------
// FIREBASE
// ---------------------------------------------------------------------
async function initFirebase(){
  const base = `https://www.gstatic.com/firebasejs/${FIREBASE_SDK}/`;
  const [{ initializeApp }, A, F] = await Promise.all([
    import(base+'firebase-app.js'), import(base+'firebase-auth.js'), import(base+'firebase-firestore.js')
  ]);
  const app = initializeApp(firebaseConfig);
  const auth = A.getAuth(app);
  const fs = F.getFirestore(app);
  TP.mode = 'firebase';

  const info = u => u ? ({ uid:u.uid, anon:u.isAnonymous, member: u.providerData.some(p=>p.providerId==='google.com'),
    name:u.displayName||'', email:u.email||'', photo:u.photoURL||'' }) : null;
  try{ await A.getRedirectResult(auth); }catch(e){ handleCredErr(e); }
  A.onAuthStateChanged(auth, async u=>{
    if(!u){ try{ await A.signInAnonymously(auth); }catch(e){ TP.error='Oturum açılamadı. İnternet bağlantını kontrol et.'; setUser(null); } return; }
    setUser(info(u));
  });
  async function handleCredErr(e){
    if(e && (e.code==='auth/credential-already-in-use' || e.code==='auth/email-already-in-use')){
      const cred = A.GoogleAuthProvider.credentialFromError(e);
      if(cred){ await A.signInWithCredential(auth, cred); return true; }
    }
    return false;
  }
  const provider = () => { const p=new A.GoogleAuthProvider(); p.setCustomParameters({ prompt:'select_account' }); return p; };
  // Android uygulaması: telefonun kendi Google hesap seçicisi (WebView'da açılır pencere çalışmaz)
  const NATIVE = window.TPAndroid && typeof window.TPAndroid.googleSignIn === 'function';
  const nativeToken = () => new Promise((res, rej)=>{
    window.__tpGoogle = (ok, val)=>{ window.__tpGoogle = null; ok ? res(val) : (val==='cancel' ? res(null) : rej(new Error(val||'google'))); };
    try{ window.TPAndroid.googleSignIn(); }catch(e){ rej(e); }
  });
  async function signInNative(){
    const token = await nativeToken(); if(!token) return;
    const cred = A.GoogleAuthProvider.credential(token), cur = auth.currentUser;
    try{
      if(cur && cur.isAnonymous) await A.linkWithCredential(cur, cred);   // misafir ilerlemesi korunur
      else await A.signInWithCredential(auth, cred);
    }catch(e){
      if(e && (e.code==='auth/credential-already-in-use' || e.code==='auth/email-already-in-use')) await A.signInWithCredential(auth, A.GoogleAuthProvider.credentialFromError(e) || cred);
      else throw e;
    }
    await auth.currentUser.reload();
    setUser(info(auth.currentUser));
  }
  TP.signInGoogle = async ()=>{
    if(NATIVE) return signInNative();
    const cur = auth.currentUser, prov = provider();
    try{
      if(cur && cur.isAnonymous) await A.linkWithPopup(cur, prov);     // misafir ilerlemesi korunur
      else await A.signInWithPopup(auth, prov);
    }catch(e){
      if(await handleCredErr(e)){ /* var olan Google hesabına geçildi */ }
      else if(e && (e.code==='auth/popup-blocked' || e.code==='auth/operation-not-supported-in-this-environment' || e.code==='auth/web-storage-unsupported')){
        if(cur && cur.isAnonymous) await A.linkWithRedirect(cur, prov); else await A.signInWithRedirect(auth, prov);
        return;
      } else if(e && (e.code==='auth/popup-closed-by-user' || e.code==='auth/cancelled-popup-request')) return;
      else throw e;
    }
    await auth.currentUser.reload();
    setUser(info(auth.currentUser));     // bağlama işleminde onAuthStateChanged tetiklenmez
  };
  TP.signOut = async ()=>{ if(NATIVE){ try{ window.TPAndroid.googleSignOut(); }catch(e){} } await A.signOut(auth); };
  TP.deleteAuthUser = async ()=>{
    const u=auth.currentUser; if(!u) return;
    try{ await A.deleteUser(u); }
    catch(e){
      if(e && e.code==='auth/requires-recent-login'){
        if(NATIVE){ const t=await nativeToken(); if(!t) return; await A.reauthenticateWithCredential(u, A.GoogleAuthProvider.credential(t)); }
        else await A.reauthenticateWithPopup(u, provider());
        await A.deleteUser(u);
      }
      else throw e;
    }
  };

  // ---- db: Claude db arayüzüyle uyumlu ----
  const clean = d => JSON.parse(JSON.stringify(d));
  const mapErr = e => ({ code: e && e.code==='permission-denied' ? 'invalid_argument' : e && e.code==='resource-exhausted' ? 'quota_exceeded' : 'unavailable', message: e && e.message || '' });
  const wrap = s => ({ id:s.id, exists:s.exists(), data:()=> s.exists() ? s.data() : undefined, metadata:{ fromCache:s.metadata.fromCache, hasPendingWrites:s.metadata.hasPendingWrites } });
  const wrapQ = s => { const docs=s.docs.map(wrap); return { docs, size:docs.length, empty:!docs.length, docChanges:()=>[], metadata:{ fromCache:s.metadata.fromCache, hasPendingWrites:s.metadata.hasPendingWrites } }; };
  const rid = () => Math.random().toString(36).slice(2,12);
  const guard = p => p.catch(e=>{ throw mapErr(e); });
  const db = {
    doc(path){ const r=F.doc(fs, path); return { id:r.id, path,
      get: ()=>guard(F.getDoc(r).then(wrap)),
      set: d=>guard(F.setDoc(r, clean(d))),
      update: d=>guard(F.setDoc(r, clean(d), { merge:true })),
      delete: ()=>guard(F.deleteDoc(r)),
      onSnapshot: (n,e)=>F.onSnapshot(r, s=>n(wrap(s)), err=>e && e(mapErr(err))),
      collection: p=>db.collection(path+'/'+p) }; },
    collection(path){ const c=F.collection(fs, path); return { path,
      doc: id=>db.doc(path+'/'+(id||rid())),
      get: ()=>guard(F.getDocs(c).then(wrapQ)),
      onSnapshot: (n,e)=>F.onSnapshot(c, s=>n(wrapQ(s)), err=>e && e(mapErr(err))) }; },
  };

  // ---- room: Firestore üzerinde canlı oda (kalp atışıyla) ----
  class FsRoom {
    constructor(name){
      this.name=name; this.me=auth.currentUser.uid; this.p={}; this.t=Date.now(); this.subs=new Set(); this.snap=Object.freeze([]); this.raw=new Map();
      this.ref=F.doc(fs, 'rooms', name, 'peers', this.me);
    }
    async start(){
      await F.setDoc(this.ref, { p:{}, seen:Date.now(), t:this.t });
      this.unsub=F.onSnapshot(F.collection(fs, 'rooms', this.name, 'peers'), s=>{ this.raw=new Map(s.docs.map(d=>[d.id, d.data()])); this.rebuild(); }, ()=>{});
      this.hb=setInterval(()=>{ F.setDoc(this.ref, { seen:Date.now() }, { merge:true }).catch(()=>{}); this.rebuild(); }, 5000);
      this.unload=()=>{ F.deleteDoc(this.ref).catch(()=>{}); }; window.addEventListener('pagehide', this.unload);
      return this;
    }
    rebuild(){
      const now=Date.now(), arr=[];
      const entry=(id,pres,seen)=>Object.freeze({ peer:id, by:id, isMe:id===this.me, sameTab:id===this.me, kind:'viewer', guest:false, presence:Object.freeze({...pres}), updatedAt:seen||now });
      for(const [id,v] of this.raw){ if(id===this.me) continue; if(now-(v.seen||0) > 20000) continue; arr.push(entry(id, v.p||{}, v.seen)); }
      arr.push(entry(this.me, this.p, now));
      this.snap=Object.freeze(arr);
      const ch={ peers:this.snap, joined:[], left:[], updated:[] };
      this.subs.forEach(f=>{ try{ f(ch); }catch(e){ console.error(e); } });
    }
    presence(patch){
      for(const k in patch){ if(patch[k]===null) delete this.p[k]; else this.p[k]=patch[k]; }
      this.rebuild();
      clearTimeout(this.wt);
      this.wt=setTimeout(()=>{ F.setDoc(this.ref, { p:clean(this.p), seen:Date.now(), t:this.t }).catch(()=>{}); }, 300);
      return Promise.resolve();
    }
    peers(){ return this.snap; }
    onPeers(fn){ this.subs.add(fn); setTimeout(()=>fn({ peers:this.snap, joined:this.snap, left:[], updated:[] }), 0); return ()=>this.subs.delete(fn); }
    connected(){ return true; }
    onConnection(fn){ setTimeout(()=>fn(true)); return ()=>{}; }
    emit(){ return Promise.resolve(); } on(){ return ()=>{}; }
    async leave(){ clearInterval(this.hb); clearTimeout(this.wt); this.unsub && this.unsub(); window.removeEventListener('pagehide', this.unload); await F.deleteDoc(this.ref).catch(()=>{}); }
  }
  const room = { join: async name=>{ await ready; return new FsRoom(name).start(); } };
  const user = { id: async()=>{ await ready; return auth.currentUser ? auth.currentUser.uid : null; }, can: async()=>true, isOwner:()=>false, canEdit:()=>false };
  window.claude = { use: async n => n==='db' ? db : n==='user' ? user : n==='room' ? room : null };
}

// ---------------------------------------------------------------------
// DEMO: sunucusuz, tarayıcı içi (her sekme ayrı oyuncu)
// ---------------------------------------------------------------------
function initDemo(){
  if(TP.mode!=='error') TP.mode='demo';
  const KEY='tp-demo-db';
  const uid = sessionStorage.getItem('tp-demo-uid') || ('d'+Math.random().toString(36).slice(2,10));
  sessionStorage.setItem('tp-demo-uid', uid);
  const load=()=>{ try{ return JSON.parse(localStorage.getItem(KEY)||'{}'); }catch(e){ return {}; } };
  const save=m=>localStorage.setItem(KEY, JSON.stringify(m));
  const subs=new Set(); const notify=()=>setTimeout(()=>subs.forEach(f=>f()),0);
  window.addEventListener('storage', e=>{ if(e.key===KEY) notify(); });
  const merge=(a,b)=>{ const o={...a}; for(const k in b){ const v=b[k]; if(v && typeof v==='object' && !Array.isArray(v) && o[k] && typeof o[k]==='object' && !Array.isArray(o[k])) o[k]=merge(o[k],v); else o[k]=v; } return o; };
  const snap=(id,d)=>({ id, exists:d!==undefined, data:()=>d, metadata:{ fromCache:false, hasPendingWrites:false } });
  const db={
    doc(path){ const id=path.split('/').pop(); return { id, path,
      get: async()=>snap(id, load()[path]),
      set: async d=>{ const m=load(); m[path]=JSON.parse(JSON.stringify(d)); save(m); notify(); },
      update: async d=>{ const m=load(); m[path]=merge(m[path]||{}, JSON.parse(JSON.stringify(d))); save(m); notify(); },
      delete: async()=>{ const m=load(); delete m[path]; save(m); notify(); },
      onSnapshot: n=>{ const f=()=>n(snap(id, load()[path])); subs.add(f); setTimeout(f,0); return ()=>subs.delete(f); },
      collection: p=>db.collection(path+'/'+p) }; },
    collection(path){ const n=path.split('/').length+1;
      const now=()=>{ const m=load(); return Object.keys(m).filter(k=>k.startsWith(path+'/') && k.split('/').length===n).sort().map(k=>snap(k.split('/').pop(), m[k])); };
      const q=()=>{ const d=now(); return { docs:d, size:d.length, empty:!d.length, docChanges:()=>[], metadata:{ fromCache:false, hasPendingWrites:false } }; };
      return { path, doc: id=>db.doc(path+'/'+(id||Math.random().toString(36).slice(2))), get: async()=>q(),
        onSnapshot: fn=>{ const f=()=>fn(q()); subs.add(f); setTimeout(f,0); return ()=>subs.delete(f); } }; },
  };
  function demoRoom(name){
    const ch=new BroadcastChannel('tp-demo-room-'+name); let mine={}; const others=new Map(); const ps=new Set(); let s=Object.freeze([]);
    const rebuild=()=>{ s=Object.freeze([{ peer:uid, by:uid, isMe:true, sameTab:true, kind:'viewer', guest:false, presence:Object.freeze({...mine}), updatedAt:Date.now() },
      ...[...others].map(([peer,pr])=>({ peer, by:peer, isMe:false, sameTab:false, kind:'viewer', guest:false, presence:Object.freeze({...pr}), updatedAt:Date.now() }))]);
      setTimeout(()=>ps.forEach(f=>f({ peers:s, joined:[], left:[], updated:[] })),0); };
    ch.onmessage=e=>{ const m=e.data; if(m.t==='p'){ others.set(m.peer, m.pr); rebuild(); } if(m.t==='hello') ch.postMessage({ t:'p', peer:uid, pr:mine }); if(m.t==='bye'){ others.delete(m.peer); rebuild(); } };
    ch.postMessage({ t:'hello' }); rebuild();
    return { name, emit:async()=>{}, on:()=>()=>{},
      presence: async patch=>{ for(const k in patch){ if(patch[k]===null) delete mine[k]; else mine[k]=patch[k]; } ch.postMessage({ t:'p', peer:uid, pr:mine }); rebuild(); },
      peers:()=>s, onPeers:f=>{ ps.add(f); setTimeout(()=>f({ peers:s, joined:s, left:[], updated:[] }),0); return ()=>ps.delete(f); },
      connected:()=>true, onConnection:()=>()=>{}, leave: async()=>{ ch.postMessage({ t:'bye', peer:uid }); ch.close(); } };
  }
  const room={ join: async n=>demoRoom(n) };
  const user={ id: async()=>uid, can: async()=>true, isOwner:()=>false, canEdit:()=>false };
  window.claude={ use: async n=> n==='db' ? db : n==='user' ? user : n==='room' ? room : null };
  const info=()=>{ const m=sessionStorage.getItem('tp-demo-member'); return { uid, anon:!m, member:!!m, name:m||'', email:m?'demo@ornek.com':'', photo:'' }; };
  TP.signInGoogle = async()=>{ let n=''; try{ n=window.prompt('DEMO: Google girişi yerine bir ad yaz', 'Demo Oyuncu')||''; }catch(e){} n=n.trim()||'Demo Oyuncu'; sessionStorage.setItem('tp-demo-member', n.slice(0,24)); setUser(info()); };
  TP.signOut = async()=>{ sessionStorage.removeItem('tp-demo-member'); setUser(info()); };
  TP.deleteAuthUser = async()=>{ sessionStorage.removeItem('tp-demo-member'); sessionStorage.removeItem('tp-demo-uid'); };
  setTimeout(()=>setUser(info()), 0);
}
