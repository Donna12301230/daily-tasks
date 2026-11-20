/* 每日任務：Google 登入與雲端資料庫
   - 沿用單字練習的 Firebase 專案（vocab-trainer-7716），資料放在 users/{uid}/apps/{DT_APP}/...
     Firestore 規則只允許本人讀寫 users/{uid}/**，所以資料只有你自己看得到。
   - 對頁面提供跟 claude.ai artifact 一樣的 window.claude.use("db" | "user" | "downloads") 介面，
     所以每日任務、工作台、考古題的程式不用改資料層就能跑。
   - 每個頁面在載入本檔前設定 window.DT_APP（daily / workbench / nsysu）。 */
(function () {
  "use strict";
  const APP = window.DT_APP || "daily";
  // 本機測試用：_test.html 會提供假的資料庫（內建網站的 iframe 也沿用平台頁的測試設定）
  let T = window.DT_TEST;
  try { if (!T && window.parent !== window) T = window.parent.DT_TEST; } catch (e) { T = null; }
  if (T) { window.claude = T.claude(APP); window.DT = T.dt(APP); return; }

  const CONFIG = { apiKey: "AIzaSyB_Zjfh6IHg8z_WaicBVADzjo0t7t3kAos", authDomain: "vocab-trainer-7716.firebaseapp.com", projectId: "vocab-trainer-7716", storageBucket: "vocab-trainer-7716.firebasestorage.app", messagingSenderId: "988782867968", appId: "1:988782867968:web:4e5e9689f88483af420ae5" };
  const SDK = "https://www.gstatic.com/firebasejs/10.14.1/";
  const load = src => new Promise((res, rej) => { const s = document.createElement("script"); s.src = src; s.onload = res; s.onerror = () => rej(new Error("無法載入 " + src)); document.head.appendChild(s); });

  let ready = null;
  function init() {
    if (ready) return ready;
    ready = (async () => {
      await load(SDK + "firebase-app-compat.js");
      await Promise.all([load(SDK + "firebase-auth-compat.js"), load(SDK + "firebase-firestore-compat.js")]);
      if (!firebase.apps.length) firebase.initializeApp(CONFIG);
      const fs = firebase.firestore();
      try { await fs.enablePersistence({ synchronizeTabs: true }); } catch (e) { /* 另一個分頁已開啟或瀏覽器不支援：照常用線上資料 */ }
      return { auth: firebase.auth(), fs };
    })();
    return ready;
  }
  const userP = init().then(({ auth }) => new Promise(res => { const off = auth.onAuthStateChanged(u => { off(); res(u); }); })).catch(() => null);

  const clean = d => JSON.parse(JSON.stringify(d == null ? {} : d));
  const mapErr = e => ({ code: e && e.code === "permission-denied" ? "invalid_argument" : e && e.code === "resource-exhausted" ? "resource_exhausted" : "unavailable", message: (e && e.message) || "" });
  const meta = m => ({ fromCache: !!(m && m.fromCache), hasPendingWrites: !!(m && m.hasPendingWrites) });
  const wrapSnap = s => ({ id: s.id, exists: s.exists, data: () => s.data(), metadata: meta(s.metadata) });
  const wrapQS = qs => ({ docs: qs.docs.map(wrapSnap), size: qs.size, empty: qs.empty, metadata: meta(qs.metadata), docChanges: () => qs.docChanges().map(c => ({ type: c.type, doc: wrapSnap(c.doc), oldIndex: c.oldIndex, newIndex: c.newIndex })) });
  function wrapQuery(q) {
    return {
      where: (f, op, v) => wrapQuery(q.where(f, op, v)),
      orderBy: (f, d) => wrapQuery(q.orderBy(f, d)),
      limit: n => wrapQuery(q.limit(n)),
      get: () => q.get().then(wrapQS),
      onSnapshot: (next, err) => q.onSnapshot({ includeMetadataChanges: true }, qs => next(wrapQS(qs)), e => err && err(mapErr(e))),
    };
  }
  function wrapCol(c) { return Object.assign(wrapQuery(c), { path: c.path, doc: id => wrapRef(id ? c.doc(id) : c.doc()), add: d => c.add(clean(d)).then(wrapRef) }); }
  function wrapRef(r) {
    return {
      id: r.id, path: r.path,
      get: () => r.get().then(wrapSnap),
      set: d => r.set(clean(d)),
      update: p => r.set(clean(p), { merge: true }), // 跟 artifact 一樣深層合併
      delete: () => r.delete(),
      onSnapshot: (next, err) => r.onSnapshot({ includeMetadataChanges: true }, s => next(wrapSnap(s)), e => err && err(mapErr(e))),
      collection: p => wrapCol(r.collection(p)),
    };
  }
  function dbFor(app, uid, fs) {
    const base = fs.collection("users").doc(uid).collection("apps").doc(app);
    return {
      collection: p => wrapCol(base.collection(p)),
      doc: p => { const i = p.lastIndexOf("/"); return wrapRef(base.collection(p.slice(0, i)).doc(p.slice(i + 1))); },
    };
  }
  function saveFile({ filename, data }) {
    const blob = data instanceof Blob ? data : new Blob([data], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = filename || "download";
    document.body.appendChild(a); a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1500);
    return Promise.resolve({ saved: true });
  }

  window.claude = {
    use: async name => {
      try {
        if (name === "db") { const u = await userP; if (!u) return null; const { fs } = await init(); return dbFor(APP, u.uid, fs); }
        if (name === "user") {
          const u = await userP;
          return { id: async () => (u ? u.uid : null), can: async () => !!u, canEdit: async () => !!u, isOwner: async () => !!u, me: async () => ({ id: u ? u.uid : null, name: (u && u.displayName) || "" }) };
        }
        if (name === "downloads") return { save: saveFile };
      } catch (e) { return null; }
      return null;
    },
  };
  window.DT = {
    app: APP,
    user: () => userP,
    dbFor: async app => { const u = await userP; if (!u) return null; const { fs } = await init(); return dbFor(app, u.uid, fs); },
    signIn: async () => {
      const { auth } = await init();
      const p = new firebase.auth.GoogleAuthProvider();
      try { await auth.signInWithPopup(p); }
      catch (e) {
        const c = (e && e.code) || "";
        if (c === "auth/popup-blocked" || c === "auth/operation-not-supported-in-this-environment") await auth.signInWithRedirect(p);
        else if (c !== "auth/popup-closed-by-user" && c !== "auth/cancelled-popup-request") throw e;
      }
    },
    signOut: async () => { const { auth } = await init(); await auth.signOut(); },
    save: saveFile,
  };
})();
