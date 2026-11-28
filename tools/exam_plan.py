# -*- coding: utf-8 -*-
"""考古題每日進度（中山計概、MIS，iPAS 初級管理、技術，多益 Vol.7、Vol.8）：從中山資管考古題（apps/nsysu/index.html）排出計概、MIS 的題目順序，
寫進工作台（apps/workbench/index.html 的 EXAM_PLAN）。工作台第一次打開時會把計概(一)、MIS 課本、
補充和它們的看題／做題換成「一天 1–2 題」的考古題（見 examPlan()）。
順序：依章節（照考古題網站「依章節」的順序），同一章裡新的年度在前、同一年照原卷題號；同一天不跨章節。選擇題一天 2 題，問答／填充／申論一天 1 題。
計概的 C 語言章節（含二元樹）也照章節排進來。
近三年（MOCK_FROM 學年度起，之後新增的年度也算）不拆進章節進度，整份留到考前一個月當模擬考，
接在計概、MIS 各自那條線的最後（見 mock()）。
用法：python tools/exam_plan.py"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(ROOT, "apps/nsysu/index.html"), encoding="utf-8").read()
D = json.loads(re.search(r'<script type="application/json" id="data">(.*?)</script>', src, re.S).group(1))
names = {k["c"]: k["name"] for k in D["cs"] + D["mis"]}


def is_c(c):
    return (c.startswith("c") and not c.startswith("cs")) or c == "bt"


def topic(c):
    n = names.get(c, "")
    n = re.sub(r"^(計概|MIS) ", "", n)
    return n.replace("新議題：", "")


# 近三年的考卷留著考前限時整份寫，不拆進章節進度
MOCK_FROM = 113


def groups(s):
    # 依章節（照考古題網站「依章節」的順序），同一章裡新的年度在前、同一年照原卷題號；同一天不跨章節
    order = {k["c"]: i for i, k in enumerate(D[s])}
    qs = []
    for p in D["papers"]:
        if p["s"] != s or p["y"] >= MOCK_FROM:
            continue
        for n, q in enumerate(p["qs"]):
            qs.append((order.get(q["c"], 999), -p["y"], n, p, q))
    qs.sort(key=lambda x: x[:3])
    out, cur, curc = [], [], None
    for _, _, _, p, q in qs:
        ref = [q["id"], "y%s%d-p%d-%s" % (s, p["y"], q["p"], re.sub(r"\s", "", q["id"])), (q.get("t") or "") + "｜" + topic(q["c"]), q["c"]]
        if cur and (q["k"] != "選" or q["c"] != curc):
            out.append(cur); cur = []
        if q["k"] != "選":
            out.append([ref])
        else:
            cur.append(ref); curc = q["c"]
            if len(cur) == 2:
                out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


# iPAS 初級、中級：依章節（tools/ipas_chapters.py 標的 c），同一章裡新的場次在前（樣題最後）；每題一筆，一天幾題由平台照期限平均分
IP = json.load(open(os.path.join(ROOT, "apps/ipas/data.json"), encoding="utf-8"))


def ipas(s):
    order = {c: i for i, (c, _) in enumerate(IP["ch"][s])}
    names = dict(IP["ch"][s])
    rows = []
    for p in IP["papers"]:
        if p["s"] != s:
            continue
        rnd = p["y"] + "-" + p["r"] if p["y"] else "樣題"
        for n, q in enumerate(p["qs"], 1):
            yk = -int(p["y"]) * 10 - int(p["r"]) if p["y"] else 0
            rows.append((order[q["c"]], yk, n, [rnd + " #" + str(n), "year/" + p["id"] + "/" + str(n), names[q["c"]].split("：")[0], q["c"]]))
    rows.sort(key=lambda x: x[:3])
    return [[r[3]] for r in rows]


# iPAS 初級以書為主：照《iPAS 初級資安工程師攻略》的小節順序，每一小節帶著配到它的題目（tools/ipas_chapters.py 標的 u）。
# 平台照期限把小節分成每天一份（看頁數和題數），所以每天是「讀幾個小節＋這幾節的考古題」。
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ipas_books  # noqa: E402


def book(s):
    qs = {}
    for p in IP["papers"]:
        if p["s"] != s:
            continue
        rnd = p["y"] + "-" + p["r"] if p["y"] else "樣題"
        yk = -int(p["y"]) * 10 - int(p["r"]) if p["y"] else 0
        for n, q in enumerate(p["qs"], 1):
            qs.setdefault(q["u"], []).append((yk, n, [rnd + " #" + str(n), "year/" + p["id"] + "/" + str(n)]))
    out = []
    for x in ipas_books.units(s):
        out.append({"u": x["u"], "t": x["t"], "p": x["p"], "n": x["n"], "q": [r[2] for r in sorted(qs.get(x["u"], []), key=lambda r: r[:2])]})
    return out


# 多益官方全真試題 Vol.7、Vol.8（各 2 回）：一天一個 Part，每一回的 Part 都做完後，在下一個週六計時做一次整回
PARTS = [("Part 1", "聽力・照片描述 6 題"), ("Part 2", "聽力・應答問題 25 題"), ("Part 3", "聽力・簡短對話 39 題"), ("Part 4", "聽力・簡短獨白 30 題"),
         ("Part 5", "閱讀・句子填空 30 題"), ("Part 6", "閱讀・段落填空 16 題"), ("Part 7", "閱讀・單篇／多篇閱讀 54 題")]


def toeic(v):
    out = []
    for t in (1, 2):
        for pt, d in PARTS:
            out.append([["Vol.%d Test %d %s" % (v, t, pt), "", d, "T%d" % t]])
        out.append([["Vol.%d Test %d 整回" % (v, t), "", "模擬考 200 題・計時 2 小時，做完再對答案", "full"]])   # 這一回的 Part 做完後的週六
    return out


# 模擬考：MOCK_FROM 學年度起每一年一份整卷（舊的年度在前，最新的一份最接近考試），接在計概、MIS 各自那條線的章節進度後面，
# 每份後面接一天檢討。整卷那一筆 [標籤, "ycs115", 說明, "mock"]，點了打開整份；檢討那一筆 [標題, "", 說明, "rev", 認得做過沒的 key]。
# 平台把章節進度排到考前一個月，模擬考排在之後到考前 3 天，計概和 MIS 的同一年排同一天（照正式考試）。
def mock(s):
    out = []
    nm = "計概" if s == "cs" else "MIS"
    for p in sorted((p for p in D["papers"] if p["s"] == s and p["y"] >= MOCK_FROM), key=lambda p: p["y"]):
        out.append([["%s %d 整卷" % (nm, p["y"]), "y%s%d" % (s, p["y"]), "照正式考試限時、不看筆記，寫完再對答案（%d 題）" % len(p["qs"]), "mock"]])
        out.append([["檢討 %s %d 錯題" % (nm, p["y"]), "", "把錯的題目整理進錯題本，回頭補那一章的觀念", "rev", "rev-%s%d" % (s, p["y"])]])
    return out


plan = {"cs": groups("cs") + mock("cs"), "mis": groups("mis") + mock("mis"), "ipm": book("I11"), "ipt": book("I12"), "ipr": ipas("I21"), "ipd": ipas("I22"), "toeic7": toeic(7), "toeic8": toeic(8)}
js = "const EXAM_PLAN = " + json.dumps(plan, ensure_ascii=False, separators=(",", ":")) + ";"
path = os.path.join(ROOT, "apps/workbench/index.html")
html = open(path, encoding="utf-8").read()
new, n = re.subn(r"  // EXAM_PLAN:BEGIN\n.*?\n  // EXAM_PLAN:END", lambda m: "  // EXAM_PLAN:BEGIN\n  " + js + "\n  // EXAM_PLAN:END", html, flags=re.S)
if not n:
    raise SystemExit("工作台裡找不到 EXAM_PLAN 標記")
open(path, "w", encoding="utf-8").write(new)
# 每一科題目的指紋寫進平台（index.html 的 EXAM_REV）：題目有增減時，平台打開就會把那一科明天起還沒做的重排
import hashlib
rev = {k: hashlib.md5(json.dumps(v, ensure_ascii=False).encode("utf-8")).hexdigest()[:8] for k, v in plan.items()}
ipath = os.path.join(ROOT, "index.html")
ih = open(ipath, encoding="utf-8").read()
ih2, n2 = re.subn(r"  // EXAM_REV:BEGIN\n.*?\n  // EXAM_REV:END", lambda m: "  // EXAM_REV:BEGIN\n  const EXAM_REV = " + json.dumps(rev) + ";\n  // EXAM_REV:END", ih, flags=re.S)
if not n2:
    raise SystemExit("平台裡找不到 EXAM_REV 標記")
open(ipath, "w", encoding="utf-8").write(ih2)
print("模擬考 %d 份（含在計概、MIS 那兩條線的最後）" % sum(1 for k in ("cs", "mis") for g in plan[k] if g[0][3] == "mock"))
print("計概 %d 天、MIS %d 天、中級規劃 %d 題、中級防護 %d 題、多益 Vol.7 %d 天、Vol.8 %d 天" % tuple(len(plan[k]) for k in ("cs", "mis", "ipr", "ipd", "toeic7", "toeic8")))
for k in ("ipm", "ipt"):
    print("iPAS %s：%d 小節、%d 頁、%d 題" % ("管理" if k == "ipm" else "技術", len(plan[k]), sum(x["n"] for x in plan[k]), sum(len(x["q"]) for x in plan[k])))
