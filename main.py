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

SITE_REPORT_TEMPLATE = """
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
            line-height: 1.3;
            font-size: 11pt;
            /* נעילת גובה התוכן לעמוד אחד + עוגן למיקום החתימה */
            position: relative;
            height: 230mm;
            overflow: hidden;
        }
        .header-logo { text-align: center; margin-bottom: 8px; }
        .header-logo img { width: 330px; max-width: 100%; }
        .meta-data { display: flex; justify-content: space-between; margin-bottom: 8px; }
        .subject {
            font-weight: bold;
            text-decoration: underline;
            text-align: center;
            font-size: 13pt;
            margin: 8px 0 8px 0;
        }
        .notes-block { margin-top: 4px; white-space: pre-line; }
        /* בברכה + שם + חתימה — תמיד בפינה השמאלית-תחתונה של הדף */
        .signoff {
            position: absolute;
            bottom: 0;
            left: 0;
            text-align: left;
        }
        .signature-img { height: 52px; margin-top: 2px; }
        .photos { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 3mm; justify-content: center; }
        .photos img {
            width: 76mm;
            height: 48mm;
            object-fit: cover;
            border: 1px solid #ccc;
        }
        .photos.single img {
            width: 150mm;
            height: 94mm;
        }
    </style>
</head>
<body>
    <div class="header-logo">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/logo.jpg" alt="פ.י. קו הנדסה בע״מ">
    </div>

    <div class="meta-data">
        <div>
            <strong>לכבוד:</strong> {{ data.client_name }}, {{ data.client_address }}
        </div>
        <div>
            <strong>תאריך:</strong> {{ data.date }}<br>
            <strong>פרוייקט:</strong> {{ data.project_number }}
        </div>
    </div>

    <div class="subject">הנדון: אישור {{ data.casting_title }}.</div>

    <div>{{ data.summary }}</div>
    <div class="notes-block">{{ data.notes }}</div>
    <div>תודה רבה.</div>

    {% if data.photo_urls %}
    <div class="photos{% if data.photo_urls|length == 1 %} single{% endif %}">
        {% for url in data.photo_urls %}
        <img src="{{ url }}" alt="תמונה מהאתר">
        {% endfor %}
    </div>
    {% endif %}

    <div class="signoff">
        בברכה,<br>
        פרוכטמן ישראל — פ.י.קו הנדסה בע"מ<br>
        <img class="signature-img" src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/signature.jpg" alt="חתימה וחותמת">
    </div>

    <div class="page-footer">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/footer.png" alt="פרטי קשר - פ.י.קו הנדסה בע״מ">
    </div>
</body>
</html>
"""

# ============================================================
# הצעת ניהול ופיקוח (שכ"ט חודשי קבוע, לא שלבי אחוזים) — מודל ותבנית
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

SUPERVISION_QUOTE_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <style>
        @page {
            size: A4;
            margin: 12mm 16mm 46mm 16mm;
            @bottom-center { content: element(pageFooter); }
        }
        .page-footer { position: running(pageFooter); text-align: center; }
        .page-footer img { width: 165mm; }
        body {
            font-family: 'Arial', sans-serif;
            direction: rtl;
            color: #1a1a1a;
            line-height: 1.28;
            font-size: 10pt;
            position: relative;
            height: 232mm;
            overflow: hidden;
        }
        .header-logo { text-align: center; margin-bottom: 6px; }
        .header-logo img { width: 300px; max-width: 100%; }
        .meta-data {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            padding-bottom: 6px;
            border-bottom: 1.5px solid #1e4d6b;
        }
        .meta-data .label { color: #1e4d6b; font-weight: bold; }
        .title-block {
            text-align: center;
            margin-bottom: 10px;
        }
        .title-block .main-title {
            font-size: 15pt;
            font-weight: bold;
            color: #1e4d6b;
            letter-spacing: 0.3px;
        }
        .title-block .subtitle {
            font-size: 10.5pt;
            margin-top: 3px;
            color: #333;
        }
        .columns {
            display: flex;
            gap: 6mm;
            margin-top: 8px;
        }
        .col { flex: 1; }
        .col-header {
            background: #1e4d6b;
            color: #fff;
            font-weight: bold;
            font-size: 10.5pt;
            padding: 4px 8px;
            border-radius: 3px 3px 0 0;
        }
        .col-body {
            border: 1px solid #cdd8de;
            border-top: none;
            padding: 6px 8px;
            border-radius: 0 0 3px 3px;
            min-height: 100%;
        }
        ol.task-list {
            margin: 0;
            padding-right: 16px;
        }
        ol.task-list li { margin-bottom: 3px; }
        .bottom-row {
            display: flex;
            gap: 6mm;
            margin-top: 10px;
            align-items: stretch;
        }
        .price-box {
            flex: 0 0 30%;
            border: 1.5px solid #1e4d6b;
            border-radius: 4px;
            padding: 8px 10px;
            text-align: center;
            align-self: center;
        }
        .price-box .amount {
            font-size: 14pt;
            font-weight: bold;
            color: #1e4d6b;
        }
        .price-box .amount-note { font-size: 9.5pt; color: #555; margin-top: 1px; }
        .payment-section { flex: 1; }
        .payment-section ol.task-list li { margin-bottom: 2px; }
        .signature-area {
            position: absolute;
            bottom: 6mm;
            right: 16mm;
            left: 16mm;
            display: flex;
            justify-content: space-between;
        }
        .signature-box {
            width: 45%;
            text-align: center;
        }
        .signature-box .role { font-weight: bold; margin-bottom: 22px; }
        .signature-box .line { border-top: 1px solid #000; padding-top: 3px; font-size: 9pt; color: #555; }
    </style>
</head>
<body>
    <div class="header-logo">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/logo.jpg" alt="פ.י. קו הנדסה בע״מ">
    </div>

    <div class="meta-data">
        <div>
            <span class="label">לכבוד:</span> {{ data.client_name }}<br>
            {{ data.client_address }}<br>
            {% if data.client_phone %}טלפון: <span dir="ltr">{{ data.client_phone }}</span><br>{% endif %}
            {% if data.client_email %}מייל: <span dir="ltr">{{ data.client_email }}</span><br>{% endif %}
            {% if data.client_id_number %}ת.ז: <span dir="ltr">{{ data.client_id_number }}</span>{% endif %}
        </div>
        <div style="text-align: left;">
            <span class="label">תאריך:</span> {{ data.date }}<br>
            <span class="label">מספר:</span> {{ data.quote_number }}
        </div>
    </div>

    <div class="title-block">
        <div class="main-title">הסכם ניהול ופיקוח</div>
        <div class="subtitle">{{ data.project_description }}</div>
    </div>

    <div class="columns">
        <div class="col">
            <div class="col-header">ניהול מקדים</div>
            <div class="col-body">
                <ol class="task-list">
                    {% for item in data.pre_construction_items %}
                    <li>{{ item }}</li>
                    {% endfor %}
                </ol>
            </div>
        </div>
        <div class="col">
            <div class="col-header">פיקוח שוטף</div>
            <div class="col-body">
                <ol class="task-list">
                    {% for item in data.supervision_items %}
                    <li>{{ item }}</li>
                    {% endfor %}
                </ol>
            </div>
        </div>
    </div>

    <div class="bottom-row">
        <div class="price-box">
            <div class="amount">{{ "{:,.0f}".format(data.monthly_fee) }} ₪ לחודש</div>
            <div class="amount-note">לפני מע"מ</div>
        </div>
        <div class="payment-section">
            <div class="col-header">שלבי ותנאי התשלום</div>
            <div class="col-body">
                <ol class="task-list">
                    {% for item in data.payment_terms_items %}
                    <li>{{ item }}</li>
                    {% endfor %}
                </ol>
            </div>
        </div>
    </div>

    <div class="signature-area">
        <div class="signature-box">
            <div class="role">המזמין</div>
            <div class="line">חתימה + ת.ז</div>
        </div>
        <div class="signature-box">
            <div class="role">המתכנן — פ.י.קו הנדסה בע"מ</div>
            <div class="line">חתימה</div>
        </div>
    </div>

    <div class="page-footer">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/footer.png" alt="פרטי קשר - פ.י.קו הנדסה בע״מ">
    </div>
</body>
</html>
"""

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

@app.post("/generate-supervision-contract")
async def generate_supervision_contract(quote: SupervisionQuoteData):
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

@app.post("/generate-supervision-quote")
async def generate_supervision_quote(quote: SupervisionQuoteData):
    try:
        template = Template(SUPERVISION_QUOTE_TEMPLATE)
        rendered_html = template.render(data=quote)
        pdf_bytes = HTML(string=rendered_html).write_pdf()
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'inline; filename="supervision-quote.pdf"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# חשבון חודשי לפי הסכם ניהול ופיקוח — שכ"ט חודשי קבוע, בלי "שכ"ט כללי"
# (בכוונה תבנית נפרדת מ-InvoiceData — שם יש "סה"כ הסכם" חד-פעמי שלא קיים כאן)
# ============================================================
class SupervisionInvoiceData(BaseModel):
    date: str                      # 01/09/2026
    quote_number: str              # "6262-1"
    invoice_number: int            # 3
    client_lines: list[str]        # ["דודו איתן", "אשדות יעקב איחוד"]
    project_description: str
    billing_month_label: str       # "חודש 3 — ספטמבר 2026"
    monthly_fee: int               # 6400
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
            <td>שכ"ט חודשי</td>
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

@app.post("/generate-site-report")
async def generate_site_report(report: SiteReportData):
    try:
        template = Template(SITE_REPORT_TEMPLATE)
        rendered_html = template.render(data=report)
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
