import smtplib, os
from email.mime.text import MIMEText
from dotenv import load_dotenv
from jose import jwt
from datetime import datetime, timedelta

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def create_verification_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=30)
    payload = {"sub": email, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> str:
    from jose.exceptions import JWTError
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except JWTError:
        return None




def send_verification_email(email: str, token: str):
    link = f"http://localhost:8000/verify-email?token={token}"

    # Plain text version
    text = f"Click this link to verify your email: {link}"

    # HTML version
    html = f"""\
    <html>
      <body>
        <p>Click <a href="{link}">here</a> to verify your account.</p>
      </body>
    </html>
    """

    # Multipart message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Verify your email"
    msg["From"] = os.getenv("EMAIL_FROM")
    msg["To"] = email

    # Attach both parts
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(os.getenv("EMAIL_HOST"), int(os.getenv("EMAIL_PORT"))) as server:
            server.starttls()
            server.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASSWORD"))
            server.send_message(msg)
    except Exception as e:
        print(f"Email sending failed: {e}")