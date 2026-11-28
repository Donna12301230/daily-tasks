# -*- coding: utf-8 -*-
"""中山資管考古題：補寫的解析（tools/nsysu_notes/*.json）併進考古題網站的 DATA.notes。

用法：python tools/nsysu_notes.py        （直接改 apps/nsysu/index.html）
tools/build.py 同步考古題網站時也會自動套用，所以重新同步不會把這裡補的解析蓋掉。
原本網站已經有的解析不會被覆蓋（同一題以原本網站為準）。

解析檔的格式（一個檔一份考卷，內容是一個陣列，每題一筆）：
  {"id": "94-1",                  題號，跟考古題的 q.id 一樣
   "s": "cs",                     科目（cs 計概、mis 資管）；省略時用檔名開頭
   "ans": "**B. Presentation**",  正確答案（顯示成「這題的正確答案是 …。」）
   "items": ["**題目**：…", "**核心觀念**：…"],
   "opts_title": "各選項解析",     可省略
   "opts": [{"h": "A. … — 錯", "x": ["…", "…"]}]}
文字裡用 **粗體** 標重點；以 ``` 開頭的一段是程式碼；其他文字有換行時每行變成一條（「- 」可省略）。
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nsysu_notes")
DATA_RE = re.compile(r'(<script type="application/json" id="data">)(.*?)(</script>)', re.S)


def runs(text):
    """「**粗體**」→ [[文字, 是否粗體], …]；``` 開頭的整段是程式碼。"""
    if text.startswith("```"):
        return [[text, False]]
    out = []
    for i, part in enumerate(re.split(r"\*\*", text)):
        if part:
            out.append([part, i % 2 == 1])
    return out


def lines(texts):
    """多行文字拆成好幾條（「- 」開頭的行去掉符號）；程式碼段落保持一整段。"""
    out = []
    for t in texts:
        if t.startswith("```"):
            out.append(runs(t))
            continue
        for line in t.split("\n"):
            line = re.sub(r"^\s*[-•]\s*", "", line).strip()
            if line:
                out.append(runs(line))
    return out


def convert(n):
    note = {"answer": [["這題的正確答案是 ", False]] + runs(n["ans"]) + [["。", False]]}
    note["items"] = lines(n.get("items", []))
    if n.get("opts"):
        note["opts_title"] = n.get("opts_title", "各選項解析")
        note["opts"] = [{"h": [[o["h"], True]], "x": lines(o.get("x", []))} for o in n["opts"]]
    return note


def load():
    notes = {}
    for f in sorted(glob.glob(os.path.join(NOTES_DIR, "*.json"))):
        subj = os.path.basename(f).split("-")[0]
        for n in json.load(open(f, encoding="utf-8")):
            notes[n.get("s", subj) + ":" + n["id"]] = convert(n)
    return notes


def apply(html):
    m = DATA_RE.search(html)
    if not m:
        print("  nsysu: 找不到題目資料，解析沒有併進去")
        return html
    data = json.loads(m.group(2))
    ids = {p["s"] + ":" + q["id"] for p in data["papers"] for q in p.get("qs", [])}
    have = data.setdefault("notes", {})
    added, missing = 0, []
    for k, v in load().items():
        if k not in ids:
            missing.append(k)
        elif k not in have or have[k].get("dt"):
            v["dt"] = 1   # 標記是這裡補的，之後改了可以再覆蓋
            have[k] = v
            added += 1
    if missing:
        print("  nsysu: 解析的題號在考古題裡找不到：" + "、".join(missing))
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    print(f"  nsysu: 併進 {added} 題補寫的解析（共 {len(have)} 題有解析）")
    return html[:m.start(2)] + raw + html[m.end(2):]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    p = os.path.join(ROOT, "apps", "nsysu", "index.html")
    html = open(p, encoding="utf-8").read()
    open(p, "w", encoding="utf-8", newline="\n").write(apply(html))
