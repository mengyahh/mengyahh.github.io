# 用 Markdown 寫文章

新的部落格文章與料理紀錄寫在這裡，一篇一個 `.md` 檔（純文字，用記事本、VS Code 都能開）。
舊的（從 Google Sites、Vocus、Strikingly 搬來的）內容還在 `data/*.json`，不用動。

```
content/blog/      部落格文章
content/cooking/   料理紀錄
content/_範本.md    複製這份來寫新的（檔名以 _ 開頭的檔案不會被發布，拿來放草稿）
```

## 日常流程

1. 改或新增 `.md` 檔
2. 雙擊 `preview.bat`（或 `python scripts/preview.py`）→ 瀏覽器開 http://localhost:8000，存檔後按 F5 就看得到
3. 滿意了，雙擊 `publish.bat`（或 `python publish.py`）→ 確認後上傳到 mengyahh.com

## 部落格文章格式

```
---
title: 文章標題
date: 2025-09-29          ← 文章上架日期；也是網址（/blog/2025-09-29/），不能和別篇重複
photos: 2025-07-26        ← 選填。照片資料夾（在 assets/blog/ 底下）；改了 date 之後照片不用搬，寫原本的資料夾名稱即可
date_label: 2025.09       ← 選填。只想顯示年月時才寫；網址還是要有日
categories: [旅遊記事, 日本打工度假]
summary: 列表上顯示的一兩句簡介
keywords: [香川, 小豆島]  ← 顯示在文章最後的標籤
---

內文。段落之間空一行。

## 中標題
### 小標題

- 條列
- 條列

**備忘**

- 「備忘」單獨一行，後面接的條列會變成淡色底的備忘框

**粗體**、[連結文字](https://example.com)、〈另一篇文章的標題〉（會自動連到那篇，只寫「：」前面的部分也可以）

![](01.webp)

**關鍵字**

（這一段以下只用來給站內搜尋，不會顯示在頁面上；可以放日文、英文的關鍵字）
```

- **照片**就是單獨一行的 `![](檔名)`，想換位置就把那一行剪下貼到別的段落之間。照片的檔案放在 `assets/blog/<資料夾>/`（資料夾就是 `photos:` 寫的名稱，沒寫 `photos:` 就是文章的日期）。圖說（alt）可以寫在方括號裡：`![湖邊的早晨](03.webp)`，不寫會自動補。
- 想換列表上的縮圖：front matter 加 `cover: 03.webp`（預設用同資料夾的 `cover.webp`，沒有就用第一張）。
- 想讓文章最上方顯示一張橫幅大圖：加 `banner: yes`。
- `categories` 可以多個。側欄有的有：各種心得、日常記事、創作、階段回顧、其他、旅遊記事、飲食料理、自然筆記、日本打工度假；寫新名字也可以，會自動出現。
- **改日期**：直接改 front matter 的 `date`，網址也會跟著變成新日期（舊網址就打不開了）。檔名開頭的日期不用手動改，`publish.bat` 會自動改成和 `date` 一致；照片不用搬。
- 不想發布：檔名前面加 `_`，或 front matter 加 `draft: yes`。

## 料理紀錄格式

```
---
title: 自己做甘酒
date: 2025-07-12          ← 只寫 2025-07 也可以，頁面顯示「2025.07」
place: 石川縣加賀市
---

![](202507-igG01-1.webp)
![](202507-igG01-2.webp)

文字（段落、條列都可以）。
```

照片的檔案在 `assets/cooking/`；文中所有 `![](…)` 會組成輪播（順序就是檔案裡的順序，想放最前面的照片就放最上面），不會出現在文字裡。`![說明](…)` 的說明會當成該張照片的圖說。

## 加照片

照片要先縮小、轉成 WebP、去掉 EXIF（含 GPS 位置），用工具一次做好（需要 `pip install pillow`）：

```
python scripts/photo.py blog content/blog/2025-09-29_小豆島.md D:\照片\a.jpg D:\照片\b.jpg
python scripts/photo.py cooking 202601-a D:\照片\a.jpg
```

執行後會印出要貼進 `.md` 的那幾行。

## 出錯時

`preview.py` / `build.py` 會直接說是哪個檔案、哪裡有問題（例如日期格式不對、照片找不到）。
