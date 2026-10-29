# 閱讀群島 READING ARCHIPELAGO

把臺北市立圖書館的服務據點畫成一片 3D 群島：14 座島、69 個據點，可以看各館開館時間、館藏特色、設施，也可以輸入書名找有館藏的島。

線上看：https://ritakiros.github.io/reading-archipelago/

- 這是非官方網站，用 Claude 做的，整個網站就是一個 `index.html`，3D 畫面用 three.js。
- 據點、館藏特色、設施、開館時間、異動與活動資料擷取自[北市圖官網](https://tpml.gov.taipei/)（2026-10-29），出門前請再確認官網公告。
- 「找書」在 Claude 以外是連結版：輸入書名或 ISBN，會出現「到北市圖查「書名」」按鈕，直接打開北市圖館藏查詢的搜尋結果（ISBN 走 ISBN 搜尋），也附博客來和 Google 圖書的搜尋連結。北市圖館藏系統不開放其他網站直接呼叫，所以這裡看不到各館在架冊數。
- 書名裡有主題關鍵字（例如漫畫、天文、園藝）時，會順便推薦館藏特色相關的分館，只比對完整關鍵字，不代表那館一定有這本書。
- 在 Claude 裡打開時，會改用 Claude 瀏覽器即時查各館冊數，或用 Claude AI 依主題推薦島嶼。
- 地圖、各館資訊、開館狀態、讀者測驗、導覽都可以正常使用。

測試：`python3 tests/test_search_links.py [網址]`（需要 `pip install playwright && playwright install chromium`；不給網址就測本機的 index.html）。

也放在 [島嶼上線](https://islelive.com)。
