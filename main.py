import math
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
from weasyprint import HTML
from jinja2 import Template

app = FastAPI()

# מודלים לקליטת הנתונים מהבוט (Supabase)
class PaymentMilestone(BaseModel):
    letter: str
    description: str
    percentage: int

class EngineeringQuoteData(BaseModel):
    date: str
    quote_number: str
    client_name: str
    client_address: str
    client_phone: str = ""         # טלפון הלקוח
    client_email: str = ""         # מייל הלקוח
    client_id_number: str = ""     # תעודת זהות — לחשבוניות מס
    subject: str
    work_description: str
    architect_name: str = ""       # אופציונלי — רק כשיש אדריכל/ית חיצוני/ת שהעביר/ה תוכניות
    project_location: str = ""     # אופציונלי — שורת "המגרש ממוקם ב..."
    scope_items: list[str]
    total_price: int
    milestones: list[PaymentMilestone]
    notes: str

# תבנית HTML המותאמת לעיצוב של פ.י. קו הנדסה
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: A4;
            margin: 15mm 18mm 50mm 18mm;
            @bottom-center {
                content: element(pageFooter);
            }
        }
        .page-footer {
            position: running(pageFooter);
            text-align: center;
        }
        .page-footer img {
            width: 165mm;
        }
        body {
            font-family: 'Arial', sans-serif;
            direction: rtl;
            color: #000;
            line-height: 1.3;
            font-size: 11pt;
        }
        .header-logo {
            text-align: center;
            margin-bottom: 10px;
        }
        .header-logo img {
            width: 360px;
            max-width: 100%;
        }
        .company-title {
            font-size: 16pt;
            font-weight: bold;
        }
        .company-subtitle {
            font-size: 12pt;
            margin-bottom: 14px;
        }
        .meta-data {
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
        }
        .subject {
            font-weight: bold;
            text-decoration: underline;
            text-align: center;
            margin-bottom: 10px;
        }
        .section-title {
            font-weight: bold;
            margin-top: 10px;
        }
        ul.scope-list, ul.milestone-list {
            list-style-type: none;
            padding-right: 0;
            margin-top: 5px;
        }
        .price {
            font-weight: bold;
            font-size: 12pt;
            margin-top: 12px;
        }
        .milestone-table {
            width: 80%;
            margin-top: 6px;
            border-collapse: collapse;
        }
        .milestone-table td {
            padding: 4px;
        }
        .notes {
            margin-top: 12px;
            font-size: 10pt;
        }
        .signature-area {
            margin-top: 42px;
            display: flex;
            justify-content: space-between;
            width: 60%;
        }
        .signature-box {
            border-top: 1px solid #000;
            width: 150px;
            text-align: center;
            padding-top: 5px;
        }
    </style>
</head>
<body>
    <div class="header-logo">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/logo.jpg" alt="פ.י. קו הנדסה בע״מ">
    </div>
    
    <div class="meta-data">
        <div>
            <strong>לכבוד:</strong> {{ data.client_name }}<br>
            {{ data.client_address }}<br>
            {% if data.client_phone %}טלפון: <span dir="ltr">{{ data.client_phone }}</span><br>{% endif %}
            {% if data.client_email %}מייל: <span dir="ltr">{{ data.client_email }}</span><br>{% endif %}
            {% if data.client_id_number %}ת.ז: <span dir="ltr">{{ data.client_id_number }}</span>{% endif %}
        </div>
        <div>
            <strong>תאריך:</strong> {{ data.date }}<br>
            <strong>מספר פרוייקט:</strong> {{ data.quote_number }}
        </div>
    </div>

    <div class="subject">הנדון: {{ data.subject }}</div>

    <div>
        <span class="section-title">תאור העבודה:</span> {{ data.work_description }}<br>
        {% if data.architect_name %}על פי תוכניות להצעת מחיר שהועברו במייל האדריכל/ית {{ data.architect_name }}.<br>{% endif %}
        {% if data.project_location %}המגרש ממוקם ב{{ data.project_location }}{% endif %}
    </div>

    <div class="section-title">התכנון כולל:</div>
    <ul class="scope-list">
        {% for item in data.scope_items %}
        <li>{{ item }}</li>
        {% endfor %}
    </ul>

    <div class="price">
        שכ"ט עבור הסעיפים הנ"ל {{ "{:,.0f}".format(data.total_price) }} ש"ח לפני מע"מ.
    </div>

    <div>
        השכר ישולם בהעברה בנקאית במועד הגשת חשבון פרופורמה לפי שלבי התקדמות העבודה כדלהלן:
        <table class="milestone-table">
            {% for milestone in data.milestones %}
            <tr>
                <td style="width: 30px;">{{ milestone.letter }}.</td>
                <td>{{ milestone.description }}</td>
                <td style="text-align: left;">{{ milestone.percentage }}%</td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <div class="notes">
        {{ data.notes | replace('\n', '<br>') }}
    </div>

    <div class="signature-area">
        <div class="signature-box">לאישור יש לחתום ולהעביר חזרה במייל</div>
        <div class="signature-box">ת.ז</div>
        <div class="signature-box">חתימה</div>
    </div>

    <div style="margin-top: 12px;">
        בברכה,<br>
        פרוכטמן ישראל<br>
        פ.י.קו הנדסה בע"מ.
    </div>

    <div class="page-footer">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/footer.png" alt="פרטי קשר - פ.י.קו הנדסה בע״מ">
    </div>
</body>
</html>
"""

# ============================================================
# חשבון חלקי (דרישת תשלום) — מודל ותבנית
# ============================================================
class InvoiceData(BaseModel):
    date: str                      # 28/05/2026
    project_number: str            # 6180
    invoice_number: int            # מס' החשבון החלקי (1, 2, 3...)
    client_lines: list[str]        # שורות "לכבוד": שם, אגודה, ח.פ...
    work_description: str
    total_fee: int                 # שכ"ט כללי לפני מע"מ
    payment_amount: int            # סכום התשלום הנוכחי לפני מע"מ
    milestone_note: str = ""       # למשל: "(סעיף ב+ג 50%)"
    is_partial: bool = True        # False = תשלום יחיד (הצעה עם שלב אחד) — "חשבון" ולא "חשבון חלקי"
    vat_percent: int = 18
    payment_terms: str = "שוטף+30"
    due_date: str = ""             # 30/06/2026
    bank_details: str = 'בנק פועלים סניף 717, חשבון 534731, ע"ש פ.י.קו הנדסה בע"מ'

INVOICE_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: A4;
            margin: 15mm 18mm 50mm 18mm;
            @bottom-center { content: element(pageFooter); }
        }
        .page-footer { position: running(pageFooter); text-align: center; }
        .page-footer img { width: 165mm; }
        body {
            font-family: 'Arial', sans-serif;
            direction: rtl;
            color: #000;
            line-height: 1.5;
            font-size: 11pt;
        }
        .header-logo { text-align: center; margin-bottom: 18px; }
        .header-logo img { width: 360px; max-width: 100%; }
        .meta-data { display: flex; justify-content: space-between; margin-bottom: 20px; }
        .subject {
            font-weight: bold;
            text-decoration: underline;
            margin: 18px 0 14px 0;
        }
        table.amounts { margin-top: 14px; border-collapse: collapse; width: 70%; }
        table.amounts td { padding: 5px 4px; }
        table.amounts .num { text-align: left; direction: ltr; }
        table.amounts .total td { font-weight: bold; border-top: 1px solid #000; }
        .pay-info { margin-top: 22px; }
        .confirm-note { margin-top: 16px; font-weight: bold; }
        .signoff { margin-top: 30px; }
    </style>
</head>
<body>
    <div class="header-logo">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/logo.jpg" alt="פ.י. קו הנדסה בע״מ">
    </div>

    <div class="meta-data">
        <div>
            <strong>לכבוד:</strong><br>
            {% for line in data.client_lines %}{{ line }}<br>{% endfor %}
        </div>
        <div>
            <strong>תאריך:</strong> {{ data.date }}<br>
            <strong>פ:</strong> {{ data.project_number }}
        </div>
    </div>

    <div class="subject">הנדון: חשבון {% if data.is_partial %}חלקי {% endif %}מס' {{ data.invoice_number }}</div>

    <div>{{ data.work_description }}</div>

    <table class="amounts">
        <tr>
            <td>שכ"ט כללי</td>
            <td class="num">{{ "{:,.0f}".format(data.total_fee) }}</td>
            <td></td>
        </tr>
        <tr>
            <td>תשלום {{ data.invoice_number }}</td>
            <td class="num">{{ "{:,.0f}".format(data.payment_amount) }}</td>
            <td>{{ data.milestone_note }}</td>
        </tr>
        <tr>
            <td>מע"מ {{ data.vat_percent }}%</td>
            <td class="num">{{ "{:,.0f}".format(vat_amount) }}</td>
            <td></td>
        </tr>
        <tr class="total">
            <td>סה"כ לתשלום</td>
            <td class="num">{{ "{:,.0f}".format(total_with_vat) }}</td>
            <td></td>
        </tr>
    </table>

    <div class="pay-info">
        <strong>מועד תשלום:</strong> {{ data.payment_terms }}{% if data.due_date %} ({{ data.due_date }}){% endif %}<br>
        <strong>ניתן להעברה בנקאית:</strong> {{ data.bank_details }}
    </div>

    <div class="confirm-note">נא לשלוח אישור ביצוע.</div>

    <div class="signoff">
        בכבוד רב,<br>
        פרוכטמן ישראל<br>
        פ.י.קו הנדסה בע"מ.
    </div>

    <div class="page-footer">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/footer.png" alt="פרטי קשר - פ.י.קו הנדסה בע״מ">
    </div>
</body>
</html>
"""

# ============================================================
# דוח ביקור באתר (אישור יציקה) — מודל ותבנית
# ============================================================
class SiteReportData(BaseModel):
    date: str                      # 10/11/2025
    project_number: str            # 5070
    client_name: str               # משפחת ברדן
    client_address: str            # מרחביה
    casting_title: str             # "יציקת יסודות" / "יציקה על קורות עץ" — הנדון: אישור <casting_title>
    summary: str = "לאחר סיור בשטח קבעתי שניתן לבצע את היציקה."
    notes: str = "אין הערות מיוחדות. הכל תקין."
    photo_urls: list[str] = []     # תמונות מהשטח (קישורים ציבוריים)

# אישור יציקה: עיצוב מקצועי (3/11/2026). אותו תוכן; Heebo, טבלת פרטים, גודל תמונות לפי כמות, חתימה חתוכה בלי שקיפות.
SITE_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <style>
        @font-face { font-family: 'Heebo'; font-weight: 400; src: url('{{ fonts }}/Heebo-Regular.ttf'); }
        @font-face { font-family: 'Heebo'; font-weight: 500; src: url('{{ fonts }}/Heebo-Medium.ttf'); }
        @font-face { font-family: 'Heebo'; font-weight: 700; src: url('{{ fonts }}/Heebo-Bold.ttf'); }
        @page {
            size: A4;
            margin: 15mm 18mm 50mm 18mm;
            @bottom-center { content: element(pageFooter); }
        }
        .page-footer { position: running(pageFooter); text-align: center; }
        .page-footer img { width: 165mm; }
        body {
            font-family: 'Heebo', 'Arial', sans-serif;
            direction: rtl;
            color: #1c2733;
            line-height: 1.45;
            font-size: 11pt;
            /* נעילת גובה התוכן לעמוד אחד + עוגן למיקום החתימה */
            position: relative;
            height: 230mm;
            overflow: hidden;
        }
        .header-logo { text-align: center; margin-bottom: 4px; }
        .header-logo img { width: 300px; max-width: 100%; }
        /* קו כותרת כפול: עבה וכהה, ומתחתיו דק ובהיר */
        .rule { border-top: 2.5px solid #1f3a5f; border-bottom: 0.6px solid #9fb0c3; height: 2px; margin: 2px 0 8px 0; }
        /* פרטי הדוח בטבלה: לכבוד מימין, תאריך ופרויקט משמאל */
        .meta { width: 100%; border-collapse: separate; border: 0.8px solid #cfd9e4; border-radius: 2mm; background: #f4f7fa; margin-bottom: 6px; }
        .meta td { padding: 5px 12px; vertical-align: top; border-right: 0.8px solid #cfd9e4; }
        .meta td.first { border-right: 0; }
        .meta td.date { width: 24%; }
        .meta td.proj { width: 18%; }
        .meta .label { color: #5c6e82; font-size: 9pt; font-weight: 500; }
        .meta .value { font-weight: 700; font-size: 11.5pt; }
        .subject {
            font-weight: 700;
            text-align: center;
            font-size: 14pt;
            color: #1f3a5f;
            border-top: 0.8px solid #1f3a5f;
            border-bottom: 0.8px solid #1f3a5f;
            padding: 4px 0;
            margin: 4px 0 8px 0;
        }
        .summary { margin-bottom: 6px; font-weight: 500; }
        .notes-block {
            white-space: pre-line;
            border-right: 3px solid #1f3a5f;
            padding: 2px 11px 2px 0;
            margin: 4px 0 8px 0;
        }
        .thanks { margin-top: 6px; }
        /* בברכה + שם + חתימה — תמיד בפינה השמאלית-תחתונה של הדף */
        .signoff {
            position: absolute;
            bottom: 0;
            left: 0;
            text-align: left;
            border-top: 0.8px solid #9fb0c3;
            padding-top: 3px;
        }
        /* חתימה וחותמת: PNG חתוך לתוכן, בלי שקיפות (תצוגות שונות לא מציגות שקיפות נכון) */
        .signature-img { height: 15mm; margin-top: 2px; }
        .photos { margin-top: 10px; display: flex; flex-wrap: wrap; gap: 3mm; justify-content: center; }
        .photos img { box-sizing: border-box; object-fit: cover; border: 0.8px solid #b9c6d4; border-radius: 1.5mm; }
        /* גודל התמונות לפי הכמות, כדי שהכול ייכנס מעל החתימה בעמוד אחד */
        .photos.c1 img { width: 130mm; height: 80mm; }
        .photos.c2 img { width: 74mm; height: 46mm; }
        .photos.c3 img { width: 54mm; height: 30mm; }
        .photos.c4 img { width: 40mm; height: 24mm; }
    </style>
</head>
<body>
    <div class="header-logo">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/logo.jpg" alt="פ.י. קו הנדסה בע״מ">
    </div>
    <div class="rule"></div>

    <table class="meta">
        <tr>
            <td class="first">
                <div class="label">לכבוד</div>
                <div class="value">{{ data.client_name }}, {{ data.client_address }}</div>
            </td>
            <td class="date">
                <div class="label">תאריך</div>
                <div class="value">{{ data.date }}</div>
            </td>
            <td class="proj">
                <div class="label">פרוייקט</div>
                <div class="value">{{ data.project_number }}</div>
            </td>
        </tr>
    </table>

    <div class="subject">הנדון: אישור {{ data.casting_title }}.</div>

    <div class="summary">{{ data.summary }}</div>
    <div class="notes-block">{{ data.notes }}</div>
    <div class="thanks">תודה רבה.</div>

    {% if data.photo_urls %}
    <div class="photos {% if data.photo_urls|length == 1 %}c1{% elif data.photo_urls|length <= 4 %}c2{% elif data.photo_urls|length <= 9 %}c3{% else %}c4{% endif %}">
        {% for url in data.photo_urls %}
        <img src="{{ url }}" alt="תמונה מהאתר">
        {% endfor %}
    </div>
    {% endif %}

    <div class="signoff">
        בברכה,<br>
        פרוכטמן ישראל — פ.י.קו הנדסה בע"מ<br>
        <img class="signature-img" src="data:image/png;base64,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" alt="חתימה וחותמת">
    </div>

    <div class="page-footer">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/footer.png" alt="פרטי קשר - פ.י.קו הנדסה בע״מ">
    </div>
</body>
</html>
"""


# ============================================================
# הסכם ניהול ופיקוח (שכר טרחה חודשי או סכום כולל, לא שלבי אחוזים) — המודל
# ============================================================
class SupervisionQuoteData(BaseModel):
    date: str                          # 10/06/2026
    quote_number: str                  # "6262-1"
    client_name: str                   # דודו איתן
    client_address: str                # אשדות יעקב איחוד
    client_phone: str = ""
    client_email: str = ""
    client_id_number: str = ""
    project_description: str           # "ניהול ופיקוח בניה תוספת בניה לבית מגורים קיים"
    pre_construction_items: list[str]  # ניהול מקדים — תיאום מכרזים, בדיקת כתבי כמויות...
    supervision_items: list[str]       # פיקוח שוטף — ליווי שטח, מעקב קבלנים...
    monthly_fee: int                   # 6400 — סכום שכר הטרחה: לחודש, או כולל כש-fee_type הוא fixed
    payment_terms_items: list[str] = [
        "תשלום ראשון כמקדמה במעמד מועד החתימה.",
        "תשלום שני בתחילת העבודות באתר.",
        "שאר התשלומים בראשון לכל חודש עד סוף ההסכם.",
        "יש לבצע את התשלום בהעברה בנקאית ולהעביר אישור העברה.",
    ]
    # התאמת ההסכם להיקף העבודה. שדה ריק — הנוסח הרגיל של הסכם על כל הפרויקט
    title: str = ""                    # כותרת ההסכם
    scope_label: str = ""              # תווית מתחת לכותרת — "שלב השלד בלבד"
    scope_text: str = ""               # מה נמסר למפקח, בהמשך ל"הואיל והמזמין מעוניין למסור למפקח את"
    general_note: str = ""             # המשפט על התוכניות והמסמכים
    scope_note: str = ""               # משפט מודגש על גבולות ההסכם — מה הוא לא כולל
    pre_construction_title: str = ""   # כותרת הרשימה הראשונה
    supervision_title: str = ""        # כותרת הרשימה השנייה
    fee_type: str = "monthly"          # monthly — שכר טרחה חודשי, fixed — סכום כולל
    fee_note: str = ""                 # השורה שמתחת לסכום

# ============================================================
# הסכם להזמנת שירותי ניהול ופיקוח — חוזה בעמוד אחד: הצדדים, תיאור הפרויקט,
# שתי רשימות סעיפים, שכר טרחה וחתימות. הנוסח מתאים את עצמו להיקף העבודה:
# כל הפרויקט, שלב השלד בלבד, או היקף אחר שמגיע בשדות.
# ההסכם נכנס לעמוד אחד — אם צריך, הגופן קטן — והחתימות יורדות לתחתית העמוד.
# טקסט לעולם לא נחתך: הסכם שלא נכנס גם בגופן הקטן ביותר ממשיך לעמוד שני.
# פריסה בטבלאות ולא ב-flex, כדי שהעמודות והגבהים יצאו אותו דבר בכל גרסה של WeasyPrint.
# ============================================================
SC_FONTS_URI = (Path(__file__).parent / "fonts").as_uri()
SC_PAGE = {"top": 8, "side": 17, "bottom": 46}
SC_CONTENT_BOTTOM = 297 - SC_PAGE["bottom"]   # סוף אזור התוכן, מראש הדף
SC_MM_PER_PX = 25.4 / 96
# גודל גופן בנק' וגובה שורה — מהרגיל עד הקטן ביותר שעוד נוח לקרוא
SC_FONTS = [(9.8, 1.36), (9.4, 1.33), (9.0, 1.3), (8.6, 1.28)]
SC_SIGNS_TOP = 5                              # הרווח המזערי מעל "ולראיה באו הצדדים על החתום"
SC_LETTERS = ["א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט", "י", "יא", "יב", "יג", "יד", "טו", "טז", "יז", "יח", "יט", "כ"]
SC_TITLE = "הסכם להזמנת שירותי ניהול ופיקוח"
SC_SCOPE_TEXT = "עבודות הניהול והפיקוח על הפרויקט, משלב הביצוע ועד גמר הפרויקט"
SC_GENERAL_NOTE = (
    "הניהול והפיקוח יבוצעו על פי תוכניות האדריכלות וההנדסה שהועברו למפקח במייל. "
    "כל המסמכים הרלוונטיים לביצוע הפרויקט יימסרו למפקח לשם ביצוע עבודתו."
)
SC_FEE = {
    "monthly": {"label": "שכר טרחה חודשי", "note": 'לחודש, לפני מע"מ'},
    "fixed": {"label": "שכר טרחה", "note": 'סכום כולל, לפני מע"מ'},
}

SUPERVISION_CONTRACT_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <style>
        @font-face { font-family: 'Heebo'; font-weight: 400; src: url('{{ fonts }}/Heebo-Regular.ttf'); }
        @font-face { font-family: 'Heebo'; font-weight: 500; src: url('{{ fonts }}/Heebo-Medium.ttf'); }
        @font-face { font-family: 'Heebo'; font-weight: 700; src: url('{{ fonts }}/Heebo-Bold.ttf'); }
        @font-face { font-family: 'Heebo'; font-weight: 800; src: url('{{ fonts }}/Heebo-ExtraBold.ttf'); }
        @page {
            size: A4;
            margin: {{ page.top }}mm {{ page.side }}mm {{ page.bottom }}mm {{ page.side }}mm;
            @bottom-center { content: element(pageFooter); }
        }
        .page-footer { position: running(pageFooter); text-align: center; }
        .page-footer img { width: 165mm; }
        /* כל הגדלים והרווחים האנכיים ב-em — כשהגופן קטן, הכל מתכווץ יחד */
        body {
            font-family: 'Heebo', 'Arial', sans-serif;
            direction: rtl;
            color: #1f2733;
            font-size: {{ font_pt }}pt;
            line-height: {{ line_height }};
            margin: 0;
        }
        table { width: 100%; border-collapse: separate; border-spacing: 0; }
        td { padding: 0; vertical-align: top; }

        .logo { text-align: center; }
        .logo img { width: 76mm; }
        .meta {
            margin-top: 0.43em;
            border-top: 0.5pt solid #c9d2e3;
            border-bottom: 0.5pt solid #c9d2e3;
            font-size: 0.97em;
        }
        .meta td { padding: 0.38em 0; }
        .meta .date { text-align: left; }
        .meta .k { color: #6a7486; }
        .meta .v { font-weight: 700; color: #22408c; }

        .title { text-align: center; margin-top: 1.3em; line-height: 1.2; }
        .title h1 { margin: 0; font-size: 1.84em; font-weight: 800; color: #22408c; }
        .title .bar { display: inline-block; width: 22mm; height: 1.1mm; background: #22408c; margin-top: 0.4em; }
        .title .scope {
            display: inline-block;
            margin-top: 0.35em;
            padding: 0.12em 5mm;
            border: 0.8pt solid #22408c;
            color: #22408c;
            font-weight: 700;
            font-size: 1.12em;
        }
        .lead { text-align: center; margin-top: 0.43em; font-size: 1.05em; }
        .lead .blank { display: inline-block; width: 34mm; border-bottom: 0.6pt solid #1f2733; margin: 0 1.5mm; }

        .parties { margin-top: 0.81em; table-layout: fixed; }
        .gap { width: 6mm; }
        .party {
            border: 0.6pt solid #c9d2e3;
            border-right: 2.4pt solid #22408c;
            background: #f6f8fc;
            padding: 0.52em 4mm 0.58em 4mm;
        }
        .party .tag { font-size: 0.87em; font-weight: 700; color: #22408c; }
        .party .name { font-size: 1.22em; font-weight: 700; line-height: 1.25; }
        .party .det { font-size: 0.94em; color: #4b5567; }

        .recital { margin-top: 0.93em; }
        b { font-weight: 700; }

        .sec { margin-top: 0.98em; }
        .sec-h { margin-bottom: 0.35em; }
        .sec-h td { vertical-align: middle; white-space: nowrap; }
        .sec-h .n { width: 1%; }
        .sec-h .n span {
            display: block;
            font-size: 0.97em;
            width: 1.6em;
            height: 1.6em;
            line-height: 1.6em;
            text-align: center;
            background: #22408c;
            color: #fff;
            font-weight: 700;
        }
        .sec-h .t { width: 1%; padding: 0 2.4mm; font-weight: 700; font-size: 1.17em; color: #22408c; }
        .sec-h .rule div { border-top: 0.5pt solid #c9d2e3; }
        .project { font-weight: 700; font-size: 1.1em; }

        .cols { margin-top: 0.98em; table-layout: fixed; }
        .cols .sec { margin-top: 0; }
        .item { position: relative; padding-right: 6.5mm; margin-bottom: 0.16em; }
        .item .i { position: absolute; right: 0; top: 0; font-weight: 700; color: #22408c; }

        .by { margin-top: 0.7em; padding: 0.35em 4mm; background: #f6f8fc; border-right: 2.4pt solid #22408c; }

        .fee { border: 0.8pt solid #22408c; }
        .fee td { vertical-align: middle; }
        .fee .amount { width: 52mm; background: #22408c; color: #fff; text-align: center; padding: 0.58em 3mm; }
        .fee .amount .lbl, .fee .amount .note { font-size: 0.94em; }
        .fee .amount .num { font-size: 1.84em; font-weight: 800; line-height: 1.12; }
        .fee .terms { padding: 0.7em 4mm; }
        .fee .terms .item:last-child { margin-bottom: 0; }

        .signs { margin-top: {{ signs_top }}mm; page-break-inside: avoid; }
        .signs .witness { text-align: center; font-weight: 700; color: #22408c; margin-bottom: 10mm; }
        .sign-row { table-layout: fixed; }
        .sign-row .gap { width: 22mm; }
        .sign { text-align: center; }
        .sign .line { border-top: 0.7pt solid #1f2733; padding-top: 1.2mm; font-weight: 700; }
        .sign .cap { font-size: 0.9em; color: #6a7486; }
    </style>
</head>
<body>
    {# בראש המסמך, כדי שגם הסכם שגולש לעמוד שני יקבל כותרת תחתונה בשני העמודים #}
    <div class="page-footer">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/footer.png" alt="פרטי קשר - פ.י.קו הנדסה בע״מ">
    </div>

    <div class="logo">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/logo.jpg" alt="פ.י. קו הנדסה בע״מ">
    </div>

    <table class="meta"><tr>
        <td><span class="k">הסכם מס'</span> <span class="v" dir="ltr">{{ data.quote_number }}</span></td>
        <td class="date"><span class="k">תאריך</span> <span class="v" dir="ltr">{{ data.date }}</span></td>
    </tr></table>

    <div class="title">
        <h1>{{ title }}</h1>
        {% if data.scope_label %}<span class="scope">{{ data.scope_label }}</span>{% else %}<span class="bar"></span>{% endif %}
    </div>
    <div class="lead">הסכם זה נערך ונחתם ביום<span class="blank">&nbsp;</span>בין הצדדים:</div>

    <table class="parties"><tr>
        <td class="party">
            <div class="tag">להלן "המזמין"</div>
            <div class="name">{{ data.client_name }}</div>
            <div class="det">{{ data.client_address }}</div>
            {% if data.client_id_number or data.client_phone %}
            <div class="det">
                {%- if data.client_id_number %}ת.ז <span dir="ltr">{{ data.client_id_number }}</span>{% endif %}
                {%- if data.client_id_number and data.client_phone %}, {% endif %}
                {%- if data.client_phone %}טלפון <span dir="ltr">{{ data.client_phone }}</span>{% endif -%}
            </div>
            {% endif %}
            {% if data.client_email %}<div class="det"><span dir="ltr">{{ data.client_email }}</span></div>{% endif %}
        </td>
        <td class="gap"></td>
        <td class="party">
            <div class="tag">להלן "המפקח"</div>
            <div class="name">פ.י. קו הנדסה בע"מ</div>
            <div class="det">קיבוץ מעוז חיים</div>
            <div class="det">לפי תקנות המהנדסים והאדריכלים תש"ח 1958</div>
        </td>
    </tr></table>

    <div class="recital">
        <b>הואיל</b> והמזמין מעוניין למסור למפקח את {{ scope_text }},<br>
        <b>לפיכך הוסכם בין הצדדים כדלקמן:</b>
    </div>

    <div class="sec">
        <table class="sec-h"><tr><td class="n"><span>1</span></td><td class="t">תיאור הפרויקט</td><td class="rule"><div></div></td></tr></table>
        <div class="project">{{ project }}.</div>
        <div>{{ general_note }}</div>
        {% if data.scope_note %}<div><b>{{ data.scope_note }}</b></div>{% endif %}
    </div>

    {% macro items(list) %}
        {% for item in list %}<div class="item"><span class="i">{{ letters[loop.index0] }}.</span>{{ item }}</div>{% endfor %}
    {% endmacro %}
    {% macro section(n, heading, list) %}
        <div class="sec">
            <table class="sec-h"><tr><td class="n"><span>{{ n }}</span></td><td class="t">{{ heading }}</td><td class="rule"><div></div></td></tr></table>
            {{ items(list) }}
        </div>
    {% endmacro %}

    {# שתי רשימות — זו לצד זו. רשימה אחת בלבד — לרוחב העמוד #}
    {% if data.pre_construction_items and data.supervision_items %}
    <table class="cols"><tr>
        <td>{{ section(2, pre_title, data.pre_construction_items) }}</td>
        <td class="gap"></td>
        <td>{{ section(3, sup_title, data.supervision_items) }}</td>
    </tr></table>
    {% elif data.pre_construction_items %}
    {{ section(2, pre_title, data.pre_construction_items) }}
    {% else %}
    {{ section(2, sup_title, data.supervision_items) }}
    {% endif %}

    <div class="by">השירותים המפורטים בהסכם זה יינתנו על ידי המהנדס <b>ישראל פרוכטמן</b>.</div>

    <div class="sec">
        <table class="sec-h"><tr><td class="n"><span>{{ fee_section }}</span></td><td class="t">שכר טרחה ותנאי תשלום</td><td class="rule"><div></div></td></tr></table>
        <table class="fee"><tr>
            <td class="amount">
                <div class="lbl">{{ fee.label }}</div>
                <div class="num">{{ "{:,.0f}".format(data.monthly_fee) }} ₪</div>
                <div class="note">{{ fee.note }}</div>
            </td>
            <td class="terms">{{ items(data.payment_terms_items) }}</td>
        </tr></table>
    </div>

    <div class="signs">
        <div class="witness">ולראיה באו הצדדים על החתום</div>
        <table class="sign-row"><tr>
            <td class="sign">
                <div class="line">המזמין</div>
                <div class="cap">שם, חתימה ותאריך</div>
            </td>
            <td class="gap"></td>
            <td class="sign">
                <div class="line">המפקח</div>
                <div class="cap">פ.י. קו הנדסה בע"מ - חתימה וחותמת</div>
            </td>
        </tr></table>
    </div>
    {# סימון סוף התוכן — לפי המיקום שלו נמדד כמה גובה נשאר בעמוד #}
    <div id="content-end"></div>
</body>
</html>
"""

def render_supervision_contract(quote: SupervisionQuoteData):
    """מחזיר את ההסכם המוכן. עמוד אחד, והחתימות בתחתיתו; רק אם זה בלתי אפשרי — יותר."""
    # autoescape: הסעיפים והתיאורים הם טקסט חופשי — תו כמו < לא אמור לשבור את ה-HTML
    template = Template(SUPERVISION_CONTRACT_TEMPLATE, autoescape=True)
    fee = dict(SC_FEE.get(quote.fee_type, SC_FEE["monthly"]))
    if quote.fee_note.strip():
        fee["note"] = quote.fee_note.strip()
    both_lists = bool(quote.pre_construction_items and quote.supervision_items)
    context = dict(
        data=quote, fonts=SC_FONTS_URI, page=SC_PAGE, letters=SC_LETTERS, fee=fee,
        title=quote.title.strip() or SC_TITLE,
        # הפסיק והנקודה שאחרי הטקסטים האלה מתווספים בתבנית — מורידים מהקלט כדי שלא יצאו כפולים
        scope_text=quote.scope_text.strip().rstrip(',.').strip() or SC_SCOPE_TEXT,
        project=quote.project_description.strip().rstrip('.').strip(),
        general_note=quote.general_note.strip() or SC_GENERAL_NOTE,
        pre_title=quote.pre_construction_title.strip() or "ניהול מקדים",
        sup_title=quote.supervision_title.strip() or "פיקוח",
        fee_section=4 if both_lists else 3,
    )

    def render(font, signs_top):
        html = template.render(**context, font_pt=font[0], line_height=font[1], signs_top=round(signs_top, 1))
        return HTML(string=html).render()

    regular = None   # התוצאה בגופן הרגיל — למקרה שעמוד אחד לא יצא באף גופן
    for font in SC_FONTS:
        doc = render(font, SC_SIGNS_TOP)
        if regular is None:
            regular = doc
        if len(doc.pages) > 1:
            continue
        # נכנס לעמוד אחד: כל הגובה שנשאר עובר אל מעל החתימות, כך שהן יורדות לתחתית העמוד
        end = (getattr(doc.pages[0], "anchors", None) or {}).get("content-end")
        free = SC_CONTENT_BOTTOM - end[1] * SC_MM_PER_PX if end else 0
        if free < 2:
            return doc
        lowered = render(font, SC_SIGNS_TOP + free - 1)
        return lowered if len(lowered.pages) == 1 else doc
    return regular

# ============================================================
# דוח ניהול/פיקוח — ביקור, ישיבה או סיור באתר. גוף הדוח טקסט חופשי,
# אבל הכותרת קבועה ותמיד מלאה: לקוח, יישוב, תאריך, מ.פ.
# הסדר: טקסט, תמונות, חתימה. הדוח נכנס לעמוד אחד — התמונות מקבלות את הגודל הכי גדול
# שנכנס במקום שנשאר בעמוד, ואם גם תמונות קטנות לא נכנסות, הגופן קטן.
# טקסט לעולם לא נחתך: דוח שלא נכנס גם בגופן הקטן ביותר ממשיך לעמוד שני.
# ============================================================
class ManagementReportData(BaseModel):
    date: str = Field(min_length=1)            # 05/10/2026
    project_number: str = Field(min_length=1)  # 6269 / 6262-1
    client_name: str = Field(min_length=1)     # משפחת לזר
    settlement: str = Field(min_length=1)      # מעגן
    subject: str = 'דו"ח ביקור באתר'           # הנדון: <subject>.
    body: str = Field(min_length=1)            # הטקסט החופשי — שבירות השורות נשמרות כמו שהן
    photo_urls: list[str] = []

# מידות במ"מ. התבנית והחישוב שמתחתיה משתמשים באותם מספרים.
MR_PAGE = {"top": 15, "side": 18, "bottom": 50}
MR_CONTENT_W = 210 - 2 * MR_PAGE["side"]
MR_CONTENT_BOTTOM = 297 - MR_PAGE["bottom"]   # סוף אזור התוכן, מראש הדף
MR_MM_PER_PX = 25.4 / 96
# גודל גופן בנק' וגובה שורה — מהרגיל עד הקטן ביותר שעוד נוח לקרוא
MR_FONTS = [(12, 1.5), (11, 1.45), (10.5, 1.4), (10, 1.35), (9.5, 1.3)]
MR_PHOTO_GAP = 3
MR_PHOTO_BORDER = 0.6                # המסגרת של תמונה, משני הצדדים יחד
MR_PHOTOS_TOP = 5                    # הרווח בין הטקסט לבלוק התמונות
MR_PHOTO_MAX_W = {1: 150, 2: 84}     # רוחב מרבי לתמונה לפי מספר התמונות בשורה
MR_PHOTO_MIN_W = 36                  # מתחת לזה התמונה כבר לא מראה כלום
MR_PHOTO_RATIO = 0.68                # גובה חלקי רוחב. עד 0.75 כשיש מקום — היחס של צילום מהטלפון
MR_SIGNOFF_H = 34                    # "בברכה" והחתימה, כולל הרווח שמעליהן
MR_MAX_RENDERS = 12

MANAGEMENT_REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: A4;
            margin: {{ page.top }}mm {{ page.side }}mm {{ page.bottom }}mm {{ page.side }}mm;
            @bottom-center { content: element(pageFooter); }
        }
        .page-footer { position: running(pageFooter); text-align: center; }
        .page-footer img { width: 165mm; }
        body {
            font-family: 'Arial', sans-serif;
            direction: rtl;
            color: #000;
            line-height: {{ line_height }};
            font-size: {{ font_pt }}pt;
        }
        .header-logo { text-align: center; margin-bottom: 14px; }
        .header-logo img { width: 330px; max-width: 100%; }
        .meta-data { display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 10px; }
        .meta-data .to-label { text-decoration: underline; }
        .subject {
            font-weight: bold;
            text-decoration: underline;
            text-align: center;
            font-size: 17pt;
            margin: 16px 0 18px 0;
        }
        .report-body { white-space: pre-line; }
        .photos { margin-top: {{ photos_top }}mm; page-break-inside: avoid; }
        .photos .photos-title { font-weight: bold; margin-bottom: 1mm; }
        {% if photo %}
        /* כל שורת תמונות היא שורה משלה — לא סומכים על גלישת שורות של flex */
        .photo-row { display: flex; justify-content: center; gap: {{ photo.gap }}mm; }
        .photo-row + .photo-row { margin-top: {{ photo.gap }}mm; }
        .photo-row img {
            flex-shrink: 0;
            width: {{ photo.w }}mm;
            height: {{ photo.h }}mm;
            object-fit: cover;
            border: 1px solid #ccc;
        }
        {% endif %}
        .signoff { margin-top: 30px; text-align: left; page-break-inside: avoid; }
        .signoff .greeting { font-size: 13pt; }
        .signature-img { height: 60px; margin-top: 2px; }
    </style>
</head>
<body>
    {# בראש המסמך, כדי שגם דוח שגולש לעמוד שני יקבל כותרת תחתונה בשני העמודים #}
    <div class="page-footer">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/footer.png" alt="פרטי קשר - פ.י.קו הנדסה בע״מ">
    </div>

    <div class="header-logo">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/logo.jpg" alt="פ.י. קו הנדסה בע״מ">
    </div>

    <div class="meta-data">
        <div>
            <span class="to-label">לכבוד:</span><br>
            {{ data.client_name }}<br>
            {{ data.settlement }}
        </div>
        <div>
            תאריך: {{ data.date }}<br>
            מ.פ: {{ data.project_number }}
        </div>
    </div>

    <div class="subject">הנדון: {{ subject }}.</div>

    <div class="report-body">{{ data.body }}</div>

    {% if photo %}
    <div class="photos">
        <div class="photos-title">תמונות מהאתר:</div>
        {% for row in data.photo_urls|batch(photo.cols) %}
        <div class="photo-row">{% for url in row %}<img src="{{ url }}" alt="תמונה מהאתר">{% endfor %}</div>
        {% endfor %}
    </div>
    {% endif %}

    <div class="signoff">
        <div class="greeting">בברכה</div>
        <img class="signature-img" src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/signature.jpg" alt="חתימה וחותמת">
    </div>
    {# סימון סוף התוכן — לפי המיקום שלו נמדד כמה גובה נשאר בעמוד #}
    <div id="content-end"></div>
</body>
</html>
"""

def mr_photo_layout(n: int, avail_mm: float) -> dict:
    """הפריסה שנותנת את התמונות הגדולות ביותר ל-n תמונות בגובה נתון, במ"מ."""
    best = None
    # שתי תמונות ומעלה — לפחות שתיים בשורה, לא טור של תמונות
    for cols in range(min(n, 2), min(n, 4) + 1):
        rows = -(-n // cols)
        row_h = (avail_mm - MR_PHOTO_GAP * (rows - 1)) / rows - MR_PHOTO_BORDER
        # מ"מ אחד נשאר פנוי ברוחב, כדי שעיגול לא ישבור את השורה
        fit_w = (MR_CONTENT_W - MR_PHOTO_GAP * (cols - 1) - 1) / cols - MR_PHOTO_BORDER
        w = min(MR_PHOTO_MAX_W.get(cols, fit_w), fit_w, row_h / MR_PHOTO_RATIO)
        # בשוויון — פחות תמונות בשורה
        if best is None or w > best["w"] + 0.5:
            best = {"cols": cols, "w": w, "row_h": row_h}
    w = math.floor(best["w"] * 10) / 10
    h = math.floor(min(w * 0.75, best["row_h"]) * 10) / 10
    return {"cols": best["cols"], "w": w, "h": h, "gap": MR_PHOTO_GAP}

def render_management_report(report: ManagementReportData, subject: str):
    """מחזיר את המסמך המוכן ואת מספר הפריסות שנדרשו. עמוד אחד; רק אם זה בלתי אפשרי — יותר."""
    # autoescape: גוף הדוח הוא טקסט חופשי — תו כמו < לא אמור לשבור את ה-HTML
    template = Template(MANAGEMENT_REPORT_TEMPLATE, autoescape=True)
    n = len(report.photo_urls)
    renders = 0

    def render(font, photo=None):
        nonlocal renders
        renders += 1
        html = template.render(
            data=report, subject=subject, page=MR_PAGE, photos_top=MR_PHOTOS_TOP,
            font_pt=font[0], line_height=font[1], photo=photo,
        )
        return HTML(string=html).render()

    def title_h(font):
        return font[0] * font[1] * 25.4 / 72 + 1

    def fit(font):
        """מכניס את התמונות בלי להוסיף עמוד. מחזיר את המסמך (None אם לא נכנסו) ואת מספר העמודים של הטקסט לבדו."""
        # קודם בלי התמונות: איפה נגמרים הטקסט והחתימה, כלומר כמה גובה נשאר לתמונות
        doc = render(font)
        pages = len(doc.pages)
        if n == 0:
            return doc, pages
        end = (getattr(doc.pages[-1], "anchors", None) or {}).get("content-end")
        # בלי מדידה מתחילים מהגודל המרבי ויורדים עד שנכנס
        free = MR_CONTENT_BOTTOM - end[1] * MR_MM_PER_PX if end else 170
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

    regular = None   # התוצאה בגופן הרגיל — למקרה שעמוד אחד לא יצא באף גופן
    for font in MR_FONTS:
        if renders >= MR_MAX_RENDERS:
            break
        doc, pages = fit(font)
        if doc and pages == 1:
            return doc, renders
        if font == MR_FONTS[0]:
            regular = doc

    # לא נכנס לעמוד אחד גם בגופן הקטן ביותר — גופן רגיל, כמה שפחות עמודים.
    # התמונות לא נכנסו אחרי הטקסט: הן והחתימה עוברות יחד לעמוד משלהן.
    if regular is None:
        font = MR_FONTS[0]
        own_page = MR_CONTENT_BOTTOM - MR_PAGE["top"] - MR_SIGNOFF_H - MR_PHOTOS_TOP - title_h(font) - 2
        regular = render(font, mr_photo_layout(n, own_page))
    return regular, renders

@app.post("/generate-management-report")
async def generate_management_report(report: ManagementReportData):
    try:
        # הנקודה בסוף הנדון מתווספת בתבנית — מורידים אותה מהקלט כדי שלא תצא כפולה
        subject = report.subject.strip().rstrip('.').strip() or 'דו"ח ביקור באתר'
        doc, renders = render_management_report(report, subject)
        return Response(
            content=doc.write_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'inline; filename="management-report.pdf"',
                "X-Page-Count": str(len(doc.pages)),
                "X-Renders": str(renders),
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-supervision-quote")
async def generate_supervision_quote(quote: SupervisionQuoteData):
    try:
        doc = render_supervision_contract(quote)
        return Response(
            content=doc.write_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'inline; filename="supervision-quote.pdf"',
                "X-Page-Count": str(len(doc.pages)),
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# חשבון לפי הסכם ניהול ופיקוח — שכ"ט חודשי, או תשלום על חשבון סכום כולל
# (בכוונה תבנית נפרדת מ-InvoiceData — שם יש "סה"כ הסכם" חד-פעמי שלא קיים כאן)
# ============================================================
class SupervisionInvoiceData(BaseModel):
    date: str                      # 01/09/2026
    quote_number: str              # "6262-1"
    invoice_number: int            # 3
    client_lines: list[str]        # ["דודו איתן", "אשדות יעקב איחוד"]
    project_description: str
    billing_month_label: str       # "חודש 3 — ספטמבר 2026"
    monthly_fee: int               # 6400 — סכום החשבון לפני מע"מ
    fee_label: str = 'שכ"ט חודשי'  # בהסכם בסכום כולל: "שכר טרחה"
    vat_percent: int = 18
    payment_terms: str = "מזומן / העברה בנקאית"
    due_date: str = ""
    bank_details: str = 'בנק פועלים סניף 717, חשבון 534731, ע"ש פ.י.קו הנדסה בע"מ'

SUPERVISION_INVOICE_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: A4;
            margin: 15mm 18mm 50mm 18mm;
            @bottom-center { content: element(pageFooter); }
        }
        .page-footer { position: running(pageFooter); text-align: center; }
        .page-footer img { width: 165mm; }
        body {
            font-family: 'Arial', sans-serif;
            direction: rtl;
            color: #000;
            line-height: 1.5;
            font-size: 11pt;
        }
        .header-logo { text-align: center; margin-bottom: 18px; }
        .header-logo img { width: 360px; max-width: 100%; }
        .meta-data { display: flex; justify-content: space-between; margin-bottom: 20px; }
        .subject {
            font-weight: bold;
            text-decoration: underline;
            margin: 18px 0 6px 0;
        }
        .billing-month { color: #1e4d6b; font-weight: bold; margin-bottom: 14px; }
        table.amounts { margin-top: 14px; border-collapse: collapse; width: 70%; }
        table.amounts td { padding: 5px 4px; }
        table.amounts .num { text-align: left; direction: ltr; }
        table.amounts .total td { font-weight: bold; border-top: 1px solid #000; }
        .pay-info { margin-top: 22px; }
        .confirm-note { margin-top: 16px; font-weight: bold; }
        .signoff { margin-top: 30px; }
    </style>
</head>
<body>
    <div class="header-logo">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/logo.jpg" alt="פ.י. קו הנדסה בע״מ">
    </div>

    <div class="meta-data">
        <div>
            <strong>לכבוד:</strong><br>
            {% for line in data.client_lines %}{{ line }}<br>{% endfor %}
        </div>
        <div>
            <strong>תאריך:</strong> {{ data.date }}<br>
            <strong>פ:</strong> {{ data.quote_number }}
        </div>
    </div>

    <div class="subject">הנדון: חשבון מס' {{ data.invoice_number }} — הסכם ניהול ופיקוח</div>
    <div>{{ data.project_description }}</div>
    <div class="billing-month">עבור: {{ data.billing_month_label }}</div>

    <table class="amounts">
        <tr>
            <td>{{ data.fee_label }}</td>
            <td class="num">{{ "{:,.0f}".format(data.monthly_fee) }}</td>
            <td></td>
        </tr>
        <tr>
            <td>מע"מ {{ data.vat_percent }}%</td>
            <td class="num">{{ "{:,.0f}".format(vat_amount) }}</td>
            <td></td>
        </tr>
        <tr class="total">
            <td>סה"כ לתשלום</td>
            <td class="num">{{ "{:,.0f}".format(total_with_vat) }}</td>
            <td></td>
        </tr>
    </table>

    <div class="pay-info">
        <strong>מועד תשלום:</strong> {{ data.payment_terms }}{% if data.due_date %} ({{ data.due_date }}){% endif %}<br>
        <strong>ניתן להעברה בנקאית:</strong> {{ data.bank_details }}
    </div>

    <div class="confirm-note">נא לשלוח אישור ביצוע.</div>

    <div class="signoff">
        בכבוד רב,<br>
        פרוכטמן ישראל<br>
        פ.י.קו הנדסה בע"מ.
    </div>

    <div class="page-footer">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/footer.png" alt="פרטי קשר - פ.י.קו הנדסה בע״מ">
    </div>
</body>
</html>
"""

@app.post("/generate-supervision-invoice")
async def generate_supervision_invoice(inv: SupervisionInvoiceData):
    try:
        vat_amount = round(inv.monthly_fee * inv.vat_percent / 100)
        total_with_vat = inv.monthly_fee + vat_amount
        template = Template(SUPERVISION_INVOICE_TEMPLATE)
        rendered_html = template.render(data=inv, vat_amount=vat_amount, total_with_vat=total_with_vat)
        pdf_bytes = HTML(string=rendered_html).write_pdf()
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'inline; filename="supervision-invoice.pdf"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# אישור יציקה עם תמונות בפריים מלא (נקודת קצה לבדיקה, עד אישור). אותו עיצוב ואותו תוכן; התמונות לא נחתכות.
SITE_REPORT_PHOTOS_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <style>
        @font-face { font-family: 'Heebo'; font-weight: 400; src: url('{{ fonts }}/Heebo-Regular.ttf'); }
        @font-face { font-family: 'Heebo'; font-weight: 500; src: url('{{ fonts }}/Heebo-Medium.ttf'); }
        @font-face { font-family: 'Heebo'; font-weight: 700; src: url('{{ fonts }}/Heebo-Bold.ttf'); }
        @page {
            size: A4;
            margin: 15mm 18mm 50mm 18mm;
            @bottom-center { content: element(pageFooter); }
        }
        .page-footer { position: running(pageFooter); text-align: center; }
        .page-footer img { width: 165mm; }
        body {
            font-family: 'Heebo', 'Arial', sans-serif;
            direction: rtl;
            color: #1c2733;
            line-height: 1.45;
            font-size: 11pt;
            /* נעילת גובה התוכן לעמוד אחד + עוגן למיקום החתימה */
            position: relative;
            height: 230mm;
            overflow: hidden;
        }
        .header-logo { text-align: center; margin-bottom: 4px; }
        .header-logo img { width: 300px; max-width: 100%; }
        /* קו כותרת כפול: עבה וכהה, ומתחתיו דק ובהיר */
        .rule { border-top: 2.5px solid #1f3a5f; border-bottom: 0.6px solid #9fb0c3; height: 2px; margin: 2px 0 8px 0; }
        /* פרטי הדוח בטבלה: לכבוד מימין, תאריך ופרויקט משמאל */
        .meta { width: 100%; border-collapse: separate; border: 0.8px solid #cfd9e4; border-radius: 2mm; background: #f4f7fa; margin-bottom: 6px; }
        .meta td { padding: 5px 12px; vertical-align: top; border-right: 0.8px solid #cfd9e4; }
        .meta td.first { border-right: 0; }
        .meta td.date { width: 24%; }
        .meta td.proj { width: 18%; }
        .meta .label { color: #5c6e82; font-size: 9pt; font-weight: 500; }
        .meta .value { font-weight: 700; font-size: 11.5pt; }
        .subject {
            font-weight: 700;
            text-align: center;
            font-size: 14pt;
            color: #1f3a5f;
            border-top: 0.8px solid #1f3a5f;
            border-bottom: 0.8px solid #1f3a5f;
            padding: 4px 0;
            margin: 4px 0 8px 0;
        }
        .summary { margin-bottom: 6px; font-weight: 500; }
        .notes-block {
            white-space: pre-line;
            border-right: 3px solid #1f3a5f;
            padding: 2px 11px 2px 0;
            margin: 4px 0 8px 0;
        }
        .thanks { margin-top: 6px; }
        /* בברכה + שם + חתימה — תמיד בפינה השמאלית-תחתונה של הדף */
        .signoff {
            position: absolute;
            bottom: 0;
            left: 0;
            text-align: left;
            border-top: 0.8px solid #9fb0c3;
            padding-top: 3px;
        }
        /* חתימה וחותמת: PNG חתוך לתוכן, בלי שקיפות (תצוגות שונות לא מציגות שקיפות נכון) */
        .signature-img { height: 15mm; margin-top: 2px; }
        /* כל תמונה במידות היחס שלה, לאורך או לרוחב, בלי חיתוך. המידות מחושבות בקוד לפי הגובה שנשאר מעל החתימה */
        .photos { margin-top: 5mm; }
        .photo-row { display: flex; justify-content: center; gap: 3mm; }
        .photo-row + .photo-row { margin-top: 3mm; }
        .photo-row img { flex-shrink: 0; box-sizing: border-box; border: 0.8px solid #b9c6d4; border-radius: 1.5mm; }
    </style>
</head>
<body>
    <div class="header-logo">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/logo.jpg" alt="פ.י. קו הנדסה בע״מ">
    </div>
    <div class="rule"></div>

    <table class="meta">
        <tr>
            <td class="first">
                <div class="label">לכבוד</div>
                <div class="value">{{ data.client_name }}, {{ data.client_address }}</div>
            </td>
            <td class="date">
                <div class="label">תאריך</div>
                <div class="value">{{ data.date }}</div>
            </td>
            <td class="proj">
                <div class="label">פרוייקט</div>
                <div class="value">{{ data.project_number }}</div>
            </td>
        </tr>
    </table>

    <div class="subject">הנדון: אישור {{ data.casting_title }}.</div>

    <div class="summary">{{ data.summary }}</div>
    <div class="notes-block">{{ data.notes }}</div>
    <div class="thanks">תודה רבה.</div>
    <div id="content-end"></div>

    {% if rows %}
    <div class="photos">
        {% for row in rows %}
        <div class="photo-row">
            {% for p in row %}<img src="{{ p.src }}" style="width: {{ p.w }}mm; height: {{ p.h }}mm;" alt="תמונה מהאתר">{% endfor %}
        </div>
        {% endfor %}
    </div>
    <div id="photos-end"></div>
    {% endif %}

    <div class="signoff" id="signoff-box">
        בברכה,<br>
        פרוכטמן ישראל — פ.י.קו הנדסה בע"מ<br>
        <img class="signature-img" src="data:image/png;base64,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" alt="חתימה וחותמת">
    </div>

    <div class="page-footer">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/footer.png" alt="פרטי קשר - פ.י.קו הנדסה בע״מ">
    </div>
</body>
</html>
"""


def render_site_report_pdf(report):
    """מחזיר (bytes של ה-PDF, מספר התמונות שנכנסו). התמונות מסודרות לפי הגובה שנשאר מעל החתימה, ונמדדות אחרי הרינדור."""
    from site_photos import layout_rows, load_photos  # נטען כאן בלבד, כדי שתקלה בו לא תפיל את בורי

    template = Template(SITE_REPORT_PHOTOS_TEMPLATE)
    mm_per_px = 25.4 / 96
    photos = load_photos(report.photo_urls)

    def render(rows):
        html = template.render(data=report, fonts=SC_FONTS_URI, rows=rows)
        return HTML(string=html).render()

    base = render([])
    anchors = getattr(base.pages[0], "anchors", None) or {}
    end, top = anchors.get("content-end"), anchors.get("signoff-box")
    doc = base
    if photos:
        aspects = [a for _, a in photos]
        # בלי מדידה נשארים עם גובה זהיר
        limit_mm = top[1] * mm_per_px - 2 if top else None
        avail = (limit_mm - end[1] * mm_per_px - 5) if (top and end) else 85.0
        for _ in range(5):
            rows = [[{"src": photos[p["index"]][0], "w": p["w"], "h": p["h"]} for p in row] for row in layout_rows(aspects, avail)]
            doc = render(rows)
            pe = (getattr(doc.pages[-1], "anchors", None) or {}).get("photos-end")
            if limit_mm is None or pe is None or pe[1] * mm_per_px <= limit_mm:
                break
            avail -= (pe[1] * mm_per_px - limit_mm) + 2
    return doc.write_pdf(), len(photos)

@app.post("/generate-site-report-v2")
async def generate_site_report_v2(report: SiteReportData):
    try:
        pdf_bytes, photos_used = render_site_report_pdf(report)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'inline; filename="site-report.pdf"', "x-photos-used": str(photos_used)},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-site-report")
async def generate_site_report(report: SiteReportData):
    try:
        template = Template(SITE_REPORT_TEMPLATE)
        rendered_html = template.render(data=report, fonts=SC_FONTS_URI)
        pdf_bytes = HTML(string=rendered_html).write_pdf()
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'inline; filename="site-report.pdf"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-invoice")
async def generate_invoice(inv: InvoiceData):
    try:
        # חישוב מע"מ וסה"כ בקוד — אף פעם לא מוזן ידנית, כדי שלא יצא חשבון שגוי
        vat_amount = round(inv.payment_amount * inv.vat_percent / 100)
        total_with_vat = inv.payment_amount + vat_amount

        template = Template(INVOICE_TEMPLATE)
        rendered_html = template.render(data=inv, vat_amount=vat_amount, total_with_vat=total_with_vat)
        pdf_bytes = HTML(string=rendered_html).write_pdf()

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'inline; filename="invoice.pdf"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-quote")
async def generate_quote(quote: EngineeringQuoteData):
    try:
        # הזנת הנתונים לתוך ה-HTML
        template = Template(HTML_TEMPLATE)
        rendered_html = template.render(data=quote)

        # יצירת ה-PDF כ-bytes (write_pdf ללא שם קובץ מחזיר את התוכן)
        pdf_bytes = HTML(string=rendered_html).write_pdf()

        # החזרת קובץ ה-PDF עצמו ללקוח (ולא שם קובץ).
        # שם הקובץ ב-header חייב להיות באנגלית בלבד — headers ב-HTTP הם latin-1,
        # ושם עם עברית (כמו "פ6300") גורם לקריסה. השם האמיתי נקבע בעת השמירה ב-Supabase.
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'inline; filename="quote.pdf"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
