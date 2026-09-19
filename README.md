# mengyahh.com — 萌芽中。

個人主站（靜態網站，部署在 GitHub Pages）。目前包含：

- `/` 首頁
- `/cooking/` 料理紀錄（由舊 Google Site 搬過來）
- `/blog/` 部落格（由 Vocus 與舊 Strikingly 部落格搬過來；每篇在 `/blog/YYYY-MM-DD/`）；列表頁右側欄有搜尋、系列、年份篩選
- `/about/` 關於、`/portfolio/` 作品集（由舊 Google Site 搬過來，米色底深色字；橫幅用 `assets/img/banner.webp`）

全站固定是淺色主題（米色底、深色字），不會跟著系統切換成深色。

## 結構

```
data/cooking.json        料理紀錄的內容來源（每則：日期、標題、文字、照片）
data/about.json          關於頁內容（分區、標籤、個人資料）
data/portfolio.json      作品集內容（分組、項目、圖片；影片只存 YouTube 代碼，頁面以本機封面圖顯示，按播放才載入）
data/blog.json           部落格文章（標題、日期、系列、內文 HTML）
assets/blog/<日期>/      文章圖片（WebP，已去除 EXIF）
assets/data/blog-search.json  站內搜尋用的索引（產生檔）
assets/cooking/          照片（xxx.webp 大圖 1280px、xxx-t.webp 縮圖 640px，已去除 EXIF）
assets/css, assets/js    樣式、輪播與燈箱
scripts/build.py         由 data/*.json 產生 index.html、about/、portfolio/、cooking/、blog/、sitemap.xml、robots.txt
```

`index.html`、`about/`、`portfolio/`、`cooking/`、`blog/`、`sitemap.xml` 是**產生出來的檔案**，不要直接改，改 `scripts/build.py` 或 `data/*.json` 後重跑。

## 新增一則料理紀錄

1. 照片放進 `assets/cooking/`，命名 `YYYYMM-N-序號.webp`（大圖）與 `YYYYMM-N-序號-t.webp`（縮圖）
2. 在 `data/cooking.json` 的 `entries` **最前面**加一筆（格式照現有的）
3. 執行 `python scripts/build.py`
4. 本機預覽：`python -m http.server 8000` → http://localhost:8000
5. `git add -A && git commit && git push`

只需要 Python 3，沒有任何套件相依。

## 瀏覽次數（GoatCounter）

文章頁可顯示「瀏覽 N 次」，由 [GoatCounter](https://www.goatcounter.com)（免費、不用 cookie）計數。啟用方式：

1. 到 goatcounter.com 註冊，取得站點代碼（`xxx.goatcounter.com` 的 `xxx`）
2. GoatCounter → Settings → 勾選 **Allow adding visitor counts on your website**
3. 把 `scripts/build.py` 裡的 `GOATCOUNTER = os.environ.get('GOATCOUNTER', '')` 的預設值改成你的代碼，重新執行 `python scripts/build.py`

目前站點代碼是 `mengyahh`。想暫時關掉追蹤（例如本機測試）：`GOATCOUNTER= python scripts/build.py`（代碼留空時網站完全不載入任何追蹤程式）。

## 新增一篇部落格文章

在 `data/blog.json` 的 `articles` 加一筆（欄位照現有的：`slug`、`title`、`date`、`categories`（例如 `["心得","日常"]`，可多個）、`abstract`、`html`，可選 `tags`、`cover`），圖片放 `assets/blog/<slug>/`，內文裡用 `@ASSET/blog/<slug>/01.webp` 引用，站內連結用 `@BLOG/<slug>/`，再執行 `python scripts/build.py`。

## 留言功能
部落格文章底下的留言區由 `worker/`（Cloudflare Worker + D1）提供，部署步驟見 [worker/README.md](worker/README.md)。`scripts/build.py` 的 `COMMENTS_API` 與 `TURNSTILE_SITEKEY` 兩個都設定時才會出現留言區；沒設定時網站完全不載入任何留言相關程式。

## 分類與側欄
部落格分類設定在 `scripts/build.py` 最上面的 `CATEGORY_GROUPS`：側欄分「類型」「主題」兩群，各群裡的順序就是這裡的順序。沒有文章的分類自動隱藏；新分類只要寫進文章的 `categories`，沒列在設定裡的會自動出現在最後一群。側欄順序：搜尋 → 類型 → 主題 → 近期文章 → 近期留言（留言功能啟用後才會出現）。

## 部落格列表的載入方式
列表頁一開始顯示 10 篇，捲到底自動再顯示 10 篇（也可按「顯示更多文章」）。全部文章仍在頁面裡，所以搜尋、分類、年份篩選一律涵蓋所有文章；換篩選條件會從第一批重新開始。每批篇數在 `assets/js/blog-filter.js` 的 `PAGE`。
