# mengyahh.com — 萌芽中。

個人主站（靜態網站，部署在 GitHub Pages）。目前包含：

- `/` 首頁
- `/cooking/` 料理紀錄（由舊 Google Site 搬過來）
- `/blog/` 部落格（由 Vocus 與舊 Strikingly 部落格搬過來；每篇在 `/blog/YYYY-MM-DD/`）；列表頁右側欄有搜尋、系列、年份篩選
- `/about/` 關於、`/portfolio/` 作品集（由舊 Google Site 搬過來，米色底深色字；橫幅用 `assets/img/banner.webp`）

全站固定是淺色主題（米色底、深色字），不會跟著系統切換成深色。

## 結構

```
content/blog/            所有部落格文章（一篇一個 Markdown 檔，含從 Vocus、Strikingly、Instagram 搬來的）
content/cooking/         新的料理紀錄（一則一個 Markdown 檔）；寫法見 content/README.md
data/cooking.json        舊的料理紀錄（Google Site 搬來的：日期、標題、文字、照片）
data/about.json          關於頁內容（分區、標籤、個人資料）
data/portfolio.json      作品集內容（分組、項目、圖片；影片只存 YouTube 代碼，頁面以本機封面圖顯示，按播放才載入）
data/blog.json           （已清空）部落格文章全部改放在 content/blog/，一篇一個 Markdown 檔
assets/blog/<日期>/      文章圖片（WebP，已去除 EXIF）
assets/data/blog-search.json  站內搜尋用的索引（產生檔）
assets/cooking/          照片（xxx.webp 大圖 1280px、xxx-t.webp 縮圖 640px，已去除 EXIF）
assets/css, assets/js    樣式、輪播與燈箱
scripts/mdcontent.py     讀 content/ 的 Markdown
scripts/photo.py         縮圖、轉 WebP、去 EXIF，並印出要貼進 .md 的照片行
scripts/preview.py       本機預覽（存檔自動重建）；preview.bat 是雙擊版
publish.py               建置、commit、push 到線上；publish.bat 是雙擊版
scripts/build.py         由 data/*.json 與 content/**/*.md 產生 index.html、about/、portfolio/、cooking/、blog/、sitemap.xml、robots.txt
```

`index.html`、`about/`、`portfolio/`、`cooking/`、`blog/`、`sitemap.xml` 是**產生出來的檔案**，不要直接改，改 `scripts/build.py` 或 `data/*.json` 後重跑。

## 新增文章／料理紀錄（Markdown）

在 `content/blog/` 或 `content/cooking/` 新增 `.md` 檔（複製 `content/_範本.md`），格式與加照片的方法見 [content/README.md](content/README.md)。
存檔 → 雙擊 `preview.bat` 預覽 → 雙擊 `publish.bat` 上線。

只需要 Python 3 就能建置與預覽；`scripts/photo.py` 另外需要 Pillow（`pip install pillow`）。

舊內容（`data/*.json`）仍可照舊直接編輯：料理紀錄在 `entries` 最前面加一筆、照片放 `assets/cooking/`；部落格文章加在 `articles`（欄位：`slug`、`title`、`date`、`categories`、`abstract`、`html`，可選 `tags`、`cover`），內文裡用 `@ASSET/blog/<slug>/01.webp` 引用圖片、`@BLOG/<slug>/` 連到站內文章。

## 瀏覽次數（GoatCounter）

文章頁可顯示「瀏覽 N 次」，由 [GoatCounter](https://www.goatcounter.com)（免費、不用 cookie）計數。啟用方式：

1. 到 goatcounter.com 註冊，取得站點代碼（`xxx.goatcounter.com` 的 `xxx`）
2. GoatCounter → Settings → 勾選 **Allow adding visitor counts on your website**
3. 把 `scripts/build.py` 裡的 `GOATCOUNTER = os.environ.get('GOATCOUNTER', '')` 的預設值改成你的代碼，重新執行 `python scripts/build.py`

目前站點代碼是 `mengyahh`。想暫時關掉追蹤（例如本機測試）：`GOATCOUNTER= python scripts/build.py`（代碼留空時網站完全不載入任何追蹤程式）。

## 留言功能
部落格文章底下的留言區由 `worker/`（Cloudflare Worker + D1）提供，部署步驟見 [worker/README.md](worker/README.md)。`scripts/build.py` 的 `COMMENTS_API` 與 `TURNSTILE_SITEKEY` 兩個都設定時才會出現留言區；沒設定時網站完全不載入任何留言相關程式。

## 分類與側欄
部落格分類設定在 `scripts/build.py` 最上面的 `CATEGORY_GROUPS`：側欄分「類型」「主題」兩群，各群裡的順序就是這裡的順序。沒有文章的分類自動隱藏；新分類只要寫進文章的 `categories`，沒列在設定裡的會自動出現在最後一群。側欄順序：搜尋 → 類型 → 主題 → 近期文章 → 近期留言（留言功能啟用後才會出現）。

## 部落格列表的載入方式
列表頁一開始顯示 10 篇，捲到底自動再顯示 10 篇（也可按「顯示更多文章」）。全部文章仍在頁面裡，所以搜尋、分類、年份篩選一律涵蓋所有文章；換篩選條件會從第一批重新開始。每批篇數在 `assets/js/blog-filter.js` 的 `PAGE`。
