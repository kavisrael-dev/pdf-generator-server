from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
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
    subject: str
    work_description: str
    architect_name: str = ""       # אופציונלי — רק כשיש אדריכל/ית חיצוני/ת
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
            {{ data.client_address }}
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

    <div class="subject">הנדון: חשבון חלקי מס' {{ data.invoice_number }}</div>

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
# ============================================================
# דוח ביקור באתר (אישור יציקה) — מודל ותבנית
# ============================================================
class SiteReportData(BaseModel):
    date: str                      # 10/11/2025
    project_number: str            # 5070
    client_name: str               # משפחת ברדן
    client_address: str            # מרחביה
    casting_title: str             # "יציקת יסודות" / "יציקה על קורות עץ"
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
        .photos { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 3mm; }
        .photos img {
            width: 76mm;
            height: 48mm;
            object-fit: cover;
            border: 1px solid #ccc;
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
    <div class="photos">
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

@app.post("/generate-quote")
async def generate_quote(quote: EngineeringQuoteData):
    try:
        # הזנת הנתונים לתוך ה-HTML
        template = Template(HTML_TEMPLATE)
        rendered_html = template.render(data=quote)

        # יצירת ה-PDF כ-bytes (write_pdf ללא שם קובץ מחזיר את התוכן)
        pdf_bytes = HTML(string=rendered_html).write_pdf()

        # החזרת קובץ ה-PDF עצמו ללקוח (שם קובץ באנגלית בלבד — headers הם latin-1)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'inline; filename="quote.pdf"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
