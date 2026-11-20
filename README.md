# 鍾雅婷每日任務

把工作和學習放在同一個地方的每日任務平台。

**網址：https://donna12301230.github.io/daily-tasks/**

## 裡面有什麼

| 區域 | 模組 | 說明 |
| --- | --- | --- |
| 今天 | — | 逾期、今天、進行中、接下來 7 天；考試倒數；工作台今天的事項；每週讀書時段；單字今日複習和考古題進度 |
| 工作 | 專案計畫 | 專案時程圖、目標、範圍與交付物、里程碑、風險 |
| | 專案管理 | 看板（待辦／進行中／等待中／完成） |
| | 工作台 | 月曆、甘特圖、IG 發文、讀書進度、清單（原本的赫滋與羊工作台） |
| 學習 | 規劃 | 學習目標拆成步驟、每週固定時段 |
| | 筆記 | 自己的筆記，可搜尋、分課程 |
| | 作業系統 | 空大作業系統白話筆記（原本的 os-notes） |
| | 生成式 AI | 一講一頁的課程講義（原本的 genai-lecture-notes） |
| | 考試 | 考試倒數、準備清單、成績 |
| | 考古題 | 中山資管考古題練習（原本的 nsysu-mis-exams） |
| | 單字 | 單字練習：閃卡、不熟清單、今日複習、考試（原本的 vocab-trainer） |
| 擴充 | — | 新增區域與模組、匯入、備份 |

## 資料存在哪裡

- 用 Google 登入後，任務、專案、工作台、考古題作答紀錄存在 Firebase（專案 `vocab-trainer-7716`）的 `users/{你的 uid}/apps/...`，只有你自己讀得到（規則見單字練習 repo 的 `firestore.rules`）。
- 單字練習沿用它原本的雲端同步（同一個 Google 帳號）。
- 這個 repo 只有程式碼，沒有任何個人資料。

## 更新內建網站

作業系統筆記、生成式 AI 講義、考古題、單字練習的程式碼是從原本的 repo 複製進 `apps/` 的。原本的網站更新後：

```
python tools/build.py
git add -A && git commit -m "同步內建網站" && git push
```

工作台（`apps/workbench/`）直接在這個 repo 裡維護。

## 擴充新的模組類型

在 `index.html` 的 `TYPES` 加一個類型（`label`、`desc`、`view(mod)`），或像內建網站一樣指定 `src` 放一個獨立頁面。

## 本機測試

```
python tools/make_test.py     # 產生 _test.html（假的資料庫，不連 Firebase）
python -m http.server 8000    # 打開 http://localhost:8000/_test.html
```
