// 放進每日任務平台時，單字練習的「考過：111-21」題號變成連結，點了跳到考古題那一題。
// 題號對照表 window.DT_TERM_REFS 由 tools/build.py 從考古題網站產生（英文小寫 → [[題號, 網址片段], ...]）。
function dtNote(w) {
  var s = String(w.note || "");
  var esc = function (x) { return String(x).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); };
  var R = window.parent !== window && window.DT_TERM_REFS && window.DT_TERM_REFS[String(w.w || "").trim().toLowerCase()];
  if (!R || !/^考過：/.test(s)) return esc(s);
  // 用完整的題號清單（單字庫裡的文字只寫了前幾個，後面是「等 N 處」）
  var links = R.map(function (r) { return '<a href="#" class="dtref" data-dtref="' + esc(r[1]) + '" title="看這一題考古題">' + esc(r[0]) + "</a>"; });
  var N = 6;
  if (links.length <= N) return "考過：" + links.join("、");
  return "考過：" + links.slice(0, N).join("、") + '<span class="dtmore" hidden>、' + links.slice(N).join("、") + '</span> <a href="#" class="dtmore-btn" data-dtmore="1">還有 ' + (links.length - N) + " 處</a>";
}
document.addEventListener("click", function (ev) {
  var t = ev.target;
  var more = t.closest && t.closest("[data-dtmore]");
  if (more) { ev.preventDefault(); ev.stopPropagation(); var sp = more.previousElementSibling; if (sp) sp.hidden = false; more.remove(); return; }
  var a = t.closest && t.closest("[data-dtref]");
  if (!a) return;
  ev.preventDefault(); ev.stopPropagation();
  parent.postMessage({ dt: "nav", type: "nsysuApp", sub: a.getAttribute("data-dtref") }, location.origin);
}, true);
