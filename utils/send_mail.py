import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

async def send_mail(email: str, subject: str, template: str, data: dict):
    # Load email template
    template_path = Path(__file__).parent.parent / "mails" / template
    with open(template_path, "r") as f:
        template_content = f.read()
    
    # Render template - convert EJS syntax to Jinja2
    template_content = template_content.replace("<%=", "{{").replace("%>", "}}")
    jinja_template = Template(template_content)
    html = jinja_template.render(**data)
    
    # Create message
    message = MIMEMultipart("alternative")
    message["From"] = os.getenv("SMTP_MAIL")
    message["To"] = email
    message["Subject"] = subject
    
    message.attach(MIMEText(html, "html"))
    
    # Send email
    await aiosmtplib.send(
        message,
        hostname=os.getenv("SMTP_HOST"),
        port=int(os.getenv("SMTP_PORT", "587")),
        username=os.getenv("SMTP_MAIL"),
        password=os.getenv("SMTP_PASSWORD"),
        use_tls=True,
    )

