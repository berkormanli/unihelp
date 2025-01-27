import smtplib
from email.mime.text import MIMEText
from typing import List

class MailService:
    def __init__(self, email_options):
        self.host = email_options['host']
        self.port = email_options['port']
        self.username = email_options['username']
        self.password = email_options['password']
        self.from_email = email_options['from']

    def send_verification_code(self, to: List[str], code: str, verification_url: str = None):
        try:
            subject = "UniHelp Hesap Onaylaması"
            if verification_url:
                body = f"UniHelp'e Hoşgeldin! Hesabını onaylamak için aşağıdaki linke tıkla:\n\n{verification_url}\n\nEğer böyle bir mail beklemiyorsanız lütfen bu maili yok sayın.\n\nOnay kodunuz: {code}"
            else:
                body = f"UniHelp'e Hoşgeldin!\n\nOnay kodunuz: {code}\n\nBu kodu girerek kaydınızı tamamlayınız."

            # Create message
            msg = MIMEText(body, "plain")
            msg['From'] = self.from_email
            msg['To'] = ", ".join(to)
            msg['Subject'] = subject

            # Connect to SMTP server and send email
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            print("Verification code sent!")
        except Exception as e:
            print(f"Error sending email: {e}")