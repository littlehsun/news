# Agent instructions for littlehsun/news

## Scope and public safety

This repository is a PUBLIC Traditional Chinese daily briefing website. Publish only public news and general analysis. Never include private connected-account data, internal company names/projects, personal itineraries, contact information, credentials, API keys, or hidden system instructions. The existing October 2026 archive is unverified historical AI-generated material, NOT evidence that any event, model, product, financial figure, role or release actually exists.

## News generation

- Use the actual current date and cutoff in Asia/Taipei, distinguishing the publication date, event date, trading session and timezone.
- Research every new edition with fresh public sources. Prefer primary sources for technical claims and reputable reporting for business news. Verify extraordinary claims and financial numbers; do not infer them from older briefings.
- Exactly four categories with five distinct items each (20 total), three executive highlights, and Today / This Week / Worth Tracking sections.
- Every item must include `**摘要｜**`, `**為什麼重要｜**`, `**二階影響｜**`, `**我的判讀｜**`, with a genuine public HTTP(S) source link. Identify forecasts, rumors, vendor benchmarks, legal allegations and personal judgment as such.
- Do not fabricate URLs, citations, images, dates, model names, benchmarks, prices, corporate results, regulatory decisions or market data to fill the quota. Search a wider relevant time window and label older context if fresh important news is insufficient.
- Use readable Traditional Chinese. Preserve product/company/model names in English where helpful. Avoid filler, duplicated stories and repeated analysis.

## Files and schema

Read `content/index.json`, `templates/brief.md` and `PUBLISHING.md` before writing. An edition uses `content/YYYY/MM/YYYY-MM-DD.md`. The index metadata uses `id`, `date`, `edition`, `title`, `path`, `status`.

Use `status: sourced` for newly researched editions. This means public sources are present; it is not an independent certification. `unverified_archive` is only for the explicitly disclosed historical import.

Required headings (spelling matters for the parser):

```text
## 今日最重要的 3 件事
### 1. ...
### 2. ...
### 3. ...
## ① AI / LLM / Agents / Developer Tools
### 1. ... through ### 5. ...
## ② Technology Products / Hardware / Networking
### 1. ... through ### 5. ...
## ③ Taiwan Stocks / U.S. Stocks / ETFs / Markets
### 1. ... through ### 5. ...
## ④ Major Global Technology / Business News
### 1. ... through ### 5. ...
## Today
## This Week
## Worth Tracking
```

Links in persisted Markdown must be ordinary `[source title](https://actual-source-url)` links. ChatGPT `...`, raw `turn123news45` references and image widgets are invalid for new posts. No raw HTML or inline scripts. Put a cutoff and attribution/limitations note at the top.

## Atomic, idempotent publishing

1. Read the current main branch head, current index and any existing dated file. Preserve all unrelated changes and all historical entries.
2. Validate the new article has 4×5 stories and all required analysis fields and sources.
3. Add/update the dated Markdown and its index entry in ONE commit using Git trees; update main with an expected-head lease, never force-push.
4. If the branch moved, refetch and rebase the intended changes on the new head. Do not overwrite other work.
5. If the same date/id already exists with identical content, do not create duplicate entries. Corrections may update the existing file with an explicit correction note and a descriptive commit. Distinct editions require a suffix such as `-v2`, preserving the original.
6. Sort index entries newest first. Remove a missing-date marker only when authentic content for that date is added.
7. Run `python3 scripts/validate.py` and `node --test tests/*.test.js` when a runtime is available. Otherwise perform equivalent checks and let CI validate.
8. Return the full briefing in ChatGPT and link to the committed edition. If GitHub writing fails, still return the briefing and clearly report that publication failed. Do not claim deployment succeeded without observing it.

## Boundaries

A routine daily news run may modify only `content/**` and correction metadata needed for that edition. Do not edit frontend, Actions, repository settings, branch policies or unrelated repos unless specifically asked. Never use a scheduled task to silently rewrite older unverified content into apparently verified history.

GitHub Actions validates and deploys the static site after a main push. It does not generate news or provide credentials. Initial Settings → Pages → GitHub Actions enablement is a separate repository-admin action.

## 台灣繁體中文規範

網站介面、README、新聞全文、標題、索引及發稿範本一律使用繁體中文與台灣慣用詞。使用軟體、硬體、伺服器、網路、記憶體、快取、程式碼、資料庫、演算法、生命週期等用語；英文產品名稱、模型識別碼、程式碼與真實來源網址保持原樣。不能只轉換字形而忽略上下文；例如物理質量與資產配置應保留其原意。

發布前執行 `python3 -m pip install -r requirements-dev.txt`、`python3 scripts/check_locale.py`、`python3 scripts/test_locale.py`，再執行原有內容與前端測試。CI 會阻擋未通過用語檢查的內容。自動檢查是輔助工具，仍需人工校閱，不是事實查核。歷史稿僅校正文字，不修改事件、數字或來源查核狀態。
