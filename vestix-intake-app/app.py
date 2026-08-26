import os
import base64
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage

from flask import Flask, render_template, request, jsonify

from pdf_generator import build_pdf, BUSINESS_FIELDS, OWNER_FIELDS

app = Flask(__name__)

SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
FROM_EMAIL = os.environ.get("FROM_EMAIL", SMTP_USER)
TO_EMAIL = os.environ.get("TO_EMAIL", "amir@vestixus.com")


@app.route("/")
def apply_form():
    return render_template("apply.html")


@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json(force=True)

    business = {key: data.get(key, "") for key, _ in BUSINESS_FIELDS}
    owner = {key: data.get(key, "") for key, _ in OWNER_FIELDS}
    print_name = data.get("print_name", "")
    title = data.get("title", "")

    sig_data_url = data.get("signature", "")
    signature_bytes = None
    if sig_data_url and "," in sig_data_url:
        signature_bytes = base64.b64decode(sig_data_url.split(",", 1)[1])

    signed_at = datetime.now(timezone.utc)

    full_pdf = build_pdf(business, owner, signature_bytes, print_name, title, signed_at, redacted=False)
    redacted_pdf = build_pdf(business, owner, signature_bytes, print_name, title, signed_at, redacted=True)

    company_slug = (business.get("legal_company_name") or "application").strip().replace(" ", "_")[:40]
    date_str = signed_at.strftime("%Y%m%d")

    try:
        send_email(
            subject=f"New Funding Application — {business.get('legal_company_name', 'Unknown')}",
            body=(
                f"A new funding application was submitted and signed.\n\n"
                f"Business: {business.get('legal_company_name', '')}\n"
                f"Owner: {owner.get('full_name', '')}\n"
                f"Requested: {business.get('financing_amount', '')}\n"
                f"Signed: {signed_at.strftime('%m/%d/%Y %I:%M %p UTC')}\n\n"
                f"Full copy and phone-redacted copy attached."
            ),
            attachments=[
                (f"{company_slug}_{date_str}_FULL.pdf", full_pdf),
                (f"{company_slug}_{date_str}_REDACTED.pdf", redacted_pdf),
            ],
        )
    except Exception as e:
        app.logger.error(f"Email send failed: {e}")
        return jsonify({"ok": False, "error": "email_failed"}), 500

    return jsonify({"ok": True})


def send_email(subject: str, body: str, attachments: list[tuple[str, bytes]]):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS):
        raise RuntimeError("SMTP is not configured — set SMTP_HOST, SMTP_USER, SMTP_PASS env vars")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = TO_EMAIL
    msg.set_content(body)

    for filename, content in attachments:
        msg.add_attachment(content, maintype="application", subtype="pdf", filename=filename)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
