"""חשבון תוספת ושינוי: עבודה נוספת שאינה חלק מהצעת המחיר המקורית.

נפרד לגמרי מ-/generate-invoice: אין "שכ"ט כללי", אין "תשלום חלקי" ואין שלבי תשלום. זה חשבון ותשלום נוספים,
בלי קשר להצעה. מספר ההצעה (project_number) מופיע רק כהפניה לפרויקט.
הסכום מחושב בפיקו, בפונקציה generate-extra-work-invoice-pdf. כאן המע"מ והסה"כ מחושבים שוב מאותו סכום, בחשבון שלמים
(מעוגל כלפי מעלה במחצית, כמו בפיקו ובמסד): round של פייתון מעגל למספר הזוגי ולא היה מתאים.
"""
from jinja2 import Template
from pydantic import BaseModel


class ExtraWorkInvoiceData(BaseModel):
    date: str                      # 12/11/2026
    project_number: str            # 6270
    invoice_number: int            # מספר התוספת בפרויקט: 1, 2, 3
    client_lines: list[str]        # שורות "לכבוד"
    description: str               # מה העבודה הנוספת
    hours: float | None = None     # שעות עבודה. אם אין, זה סכום קבוע
    hourly_rate: float | None = None
    payment_amount: int            # הסכום לפני מע"מ
    vat_percent: int = 18
    payment_terms: str = "מזומן"
    due_date: str = ""
    bank_details: str = 'בנק פועלים סניף 717, חשבון 534731, ע"ש פ.י.קו הנדסה בע"מ'


def vat_of(amount: int, vat_percent: int) -> int:
    """מע"מ בשקלים שלמים, מחצית כלפי מעלה"""
    return (amount * vat_percent + 50) // 100


def fmt_hours(h: float) -> str:
    """4.0 -> 4, 1.5 -> 1.5"""
    return f"{h:.2f}".rstrip("0").rstrip(".")


EXTRA_WORK_INVOICE_TEMPLATE = """
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
        .separate-note { margin-top: 4px; }
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

    <div class="subject">הנדון: חשבון עבודה נוספת מס' {{ data.invoice_number }}</div>

    <div>{{ data.description }}</div>
    <div class="separate-note">עבודה נוספת מעבר להצעת המחיר המקורית, ולכן חשבון נפרד.</div>

    <table class="amounts">
        {% if data.hours %}
        <tr>
            <td>{{ hours_text }} שעות עבודה</td>
            <td class="num">{{ "{:,.0f}".format(data.hourly_rate) }} לשעה</td>
            <td></td>
        </tr>
        {% endif %}
        <tr>
            <td>סכום לפני מע"מ</td>
            <td class="num">{{ "{:,.0f}".format(data.payment_amount) }}</td>
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
        <strong>מועד תשלום:</strong> {{ data.payment_terms }}{% if data.due_date %} עד {{ data.due_date }}{% endif %}<br>
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


def render_extra_work_invoice_html(inv: ExtraWorkInvoiceData) -> str:
    vat_amount = vat_of(inv.payment_amount, inv.vat_percent)
    return Template(EXTRA_WORK_INVOICE_TEMPLATE).render(
        data=inv,
        vat_amount=vat_amount,
        total_with_vat=inv.payment_amount + vat_amount,
        hours_text=fmt_hours(inv.hours) if inv.hours else "",
    )


def render_extra_work_invoice(inv: ExtraWorkInvoiceData) -> bytes:
    # weasyprint נטען כאן ולא בראש הקובץ: כך אפשר לבדוק את ה-HTML והחישוב גם בלעדיו
    from weasyprint import HTML

    return HTML(string=render_extra_work_invoice_html(inv)).write_pdf()
