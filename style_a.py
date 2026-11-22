"""עיצוב A — השפה העיצובית החדשה של מסמכי המשרד, נאמנה לנייר המכתבים המקורי.

כל המסמכים בנויים מתבנית בסיס אחת (templates_a/base.html.j2), והעיצוב מגיע ממשתנים אחידים
(COLORS, TYPE, PAGE) שנכנסים ל-templates_a/style.css.j2. הנתונים מגיעים מבחוץ כמו שהם:
הקובץ הזה לא משנה מספור, חישובים או נתונים. הסכומים שמוצגים מחושבים בקוד שקורא לו, כמו בתבניות הישנות.
היחיד שמחושב כאן לתצוגה הוא הסכום בשקלים של כל שלב בהצעת המחיר, באותו עיגול של חשבון השלב בפיקו.

נטען רק כשמבקשים עיצוב A, כדי שתקלה כאן לא תפיל את שאר בורי. weasyprint נטען בתוך הפונקציות,
כדי שאפשר יהיה לבנות ולבדוק את ה-HTML גם בלעדיו.
"""
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

HERE = Path(__file__).parent
FONTS_DIR = HERE / "fonts"
NARKISIM_FILE = "Narkisim.ttf"     # לא בגיט: המאגר ציבורי והרישיון של הגופן לא מתיר. בלעדיו — Heebo
TEMPLATES_DIR = HERE / "templates_a"
ASSETS_DIR = HERE / "assets"

# ---------- משתני העיצוב ----------
# מידות במ"מ. השוליים התחתונים שומרים מקום לציור הבית ולפרטי ההתקשרות של נייר המכתבים.
PAGE = {"top": 12, "side": 22, "bottom": 58}
CONTENT_W = 210 - 2 * PAGE["side"]
CONTENT_BOTTOM = 297 - PAGE["bottom"]
MM_PER_PX = 25.4 / 96
FOOTER = {"w": 176.1, "h": 56.4}   # התמונה מנייר המכתבים המקורי, צמודה לפינה הימנית התחתונה של הדף

COLORS = {
    "ink": "#1b1b1b",       # טקסט
    "ink_2": "#4a4f59",     # טקסט משני
    "mute": "#6e737c",      # תוויות
    "rule": "#9a9a9a",      # קווים דקים
    "rule_soft": "#c9c9c9",
    "blue": "#2a4088",      # הכחול של הלוגו
}

# גופן: נרקיסים כשהקובץ קיים בשרת, ואחרת Heebo — בגודל שמתאים לכל אחד מהם
TYPE_NARKISIM = {"family": "'Narkisim', 'Heebo', sans-serif", "body": 12, "lh": 1.4, "small": 11, "label": 10}
TYPE_HEEBO = {"family": "'Heebo', sans-serif", "body": 10.5, "lh": 1.5, "small": 9.6, "label": 9}

SIGNOFF = {"name": "פרוכטמן ישראל", "company": 'פ.י.קו הנדסה בע"מ'}


def has_narkisim() -> bool:
    return (FONTS_DIR / NARKISIM_FILE).exists()


def type_tokens() -> dict:
    return TYPE_NARKISIM if has_narkisim() else TYPE_HEEBO


def money(value) -> str:
    """1234567 -> 1,234,567. כמו בתבניות הישנות."""
    return "{:,.0f}".format(value)


def no_parens(text: str) -> str:
    """אין סוגריים במסמכים (בעיות RTL). כמו stripParens ב-generate-quote-pdf."""
    return re.sub(r"\s{2,}", " ", re.sub(r"[()]", "", text or "")).strip()


_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)
_env.filters["money"] = money


def render_html(template: str, **context) -> str:
    base = dict(
        fonts=FONTS_DIR.as_uri(), assets=ASSETS_DIR.as_uri(), narkisim=has_narkisim(),
        page=PAGE, footer=FOOTER, c=COLORS, t=type_tokens(), signoff=SIGNOFF,
        font_pt=None, line_height=None,
    )
    base.update(context)
    return _env.get_template(template).render(**base)


def _html(html: str):
    from weasyprint import HTML
    return HTML(string=html)


def _client_lines(lines):
    """שורות 'לכבוד': הראשונה היא השם, והשאר מתחתיה."""
    clean = [l.strip() for l in lines if l and l.strip()]
    return (clean[0] if clean else ""), clean[1:]


# ============================================================
# הצעת מחיר
# ============================================================
def quote_html(q) -> str:
    total = int(q.total_price)
    stages = [
        {
            "letter": m.letter,
            "description": m.description,
            "percentage": m.percentage,
            # כמו חשבון השלב בפיקו: Math.round(fee * percent / 100)
            "amount": (total * int(m.percentage) + 50) // 100,
        }
        for m in q.milestones
    ]
    contact = " · ".join(
        x for x in [
            f"טלפון {q.client_phone}" if q.client_phone else "",
            q.client_email or "",
        ] if x
    )
    to_lines = [x for x in [q.client_address, contact, f"ת.ז {q.client_id_number}" if q.client_id_number else ""] if x]
    notes = [l.strip() for l in (q.notes or "").split("\n") if l.strip()]
    return render_html(
        "quote.html.j2", data=q, stages=stages, notes=notes,
        to_name=q.client_name, to_lines=to_lines,
        meta=[("תאריך", q.date), ("מספר פרויקט", q.quote_number)],
        subject=q.subject,
    )


def quote_pdf(q) -> bytes:
    return _html(quote_html(q)).write_pdf()


# ============================================================
# חשבונות — חשבון רגיל או חלקי, חשבון להסכם ניהול ופיקוח, חשבון עבודה נוספת.
# שלושתם באותה תבנית: שורות סכום, סה"כ, פרטי תשלום. הסכומים מגיעים מחושבים.
# ============================================================
def _due(terms: str, due_date: str) -> str:
    return f"{terms} עד {due_date}" if due_date else terms


def invoice_html(inv, vat_amount: int, total_with_vat: int) -> str:
    to_name, to_lines = _client_lines(inv.client_lines)
    note = no_parens(inv.milestone_note)
    rows = [
        {"label": 'שכ"ט כללי', "amount": money(inv.total_fee) + " ₪", "muted": True},
        {"label": f"תשלום {inv.invoice_number}", "sub": note, "amount": money(inv.payment_amount) + " ₪"},
        {"label": f'מע"מ {inv.vat_percent}%', "amount": money(vat_amount) + " ₪"},
    ]
    kind = "חשבון חלקי" if inv.is_partial else "חשבון"
    return render_html(
        "invoice.html.j2", to_name=to_name, to_lines=to_lines,
        meta=[("תאריך", inv.date), ("מספר פרויקט", inv.project_number)],
        subject=f"{kind} מס' {inv.invoice_number}", subject_lines=[inv.work_description],
        rows=rows, total=money(total_with_vat) + " ₪",
        pay=[("מועד תשלום", _due(inv.payment_terms, inv.due_date)), ("העברה בנקאית", inv.bank_details)],
    )


def invoice_pdf(inv, vat_amount: int, total_with_vat: int) -> bytes:
    return _html(invoice_html(inv, vat_amount, total_with_vat)).write_pdf()


def supervision_invoice_html(inv, vat_amount: int, total_with_vat: int) -> str:
    to_name, to_lines = _client_lines(inv.client_lines)
    rows = [
        {"label": inv.fee_label, "amount": money(inv.monthly_fee) + " ₪"},
        {"label": f'מע"מ {inv.vat_percent}%', "amount": money(vat_amount) + " ₪"},
    ]
    return render_html(
        "invoice.html.j2", to_name=to_name, to_lines=to_lines,
        meta=[("תאריך", inv.date), ("מספר פרויקט", inv.quote_number)],
        subject=f"חשבון מס' {inv.invoice_number} — הסכם ניהול ופיקוח",
        subject_lines=[inv.project_description, f"עבור: {inv.billing_month_label}"],
        rows=rows, total=money(total_with_vat) + " ₪",
        pay=[("מועד תשלום", _due(inv.payment_terms, inv.due_date)), ("העברה בנקאית", inv.bank_details)],
    )


def supervision_invoice_pdf(inv, vat_amount: int, total_with_vat: int) -> bytes:
    return _html(supervision_invoice_html(inv, vat_amount, total_with_vat)).write_pdf()


def extra_work_invoice_html(inv, vat_amount: int, total_with_vat: int, hours_text: str) -> str:
    to_name, to_lines = _client_lines(inv.client_lines)
    rows = []
    if inv.hours:
        rows.append({"label": f"{hours_text} שעות עבודה", "amount": f"{money(inv.hourly_rate)} ₪ לשעה", "muted": True, "rtl": True})
    rows += [
        {"label": 'סכום לפני מע"מ', "amount": money(inv.payment_amount) + " ₪"},
        {"label": f'מע"מ {inv.vat_percent}%', "amount": money(vat_amount) + " ₪"},
    ]
    return render_html(
        "invoice.html.j2", to_name=to_name, to_lines=to_lines,
        meta=[("תאריך", inv.date), ("מספר פרויקט", inv.project_number)],
        subject=f"חשבון עבודה נוספת מס' {inv.invoice_number}",
        subject_lines=[inv.description],
        intro="עבודה נוספת מעבר להצעת המחיר המקורית, ולכן חשבון נפרד.",
        rows=rows, total=money(total_with_vat) + " ₪",
        pay=[("מועד תשלום", _due(inv.payment_terms, inv.due_date)), ("העברה בנקאית", inv.bank_details)],
    )


def extra_work_invoice_pdf(inv, vat_amount: int, total_with_vat: int, hours_text: str) -> bytes:
    return _html(extra_work_invoice_html(inv, vat_amount, total_with_vat, hours_text)).write_pdf()


# ============================================================
# אישור יציקה — אותו מנגנון של היום: גובה העמוד נעול, החתימה בפינה השמאלית התחתונה,
# והתמונות בפריים מלא מקבלות את הגובה שנשאר ביניהן. ראו site_photos.py.
# ============================================================
SR_GAP_ABOVE_PHOTOS = 4    # מ"מ, כמו margin-top של .photos


def site_report_html(report, rows) -> str:
    return render_html(
        "site_report.html.j2", data=report, rows=rows,
        to_name=report.client_name, to_lines=[report.client_address],
        meta=[("תאריך", report.date), ("מספר פרויקט", report.project_number)],
        subject=f"אישור {report.casting_title}.",
        content_h=CONTENT_BOTTOM - PAGE["top"],
    )


def site_report_fallback_rows(urls):
    """אם הסידור נכשל: תמונות בתיבות קבועות, שתיים בשורה. הדוח לא נכשל בגלל תמונות."""
    clean = [u for u in list(urls)[:12] if isinstance(u, str) and u.strip()]
    return [[{"src": u, "w": 70.0, "h": 48.0} for u in clean[i:i + 2]] for i in range(0, len(clean), 2)]


def site_report_pdf(report):
    """מחזיר (bytes של ה-PDF, מספר התמונות שנכנסו)."""
    try:
        return _site_report_fitted(report)
    except Exception as e:
        print(f"style A site report photo layout failed, using fallback: {e}")
        return _html(site_report_html(report, site_report_fallback_rows(report.photo_urls))).write_pdf(), len(report.photo_urls)


def _site_report_fitted(report):
    from site_photos import layout_rows, load_photos

    photos = load_photos(report.photo_urls)

    def render(rows):
        return _html(site_report_html(report, rows)).render()

    base = render([])
    anchors = getattr(base.pages[0], "anchors", None) or {}
    end, top = anchors.get("content-end"), anchors.get("signoff-box")
    doc = base
    if photos:
        aspects = [a for _, a in photos]
        limit_mm = top[1] * MM_PER_PX - 3 if top else None
        avail = (limit_mm - end[1] * MM_PER_PX - SR_GAP_ABOVE_PHOTOS - 1) if (top and end) else 85.0
        for _ in range(5):
            rows = [[{"src": photos[p["index"]][0], "w": p["w"], "h": p["h"]} for p in row]
                    for row in layout_rows(aspects, avail, width=CONTENT_W)]
            doc = render(rows)
            pe = (getattr(doc.pages[-1], "anchors", None) or {}).get("photos-end")
            if limit_mm is None or pe is None or pe[1] * MM_PER_PX <= limit_mm:
                break
            avail -= (pe[1] * MM_PER_PX - limit_mm) + 2
    return doc.write_pdf(), len(photos)


# ============================================================
# דוח ביקור באתר (דוח ניהול ופיקוח) — אותו מנגנון של היום: טקסט, תמונות, חתימה,
# בעמוד אחד; התמונות מקבלות את הגודל הכי גדול שנכנס, ואם צריך הגופן קטן.
# טקסט לעולם לא נחתך: דוח שלא נכנס גם בגופן הקטן ביותר ממשיך לעמוד שני.
# ============================================================
MR_FONTS_NARKISIM = [(12, 1.4), (11.5, 1.38), (11, 1.35), (10.5, 1.32), (10, 1.3)]
MR_FONTS_HEEBO = [(10.5, 1.5), (10, 1.45), (9.5, 1.4), (9, 1.35), (8.5, 1.3)]
MR_PHOTO_GAP = 2.5
MR_PHOTO_BORDER = 0.4
MR_PHOTOS_TOP = 4
MR_PHOTO_MAX_W = {1: 140, 2: 80}
MR_PHOTO_MIN_W = 36
MR_PHOTO_RATIO = 0.68
MR_SIGNOFF_H = 30
MR_MAX_RENDERS = 12


def body_lines(body: str):
    """הטקסט החופשי בשורות, כמו שנכתב. שורה שנגמרת בנקודתיים — כותרת משנה, שורה שמתחילה במקף — סעיף.
    עיצוב בלבד: הטקסט עצמו לא משתנה."""
    out = []
    for raw in (body or "").split("\n"):
        line = raw.strip()
        if not line:
            out.append({"kind": "gap", "text": ""})
        elif line.endswith(":"):
            out.append({"kind": "head", "text": line})
        elif line[0] in "-•":
            out.append({"kind": "item", "text": line})
        else:
            out.append({"kind": "p", "text": line})
    return out


def mr_photo_layout(n: int, avail_mm: float) -> dict:
    best = None
    for cols in range(min(n, 2), min(n, 4) + 1):
        rows = -(-n // cols)
        row_h = (avail_mm - MR_PHOTO_GAP * (rows - 1)) / rows - MR_PHOTO_BORDER
        fit_w = (CONTENT_W - MR_PHOTO_GAP * (cols - 1) - 1) / cols - MR_PHOTO_BORDER
        w = min(MR_PHOTO_MAX_W.get(cols, fit_w), fit_w, row_h / MR_PHOTO_RATIO)
        if best is None or w > best["w"] + 0.5:
            best = {"cols": cols, "w": w, "row_h": row_h}
    w = int(best["w"] * 10) / 10
    h = int(min(w * 0.75, best["row_h"]) * 10) / 10
    return {"cols": best["cols"], "w": w, "h": h, "gap": MR_PHOTO_GAP}


def management_report_html(report, subject, font, photo) -> str:
    photo_rows = []
    if photo:
        urls = list(report.photo_urls)
        photo_rows = [urls[i:i + photo["cols"]] for i in range(0, len(urls), photo["cols"])]
    return render_html(
        "management_report.html.j2", data=report, lines=body_lines(report.body),
        to_name=report.client_name, to_lines=[report.settlement],
        meta=[("תאריך", report.date), ("מספר פרויקט", report.project_number)],
        subject=f"{subject}.", font_pt=font[0], line_height=font[1],
        photo=photo, photo_rows=photo_rows, photos_top=MR_PHOTOS_TOP,
    )


def management_report_doc(report, subject):
    """מחזיר את המסמך המוכן ואת מספר הפריסות שנדרשו."""
    fonts = MR_FONTS_NARKISIM if has_narkisim() else MR_FONTS_HEEBO
    n = len(report.photo_urls)
    renders = 0

    def render(font, photo=None):
        nonlocal renders
        renders += 1
        return _html(management_report_html(report, subject, font, photo)).render()

    def title_h(font):
        return font[0] * font[1] * 25.4 / 72 + 1

    def fit(font):
        doc = render(font)
        pages = len(doc.pages)
        if n == 0:
            return doc, pages
        end = (getattr(doc.pages[-1], "anchors", None) or {}).get("content-end")
        free = CONTENT_BOTTOM - end[1] * MM_PER_PX if end else 170
        avail = free - MR_PHOTOS_TOP - title_h(font) - 2
        while renders < MR_MAX_RENDERS:
            photo = mr_photo_layout(n, avail)
            if photo["w"] < MR_PHOTO_MIN_W:
                break
            doc = render(font, photo)
            if len(doc.pages) == pages:
                return doc, pages
            avail *= 0.88
        return None, pages

    regular = None
    for font in fonts:
        if renders >= MR_MAX_RENDERS:
            break
        doc, pages = fit(font)
        if doc and pages == 1:
            return doc, renders
        if font == fonts[0]:
            regular = doc

    if regular is None:
        font = fonts[0]
        own_page = CONTENT_BOTTOM - PAGE["top"] - MR_SIGNOFF_H - MR_PHOTOS_TOP - title_h(font) - 2
        regular = render(font, mr_photo_layout(n, own_page))
    return regular, renders


# ============================================================
# הסכם ניהול ופיקוח — אותו נוסח בדיוק, בעיצוב A. עמוד אחד, והחתימות בתחתיתו;
# אם צריך הגופן קטן, ורק אם זה בלתי אפשרי — עמוד שני.
# ============================================================
SC_FONTS_NARKISIM = [(11.5, 1.36), (11, 1.33), (10.5, 1.3), (10, 1.28)]
SC_FONTS_HEEBO = [(9.8, 1.36), (9.4, 1.33), (9.0, 1.3), (8.6, 1.28)]
SC_SIGNS_TOP = 6


def supervision_contract_html(context: dict, font, signs_top) -> str:
    q = context["data"]
    return render_html(
        "supervision_contract.html.j2", **context,
        meta=[("הסכם מס'", q.quote_number), ("תאריך", q.date)],
        font_pt=font[0], line_height=font[1], signs_top=round(signs_top, 1),
    )


def supervision_contract_doc(context: dict):
    """context — אותם ערכים שהתבנית הישנה מקבלת: data, title, scope_text, project, general_note,
    pre_title, sup_title, fee, fee_section, letters."""
    fonts = SC_FONTS_NARKISIM if has_narkisim() else SC_FONTS_HEEBO

    def render(font, signs_top):
        return _html(supervision_contract_html(context, font, signs_top)).render()

    regular = None
    for font in fonts:
        doc = render(font, SC_SIGNS_TOP)
        if regular is None:
            regular = doc
        if len(doc.pages) > 1:
            continue
        end = (getattr(doc.pages[0], "anchors", None) or {}).get("content-end")
        free = CONTENT_BOTTOM - end[1] * MM_PER_PX if end else 0
        if free < 2:
            return doc
        lowered = render(font, SC_SIGNS_TOP + free - 1)
        return lowered if len(lowered.pages) == 1 else doc
    return regular
