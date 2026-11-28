# -*- coding: utf-8 -*-
"""把學習網站複製進每日任務平台（apps/），加上平台的配色、站內導覽與雲端同步。

用法：python tools/build.py

來源預設是跟 daily-tasks 放在同一層的 repo（修課/ 底下），作業系統筆記在 115上/作業系統/os-notes。
原本的網站更新後（例如加了新的一講、新的單字庫），重新執行這支程式再 commit、push 即可。
工作台（apps/workbench/）是直接在這個 repo 裡維護的，不會被覆蓋。
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
PARENT = os.path.dirname(ROOT)
SOURCES = {
    "vocab": os.path.join(PARENT, "vocab-trainer"),
    "nsysu": os.path.join(PARENT, "nsysu-mis-exams"),
    "os-notes": os.path.normpath(os.path.join(PARENT, "..", "115上", "作業系統", "os-notes")),
    "genai": os.path.join(PARENT, "genai-lecture-notes"),
}
FILES = {
    "vocab": ["index.html", "icon.png"],
    "nsysu": ["index.html", "img"],
    "os-notes": ["index.html"],
    "genai": ["index.html", "lesson.html", "glossary.html", "about.html", "assets", "notes"],
}
# 需要雲端同步（用 fb.js 提供的 window.claude 介面）的網站
CLOUD = {"nsysu"}
# 放進平台時的小改動（原本的網站不受影響）：每次同步都會重新套用，找不到原句時會提醒
TOOLS = os.path.dirname(os.path.abspath(__file__))
PICK_CSS = open(os.path.join(TOOLS, "nsysu_pick.css"), encoding="utf-8").read()     # 考古題放進平台時的小樣式
PATCHES = {
    "nsysu": [
        # 英文術語已經併到單字（中山資管英文術語），在平台裡不顯示這個分頁；舊連結 #terms 改到依年度
        ('else if (h === "terms") view = "terms";', 'else if (h === "terms") view = document.documentElement.classList.contains("in-dt") ? "year" : "terms";'),
        ('<a href="#terms" data-v="terms">英文術語</a>', '<a href="#terms" data-v="terms" class="dt-hide">英文術語</a>'),
        # 左上角「← 選擇考古題」：回到平台的「選擇考古題」（之後會有多益、iPAS 等其他套）
        ('<a href="#year" data-v="year">依年度</a>', '<a href="#" class="dt-back" onclick="parent.postMessage({dt:\'nav\',type:\'examBanks\'},location.origin);return false;">← 選擇考古題</a>\n    <a href="#year" data-v="year">依年度</a>'),
    ],
    "vocab": [
        # 一進單字先選單字庫：目前使用中的單字庫也要有「進入」按鈕
        ("""${cur ? '' : `<button class="btn sm primary" data-act="bank-use" data-b="${esc(b.id)}">使用這個</button>`}""",
         """${cur ? '<a class="btn sm primary" href="#/">進入</a>' : `<button class="btn sm primary" data-act="bank-use" data-b="${esc(b.id)}">進入</button>`}"""),
        # 單字庫清單就是第一頁：不再有「回首頁」，標題改成「選擇單字庫」（跟筆記的「選擇課程」一致）
        ('<div class="crumb"><a href="#/">← 回首頁</a></div>\n  <h2>單字庫</h2>', "<h2>選擇單字庫</h2>"),
        # 進到單字庫裡：左上角「← 選擇單字庫」（跟筆記的「← 選擇課程」一致），拿掉右邊的「切換／新增單字庫」
        ('<a class="btn sm" href="#/banks">切換／新增單字庫</a>', ""),
        ('<section class="hero">', '<div class="crumb"><a href="#/banks">← 選擇單字庫</a></div>\n  <section class="hero">'),
        # 選擇單字庫頁不顯示上方工具列（單字組、不熟、考試、設定），進到單字庫才出現
        ("function render(){\n  const r = route();", "function render(){\n  const r = route();\n  document.documentElement.classList.toggle('dt-picking', r.a === 'banks');"),
        # 不顯示「新增單字庫」：新的單字庫用 AI 整理好一整套，再請 Claude 加進來
        ('<section class="panel" id="addBank">', '<section class="panel" id="addBank" style="display:none">'),
        # 「考過：111-21」的題號可以點，跳到考古題那一題
        ("${w.note ? `<div class=\"note\">${esc(w.note)}</div>` : ''}", "${w.note ? `<div class=\"note\">${dtNote(w)}</div>` : ''}"),
        ("${w.note ? `<div class=\"c-note\">${esc(w.note)}</div>` : ''}", "${w.note ? `<div class=\"c-note\">${dtNote(w)}</div>` : ''}"),
    ],
}

# 平台配色（跟 index.html 的 :root 一致）
LIGHT = dict(bg="#f3f5f9", surface="#ffffff", sunk="#e9edf3", ink="#1c2333", muted="#5b6678", line="#d8dee8",
             accent="#2b3f7a", accent_soft="#e2e7f5", accent_ink="#ffffff")
DARK = dict(bg="#12151c", surface="#1a1f29", sunk="#232a37", ink="#e3e7ef", muted="#98a2b4", line="#2e3544",
            accent="#9fb4f0", accent_soft="#263055", accent_ink="#10162a")
# 每個網站自己的變數名稱 → 平台配色
VARMAP = {
    "vocab": {"--bg": "bg", "--surface": "surface", "--text": "ink", "--muted": "muted", "--line": "line",
              "--accent": "accent", "--accent-soft": "accent_soft", "--accent-ink": "accent_ink"},
    "nsysu": {"--bg": "bg", "--paper": "surface", "--ink": "ink", "--muted": "muted", "--line": "line",
              "--accent": "accent", "--accent-soft": "accent_soft"},
    "os-notes": {"--bg": "bg", "--grid": "sunk", "--surface": "surface", "--ink": "ink", "--muted": "muted",
                 "--rule": "line", "--accent": "accent", "--accent-soft": "accent_soft"},
    "genai": {"--paper": "bg", "--paper-2": "sunk", "--ink": "ink", "--ink-soft": "muted", "--line": "line",
              "--accent": "accent", "--accent-soft": "accent_soft"},
}


def theme(app):
    m = VARMAP[app]
    decl = lambda pal: ";".join(f"{k}:{pal[v]}" for k, v in m.items())
    return ('<style id="dt-theme">'
            f'html.in-dt:root{{{decl(LIGHT)}}}'
            f'@media (prefers-color-scheme: dark){{html.in-dt:root:not([data-theme="light"]){{{decl(DARK)};color-scheme:dark}}}}'
            f'html.in-dt:root[data-theme="dark"]{{{decl(DARK)};color-scheme:dark}}'
            '</style>')


def term_refs():
    """從考古題網站取出每個術語考過的題號 → 題目位置，給單字練習用（英文小寫 → [[題號, 網址片段], ...]）。"""
    src = os.path.join(SOURCES["nsysu"], "index.html")
    if not os.path.isfile(src):
        return {}
    s = open(src, encoding="utf-8").read()
    i = s.find('"terms":[')
    if i < 0:
        return {}
    i = s.index("[", i)
    depth, j, ins, esc_ = 0, i, False, False
    while j < len(s):
        ch = s[j]
        if ins:
            if esc_:
                esc_ = False
            elif ch == "\\":
                esc_ = True
            elif ch == '"':
                ins = False
        elif ch == '"':
            ins = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                break
        j += 1
    out = {}
    for t in json.loads(s[i:j + 1]):
        refs = [[r["l"], r["h"]] for r in t.get("refs", []) if r.get("l") and r.get("h")]
        if refs:
            out.setdefault(t["en"].strip().lower(), refs)
    return out


VOCAB_CSS = open(os.path.join(TOOLS, "vocab_dt.css"), encoding="utf-8").read()   # 單字放進平台時：字型與介面跟筆記、考古題一致
VOCAB_FONT = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
              'family=IBM+Plex+Mono:wght@400;600&family=LXGW+WenKai+TC:wght@400;700&family=Noto+Sans+TC:wght@400;500;700&display=swap">')
VOCAB_JS = ("<script>window.DT_TERM_REFS=__REFS__;\n" + open(os.path.join(TOOLS, "vocab_refs.js"), encoding="utf-8").read() + "</script>"
            "<style>html.in-dt.dt-picking header.top{display:none}"
            "html.in-dt a.dtref,html.in-dt a.dtmore-btn{color:var(--accent);text-decoration:underline;text-underline-offset:3px;cursor:pointer}</style>")


def embed_v():
    import hashlib
    h = hashlib.md5()
    for f in ("embed.js", "embed.css"):
        h.update(open(os.path.join(ROOT, "apps", f), "rb").read())
    return h.hexdigest()[:8]


def inject(html, app, depth):
    head = (f'<script>document.documentElement.dataset.dtApp="{app}";'
            'if(window.parent!==window)document.documentElement.classList.add("in-dt")</script>'
            + theme(app))
    if app in CLOUD:
        head += f'<script>window.DT_APP="{app}"</script><script src="{depth}fb.js"></script>'
    head += f'<link rel="stylesheet" href="{depth}apps/embed.css?v={embed_v()}">'
    if app == "nsysu":
        head += "<style>" + PICK_CSS + "</style>"
    if app == "vocab":
        head += VOCAB_JS.replace("__REFS__", json.dumps(term_refs(), ensure_ascii=False, separators=(",", ":")))
        head += VOCAB_FONT + '<style id="dt-vocab">' + VOCAB_CSS + "</style>"
    if "</head>" not in html or "</body>" not in html:
        raise SystemExit(f"{app}: 找不到 </head> 或 </body>")
    html = html.replace("</head>", head + "\n</head>", 1)
    i = html.rfind("</body>")
    return html[:i] + f'<script src="{depth}apps/embed.js?v={embed_v()}"></script>\n' + html[i:]


def build(app):
    src, dst = SOURCES[app], os.path.join(ROOT, "apps", app)
    if not os.path.isdir(src):
        print(f"跳過 {app}：找不到 {src}")
        return
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for name in FILES[app]:
        s, d = os.path.join(src, name), os.path.join(dst, name)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        elif os.path.isfile(s):
            shutil.copy2(s, d)
        else:
            print(f"  {app}: 沒有 {name}")
    n = 0
    for dirpath, _, files in os.walk(dst):
        for f in files:
            if not f.endswith(".html"):
                continue
            p = os.path.join(dirpath, f)
            depth = "../" * (os.path.relpath(p, ROOT).count(os.sep))
            html = open(p, encoding="utf-8").read()
            if f == "index.html" and dirpath == dst:
                for a, b in PATCHES.get(app, []):
                    if a in html:
                        html = html.replace(a, b, 1)
                    else:
                        print(f"  {app}: 找不到要修改的地方，請檢查 PATCHES：{a[:40]}…")
                if app == "nsysu":
                    import nsysu_notes   # 補寫的解析（tools/nsysu_notes/）
                    html = nsysu_notes.apply(html)
            open(p, "w", encoding="utf-8", newline="\n").write(inject(html, app, depth))
            n += 1
    size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(dst) for f in fs)
    print(f"{app}: {n} 個頁面，{size / 1048576:.1f} MB")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for a in (sys.argv[1:] or SOURCES):
        build(a)
