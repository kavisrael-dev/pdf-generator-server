import math
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
from weasyprint import HTML
from jinja2 import Template

from financial_report import FinancialReportData, render_financial_report

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

@app.post("/generate-financial-report")
async def generate_financial_report(report: FinancialReportData):
    try:
        doc = render_financial_report(report)
        return Response(
            content=doc.write_pdf(),
            media_type="application/pdf",
            headers={"Content-Disposition": 'inline; filename="financial-report.pdf"', "X-Page-Count": str(len(doc.pages))},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


# אישור יציקה: עיצוב מקצועי, ותמונות בפריים מלא (לאורך או לרוחב, בלי חיתוך) בעמוד אחד. ראו site_photos.py.
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
        /* חתימה וחותמת: סריקה חדה (2000 פיקסלים), חתוכה לתוכן ובלי שקיפות, כדי שתודפס חדה ולא תכסה דבר */
        .signature-img { height: 17mm; margin-top: 2px; }
        /* כל תמונה במידות היחס שלה, לאורך או לרוחב, בלי חיתוך. המידות מחושבות בקוד לפי הגובה שנשאר מעל החתימה */
        .photos { margin-top: 5mm; }
        .photo-row { display: flex; justify-content: center; gap: 3mm; }
        .photo-row + .photo-row { margin-top: 3mm; }
        .photo-row img { flex-shrink: 0; object-fit: contain; box-sizing: border-box; border: 0.8px solid #b9c6d4; border-radius: 1.5mm; }
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

    {% if data.summary %}<div class="summary">{{ data.summary }}</div>{% endif %}
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
        <img class="signature-img" src="data:image/jpeg;base64,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" alt="חתימה וחותמת">
    </div>

    <div class="page-footer">
        <img src="https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets/footer.png" alt="פרטי קשר - פ.י.קו הנדסה בע״מ">
    </div>
</body>
</html>
"""


def site_report_fallback_rows(urls):
    """אם הסידור החדש נכשל: תמונות בתיבות קבועות, שתיים בשורה, בלי חיתוך. הדוח לא נכשל בגלל תמונות."""
    clean = [u for u in list(urls)[:12] if isinstance(u, str) and u.strip()]
    rows = []
    for i in range(0, len(clean), 2):
        rows.append([{"src": u, "w": 74.0, "h": 50.0} for u in clean[i:i + 2]])
    return rows


def render_site_report_pdf(report):
    try:
        return render_site_report_pdf_fitted(report)
    except Exception as e:
        print(f"site report photo layout failed, using fallback: {e}")
        html = Template(SITE_REPORT_TEMPLATE).render(data=report, fonts=SC_FONTS_URI, rows=site_report_fallback_rows(report.photo_urls))
        return HTML(string=html).write_pdf(), len(report.photo_urls)


def render_site_report_pdf_fitted(report):
    """מחזיר (bytes של ה-PDF, מספר התמונות שנכנסו). התמונות מסודרות לפי הגובה שנשאר מעל החתימה, ונמדדות אחרי הרינדור."""
    from site_photos import layout_rows, load_photos  # נטען כאן בלבד, כדי שתקלה בו לא תפיל את בורי

    template = Template(SITE_REPORT_TEMPLATE)
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

@app.post("/generate-site-report")
async def generate_site_report(report: SiteReportData):
    try:
        pdf_bytes, photos_used = render_site_report_pdf(report)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": 'inline; filename="site-report.pdf"', "x-photos-used": str(photos_used)},
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
