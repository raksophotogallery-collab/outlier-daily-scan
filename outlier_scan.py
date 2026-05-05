import os
import smtplib
import requests
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ── CONFIG ──────────────────────────────────────────────
PERPLEXITY_API_KEY = os.environ["PERPLEXITY_API_KEY"].strip()
GMAIL_SENDER      = os.environ["GMAIL_SENDER"].strip()
GMAIL_PASSWORD    = os.environ["GMAIL_APP_PASSWORD"].strip()
RECIPIENT         = "raksophotogallery@gmail.com"
TODAY             = datetime.now().strftime("%A %d %B %Y")

# ── PROMPT ──────────────────────────────────────────────
PROMPT = """
Du ar en professionell aktieanalytiker specialiserad pa Stan Weinstein Stage Analysis och momentum-trading.

Dagens datum: {today}

Din uppgift: Identifiera de 3 absolut starkaste amerikanska aktierna som just nu:
1. Gar fran Stage 1 till Stage 2 (Weinstein) - dvs bryter ut over 30-veckors glidande medelvarde pa stark volym
2. ELLER bygger sin forsta eller andra bas i Stage 2
3. Har Relativ Styrka (RS) i topp 10% mot marknaden (RS 90+)
4. Befinner sig i en stark sektor dar flera aktier ror sig upp tillsammans
5. Har antingen: stark EPS/Sales-acceleration (fundamental outlier) ELLER en kraftfull story/catalyst (expectation outlier)

For varje aktie - skriv ett detaljerat avsnitt med:
- TICKER och bolagsnamn som rubrik
- Vad bolaget gor (2-3 meningar)
- Varfor det kan bli en outlier de kommande 3-12 manaderna
- Stage-analys: nuvarande Weinstein-stage, EMA200-lage, EMA50-lage, RS-rating, volymbekraftelse
- Vad tradaren ska vanta pa som entry-signal (VCP, flat base, breakout over pivot)
- Typ: FUNDAMENTAL OUTLIER eller EXPECTATION/STORY OUTLIER

Avsluta med en sammanfattningstabell med: Ticker | Pris | Sektor | RS 3M | Stage | Typ | Entry-setup

Skriv pa svenska. Var konkret och specifik - inga vaga formuleringar.
""".format(today=TODAY)

def get_outliers():
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "sonar-pro",
        "messages": [
            {"role": "system", "content": "Du ar en expert pa teknisk aktieanalys och Stan Weinstein Stage Analysis."},
            {"role": "user",   "content": PROMPT}
        ],
        "max_tokens": 3000,
        "temperature": 0.3
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def build_html(content):
    # Konvertera markdown-liknande text till enkel HTML
    lines = content.split("\n")
    html_lines = []
    for line in lines:
        if line.startswith("### "):
            html_lines.append(f"<h3 style='color:#00d4aa;margin-top:24px'>{line[4:]}</h3>")
        elif line.startswith("## "):
            html_lines.append(f"<h2 style='color:#ffffff;margin-top:32px;border-bottom:1px solid #333;padding-bottom:8px'>{line[3:]}</h2>")
        elif line.startswith("# "):
            html_lines.append(f"<h1 style='color:#ffffff'>{line[2:]}</h1>")
        elif line.startswith("**") and line.endswith("**"):
            html_lines.append(f"<p><strong style='color:#00d4aa'>{line[2:-2]}</strong></p>")
        elif line.startswith("- "):
            html_lines.append(f"<li style='margin-bottom:4px'>{line[2:]}</li>")
        elif line.strip() == "":
            html_lines.append("<br>")
        else:
            html_lines.append(f"<p style='margin:6px 0'>{line}</p>")

    body = "\n".join(html_lines)

    return f"""
    <html>
    <body style="background:#0d0d0d;color:#e0e0e0;font-family:'Helvetica Neue',Arial,sans-serif;max-width:700px;margin:0 auto;padding:32px 24px">

      <div style="border-bottom:2px solid #00d4aa;padding-bottom:16px;margin-bottom:32px">
        <h1 style="color:#ffffff;font-size:22px;margin:0">OUTLIER DAILY SCAN</h1>
        <p style="color:#888;margin:4px 0 0 0;font-size:13px">{TODAY} &nbsp;&bull;&nbsp; Weinstein Stage 2 Leaders &nbsp;&bull;&nbsp; US Market</p>
      </div>

      {body}

      <div style="margin-top:48px;padding-top:16px;border-top:1px solid #333;color:#555;font-size:11px">
        Genererad automatiskt via Perplexity AI &amp; GitHub Actions &bull; Endast for informationssyften, ej finansiell radgivning.
      </div>

    </body>
    </html>
    """

def send_email(html_content):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Outlier Scan {TODAY}"
    msg["From"]    = GMAIL_SENDER
    msg["To"]      = RECIPIENT
    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_SENDER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_SENDER, RECIPIENT, msg.as_string())

    print(f"Mail skickat till {RECIPIENT}")

if __name__ == "__main__":
    print("Hamtar outliers fran Perplexity...")
    content = get_outliers()
    print("Bygger HTML-mail...")
    html = build_html(content)
    print("Skickar mail...")
    send_email(html)
    print("Klart!")
