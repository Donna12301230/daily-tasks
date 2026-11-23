# -*- coding: utf-8 -*-
"""iPAS 資安初級考古題：替每一題標章節（寫進 apps/ipas/data.json 每題的 c，章節清單放在 data.json 的 ch）。
章節照 iPAS 資訊安全工程師初級的評鑑範圍整理；用關鍵字判斷，題目、選項都看，題目的分數加倍。
判斷不出來的題目沿用同一份卷子前一題的章節（原卷大致照主題排）。
用法：python tools/ipas_chapters.py   （之後再跑 python tools/exam_plan.py 更新每日進度）"""
import json
import os
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATH = os.path.join(ROOT, "apps/ipas/data.json")

CH = {
    "I11": [
        ("m1", "資安基本概念：CIA、威脅與控制類型", r"機密性|完整性|可用性|不可否認|CIA|資訊安全特性|控制的類型|嚇阻性|矯正性|預防性控制|偵測性控制|縱深防禦|社交工程|垃圾搜尋|攻擊手法|網路攻擊"),
        ("m2", "資訊安全管理系統與標準：ISMS、ISO 27001/27002、PDCA", r"ISMS|資訊安全管理系統|27001|27002|2700\d|PDCA|戴明|Deming|適用性聲明|SoA|管理審查|資訊安全政策|資安政策|管理階層|高階管理|國際標準|ISO/IEC|資安長|資通安全責任等級"),
        ("m3", "資產管理：盤點、分級、擁有者", r"資產|盤點|分級|擁有者|標示|媒體處理|媒體銷毀|保管"),
        ("m4", "風險管理：評鑑、處置", r"風險|威脅與脆弱|脆弱性|弱點評估|衝擊分析|殘餘|迴避|轉嫁|移轉|降低風險|接受"),
        ("m5", "存取控制與身分認證：帳號、特權、密碼", r"存取控制|存取權|權限|特權|帳號|身分認證|身分驗證|鑑別|Authentication|Authorization|授權|多因子|雙因|MFA|密碼原則|密碼長度|密碼設定|最小權限|職務區隔|MAC|DAC|RBAC|單一登入|SSO|生物辨識"),
        ("m6", "密碼學應用：加密、雜湊、數位簽章、PKI", r"密碼學|Cryptography|Kerberos|加密|解密|金鑰|公鑰|私鑰|雜湊|Hash|數位簽章|數位信封|憑證|PKI|CA|對稱|非對稱|RSA|AES|DES"),
        ("m7", "資安事件管理與通報應變", r"事件|通報|應變|鑑識|證據|勒索|入侵|資安事故|CERT|SOC|SIEM"),
        ("m8", "營運持續與備份備援：BCP、DRP、RTO/RPO", r"備份|備援|異地|營運持續|BCP|DRP|災難|復原|RTO|RPO|MTD|熱備|冷備|暖備|不斷電|UPS|中斷"),
        ("m9", "法規、個資與資訊倫理", r"個人資料|個資|隱私|著作權|智慧財產|專利|商標|營業秘密|法規|法律|資通安全管理法|資安法|GDPR|OECD|倫理|PAPA|刑法|電子簽章法|去識別"),
        ("m10", "稽核與驗證", r"稽核|驗證|第一方|第二方|第三方|查核|矯正措施|不符合|審查證據"),
        ("m11", "人員、實體環境與委外／供應鏈安全", r"人員|員工|離職|教育訓練|訓練|保密協議|實體|機房|門禁|環境|委外|供應商|供應鏈|外包|雲端服務|服務水準|SLA|桌面淨空|螢幕淨空|行動裝置|BYOD|遠距"),
    ],
    "I12": [
        ("t1", "網路基礎與通訊協定：OSI、TCP/IP、無線", r"OSI|TCP|UDP|IP 位址|IPv|ICMP|ARP|DNS|DHCP|HTTP(?!S)|SMTP|FTP|Telnet|SNMP|通訊協定|傳輸層|網路層|應用層|表達層|會議層|資料鏈結|實體層|三向交握|封包|路由|交換器|廣播|VLAN|NAT|埠|Port|無線|Wi-?Fi|WPA|WEP|藍牙|行動通訊|[2345]G"),
        ("t2", "網路安全防護：防火牆、IDS/IPS、VPN、DMZ", r"防火牆|Firewall|IDS|IPS|入侵偵測|入侵防禦|VPN|DMZ|代理伺服器|Proxy|蜜罐|Honeypot|WAF|網路分段|網路架構|UTM|安全閘道"),
        ("t3", "密碼學與安全傳輸：加密、雜湊、簽章、SSL/TLS", r"密碼學|Cryptography|安全協定|加密傳送|SFTP|加密|解密|金鑰|公鑰|私鑰|雜湊|Hash|MD5|SHA|數位簽章|憑證|PKI|對稱|非對稱|RSA|AES|DES|ECC|Diffie|SSL|TLS|HTTPS|SSH|IPsec|PGP|S/MIME|隱寫|Steganography"),
        ("t4", "作業系統與主機安全：帳號、權限、修補、強化", r"作業系統|核心|Kernel|Ring|ASLR|DEP|緩衝區|Buffer|記憶體|主機|伺服器|修補|更新|Patch|Linux|Windows|Unix|指令|bash|chmod|root|管理員權限|服務|登錄檔|Registry|虛擬化|虛擬機|容器|沙箱|Sandbox|帳號|密碼|身分|認證|權限|存取控制"),
        ("t5", "惡意程式與攻擊手法：病毒、勒索、DDoS、社交工程", r"病毒|蠕蟲|Worm|木馬|Trojan|後門|勒索|Ransom|WannaCry|殭屍|Botnet|Rootkit|間諜|Spyware|惡意|Malware|DoS|DDoS|阻斷|SYN Flood|Smurf|社交工程|釣魚|Phishing|APT|零時差|Zero-?day|駭客|攻擊|欺騙|Spoofing|中間人|側錄|嗅探|Sniff|暴力破解|字典攻擊|nslookup|掃描|Nmap"),
        ("t6", "應用程式與 Web 安全：注入、XSS、OWASP、安全開發", r"SQL|Injection|注入|隱碼|XSS|跨站|跨網站|CSRF|OWASP|網頁|網站|Web|Cookie|Session|PHP|JSP|ASP|JavaScript|<script|程式碼|原始碼|源碼|開發|SDLC|SSDLC|測試|白箱|黑箱|弱點|漏洞|CVE|CVSS|滲透|逆向|程式語言|API|資料庫|應用程式|應用系統|程式碼簽署"),
        ("t7", "資料保護、備份與日誌：備份、日誌、稽核軌跡", r"SIEM|安全性資訊與事件管理|備份|復原|回復|RPO|RTO|日誌|Log|記錄檔|稽核軌跡|Syslog|時脈|同步|NTP|資料外洩|DLP|去識別|個人資料|個資|資料保護|資料安全|儲存媒體|RAID|抹除|銷毀"),
        ("t8", "雲端、行動裝置與物聯網安全", r"雲端|雲服務|雲|Cloud|IaaS|PaaS|SaaS|行動裝置|手機|Android|iOS|App|BYOD|MDM|物聯網|IoT|智慧|工控|SCADA|OT|區塊鏈|AI|人工智慧|5G|邊緣"),
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


D = json.load(open(PATH, encoding="utf-8"))
D["ch"] = {s: [[c, n] for c, n, _ in v] for s, v in CH.items()}
cnt = {s: Counter() for s in CH}
guess = 0
for p in D["papers"]:
    prev = None
    for q in p["qs"]:
        c = score(p["s"], q)
        if not c:
            c = prev or RX[p["s"]][0][0]
            guess += 1
        q["c"] = c
        prev = c
        cnt[p["s"]][c] += 1
json.dump(D, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
for s in CH:
    print(s, ", ".join("%s %d" % (c, cnt[s][c]) for c, _, _ in RX[s]))
print("沿用前一題章節：%d 題" % guess)
