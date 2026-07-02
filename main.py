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
    architect_name: str
    project_location: str
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
            margin: 15mm 18mm 26mm 18mm;
            @bottom-center {
                content: "פרוכטמן ישראל | פ.י.קו הנדסה בע\\"מ.\\n kavisrael@gmail.com | 050-7568472 | 04-6064455\\n קיבוץ מעוז חיים, ד.נ. עמק המעיינות, 1084500 | www.kav28.co.il";
                font-size: 10pt;
                font-family: 'Arial', sans-serif;
                white-space: pre-line;
                text-align: center;
                border-top: 1px solid #ccc;
                padding-top: 10px;
            }
        }
        body {
            font-family: 'Arial', sans-serif;
            direction: rtl;
            color: #000;
            line-height: 1.4;
            font-size: 11pt;
        }
        .header-logo {
            text-align: center;
            margin-bottom: 18px;
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
            margin-bottom: 20px;
        }
        .subject {
            font-weight: bold;
            text-decoration: underline;
            text-align: center;
            margin-bottom: 12px;
        }
        .section-title {
            font-weight: bold;
            margin-top: 15px;
        }
        ul.scope-list, ul.milestone-list {
            list-style-type: none;
            padding-right: 0;
            margin-top: 5px;
        }
        .price {
            font-weight: bold;
            font-size: 12pt;
            margin-top: 20px;
        }
        .milestone-table {
            width: 80%;
            margin-top: 10px;
            border-collapse: collapse;
        }
        .milestone-table td {
            padding: 4px;
        }
        .notes {
            margin-top: 16px;
            font-size: 10pt;
        }
        .signature-area {
            margin-top: 28px;
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
        על פי תוכניות להצעת מחיר שהועברו במייל האדריכל/ית {{ data.architect_name }}.<br>
        המגרש ממוקם ב{{ data.project_location }}
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

    <div style="margin-top: 22px;">
        בברכה,<br>
        פרוכטמן ישראל<br>
        פ.י.קו הנדסה בע"מ.
    </div>
</body>
</html>
"""

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
