/* 內建網站共用：放進每日任務平台時，網站之間的連結改成在平台裡切換，不跳出去。
   由 tools/build.py 自動加進每個內建網站。 */
(function () {
  "use strict";
  const inFrame = window.parent !== window;
  // 連結 → 平台裡的模組類型（找不到該類型時才在原頁開啟）
  const MAP = [
    [/^https?:\/\/donna12301230\.github\.io\/vocab-trainer\/?/i, "vocabApp"],
    [/^https?:\/\/donna12301230\.github\.io\/nsysu-mis-exams\/?/i, "nsysuApp"],
    [/^https?:\/\/donna12301230\.github\.io\/os-notes\/?/i, "osNotesApp"],
    [/^https?:\/\/donna12301230\.github\.io\/genai-lecture-notes\/?/i, "genaiApp"],
    [/^https?:\/\/claude\.ai\/artifact\/2Mg8JKJ6LYiTEAckxVtxeo/i, "workbenchApp"],
    [/^https?:\/\/claude\.ai\/artifact\/UrvKirykZ36DuoPtDuQFHE/i, "nsysuApp"],
    [/^https?:\/\/claude\.ai\/artifact\/KvWTWGrLts9Pg7fjH5pa6w/i, "studyPlan"],
  ];
  const SOURCE = /^https?:\/\/github\.com\/Donna12301230\//i;
  document.documentElement.classList.toggle("in-dt", inFrame);
  function go(type) {
    if (inFrame) parent.postMessage({ dt: "nav", type }, location.origin);
    else location.href = new URL("../../#type-" + type, location.href).href;
  }
  window.DTNav = go;
  document.addEventListener("click", e => {
    const a = e.target.closest && e.target.closest("a[href]"); if (!a) return;
    for (const [re, type] of MAP) if (re.test(a.href)) { e.preventDefault(); go(type); return; }
  }, true);
  function tidy() { document.querySelectorAll("a[href]").forEach(a => { if (SOURCE.test(a.href)) a.hidden = true; }); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", tidy); else tidy();
  new MutationObserver(tidy).observe(document.documentElement, { childList: true, subtree: true });
  // 考古題：從別處跳到某一題時（例如單字的「考過」題號），題目圖片載入後畫面會位移，等圖片載好再對準那一題；使用者一捲動就不再自動對準
  if (document.documentElement.dataset.dtApp === "nsysu") {
    let stop = 0;
    const target = () => { const m = /^#y(cs|mis)(\d{2,3})-p\d+-(.+)$/.exec(location.hash); return m ? document.getElementById("q-" + m[1] + m[2] + "-" + decodeURIComponent(m[3])) : null; };
    const aim = () => { if (Date.now() > stop) return; const el = target(); if (el) el.scrollIntoView({ block: "start" }); };
    const arm = () => {
      stop = Date.now() + 4000;
      [150, 500, 1000, 1800, 3000].forEach(t => setTimeout(aim, t));
      document.querySelectorAll("img").forEach(img => { if (!img.complete) img.addEventListener("load", aim, { once: true }); });
    };
    ["wheel", "touchstart", "keydown", "mousedown"].forEach(ev => window.addEventListener(ev, () => { stop = 0; }, { passive: true }));
    window.addEventListener("hashchange", arm);
    if (/^#y(cs|mis)\d/.test(location.hash)) window.addEventListener("load", arm);
  }
  // 讓平台的「今天」頁知道這個網站的資料剛更新過
  window.addEventListener("storage", () => {});
  if (inFrame) {
    const ping = () => parent.postMessage({ dt: "changed", app: document.documentElement.dataset.dtApp || "" }, location.origin);
    const _set = Storage.prototype.setItem;
    Storage.prototype.setItem = function (k, v) { _set.call(this, k, v); clearTimeout(ping.t); ping.t = setTimeout(ping, 400); };
  }
})();
