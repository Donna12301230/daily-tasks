# -*- coding: utf-8 -*-
"""把 iPAS 資安初級、中級考古題 PDF 轉成題目資料（apps/ipas/data.json），有圖或表的題目另外截圖。

用法：python tools/ipas_extract.py
需要 poppler（pdftotext、pdftohtml、pdftoppm）。PDF 放在 apps/ipas/pdf/，檔名「場次_I11…pdf」（初級 I11、I12 每份 50 題；中級 I21、I22 每份 40 題，有複選和題組）。
"""
import glob, json, os, re, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "apps", "ipas")
PDF = os.path.join(APP, "pdf")
IMG = os.path.join(APP, "img")
FW = str.maketrans("ＡＢＣＤ", "ABCD")
FIG = re.compile(r"附圖|下圖|如圖|圖中|圖示|下表|附表|如表|表中|示意圖|下列程式|程式碼如下|如下所示|附件")
SUBJ = {"I11": "資訊安全管理概論", "I12": "資訊安全技術概論", "I21": "資訊安全規劃實務", "I22": "資訊安全防護實務"}
COUNT = {"I11": 50, "I12": 50, "I21": 40, "I22": 40}


def run(*a):
    return subprocess.run(a, capture_output=True, check=True).stdout.decode("utf-8", "replace")


def header(line):
    s = line.strip()
    return (not s or re.fullmatch(r"\d{1,2}", s) or "初級試題" in s or "能力鑑定樣題" in s or s.startswith("科目")
            or "考試日期" in s or re.search(r"第\s*\d+\s*頁，共", s) or s.startswith("單選題")
            or "公告試題" in s or re.fullmatch(r"答案\s*題目", s) or re.match(r"[一二三]、\s*選擇題", s) or "以下空白" in s or re.fullmatch(r"第[一二]科：\S+", s))


def parse_text(path):
    pages = run("pdftotext", "-layout", path, "-").split("\f")
    qs, cur, pend = [], None, None   # pend: 111-2 那種答案寫在題號下一行
    for pi, page in enumerate(pages, 1):
        for raw in page.split("\n"):
            line = raw.translate(FW).rstrip()
            if header(line):
                continue
            m = re.match(r"^\s*([A-D]{1,4})?\s*(\d{1,2})\.\s*(.*)$", line)   # 中級複選題的答案是 ACD 這樣
            if m and int(m.group(2)) == len(qs) + 1 and (m.group(1) or re.match(r"^\s{0,8}\d", line)):
                cur = {"n": int(m.group(2)), "a": m.group(1) or "", "q": m.group(3).strip(), "o": [], "p": pi}
                qs.append(cur); pend = None if m.group(1) else cur
                continue
            if pend is not None and re.fullmatch(r"\s*[A-D]\s*", line):
                pend["a"] = line.strip(); pend = None; continue
            if not cur:
                continue
            parts = re.split(r"\(([A-D])\)", line)
            if len(parts) > 1:
                pre = parts[0].strip()
                if pre:
                    add(cur, pre)
                for k in range(1, len(parts), 2):
                    cur["o"].append(parts[k + 1].strip())
            else:
                add(cur, line.strip())
    return qs


def join(a, b):
    if not a: return b
    if not b: return a
    if re.match(r"[\u0000-ɏ]", a[-1]) and re.match(r"[\u0000-ɏ]", b[0]):
        return a + " " + b
    return a + b


CJK = "\u2e80-\u9fff\uff00-\uffef\u3000-\u303f"


def tidy(t):
    """左右對齊的排版會在中文字之間多出空白，拿掉。"""
    t = re.sub(r"(?<=[%s])[ \t]+(?=[%s])" % (CJK, CJK), "", t)
    t = re.sub(r"(?<=[%s])[ \t]+(?=[A-Za-z0-9(])|(?<=[A-Za-z0-9)])[ \t]+(?=[%s])" % (CJK, CJK), " ", t)
    return re.sub(r"[ \t]{2,}", " ", t).strip()


def add(cur, txt):
    if cur["o"]:
        cur["o"][-1] = join(cur["o"][-1], txt)
    else:
        cur["q"] = join(cur["q"], txt)


def positions(path):
    """每一題題號的位置：[(頁, y)]，和每頁的圖片位置。"""
    html = run("pdftotext", "-bbox", path, "-")
    cand, pg = [], 0
    for m in re.finditer(r'<page width="([\d.]+)" height="([\d.]+)">|<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="[\d.]+" yMax="[\d.]+">([^<]*)</word>', html):
        if m.group(1):
            pg += 1; continue
        mm = re.fullmatch(r"(\d{1,2})\.", m.group(5))
        if mm and float(m.group(3)) < 160:
            cand.append((pg, float(m.group(4)), int(mm.group(1)), float(m.group(3))))
    out = []
    for pg, y, n, x in sorted(cand):
        if n == len(out) + 1:
            out.append((pg, y, x))
    return out


def images(path):
    """每頁的圖片：[(頁, top, height)]，單位跟 pdftotext 一樣是 pt（pdftohtml -xml 預設放大 1.5 倍）。"""
    with tempfile.TemporaryDirectory() as d:
        xml = run("pdftohtml", "-xml", "-stdout", "-enc", "UTF-8", path, os.path.join(d, "x"))
    res, pg, raw = [], 0, []
    for m in re.finditer(r'<page number="(\d+)"|<image top="(\d+)" left="(\d+)" width="(\d+)" height="(\d+)"', xml):
        if m.group(1):
            pg = int(m.group(1)); continue
        if int(m.group(4)) > 60 and int(m.group(5)) > 40:
            raw.append((pg, m.group(2), m.group(3), m.group(4), m.group(5)))
    # 每一頁同一個位置都有的圖是浮水印，不算題目的圖
    seen = {}
    for r in raw:
        seen.setdefault(r[1:], set()).add(r[0])
    wm = {k for k, v in seen.items() if len(v) >= max(3, pg // 2)}
    for r in raw:
        if r[1:] not in wm:
            res.append((r[0], int(r[1]) / 1.5, int(r[4]) / 1.5))
    return res


def main():
    os.makedirs(IMG, exist_ok=True)
    for f in glob.glob(os.path.join(IMG, "*.jpg")):
        os.remove(f)
    papers = []
    for path in sorted(glob.glob(os.path.join(PDF, "*.pdf"))):
        name = os.path.basename(path)
        rnd, rest = name.split("_", 1)
        subj = rest[:3]
        pid = ("s" if rnd == "樣題" else rnd) + "-" + subj
        qs = parse_text(path)
        pos = positions(path)
        info = run("pdfinfo", path)
        W = float(re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", info).group(1))
        H = float(re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", info).group(2))
        # pdftohtml -xml 的座標是 1.5 倍
        imgs = images(path)
        bad = [q["n"] for q in qs if not q["a"] or len(q["o"]) != 4]
        want = COUNT.get(subj, 50)
        if len(qs) != want or len(pos) != want or bad:
            print(f"  ⚠ {name}: {len(qs)} 題、{len(pos)} 個題號位置，有問題的題：{bad}")
        for i, q in enumerate(qs):
            if i >= len(pos):
                break
            p, y, x0 = pos[i]
            nxt = pos[i + 1] if i + 1 < len(pos) else (p, H - 60, 0)
            ends = [(p, nxt[1] - 3)] if nxt[0] == p else [(p, H - 60), (nxt[0], nxt[1] - 3)]
            has_img = any(ip == p and y - 5 <= it <= (nxt[1] if nxt[0] == p else H) for ip, it, _ in imgs) or \
                any(nxt[0] != p and ip == nxt[0] and it < nxt[1] for ip, it, _ in imgs)
            if not (has_img or FIG.search(q["q"])):
                continue
            files = []
            segs = [(p, y - 4, ends[0][1])] + ([(ends[1][0], 96, ends[1][1])] if len(ends) > 1 else [])
            for k, (sp, y0, y1) in enumerate(segs):
                if y1 - y0 < 12:
                    continue
                dpi = 150; sc = dpi / 72
                out = os.path.join(IMG, f"{pid}-{q['n']}{'' if k == 0 else '-' + str(k + 1)}")
                subprocess.run(["pdftoppm", "-jpeg", "-jpegopt", "quality=80", "-r", str(dpi), "-f", str(sp), "-l", str(sp), "-singlefile",
                                "-x", str(int((x0 - 3) * sc)), "-y", str(int(y0 * sc)), "-W", str(int((W - (58 if subj[1] == "1" else 22) - x0) * sc)), "-H", str(int((y1 - y0) * sc)), path, out], check=True)
                files.append(os.path.basename(out) + ".jpg")
            q["img"] = files
        for q in qs:
            q.pop("n", None)
            q["q"] = tidy(q["q"]); q["o"] = [tidy(o) for o in q["o"]]
        y, r = (rnd.split("-") + [""])[:2] if rnd != "樣題" else ("", "")
        papers.append({"id": pid, "y": y, "r": r, "s": subj, "name": ("樣題" if rnd == "樣題" else f"{y} 年第 {r} 次") + "・" + SUBJ[subj],
                       "pdf": "pdf/" + name, "qs": qs})
    papers.sort(key=lambda x: (x["y"] == "", x["y"], x["r"], x["s"]), reverse=False)
    json.dump({"papers": papers}, open(os.path.join(APP, "data.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    n = sum(len(p["qs"]) for p in papers); ni = sum(1 for p in papers for q in p["qs"] if q.get("img"))
    print(f"{len(papers)} 份、{n} 題，{ni} 題有截圖")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
