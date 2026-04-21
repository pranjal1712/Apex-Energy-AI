import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr

class MailHandler:
    def __init__(self):
        self.conf = ConnectionConfig(
            MAIL_USERNAME=os.getenv("MAIL_USERNAME", "").strip(),
            MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "").strip(),
            MAIL_FROM=os.getenv("MAIL_FROM", "").strip(),
            MAIL_PORT=465,
            MAIL_SERVER="smtp.gmail.com",
            MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "Apex Energy AI"),
            MAIL_STARTTLS=False,
            MAIL_SSL_TLS=True,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True
        )
        self.fm = FastMail(self.conf)

    async def send_otp_email(self, email_to: EmailStr, otp: str):
        # Using local static folder in backend for reliable access on Render
        logo_path = os.path.join(os.path.dirname(__file__), "static", "logo.png")
        
        html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 500px; margin: auto; padding: 30px; border: 1px solid #1a1a1a; border-radius: 20px; background-color: #050505; color: #ffffff; box-shadow: 0 10px 40px rgba(168,85,247,0.15);">
            <div style="text-align: center; margin-bottom: 30px;">
                <img src="cid:logo" alt="Apex Energy AI" style="width: 100px; height: auto; margin-bottom: 10px;" />
                <h1 style="color: #a855f7; margin: 0; font-size: 26px; letter-spacing: -0.5px; font-weight: 800;">Identity Verification</h1>
                <p style="color: #888888; font-size: 13px; margin-top: 5px; text-transform: uppercase; letter-spacing: 2px;">Secure Nebula Intelligence Hub</p>
            </div>
            
            <div style="background: rgba(255,255,255,0.02); padding: 30px; border-radius: 16px; border: 1px solid rgba(168,85,247,0.1);">
                <p style="margin-top: 0; font-size: 16px; color: #ffffff;">Hello,</p>
                <p style="color: #bbbbbb; line-height: 1.6; font-size: 14px;">Welcome to the future of energy intelligence. To complete your activation on <strong>Apex Energy AI</strong>, please use the following secure verification code:</p>
                
                <div style="text-align: center; margin: 40px 0;">
                    <div style="display: inline-block; font-size: 38px; font-weight: 900; letter-spacing: 10px; color: #ffffff; background: linear-gradient(135deg, #a855f7, #3b82f6); padding: 20px 40px; border-radius: 12px; box-shadow: 0 0 25px rgba(168,85,247,0.3);">
                        {otp}
                    </div>
                </div>
                
                <p style="font-size: 11px; color: #555555; text-align: center; line-height: 1.4;">This security code will expire in 10 minutes. If you did not initiate this request, please disregard this communication.</p>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <p style="font-size: 11px; color: #333333; margin: 0; text-transform: uppercase; letter-spacing: 1px;">&copy; 2026 Apex Energy AI - Nebula Systems Hub</p>
                <p style="font-size: 10px; color: #222222; margin-top: 5px;">Advanced Energy Retieval & Analysis Pipeline • Encryption Verified</p>
            </div>
        </div>
        """
        
        message = MessageSchema(
            subject="Apex Energy AI - Verification Code Required",
            recipients=[email_to],
            body=html,
            subtype=MessageType.html,
            attachments=[
                {
                    "file": logo_path,
                    "headers": {
                        "Content-ID": "<logo>",
                        "Content-Disposition": "inline; filename=\"logo.png\"",
                    },
                    "mime_type": "image",
                    "mime_subtype": "png",
                }
            ]
        )
        
        try:
            await self.fm.send_message(message)
            return True
        except Exception as e:
            print(f"[MAIL ERROR] Failed to send OTP to {email_to}: {e}")
            return False

# Initialize singleton
mail_handler = MailHandler()
