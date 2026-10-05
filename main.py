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
    monthly_fee: int                   # 6400
    payment_terms_items: list[str] = [
        "תשלום ראשון כמקדמה במעמד מועד החתימה.",
        "תשלום שני בתחילת העבודות באתר.",
        "שאר התשלומים בראשון לכל חודש עד סוף ההסכם.",
        "יש לבצע את התשלום בהעברה בנקאית ולהעביר אישור העברה.",
    ]

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
# דוח ניהול/פיקוח — ביקור, ישיבה או סיור באתר. גוף הדוח טקסט חופשי,
# אבל הכותרת קבועה ותמיד מלאה: לקוח, יישוב, תאריך, מ.פ.
# בניגוד לאישור יציקה: בלי נוסח קבוע ובלי נעילה לעמוד אחד — דוח ישיבה יכול להיות ארוך.
# ============================================================
class ManagementReportData(BaseModel):
    date: str = Field(min_length=1)            # 05/10/2026
    project_number: str = Field(min_length=1)  # 6269 / 6262-1
    client_name: str = Field(min_length=1)     # משפחת לזר
    settlement: str = Field(min_length=1)      # מעגן
    subject: str = 'דו"ח ביקור באתר'           # הנדון: <subject>.
    body: str = Field(min_length=1)            # הטקסט החופשי — שבירות השורות נשמרות כמו שהן
    photo_urls: list[str] = []

MANAGEMENT_REPORT_TEMPLATE = """
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
            font-size: 12pt;
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
        .signoff { margin-top: 30px; text-align: left; page-break-inside: avoid; }
        .signoff .greeting { font-size: 13pt; }
        .signature-img { height: 60px; margin-top: 2px; }
        .photos { margin-top: 18px; text-align: center; }
        .photos .photos-title { font-weight: bold; text-align: right; margin-bottom: 4px; }
        .photos img {
            display: inline-block;
            width: 76mm;
            height: 52mm;
            object-fit: cover;
            border: 1px solid #ccc;
            margin: 1.5mm;
        }
        .photos.single img { width: 150mm; height: 100mm; }
    </style>
</head>
<body>
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

    <div class="signoff">
        <div class="greeting">בברכה</div>
        <img class="signature-img" src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/signature.jpg" alt="חתימה וחותמת">
    </div>

    {% if data.photo_urls %}
    <div class="photos{% if data.photo_urls|length == 1 %} single{% endif %}">
        <div class="photos-title">תמונות מהאתר:</div>
        {% for url in data.photo_urls %}<img src="{{ url }}" alt="תמונה מהאתר">{% endfor %}
    </div>
    {% endif %}

    <div class="page-footer">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/footer.png" alt="פרטי קשר - פ.י.קו הנדסה בע״מ">
    </div>
</body>
</html>
"""

@app.post("/generate-management-report")
async def generate_management_report(report: ManagementReportData):
    try:
        # הנקודה בסוף הנדון מתווספת בתבנית — מורידים אותה מהקלט כדי שלא תצא כפולה
        subject = report.subject.strip().rstrip('.').strip() or 'דו"ח ביקור באתר'
        # autoescape: גוף הדוח הוא טקסט חופשי — תו כמו < לא אמור לשבור את ה-HTML
        template = Template(MANAGEMENT_REPORT_TEMPLATE, autoescape=True)
        rendered_html = template.render(data=report, subject=subject)
        pdf_bytes = HTML(string=rendered_html).write_pdf()
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'inline; filename="management-report.pdf"'},
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
