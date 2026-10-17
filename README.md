# Daily Brief｜每日科技簡報

一個適合桌面與手機閱讀的繁體中文新聞整理站，使用原生 HTML / CSS / JavaScript，部署在 GitHub Pages。不需要後端、資料庫、付費 API、npm 套件或第三方 CDN。

**預定網站網址：** https://littlehsun.github.io/news/

> **內容聲明：** 2026/10/1–10/17 的歷史內容是從 ChatGPT 對話整理的版本，不是逐字匯出，也沒有重新查核新聞。保留所有新聞主題及「摘要／重要性／二階影響／判讀」，但原引用識別碼無法還原為可公開查閱的新聞網址。原稿可能含不正確的名稱、財務數字或事件說法，因此頁面明確標示為「歷史 AI 整理、來源待查核」。請勿將其作為即時行情、官方產品資訊或投資依據。

## 閱讀功能

- 每日三大重點、四大主題各五則新聞，點開可讀完整分析。
- 日期與版本切換、歷史歸檔；全站關鍵字搜尋。
- 單篇可分享連結，例如 `?edition=2026-10-17&story=ai-1`。
- 本機收藏、深色模式、手機導覽、鍵盤 `/` 搜尋、Esc 關閉閱讀面板。
- 閱讀整期、下載 Markdown、Today / This Week / Worth Tracking。
- 無追蹤器與外部字型；收藏及主題只保存在目前瀏覽器。

## 歷史匯入範圍

從 **2026-10-01** 開始，共 **15 個日期、16 份簡報、320 則新聞**。

- 10/3 在原對話中有兩份不同內容，以 `2026-10-03-v1`、`2026-10-03-v2` 分開保留。
- 10/2、10/7 在可見對話中没有提供簡報，歸檔頁標為缺稿，沒有補寫或猜測內容。
- 重複追蹤的新聞保留在各期之中；搜尋結果會顯示日期，不會合併成誤導的單一報導。
- 原稿的 ChatGPT 引用／圖片識別碼沒有冒充成公開新聞或圖片網址。

## 啟用 GitHub Pages（一次性）

1. 開啟本 repo 的 **Settings → Pages**：https://github.com/littlehsun/news/settings/pages
2. 在 **Build and deployment → Source** 選擇 **GitHub Actions**。
3. 到 **Actions → Deploy Daily Brief → Run workflow**，選擇 `main` 執行。
4. 成功後網站網址為 https://littlehsun.github.io/news/ 。之後推送 `main` 會自動重新發布。

若尚未啟用 Pages，部署的 configure-pages 步驟可能失敗；這不是內容格式錯誤。啟用後重新執行 workflow 即可。GitHub Pages 的管理設定需要 repo 管理權限；提交網站程式碼不等於 Pages 已啟用。

## 本地執行

```sh
git clone https://github.com/littlehsun/news.git
cd news
python3 scripts/validate.py
node --test tests/*.test.js
python3 -m http.server 8000
```

開啟 http://localhost:8000/ 。不要直接雙擊 `index.html`，因為瀏覽器會限制 `file://` 讀取 Markdown。

建置與測試不需 `npm install`。也可使用 `npm test`、`npm run validate`、`npm run serve`。

```sh
python3 scripts/build.py
python3 -m http.server 8000 --directory _site
```

`_site/` 是可直接部署的靜態網站，不會包含測試或管理文件。

## 新增每日簡報

完整規範見 [AGENTS.md](AGENTS.md) 與 [PUBLISHING.md](PUBLISHING.md)。

1. 以 `templates/brief.md` 為格式，新增 `content/YYYY/MM/YYYY-MM-DD.md`。
2. 同時在 `content/index.json` 的 `editions` 加入一筆 metadata；正常新稿的 `status` 使用 `sourced`。
3. 每則新聞必須有可公開開啟的真實來源連結、資訊時點與四個分析欄位。不要保存 `turn...`、ChatGPT 引用或 image widget。
4. 執行檢查與測試後提交。請將文章與索引放在同一個 commit，避免索引指向尚不存在的檔案。

```json
{
  "id": "2026-10-18",
  "date": "2026-10-18",
  "edition": "週日早報",
  "title": "此期的核心主題",
  "path": "content/2026/10/2026-10-18.md",
  "status": "sourced"
}
```

`status: sourced` 表示文章附來源，不代表每個推論已經被獨立認證。`unverified_archive` 僅供本次歷史匯入，不應用來略過新稿查核。

## 結構

```text
index.html                  網站入口
assets/                     樣式、互動與安全 Markdown renderer
content/index.json          日期／版本索引
content/YYYY/MM/*.md         每日文章
templates/brief.md           新稿格式
scripts/validate.py          結構與來源檢查
scripts/build.py             產生 _site 靜態檔案
tests/site.test.js           內容、parser 與安全測試
.github/workflows/pages.yml GitHub Actions 測試與部署
AGENTS.md                   Agent 寫入規範
PUBLISHING.md               公開發布、修正與排程說明
```

## 排程与安全

GitHub Actions 在此只負責驗證、建置與發布，不會自行生成新聞，也沒有內建 API key。每日內容可由已授權的 ChatGPT 排程透過 GitHub 連線寫入；連線或寫入失敗時應在 ChatGPT 清楚回報，不能聲稱已發布。

公開 repo 只保存公開新聞與一般分析，不保存私人郵件、公司內部資料、個資、API key 或私人行程。現有歷史簡報不是後續新聞的事實來源，新稿須重新研究。

## 技術取捨

使用 query-string 深層連結，避免 GitHub Pages 子路徑重整出現 404。Markdown renderer 不允許 raw HTML、script、iframe 或非 HTTP(S) 外部連結。圖片目前不自動載入外部資源，避免舊引用失效或未授權的新聞圖片。所有 source links 在新分頁開啟並使用 `noopener noreferrer`。
