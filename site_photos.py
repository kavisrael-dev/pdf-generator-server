"""תמונות לדוח אישור יציקה: כל תמונה נראית בפריים המלא שלה, לאורך או לרוחב, והדוח נשאר בעמוד אחד.

מצלמים בנייד לאורך או לרוחב, ובעבר התמונות נחתכו לריבוע קבוע. כאן:
1. כל תמונה מורדת ומסובבת לפי סימון הסיבוב של הנייד (EXIF), כדי שהכיוון והיחס ישקפו את מה שרואים.
2. התמונות מסודרות בשורות באופן שכל שורה ממלאת את רוחב הדף, וגובה כל שורה לפי יחסי התמונות שבה.
3. אם הכול לא נכנס בגובה שנשאר מעל החתימה, הכול מוקטן ביחס שווה, בלי לחתוך.
"""
import base64
import io
import urllib.request

from PIL import Image, ImageOps

MAX_PHOTOS = 12
MAX_SIDE_PX = 1400        # גדול מספיק להדפסה, וקטן מספיק לקובץ קל
JPEG_QUALITY = 82
FETCH_TIMEOUT = 25
MAX_BYTES = 25 * 1024 * 1024

CONTENT_W_MM = 174.0      # רוחב הדף פחות שוליים
GAP_MM = 3.0
ROW_MAX_H_MM = 100.0      # תמונה בודדת לא גדולה מזה, גם כשיש הרבה מקום


def load_photo(url):
    """(מקור data:, יחס רוחב לגובה) של תמונה מוכנה לדוח, או None כשאי אפשר לקרוא אותה."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "bori-site-report"})
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as r:
            raw = r.read(MAX_BYTES)
        img = Image.open(io.BytesIO(raw))
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        w, h = img.size
        if w < 1 or h < 1:
            return None
        scale = min(1.0, MAX_SIDE_PX / max(w, h))
        if scale < 1:
            resample = getattr(Image, "Resampling", Image).LANCZOS
            img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), resample)
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=JPEG_QUALITY, optimize=True)
        uri = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
        return uri, img.size[0] / img.size[1]
    except Exception:
        return None


def load_photos(urls):
    """התמונות שנקראו בהצלחה, לפי הסדר, עד המרבי. תמונה שלא נקראה מדולגת ולא שוברת את הדוח."""
    out = []
    for url in list(urls)[:MAX_PHOTOS]:
        if not isinstance(url, str) or not url.strip():
            continue
        photo = load_photo(url.strip())
        if photo:
            out.append(photo)
    return out


def _partition(aspects, rows_count):
    """חלוקה של התמונות ברצף ל-rows_count שורות, כך שסכום היחסים בשורה הגדולה ביותר הוא הקטן ביותר."""
    n = len(aspects)
    if rows_count >= n:
        return [[i] for i in range(n)]
    pre = [0.0]
    for a in aspects:
        pre.append(pre[-1] + a)
    inf = float("inf")
    dp = [[inf] * (n + 1) for _ in range(rows_count + 1)]
    cut = [[0] * (n + 1) for _ in range(rows_count + 1)]
    dp[0][0] = 0.0
    for k in range(1, rows_count + 1):
        for j in range(k, n + 1):
            for i in range(k - 1, j):
                v = max(dp[k - 1][i], pre[j] - pre[i])
                if v < dp[k][j]:
                    dp[k][j] = v
                    cut[k][j] = i
    rows = []
    j = n
    for k in range(rows_count, 0, -1):
        i = cut[k][j]
        rows.append(list(range(i, j)))
        j = i
    rows.reverse()
    return rows


def layout_rows(aspects, avail_mm, width=CONTENT_W_MM, gap=GAP_MM, max_h=ROW_MAX_H_MM):
    """שורות של {index, w, h} במ"מ. בוחר את מספר השורות שנותן את התמונה הקטנה ביותר הגדולה ביותר."""
    n = len(aspects)
    if n == 0:
        return []
    avail_mm = max(avail_mm, 20.0)
    best = None
    for rows_count in range(1, n + 1):
        rows = _partition(aspects, rows_count)
        heights = [min(max_h, (width - gap * (len(r) - 1)) / sum(aspects[i] for i in r)) for r in rows]
        gaps = gap * (len(rows) - 1)
        # הרווחים בין השורות קבועים, ורק התמונות מוקטנות
        scale = min(1.0, max(avail_mm - gaps, 1.0) / sum(heights))
        score = min(heights) * scale
        # בשוויון, פחות שורות
        if best is None or score > best[0] + 0.5:
            best = (score, rows, heights, scale)
    _, rows, heights, scale = best
    out = []
    for r, h in zip(rows, heights):
        row_h = h * scale
        out.append([
            {"index": i, "w": int(aspects[i] * row_h * 10) / 10, "h": int(row_h * 10) / 10}
            for i in r
        ])
    return out
