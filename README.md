# mengyahh.com — 萌芽中。

個人主站（靜態網站，部署在 GitHub Pages）。目前包含：

- `/` 首頁
- `/cooking/` 料理紀錄（由舊 Google Site 搬過來，38 則、94 張照片）
- `/about/` 暫時導向舊 Google Site 的「關於」頁（等關於頁搬過來後換成真正的頁面）

「關於」「作品集」目前仍連到 `sites.google.com/view/mengyahh/…`。

## 結構

```
data/cooking.json        料理紀錄的內容來源（每則：日期、標題、文字、照片）
assets/cooking/          照片（xxx.webp 大圖 1280px、xxx-t.webp 縮圖 640px，已去除 EXIF）
assets/css, assets/js    樣式、輪播與燈箱
scripts/build.py         由 data/cooking.json 產生 index.html、cooking/index.html、about/index.html
```

`index.html`、`cooking/index.html`、`about/index.html` 是**產生出來的檔案**，不要直接改，改 `scripts/build.py` 或 `data/cooking.json` 後重跑。

## 新增一則料理紀錄

1. 照片放進 `assets/cooking/`，命名 `YYYYMM-N-序號.webp`（大圖）與 `YYYYMM-N-序號-t.webp`（縮圖）
2. 在 `data/cooking.json` 的 `entries` **最前面**加一筆（格式照現有的）
3. 執行 `python scripts/build.py`
4. 本機預覽：`python -m http.server 8000` → http://localhost:8000
5. `git add -A && git commit && git push`

只需要 Python 3，沒有任何套件相依。
