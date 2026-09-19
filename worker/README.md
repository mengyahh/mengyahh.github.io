# 留言後端（Cloudflare Worker + D1）

部落格文章底下的留言功能。前端在 `assets/js/comments.js`，後端是這個資料夾裡**單一檔案** `src/index.js`（沒有任何套件相依，可以直接貼進 Cloudflare 網頁介面）。

## 它怎麼運作
- 留言存在你自己 Cloudflare 帳號裡的 D1 資料庫。
- 電子郵件**只存在資料庫**，公開的介面（`GET /comments`）永遠不會回傳。頭像是用「電子郵件＋只有你知道的 `PEPPER`」算出的雜湊產生，看不出原本的 Email，也不會連到 Gravatar 之類的第三方。
- 第一次留言（或沒填 Email）先進「待審核」；同一個 Email 之後只要有一則被核准過，新的留言就直接發布。留言裡連結超過 1 個的一律先審核。
- 防垃圾：Cloudflare Turnstile、隱藏欄位、送出時間下限、同一個 IP 10 分鐘 3 則／一天 15 則、可封鎖 Email。
- 作者身分只能透過 `/admin` 回覆，前台任何人填「萌芽」這個名稱都會被拒絕（避免冒充）。
- 留言內容只當純文字顯示，不會執行任何 HTML。

**已知限制**：Email 沒有做驗證信。也就是說，知道某位留言者 Email 的人，可以用它的 Email 讓留言直接發布（冒用身分）。這種情況只要在後台刪除、或「封鎖此 Email」即可。

## 部署步驟（全部在 Cloudflare 網頁介面操作）

### 1. 建立資料庫
Cloudflare 後台 → **儲存和資料庫 (Storage & databases)** → **D1 SQL 資料庫** → 建立資料庫，名稱 `mengyahh-comments`。
進到這個資料庫 → **Console** 分頁 → 把 [`schema.sql`](schema.sql) 全部貼上執行。

### 2. 建立 Turnstile（防垃圾驗證）
後台 → **Turnstile** → 新增小工具：名稱隨意，主機名稱填 `mengyahh.com`，模式選 **Managed**。
建立後會得到兩個東西：**網站金鑰（Site Key，公開）** 和 **密鑰（Secret Key，機密）**。

### 3. 建立 Worker
後台 → **Workers 和 Pages** → 建立 → **建立 Worker**，名稱 `mengyahh-comments` → 部署（先用預設範例）→ **編輯程式碼** → 全選、貼上 [`src/index.js`](src/index.js) 的全部內容 → **部署**。

接著在這個 Worker 的 **設定**：

**繫結 (Bindings)** → 新增 → **D1 資料庫**
- 變數名稱：`DB`
- 資料庫：選 `mengyahh-comments`

**變數和密鑰 (Variables and Secrets)** → 新增：

| 類型 | 名稱 | 內容 |
|---|---|---|
| 密鑰 (Secret) | `TURNSTILE_SECRET` | 步驟 2 的 Secret Key |
| 密鑰 (Secret) | `ADMIN_TOKEN` | 你的後台密碼（自訂，20 字以上，建議用密碼管理器產生） |
| 密鑰 (Secret) | `PEPPER` | 隨機長字串（32 字以上，同樣用密碼管理器產生；**之後不要更改**，改了所有頭像會變） |
| 文字 (Text) | `ALLOWED_ORIGINS` | `https://mengyahh.com` |
| 文字 (Text) | `OWNER_NAME` | `萌芽` |

**網域和路由 (Domains & Routes)** → 新增 → **自訂網域** → `comments.mengyahh.com`
（Cloudflare 會自動建立這個子網域的 DNS 記錄。它只影響 `comments` 這個子網域，和網站主站的設定無關。）

### 4. 檢查
瀏覽器打開 `https://comments.mengyahh.com/`，應該看到一段 JSON，`db`、`turnstile_secret`、`admin_token`、`pepper` 都是 `true`。

### 5. 打開網站上的留言區
把兩個值告訴 Claude（或自己設定）：
- 後端網址：`https://comments.mengyahh.com`
- Turnstile 的**網站金鑰（Site Key）**（公開的那個，不是密鑰）

網站就會用這兩個值重新建置：

```bash
COMMENTS_API=https://comments.mengyahh.com TURNSTILE_SITEKEY=<網站金鑰> python scripts/build.py
```

（也可以把預設值寫進 `scripts/build.py` 最上面的 `COMMENTS_API`、`TURNSTILE_SITEKEY`。兩個都沒設定時，網站不會出現留言區。）

## 管理留言
打開 `https://comments.mengyahh.com/admin`，輸入 `ADMIN_TOKEN`。
- **待審核 / 已公開 / 垃圾** 三個分頁
- **核准**、**回覆（以作者身分）**、**標記垃圾**、**封鎖此 Email**、**刪除**（會連同底下的回覆一起刪）
- 直接回覆一則待審核的留言，會同時把它核准

## 資料與隱私
資料庫裡有：留言內容、名稱、Email、時間、IP 的雜湊（只用來限流，看不出原本的 IP）。Email 只會在 `/admin` 顯示給你看。想刪除某人的資料，在後台刪除他的留言即可。

## 本機檢查（不需要 Cloudflare）
`worker/src/index.js` 是一般的 ES module，本專案開發時用「瀏覽器＋SQLite (WASM) 模擬的 D1」跑過完整測試（驗證、審核流程、限流、回覆、作者回覆、封鎖、CORS、XSS）。
