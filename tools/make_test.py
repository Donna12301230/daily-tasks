# -*- coding: utf-8 -*-
"""本機測試：產生 _test.html（假的資料庫，不連 Firebase）。不會 commit（見 .gitignore）。
用法：python tools/make_test.py [匯入檔.json]   然後 python -m http.server 開 http://localhost:8000/_test.html"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = {}
if len(sys.argv) > 1:
    src = json.load(open(sys.argv[1], encoding="utf-8"))
    daily = src.get("daily", {})
    data = {"daily": {k: v for k, v in daily.items()}, "workbench": src.get("workbench", {})}
FAKE = r"""<script>
(function () {
  const store = __DATA__;
  const lis = [];
  const frz = o => JSON.parse(JSON.stringify(o));
  window.__writes = []; window.__store = store;
  // 跟 Firestore 一樣：陣列裡不能直接放陣列，寫入時當場丟錯
  function noNested(v, inArr) { if (Array.isArray(v)) { if (inArr) throw new Error("Nested arrays are not supported"); v.forEach(x => noNested(x, true)); } else if (v && typeof v === "object") for (const k in v) noNested(v[k], false); }
  function merge(t, p) { for (const k in p) { const v = p[k]; if (v && typeof v === "object" && !Array.isArray(v)) { if (!t[k] || typeof t[k] !== "object") t[k] = {}; merge(t[k], v); } else t[k] = v; } return t; }
  function makeDb(app) {
    const base = store[app] = store[app] || {};
    const colOf = c => (base[c] = base[c] || {});
    const snap = (c, id) => { const d = (base[c] || {})[id]; return { id, exists: !!d, data: () => (d ? frz(d) : undefined), metadata: { fromCache: false, hasPendingWrites: false } }; };
    const qs = c => { const docs = Object.keys(base[c] || {}).map(id => snap(c, id)); return { docs, size: docs.length, empty: !docs.length, metadata: { fromCache: false, hasPendingWrites: false }, docChanges: () => [] }; };
    const emit = c => lis.filter(l => l.app === app && l.c === c).forEach(l => setTimeout(() => l.next(l.id ? snap(c, l.id) : qs(c)), 5));
    const ref = (c, id) => ({ id, path: c + "/" + id,
      get: async () => snap(c, id),
      set: d => { noNested(d); return (async () => { if (new TextEncoder().encode(JSON.stringify(d)).length > 1048576) throw Object.assign(new Error("Document exceeds 1 MiB"), { code: "invalid-argument" }); colOf(c)[id] = frz(d); __writes.push(["set", app, c, id]); emit(c); })(); },
      update: p => { noNested(p); return (async () => { if (new TextEncoder().encode(JSON.stringify(merge(frz(colOf(c)[id] || {}), frz(p)))).length > 1048576) throw Object.assign(new Error("Document exceeds 1 MiB"), { code: "invalid-argument" }); colOf(c)[id] = merge(colOf(c)[id] || {}, frz(p)); __writes.push(["update", app, c, id]); emit(c); })(); },
      delete: async () => { delete colOf(c)[id]; __writes.push(["delete", app, c, id]); emit(c); },
      onSnapshot: next => { const l = { app, c, id, next }; lis.push(l); setTimeout(() => next(snap(c, id)), 15); return () => { const i = lis.indexOf(l); if (i >= 0) lis.splice(i, 1); }; } });
    const col = c => ({ path: c, doc: id => ref(c, id || "x" + Math.random().toString(36).slice(2, 8)), get: async () => qs(c),
      onSnapshot: next => { const l = { app, c, next }; lis.push(l); setTimeout(() => next(qs(c)), 15); return () => {}; } });
    return { collection: col, doc: p => { const i = p.lastIndexOf("/"); return ref(p.slice(0, i), p.slice(i + 1)); } };
  }
  const user = { uid: "u1", displayName: "雅婷（測試）" };
  window.DT_TEST = {
    claude: app => ({ use: async n => n === "db" ? makeDb(app) : n === "user" ? { id: async () => user.uid, can: async () => true } : null }),
    dt: app => ({ app, user: async () => user, dbFor: async a => makeDb(a), signIn: async () => {}, signOut: async () => {}, save: async () => ({}) }),
  };
})();
</script>
"""
html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
mark = '<script>window.DT_APP = "daily";</script>'
assert mark in html
html = html.replace(mark, FAKE.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")) + mark, 1)
open(os.path.join(ROOT, "_test.html"), "w", encoding="utf-8", newline="\n").write(html)
print("_test.html", len(html))
