# 用 Markdown 改「工作」區的內容（mengyahh.com/work/）

```
content/work/about.md                 工作頁 /work/（做什麼、做過的專案、合作方式、聯絡）
content/work/appsheet.md              /work/ 裡的 AppSheet 區塊：介紹、提供的方式、既有作品卡片（自動產生）、收合的說明
content/work/products/invoice.md      作品頁：內部請款系統
content/work/products/freelance.md    作品頁：自由工作收支管理系統
content/work/products/case.md         作品頁：個案管理系統
content/work/products/poultry.md      作品頁：白肉雞養殖紀錄系統
content/work/portfolio/*.md           作品集頁 /work/portfolio/<名稱>/（檔名開頭是 _ 的不會發布）
assets/work/portfolio/                作品集圖片（寫在 .md 裡時從 portfolio/ 開始）
assets/work/screenshots/              各作品的 App 畫面（寫在 .md 裡時從 screenshots/ 開始）
```

導覽列、頁尾等整個網站共用的文字在 `scripts/build.py`（`STRINGS`）。

**不要直接改產生出來的 HTML**（`work/` 底下的 `index.html`）：下次建置會被蓋掉。改上面的 `.md`。

## 日常流程

1. 改 `.md` 檔（記事本、VS Code 都能開）
2. 雙擊 `preview.bat`，瀏覽器開 http://localhost:8000/work/，存檔後按 F5 就看得到
3. 滿意了，雙擊 `publish.bat`，確認後上傳到 mengyahh.com

（也可以用 `python scripts/preview.py`、`python publish.py`。）

## 關於頁 `content/work/about.md`

開頭是設定，接著是一段一段的「區塊」，每個區塊用 `::: 類型 小標` 開頭、單獨一行 `:::` 結尾。**區塊的順序就是頁面的順序**，可以搬動。

```
---
title: 工作                              ← 瀏覽器分頁標題
description: 搜尋結果下面的那一兩句簡介
email: mengyahh@gmail.com               ← 聯絡區塊的 email
---
```

| 區塊 | 寫法重點 |
|---|---|
| `::: hero` | 第一行是小字標題；`# ` 開頭是大標題，`**粗體**` 的部分會變成綠色強調；後面的文字是簡介 |
| `::: skills 能力` | `## ` 大標、下面一段是簡介；每個 `### 名稱` 是一張卡片（文字一段、`> ` 開頭是灰色備註、`- 標籤：內容` 條列會排成兩欄）；單獨一行 `---` 之後的那一段是「合作單位…」；`#### 常用工具` 底下 `- 類別：A、B、C` 會變成一個個小標籤 |
| `::: projects 專案類型` | `## ` 大標、簡介；每個 `### 專案名稱` 是一列，**同一行最後面可以放連結** `[名稱](網址)`，下一行用「、」隔開的是標籤；`---` 之後那段是結語 |
| `::: process 合作方式` | 每個 `### 步驟名稱` 後面一段說明，依序自動編號；`---` 之後那段是補充 |
| `::: why 為什麼找我` | `- **標題**：說明` |
| `::: name 名稱` | 一段文字（目前沒有使用） |
| `::: contact` | `## ` 標題、一段說明，`- [文字](網址)` 是下面的連結 |

專案連結的網址如果是 `http` 開頭，會自動加上「↗」（另開網站）；如果是站內的（例如 `portfolio/lecheng/`），會加上「→」。

## 作品頁 `content/work/portfolio/<網址名稱>.md`

檔名就是網址：`lecheng.md` → `mengyahh.com/work/portfolio/lecheng/`（檔名請用英文、數字、`-`）。

```
---
title: 【樂城生活節】藝文市集             ← 頁面大標題
description: （選填）搜尋結果的簡介
---

## 社群圖片製作                          ← 每個 ## 是一列：左邊是說明、右邊是作品
這一列的說明文字（可以有好幾段）

⮕ [文字](https://網址) 也可以放連結

![](portfolio/11.webp)                  ← 作品圖片（一行一張）
![](portfolio/12.webp "圖片說明")       ← 加引號＝圖片下方的說明文字
[![](portfolio/24.webp "說明")](https://網址)   ← 圖片本身連到外部網址（不放大，另開頁面）
![](youtube:qbjOpJ7ApBo "說明")         ← YouTube 影片（按了播放才載入）
```

- 圖片放在 `assets/portfolio/`，小圖用 `xx-t.webp`；影片的封面圖是 `assets/portfolio/yt-影片代碼.webp`。
- 加新圖片：`python scripts/photo.py D:\照片\a.jpg`（需要 `pip install pillow`），它會縮小、去掉 EXIF（含 GPS 位置）、編號，並印出要貼進去的那幾行。
- 新增一個作品頁：複製一個現有的 `.md` 改內容，檔名取新的網址名稱；記得到 `about.md` 的專案列表加上連結。
- 想暫時不發布：檔名前面加 `_`。

## AppSheet 區塊 `content/work/appsheet.md`

它**不是獨立的一頁**，而是 `/work/` 裡的「AppSheet」區塊（在 `about.md` 裡的 `::: appsheet` 那一行決定它出現在哪裡，目前在「能力」和「專案類型」之間）。舊網址 `/work/appsheet/` 會自動轉到 `/work/#appsheet`。

```
---
title: AppSheet 管理系統          ← 區塊標題
cta: 來信申請試用                 ← 標題下方那顆按鈕的文字（連到頁面最下面的聯絡區）
description: ...                  ← 沒有用到（搜尋結果的簡介用 about.md 的）
---

開頭一兩段介紹。

::: offers 我如何提供服務？       ← 條列會變成並排的卡片（每項 **標題：** 後面接說明）
- **完全客製化製作：**說明
- **購買既有作品：**說明

**保固服務：**…                  ← 卡片下面的一行補充（一般段落）
:::

::: systems 既有作品              ← 底下自動列出 content/work/products/ 裡的每個作品卡片
這一行是卡片上方的說明文字。
:::

::: details 誰適合使用 AppSheet 製作的系統？   ← 預設收合，點了才展開（條列）
- ...
:::
```

作品卡片的內容（標題、適用對象、一句話介紹、順序）來自各作品頁最上面的 `title`、`for`、`summary`、`order`；桌機一排四張、平板兩張、手機左右滑動。

「做過什麼樣的專案」預設只顯示前 5 個，其餘收在「看其餘 N 個專案」（數字在 `scripts/work.py` 的 `PROJECTS_VISIBLE`），所以 `about.md` 裡越重要的專案越要放前面。

頁面最上面的「能力｜AppSheet｜專案類型｜…」頁內導覽會依區塊自動產生，標籤就是各區塊 `:::` 後面的小標。

## 產品頁 `content/work/products/<網址名稱>.md`

每個產品一頁：`freelance.md` → `mengyahh.com/work/appsheet/freelance/`。首頁只放產品的簡短說明（小卡片），完整介紹在這裡。

```
---
title: 自由工作收支管理系統
eyebrow: 作品 · 自由接案管理          ← 標題上方的小字
description: 搜尋結果的簡介（記得自然帶入使用者會搜尋的關鍵字）
order: 2                              ← 總覽頁與首頁小卡片的順序（數字小的在前）
for: 自由工作者、接案工作者            ← 適用對象（頁面標題下方、總覽頁都會顯示）
summary: 一句話介紹                    ← 總覽頁與首頁小卡片上的文字
status: 作品                          ← 首頁小卡片上的狀態小標籤
status_style: open                    ← （選填）標籤用強調色
---

開頭一兩段介紹文字（不需要區塊符號）。

::: features                       ← 功能卡片：每個 ### 是一張（標題＋下一段說明）
### 接案追蹤
記錄合作單位、專案、費用方式。
:::

::: screens App 實際畫面             ← 畫面截圖：圖片一行一張，引號裡是圖說；--- 之後那段是備註
![畫面說明](screenshots/xxx.png "圖說")
---
畫面中的資料皆為測試資料。
:::

::: note                            ← 灰色小字的補充說明
:::

::: callout open                    ← 結尾的行動方塊（open ＝ 邊框用強調色；所有作品頁用同樣的說法）
**想用這套系統？**……

- [按鈕文字 →](https://網址)          ← 列表會變成按鈕，第一個是主要按鈕
:::
```

新增作品：複製一個現有的 `.md` 改內容（最好保持同樣的區塊：適用對象、功能卡片、結尾方塊），首頁卡片與 AppSheet 總覽頁的清單會自動多一項；導覽列下拉選單要到 `scripts/build.py` 的 `nav_html()` 加上。所有作品的規格要一致。首頁本身現在也是 Markdown（`content/work/about.md`）。

## 出錯時

`preview.py` / `build.py` 會直接說是哪個檔案、哪裡有問題（例如找不到圖片、區塊類型打錯）。
