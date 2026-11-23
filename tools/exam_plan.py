# -*- coding: utf-8 -*-
"""碩班考古題每日進度：從中山資管考古題（apps/nsysu/index.html）排出計概、MIS 的題目順序，
寫進工作台（apps/workbench/index.html 的 EXAM_PLAN）。工作台第一次打開時會把計概(一)、MIS 課本、
補充和它們的看題／做題換成「一天 1–2 題」的考古題（見 examPlan()）。
順序：依章節（照考古題網站「依章節」的順序），同一章裡新的年度在前、同一年照原卷題號；同一天不跨章節。選擇題一天 2 題，問答／填充／申論一天 1 題。
計概的 C 語言章節（含二元樹）不排進來，留給 C 語言課本那條線。
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


def groups(s):
    # 依章節（照考古題網站「依章節」的順序），同一章裡新的年度在前、同一年照原卷題號；同一天不跨章節
    order = {k["c"]: i for i, k in enumerate(D[s])}
    qs = []
    for p in D["papers"]:
        if p["s"] != s:
            continue
        for n, q in enumerate(p["qs"]):
            if s == "cs" and is_c(q["c"]):
                continue
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


plan = {"cs": groups("cs"), "mis": groups("mis")}
js = "const EXAM_PLAN = " + json.dumps(plan, ensure_ascii=False, separators=(",", ":")) + ";"
path = os.path.join(ROOT, "apps/workbench/index.html")
html = open(path, encoding="utf-8").read()
new, n = re.subn(r"  // EXAM_PLAN:BEGIN\n.*?\n  // EXAM_PLAN:END", lambda m: "  // EXAM_PLAN:BEGIN\n  " + js + "\n  // EXAM_PLAN:END", html, flags=re.S)
if not n:
    raise SystemExit("工作台裡找不到 EXAM_PLAN 標記")
open(path, "w", encoding="utf-8").write(new)
print("計概 %d 天、MIS %d 天" % (len(plan["cs"]), len(plan["mis"])))
