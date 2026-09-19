# mengyahh.com — 萌芽中。

個人主站（靜態網站，部署在 GitHub Pages）。目前包含：

- `/` 首頁
- `/cooking/` 料理紀錄（由舊 Google Site 搬過來）
- `/blog/` 部落格（由 Vocus 與舊 Strikingly 部落格搬過來；每篇在 `/blog/YYYY-MM-DD/`）；列表頁右側欄有搜尋、系列、年份篩選
- `/about/` 暫時導向舊 Google Site 的「關於」頁（等關於頁搬過來後換成真正的頁面）

「關於」「作品集」目前仍連到 `sites.google.com/view/mengyahh/…`。

## 結構

```
data/cooking.json        料理紀錄的內容來源（每則：日期、標題、文字、照片）
data/blog.json           部落格文章（標題、日期、系列、內文 HTML）
assets/blog/<日期>/      文章圖片（WebP，已去除 EXIF）
assets/data/blog-search.json  站內搜尋用的索引（產生檔）
assets/cooking/          照片（xxx.webp 大圖 1280px、xxx-t.webp 縮圖 640px，已去除 EXIF）
assets/css, assets/js    樣式、輪播與燈箱
scripts/build.py         由 data/*.json 產生 index.html、cooking/、blog/、about/、sitemap.xml、robots.txt
```

`index.html`、`cooking/`、`blog/`、`about/`、`sitemap.xml` 是**產生出來的檔案**，不要直接改，改 `scripts/build.py` 或 `data/*.json` 後重跑。

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
