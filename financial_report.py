"""דוח כספי: נתונים מסודרים ← PDF בעיצוב המשרד. הנתונים והסכומים מחושבים בצד של פיקו; כאן רק תצוגה."""
from pathlib import Path

from jinja2 import Template
from pydantic import BaseModel
from weasyprint import HTML

FONTS_URI = (Path(__file__).parent / "fonts").as_uri()
ASSETS = "https://sldbtxhfmdhkllmfwusw.supabase.co/storage/v1/object/public/quotes/assets"


class Card(BaseModel):
    label: str
    value: str


class Section(BaseModel):
    title: str
    summary: str = ""          # שורת סיכום מתחת לכותרת, למשל הסכום הכולל של הסעיף
    headers: list[str] = []
    rows: list[list[str]] = []
    more: str = ""             # "ועוד N נוספים" כשהרשימה קוצרה
    empty_text: str = "אין רישומים"


class FinancialReportData(BaseModel):
    title: str
    subtitle: str = ""
    note: str = ""
    cards: list[Card] = []
    sections: list[Section] = []
    total_label: str = ""
    total_value: str = ""
    total_detail: str = ""


TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
    @font-face { font-family: 'Heebo'; font-weight: 400; src: url('{{ fonts }}/Heebo-Regular.ttf'); }
    @font-face { font-family: 'Heebo'; font-weight: 500; src: url('{{ fonts }}/Heebo-Medium.ttf'); }
    @font-face { font-family: 'Heebo'; font-weight: 700; src: url('{{ fonts }}/Heebo-Bold.ttf'); }
    @page { size: A4; margin: 14mm 16mm 16mm 16mm; @bottom-center { content: element(pageFooter); } }
    .page-footer { position: running(pageFooter); text-align: center; }
    .page-footer img { width: 150mm; }
    body { font-family: 'Heebo', 'Arial', sans-serif; direction: rtl; color: #1f2733; font-size: 10pt; line-height: 1.4; margin: 0; }
    table { width: 100%; border-collapse: collapse; }
    .logo { text-align: center; }
    .logo img { width: 62mm; }
    h1 { text-align: center; font-size: 19pt; font-weight: 800; margin: 3mm 0 0 0; color: #16315c; }
    .sub { text-align: center; color: #5a6578; font-size: 10.5pt; margin: 1mm 0 0 0; }
    .rule { border: 0; border-top: 0.6pt solid #16315c; border-bottom: 0.6pt solid #16315c; height: 1.2pt; margin: 3mm 0 4mm 0; }
    .note { color: #5a6578; font-size: 9pt; margin: 0 0 3mm 0; }
    .cards td { width: 25%; padding: 0 0 0 3mm; }
    .cards td:last-child { padding-left: 0; }
    .card { border: 0.6pt solid #c9d2e3; border-radius: 2mm; padding: 2.5mm 3mm; background: #f5f8fd; }
    .card .l { font-size: 8.5pt; color: #5a6578; }
    .card .v { font-size: 13pt; font-weight: 700; color: #16315c; margin-top: 0.5mm; }
    .sec { margin-top: 6mm; }
    .sec h2 { font-size: 12pt; font-weight: 700; margin: 0; color: #16315c; border-bottom: 0.6pt solid #c9d2e3; padding-bottom: 1mm; }
    .sec .s { font-size: 10pt; font-weight: 500; margin: 1.5mm 0 1.5mm 0; }
    .sec table { margin-top: 1mm; }
    .sec th { background: #e8eef9; text-align: right; font-weight: 700; font-size: 9pt; padding: 1.4mm 2mm; }
    .sec td { padding: 1.3mm 2mm; border-bottom: 0.4pt solid #e1e6f0; font-size: 9.5pt; }
    .sec tr { page-break-inside: avoid; }
    .sec thead { display: table-header-group; }
    .more, .empty { color: #5a6578; font-size: 9pt; margin-top: 1.5mm; }
    .total { margin-top: 7mm; border: 0.8pt solid #16315c; border-radius: 2mm; padding: 3mm 4mm; page-break-inside: avoid; }
    .total .l { font-size: 10.5pt; font-weight: 500; }
    .total .v { font-size: 17pt; font-weight: 800; color: #16315c; }
    .total .d { font-size: 9pt; color: #5a6578; margin-top: 0.5mm; }
    .num { white-space: nowrap; }
</style>
</head>
<body>
<div class="page-footer"><img src="{{ assets }}/footer.png" alt=""></div>
<div class="logo"><img src="{{ assets }}/logo.jpg" alt="פ.י. קו הנדסה בע״מ"></div>
<h1>{{ data.title }}</h1>
{% if data.subtitle %}<p class="sub">{{ data.subtitle }}</p>{% endif %}
<div class="rule"></div>
{% if data.note %}<p class="note">{{ data.note }}</p>{% endif %}
{% if data.cards %}
<table class="cards"><tr>
{% for c in data.cards %}<td><div class="card"><div class="l">{{ c.label }}</div><div class="v">{{ c.value }}</div></div></td>{% endfor %}
</tr></table>
{% endif %}
{% for s in data.sections %}
<div class="sec">
    <h2>{{ s.title }}</h2>
    {% if s.summary %}<div class="s">{{ s.summary }}</div>{% endif %}
    {% if s.rows %}
    <table>
        {% if s.headers %}<thead><tr>{% for h in s.headers %}<th>{{ h }}</th>{% endfor %}</tr></thead>{% endif %}
        <tbody>{% for r in s.rows %}<tr>{% for cell in r %}<td class="{{ 'num' if loop.last else '' }}">{{ cell }}</td>{% endfor %}</tr>{% endfor %}</tbody>
    </table>
    {% else %}<div class="empty">{{ s.empty_text }}</div>{% endif %}
    {% if s.more %}<div class="more">{{ s.more }}</div>{% endif %}
</div>
{% endfor %}
{% if data.total_label %}
<div class="total">
    <div class="l">{{ data.total_label }}</div>
    <div class="v">{{ data.total_value }}</div>
    {% if data.total_detail %}<div class="d">{{ data.total_detail }}</div>{% endif %}
</div>
{% endif %}
</body>
</html>
"""


def render_financial_report(data: FinancialReportData):
    # autoescape: שמות לקוחות הם טקסט חופשי
    html = Template(TEMPLATE, autoescape=True).render(data=data, fonts=FONTS_URI, assets=ASSETS)
    return HTML(string=html).render()
