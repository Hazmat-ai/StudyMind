import smtplib
import ssl
from email.message import EmailMessage
import anyio


async def send_email(config, recipient: str, subject: str, body: str) -> None:
    if not config.mail_ready:
        raise RuntimeError("Email delivery is not configured")

    def deliver():
        message = EmailMessage()
        message["From"] = config.smtp_from
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)
        context = ssl.create_default_context()
        if config.smtp_port == 465:
            connection = smtplib.SMTP_SSL(
                config.smtp_host, config.smtp_port, timeout=10, context=context
            )
        else:
            connection = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=10)
        with connection:
            if config.smtp_port != 465:
                connection.starttls(context=context)
            if config.smtp_username:
                connection.login(config.smtp_username, config.smtp_password)
            connection.send_message(message)

    await anyio.to_thread.run_sync(deliver)
