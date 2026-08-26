import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.colors import HexColor, white
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit, ImageReader

PAGE_W, PAGE_H = letter
MARGIN = 40
CONTENT_W = PAGE_W - 2 * MARGIN

FOREST = HexColor('#1e4a3a')
TERRACOTTA = HexColor('#d99562')
LABEL_C = HexColor('#3f6657')
DARK = HexColor('#222222')
GRAY = HexColor('#666666')
LIGHT = HexColor('#d9d9d9')
BOXFILL = HexColor('#f4f1ec')

DISCLOSURE = (
    'By signing below, each of the above listed Business Applicant and Principal Owner '
    '(individually and collectively, "you") authorize Vestix Financial ("VESTIX FINANCIAL") '
    'and each of its representatives, successors, assigns and designees that may be involved '
    'with or acquire purchases of future receivables including Merchant Cash Advance '
    'transactions ("Recipients") to obtain consumer or personal and business reports and '
    'other information about you, including credit card processor statements and bank '
    'statements, from one or more consumer reporting agencies, such as TransUnion, Experian, '
    'and Equifax, and from other credit bureaus, banks, creditors and other third parties '
    '(1) to review the transaction you have applied for, including to authenticate your '
    'identity, verify information in your application, make underwriting decisions, and for '
    'related purposes, and (2) if your application results in your entering into any '
    'transaction with any of the Recipients, to service, monitor, collect and enforce the '
    'transaction. You also authorize Vestix Financial, as agent for the Recipients, to '
    'transmit this application form, along with any of the foregoing information obtained in '
    'connection with this application, to any or all of the Recipients for the foregoing '
    'purposes. You also consent to the release, by any creditor or financial institution, of '
    'any information relating to any of you, to Vestix Financial, as agent on behalf of the '
    'Recipients, and to each of the Recipients, on its own behalf.'
)

# (field key, display label)
BUSINESS_FIELDS = [
    ("legal_company_name", "Legal Company Name"),
    ("dba", "Doing Business As"),
    ("website", "Company Website"),
    ("business_phone", "Business Phone Number"),
    ("tax_id", "Tax ID / EIN"),
    ("start_date", "Business Start Date"),
    ("state_incorporation", "State of Incorporation"),
    ("industry", "Industry"),
    ("address", "Business Address"),
    ("city_state_zip", "City / State / ZIP"),
    ("process_credit_cards", "Do You Process Credit Cards?"),
    ("financing_amount", "Financing Amount Requested"),
    ("existing_mca_balance", "Existing MCA Balance (if any)"),
    ("mca_lender_name", "MCA Lender Name (if any)"),
]

OWNER_FIELDS = [
    ("full_name", "Full Legal Name"),
    ("cell_phone", "Cell Phone Number"),
    ("ownership_pct", "Ownership %"),
    ("ssn", "Social Security Number"),
    ("fico_score", "FICO Score"),
    ("home_address", "Home Address"),
    ("owner_city_state_zip", "City / State / ZIP"),
    ("dob", "Date of Birth"),
]

REDACTED_KEYS = {"business_phone", "cell_phone"}


def build_pdf(business: dict, owner: dict, signature_png_bytes: bytes,
              print_name: str, title: str, signed_at: datetime = None,
              redacted: bool = False) -> bytes:
    signed_at = signed_at or datetime.utcnow()
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    top = PAGE_H - MARGIN

    # ---- Logo mark ----
    lx, ly = MARGIN, top - 34
    c.saveState()
    c.setLineCap(1)
    c.setStrokeColor(FOREST)
    c.setLineWidth(4.5)
    c.line(lx + 2, ly + 32, lx + 16, ly + 2)
    c.setStrokeColor(TERRACOTTA)
    c.line(lx + 30, ly + 32, lx + 16, ly + 2)
    c.setFillColor(white)
    c.setStrokeColor(FOREST)
    c.setLineWidth(1)
    c.circle(lx + 16, ly + 4, 2.8, fill=1, stroke=1)
    c.restoreState()

    c.setFont('Helvetica-Bold', 18)
    c.setFillColor(FOREST)
    c.drawString(MARGIN + 44, top - 12, "Vestix Financial")
    c.setFont('Helvetica-Bold', 15)
    c.setFillColor(TERRACOTTA)
    c.drawRightString(PAGE_W - MARGIN, top - 12, "Funding Application")
    if redacted:
        c.setFont('Helvetica-Bold', 8)
        c.setFillColor(GRAY)
        c.drawRightString(PAGE_W - MARGIN, top - 24, "REDACTED COPY \u2014 phone numbers withheld")

    c.setStrokeColor(FOREST)
    c.setLineWidth(1.4)
    c.line(MARGIN, top - 42, PAGE_W - MARGIN, top - 42)

    y = top - 58
    c.setFont('Helvetica', 9)
    c.setFillColor(GRAY)
    c.drawString(MARGIN, y, "Thank you for choosing Vestix Financial. Application submitted and signed below.")
    y -= 26

    col_w = 250
    gap = CONTENT_W - 2 * col_w
    left_x = MARGIN
    right_x = MARGIN + col_w + gap
    section_top = y

    def column(x, heading, field_defs, data):
        yy = section_top
        c.setFont('Helvetica-Bold', 10)
        c.setFillColor(FOREST)
        c.drawString(x, yy, heading.upper())
        c.setStrokeColor(FOREST)
        c.setLineWidth(1)
        c.line(x, yy - 4, x + col_w, yy - 4)
        yy -= 20
        for key, label in field_defs:
            raw_val = data.get(key, "") or ""
            if redacted and key in REDACTED_KEYS:
                val = "REDACTED"
            else:
                val = raw_val
            c.setFont('Helvetica', 7.6)
            c.setFillColor(LABEL_C)
            c.drawString(x, yy, label)
            if val:
                c.setFont('Helvetica-Bold', 8.2)
                c.setFillColor(DARK)
                c.drawRightString(x + col_w, yy, str(val)[:42])
            c.setStrokeColor(LIGHT)
            c.setLineWidth(0.6)
            c.line(x, yy - 6, x + col_w, yy - 6)
            yy -= 18
        return yy

    y_left_end = column(left_x, "Business Information", BUSINESS_FIELDS, business)
    y_right_end = column(right_x, "Owner Information", OWNER_FIELDS, owner)
    y = min(y_left_end, y_right_end) - 14

    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(FOREST)
    c.drawString(MARGIN, y, "TERMS OF USE")
    c.setStrokeColor(FOREST)
    c.setLineWidth(1)
    c.line(MARGIN, y - 4, PAGE_W - MARGIN, y - 4)
    y -= 18

    c.setFont('Helvetica', 7.8)
    c.setFillColor(DARK)
    for line in simpleSplit(DISCLOSURE, 'Helvetica', 7.8, CONTENT_W):
        c.drawString(MARGIN, y, line)
        y -= 10.4
    y -= 14

    c.setFont('Helvetica-Bold', 10)
    c.setFillColor(FOREST)
    c.drawString(MARGIN, y, "SIGNATURE")
    c.setStrokeColor(FOREST)
    c.setLineWidth(1)
    c.line(MARGIN, y - 4, PAGE_W - MARGIN, y - 4)
    y -= 16

    box_w, box_h = 200, 60
    c.setFillColor(BOXFILL)
    c.setStrokeColor(LIGHT)
    c.setLineWidth(0.8)
    c.rect(MARGIN, y - box_h, box_w, box_h, fill=1, stroke=1)
    if signature_png_bytes:
        img = ImageReader(io.BytesIO(signature_png_bytes))
        c.drawImage(img, MARGIN + 4, y - box_h + 4, width=box_w - 8, height=box_h - 8,
                    preserveAspectRatio=True, mask='auto')

    name_x = MARGIN + box_w + 30
    c.setStrokeColor(DARK)
    c.setLineWidth(0.7)
    c.line(name_x, y - 18, PAGE_W - MARGIN, y - 18)
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(DARK)
    c.drawString(name_x, y - 15, print_name or "")
    c.setFont('Helvetica', 7)
    c.setFillColor(GRAY)
    c.drawString(name_x, y - 28, "Print Name")

    c.line(name_x, y - 46, PAGE_W - MARGIN, y - 46)
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(DARK)
    c.drawString(name_x, y - 43, title or "")
    c.setFont('Helvetica', 7)
    c.setFillColor(GRAY)
    c.drawString(name_x, y - 56, "Title")

    y -= box_h + 10

    c.setStrokeColor(LIGHT)
    c.setLineWidth(0.7)
    c.line(MARGIN, MARGIN + 14, PAGE_W - MARGIN, MARGIN + 14)
    c.setFont('Helvetica', 7.5)
    c.setFillColor(GRAY)
    ts = signed_at.strftime("%m/%d/%Y %I:%M %p UTC")
    c.drawString(MARGIN, MARGIN, f"Signed: {ts}  |  VESTIXUS.COM")
    c.drawRightString(PAGE_W - MARGIN, MARGIN, "VESTIX FINANCIAL | FUNDING APPLICATION   1 OF 1")

    c.save()
    return buf.getvalue()
