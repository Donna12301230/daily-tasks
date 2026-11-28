# -*- coding: utf-8 -*-
"""iPAS 資安考古題（初級、中級）：替每一題標章節（寫進 apps/ipas/data.json 每題的 c，章節清單放在 data.json 的 ch）。
初級章節、順序照官方學習指引和《iPAS 初級資安工程師攻略》管理概論篇、技術概論篇的評鑑主題；用關鍵字判斷，題目、選項都看，題目的分數加倍。
判斷不出來的題目沿用同一份卷子前一題的章節（原卷大致照主題排）。
用法：python tools/ipas_chapters.py   （之後再跑 python tools/exam_plan.py 更新每日進度）"""
import json
import os
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "apps/ipas/data.json")

CH = {
    # 初級：管理照《iPAS 初級資安工程師攻略─管理概論篇》（博碩）目錄的節次與順序（第 1 章是錯題本，從 2.1 起）；
    # 技術照同系列技術概論篇，節次用官方學習指引的評鑑主題、編號照書的排法
    "I11": [
        ("m11", "2.1 資訊安全管理系統", r"機密性|完整性|可用性|不可否認|CIA|資訊安全特性|ISMS|PCI|BS 7799|BS 10012|62443|27701|資訊安全管理系統|27001|27002|2700\d|PDCA|戴明|Deming|適用性聲明|SoA|管理審查|資訊安全政策|資安政策|管理階層|高階管理|國際標準|ISO/IEC|資安長|稽核|驗證|第一方|第二方|第三方|矯正措施|不符合|人員|員工|離職|教育訓練|保密協議|實體|機房|門禁|委外|供應商|供應鏈|外包|SLA|桌面淨空|螢幕淨空"),
        ("m12", "2.2 相關法規概論與遵循", r"上市上櫃|內部控制|情資分享|法規|法律|資通安全管理法|資安法|資通安全責任等級|公務機關|特定非公務機關|關鍵基礎設施|刑法|電子簽章法|遵循|適法"),
        ("m13", "2.3 隱私權保護與智慧財產權", r"HIPAA|HIPPA|29100|DLP|創用|Creative Commons|個人資料|個資|隱私|著作權|智慧財產|專利|商標|營業秘密|GDPR|OECD|倫理|PAPA|去識別"),
        ("m24", "2.4 資安時事分析", r"FIDO|零信任|Zero Trust|暗網|Dark ?Web|勒索|Living Off|LotL|TPM|信任運算|生日攻擊|Birthday"),
        ("m21", "3.1 資訊資產分級分類與盤點", r"資產|盤點|分級|分類|擁有者|標示|媒體處理|媒體銷毀|保管"),
        ("m22", "3.2 風險評鑑與風險處理", r"風險|威脅與脆弱|脆弱性|衝擊分析|殘餘|迴避|轉嫁|移轉|降低風險|SLE|ALE|ARO"),
        ("m31", "4.1 存取控制與身分認證", r"縱深防禦|控制措施|控制的類型|嚇阻性|矯正性|AAA|僅知|職務輪調|N/M|存取控制|存取權|權限|特權|帳號|身分認證|身分驗證|身份|鑑別|Authentication|Authorization|授權|多因子|雙因|MFA|密碼原則|密碼長度|密碼設定|最小權限|職務區隔|MAC|DAC|RBAC|單一登入|SSO|生物辨識|Kerberos"),
        ("m32", "4.2 加解密與金鑰生命週期", r"編碼|密碼學|Cryptography|加密|解密|金鑰|公鑰|私鑰|雜湊|Hash|數位簽章|數位信封|憑證|PKI|CA|對稱|非對稱|RSA|AES|DES"),
        ("m41", "5.1 事件與事故管理", r"日誌|Log|紀錄檔|OSINT|數位證據|事件|事故|通報|應變|鑑識|證據|勒索|入侵|CERT|SOC|SIEM|社交工程|攻擊"),
        ("m42", "5.2 備援與營運持續", r"MTPD|BIA|營運衝擊|Disrupt|可承受|最長中斷|備份|備援|異地|營運持續|BCP|DRP|災難|復原|RTO|RPO|MTD|熱備|冷備|暖備|不斷電|UPS|中斷"),
    ],
    "I12": [
        ("t11", "2.1 網路安全", r"OSI|TCP|UDP|IP 位址|IPv|ICMP|ARP|DNS|DHCP|SMTP|FTP|Telnet|SNMP|通訊協定|傳輸層|網路層|應用層|表達層|會議層|資料鏈結|實體層|三向交握|封包|路由|交換器|廣播|VLAN|NAT|埠|Port|防火牆|Firewall|IDS|IPS|入侵偵測|入侵防禦|DMZ|代理伺服器|Proxy|蜜罐|Honeypot|WAF|網路分段|網路架構|UTM|DoS|DDoS|阻斷|SYN Flood|Smurf|Spoofing|欺騙|中間人|嗅探|Sniff|劫持|nslookup|Nmap|RADIUS"),
        ("t12", "2.2 通訊安全", r"SSL|TLS|HTTPS|SSH|SFTP|IPsec|VPN|PGP|S/MIME|電子郵件|郵件|無線|Wi-?Fi|WPA|WEP|藍牙|行動通訊|[2345]G|加密傳送|安全協定|加密|金鑰|雜湊|Hash|簽章|憑證|PKI|對稱|非對稱|RSA|AES|DES"),
        ("t21", "3.1 作業系統安全", r"作業系統|核心|Kernel|Ring|ASLR|DEP|記憶體|主機|伺服器|修補|更新|Patch|Linux|Windows|Unix|指令|bash|chmod|root|管理員權限|服務|登錄檔|Registry|虛擬化|虛擬機|沙箱|Sandbox|帳號|密碼|身分|認證|權限|存取控制|雙因|多因"),
        ("t22", "3.2 作業系統與應用程式（含資料庫與網頁）攻擊手法", r"SQL|Injection|注入|隱碼|XSS|跨站|跨網站|CSRF|緩衝區|Buffer|溢位|Cookie|Session|<script|alert\(|資料庫|網頁攻擊|網站攻擊|目錄遍歷|檔案包含"),
        ("t23", "3.3 程式與開發安全", r"開發|SDLC|SSDLC|測試|白箱|黑箱|原始碼|源碼|程式碼|OWASP|程式語言|PHP|JSP|ASP|JavaScript|逆向|程式碼簽署|Code Signing|API|安全程式"),
        ("t31", "4.1 惡意程式防護與弱點管理", r"病毒|蠕蟲|Worm|木馬|Trojan|後門|勒索|Ransom|WannaCry|殭屍|Botnet|Rootkit|間諜|Spyware|惡意|Malware|防毒|APT|零時差|Zero-?day|社交工程|釣魚|Phishing|駭客|弱點|漏洞|CVE|CVSS|弱點掃描|滲透|行動碼"),
        ("t32", "4.2 資料安全及備份管理", r"備份|復原|回復|RPO|RTO|RAID|資料外洩|DLP|去識別|個人資料|個資|資料保護|資料安全|儲存媒體|抹除|銷毀"),
        ("t33", "4.3 日誌管理", r"日誌|Log|記錄檔|稽核軌跡|Syslog|SIEM|安全性資訊與事件管理|時脈|同步|NTP|事件紀錄"),
        ("t41", "5.1 雲端安全概論", r"雲端|雲服務|雲|Cloud|IaaS|PaaS|SaaS|容器|Container|Docker|Kubernetes"),
        ("t42", "5.2 行動裝置安全概論", r"行動裝置|手機|Android|iOS|App|BYOD|MDM|行動"),
        ("t43", "5.3 物聯網安全概論", r"物聯網|IoT|智慧|工控|SCADA|OT|區塊鏈|AI|人工智慧|邊緣|節點"),
    ],
    # 中級（題目少，章節粗分）
    "I21": [
        ("r1", "資安治理、法規與標準：ISO 27001:2022、資通安全管理法、個資", r"治理|ISO|27001|27002|2700\d|ISMS|資通安全管理法|資安法|個資|個人資料|GDPR|法規|合規|遵循|稽核|SoA|適用性聲明|管理審查|KPI|指標|政策"),
        ("r2", "風險評鑑與管理", r"風險|威脅|弱點|衝擊|評鑑|處置|殘餘"),
        ("r3", "雲端、供應鏈與委外安全", r"雲|SaaS|PaaS|IaaS|供應鏈|供應商|委外|第三方|SBOM|SLA|合約|責任分擔"),
        ("r4", "資安架構：零信任、身分與存取管理", r"零信任|ZTA|身分|身份|存取|權限|MFA|多因子|IAM|PAM|特權|架構|網段|分段"),
        ("r5", "營運持續與事件應變規劃", r"營運持續|BCP|DRP|備份|備援|復原|RTO|RPO|事件|應變|通報|演練|勒索"),
        ("r6", "AI 與新興科技風險", r"AI|人工智慧|生成式|LLM|模型|提示詞|Prompt|機器學習|深偽|量子|區塊鏈|物聯網|IoT|OT"),
    ],
    "I22": [
        ("d1", "網路與端點防護", r"防火牆|WAF|IDS|IPS|EDR|XDR|端點|網路|封包|VPN|DNS|TLS|SSL|HTTP|埠|DDoS|阻斷"),
        ("d2", "攻擊手法與威脅分析", r"攻擊|ATT&CK|MITRE|APT|惡意|木馬|勒索|釣魚|社交工程|橫向移動|提權|持久化|C2|中間人|噴灑|暴力|漏洞利用|RCE|零時差"),
        ("d3", "應用程式、雲端與容器安全", r"SQL|XSS|CSRF|SSRF|注入|Injection|OWASP|Web|API|程式碼|原始碼|容器|Container|Kubernetes|Docker|映像檔|雲|CI/CD|DevSecOps|供應鏈"),
        ("d4", "事件應變、鑑識與日誌監控", r"事件|應變|鑑識|證據|日誌|Log|SIEM|SOC|監控|偵測|告警|IoC|威脅獵捕|復原|隔離"),
        ("d5", "密碼學與身分驗證", r"加密|解密|金鑰|雜湊|Hash|簽章|憑證|PKI|密碼學|身分|身份|驗證|認證|MFA|OAuth|SAML|JWT|Token|Kerberos"),
        ("d6", "AI／LLM 與新興威脅", r"AI|人工智慧|生成式|LLM|模型|提示詞|Prompt|深偽|量子|物聯網|IoT|OT|工控"),
    ],
}
# 章節名稱裡不分大小寫的英文縮寫才比對，避免「CA」這種短字亂中：短的英文縮寫要前後不是英文字母
def compile_rx(rx):
    parts = []
    for w in rx.split("|"):
        if re.fullmatch(r"[A-Za-z]{2,4}", w):
            parts.append(r"(?<![A-Za-z])" + w + r"(?![A-Za-z])")
        else:
            parts.append(w)
    return re.compile("|".join(parts), re.I)


RX = {s: [(c, n, compile_rx(r)) for c, n, r in v] for s, v in CH.items()}


def score(s, q):
    text_q = q["q"]
    text_o = " ".join(q["o"])
    best, bs = None, 0
    for c, _, rx in RX[s]:
        v = 2 * len(rx.findall(text_q)) + len(rx.findall(text_o))
        if v > bs:
            best, bs = c, v
    return best


# 初級改以書為主：關鍵字先判斷大概的節（上面的 CH），再配到書裡最相關的小節（tools/ipas_books.py）；
# 配不到小節的，平均分給同一節的各小節。每題記 c＝書的節（例如 2.1）、u＝小節（例如 2.1.3）。
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ipas_books  # noqa: E402

HINT = {"I11": {"m11": "2.1", "m12": "2.2", "m13": "2.3", "m24": "2.4", "m21": "3.1", "m22": "3.2", "m31": "4.1", "m32": "4.2", "m41": "5.1", "m42": "5.2"},
        "I12": {"t11": "2.1", "t12": "2.2", "t21": "3.1", "t22": "3.2", "t23": "3.3", "t31": "4.1", "t32": "4.1", "t33": "4.2", "t41": "5.1", "t42": "5.2", "t43": "5.3"}}

D = json.load(open(PATH, encoding="utf-8"))
D["ch"] = {s: [[c, n] for c, n, _ in v] for s, v in CH.items()}
for s, b in ipas_books.BOOKS.items():
    D["ch"][s] = [[sec, sec + " " + name] for sec, name, _ in b["sections"]]
cnt = {s: Counter() for s in CH}
guess = 0
load = Counter()
book_units = {s: ipas_books.units(s) for s in ipas_books.BOOKS}
for p in D["papers"]:
    prev = None
    for q in p["qs"]:
        c = score(p["s"], q)
        if not c:
            c = prev or RX[p["s"]][0][0]
            guess += 1
        prev = c
        if p["s"] in ipas_books.BOOKS:
            hint = HINT[p["s"]][c]
            u, v = ipas_books.match(p["s"], q, hint)
            if not u or v < 2:   # 只有選項裡零星提到的不算，分給同一節題目最少的小節
                us = [x["u"] for x in book_units[p["s"]] if x["sec"] == hint]
                u = min(us, key=lambda x: (load[(p["s"], x)], us.index(x)))
            load[(p["s"], u)] += 1
            q["u"] = u
            c = u.rsplit(".", 1)[0]
        q["c"] = c
        cnt[p["s"]][c] += 1
json.dump(D, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
for s in CH:
    print(s, ", ".join("%s %d" % (c, cnt[s][c]) for c, _ in D["ch"][s]))
print("沿用前一題章節：%d 題" % guess)
