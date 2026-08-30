"""Small script to test SMTP settings from app.core.config.Settings.

Usage:
  - Set SMTP env vars (SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, ADMIN_EMAILS)
  - For local testing run: `python -m smtpd -n -c DebuggingServer localhost:1025`
  - Then run: `venv/bin/python scripts/test_smtp.py`
"""
import os
import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_test_email():
    smtp_host = os.getenv('SMTP_HOST') or settings.SMTP_HOST
    smtp_port = int(os.getenv('SMTP_PORT') or settings.SMTP_PORT or 0)
    smtp_user = os.getenv('SMTP_USER') or settings.SMTP_USER
    smtp_password = os.getenv('SMTP_PASSWORD') or settings.SMTP_PASSWORD
    smtp_from = os.getenv('SMTP_FROM') or settings.SMTP_FROM or smtp_user
    admin_emails = os.getenv('ADMIN_EMAILS') or ",".join(settings.ADMIN_EMAILS or [])
    if isinstance(admin_emails, str):
        admin_list = [e.strip() for e in admin_emails.split(',') if e.strip()]
    else:
        admin_list = list(admin_emails)

    if not smtp_host or not smtp_port:
        print("SMTP_HOST and SMTP_PORT must be set (or use DebuggingServer on localhost:1025).")
        return
    if not admin_list:
        print("No ADMIN_EMAILS configured; nothing to send to.")
        return

    msg = EmailMessage()
    msg['Subject'] = 'Test SMTP from freelance_p app'
    msg['From'] = smtp_from
    msg['To'] = ', '.join(admin_list)
    msg.set_content('This is a test message sent by scripts/test_smtp.py')

    try:
        if smtp_port in (465,):
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            server.ehlo()
            env_starttls = os.getenv('SMTP_STARTTLS')
            if env_starttls is not None:
                starttls = env_starttls.lower() not in ('0', 'false', 'no')
            else:
                starttls = bool(getattr(settings, 'SMTP_STARTTLS', True))
            if starttls:
                server.starttls()
                server.ehlo()

        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)

        server.send_message(msg)
        server.quit()
        print('Test email sent to:', admin_list)
    except Exception as e:
        print('Failed to send test email:', e)


if __name__ == '__main__':
    send_test_email()
