# -*- coding: utf-8 -*-
"""把學習網站複製進每日任務平台（apps/），加上平台的配色、站內導覽與雲端同步。

用法：python tools/build.py

來源預設是跟 daily-tasks 放在同一層的 repo（修課/ 底下），作業系統筆記在 115上/作業系統/os-notes。
原本的網站更新後（例如加了新的一講、新的單字庫），重新執行這支程式再 commit、push 即可。
工作台（apps/workbench/）是直接在這個 repo 裡維護的，不會被覆蓋。
"""
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


def inject(html, app, depth):
    head = (f'<script>document.documentElement.dataset.dtApp="{app}";'
            'if(window.parent!==window)document.documentElement.classList.add("in-dt")</script>'
            + theme(app))
    if app in CLOUD:
        head += f'<script>window.DT_APP="{app}"</script><script src="{depth}fb.js"></script>'
    head += f'<link rel="stylesheet" href="{depth}apps/embed.css">'
    if "</head>" not in html or "</body>" not in html:
        raise SystemExit(f"{app}: 找不到 </head> 或 </body>")
    html = html.replace("</head>", head + "\n</head>", 1)
    i = html.rfind("</body>")
    return html[:i] + f'<script src="{depth}apps/embed.js"></script>\n' + html[i:]


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
            open(p, "w", encoding="utf-8", newline="\n").write(inject(html, app, depth))
            n += 1
    size = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(dst) for f in fs)
    print(f"{app}: {n} 個頁面，{size / 1048576:.1f} MB")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for a in (sys.argv[1:] or SOURCES):
        build(a)
