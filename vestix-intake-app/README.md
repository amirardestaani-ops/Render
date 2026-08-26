# Vestix Financial — Automated Funding Application

Merchant fills out the form, signs on-screen, and the moment they hit submit
you get two PDFs emailed to you automatically: a full copy and a copy with
phone numbers redacted. No manual steps.

## What's in this folder

- `app.py` — the web server (Flask)
- `pdf_generator.py` — builds the PDF from submitted data (the same design we tested in chat)
- `templates/apply.html` — the merchant-facing form + signature pad
- `requirements.txt`, `Procfile` — for deployment

## 1. Deploy it (Render.com, free tier)

1. Create a free account at render.com
2. Put this folder in a GitHub repo (or use Render's "deploy from a zip" option if you don't want to use git)
3. In Render: **New > Web Service**, connect the repo
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn app:app` (already set in the Procfile, Render should detect it automatically)
6. Add the environment variables below, then deploy

Render gives you a URL like `https://vestix-intake.onrender.com` with HTTPS
already set up — that's the link merchants will use.

## 2. Environment variables to set in Render

| Variable | What it is |
|---|---|
| `SMTP_HOST` | Your email provider's SMTP server (see below) |
| `SMTP_PORT` | Usually `587` |
| `SMTP_USER` | The email account that sends the notification |
| `SMTP_PASS` | Its password (or app password — see below) |
| `FROM_EMAIL` | Usually same as `SMTP_USER` |
| `TO_EMAIL` | `amir@vestixus.com` (already the default if you skip this) |

**Finding your SMTP details**: if `amir@vestixus.com` is hosted through
Google Workspace, Zoho Mail, or your web host, search "[your provider] SMTP
settings" — they all publish this. If you'd rather not deal with SMTP setup
at all, a free Gmail account works too: turn on 2-factor auth, generate an
**App Password**, and use `smtp.gmail.com` / port `587` with that app
password as `SMTP_PASS`.

## 3. Link it from your WordPress site

Simplest option — add a button in your existing code block:

```html
<a href="https://vestix-intake.onrender.com" target="_blank"
   style="background:#1e4a3a;color:white;padding:12px 24px;border-radius:6px;text-decoration:none;">
  Start Your Application
</a>
```

Or embed it directly on the page with an iframe:

```html
<iframe src="https://vestix-intake.onrender.com" style="width:100%;height:1400px;border:none;"></iframe>
```

The button/link approach is usually more reliable — iframes can be finicky
with mobile keyboards and page height.

## 4. Testing locally before you deploy (optional)

```
pip install -r requirements.txt
export SMTP_HOST=smtp.gmail.com SMTP_PORT=587 SMTP_USER=you@gmail.com SMTP_PASS=yourapppassword TO_EMAIL=amir@vestixus.com
python3 app.py
```

Then open `http://localhost:5000`.

## Notes on what's NOT included yet (easy to add later if wanted)

- **Spam protection** — a public form URL will eventually attract bots. Adding
  a CAPTCHA (e.g. Cloudflare Turnstile, free) is a quick follow-up.
- **Merchant confirmation email** — right now only you get emailed. Sending
  the merchant their own signed copy is a small addition.
- **Storage** — PDFs are emailed and not saved anywhere else. If you want a
  searchable archive later, that's a bigger addition (database or cloud storage).
- **Field validation** — SSN/EIN/phone fields accept any text right now
  (no format enforcement beyond "required"). Can be tightened if you're
  seeing malformed submissions.
