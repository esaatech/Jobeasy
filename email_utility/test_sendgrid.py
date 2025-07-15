import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SendGrid configuration
sender_email = "support@jobeas.com"  # Your verified domain email
sendgrid_api_key = os.getenv('SENDGRID_MAIL_ACCESS')
from_email = os.getenv('FROM_EMAIL', 'support@jobeas.com')  # New environment variable name
receiver_email = "engrjoelivon@yahoo.com"  # Test recipient

print(f"SendGrid Configuration:")
print(f"Sender email: {sender_email}")
print(f"From email: {from_email}")
print(f"API Key is set: {'Yes' if sendgrid_api_key else 'No'}")
print(f"Receiver email: {receiver_email}")

if not sendgrid_api_key:
    print("ERROR: SENDGRID_MAIL_ACCESS environment variable not set!")
    exit(1)

try:
    # Create the email message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Test Email from Jobeas via SendGrid"

    # Add body to email
    body = """
    This is a test email sent from Jobeas using SendGrid.
    
    If you receive this, the SendGrid configuration is working correctly!
    
    Best regards,
    Jobeas Team
    """
    message.attach(MIMEText(body, "plain"))

    # Create SMTP session with SendGrid
    print("\nCreating SMTP session with SendGrid...")
    server = smtplib.SMTP('smtp.sendgrid.net', 587)
    server.set_debuglevel(1)  # Add debug information
    server.starttls()  # Enable TLS
    
    # Login to SendGrid (always use 'apikey' as username)
    print("\nAttempting to log in to SendGrid...")
    server.login('apikey', sendgrid_api_key)
    print("Login successful!")

    # Send email
    print("\nSending email...")
    text = message.as_string()
    server.sendmail(sender_email, receiver_email, text)
    print("Email sent successfully via SendGrid!")

except Exception as e:
    print(f"\nAn error occurred: {str(e)}")
    if isinstance(e, smtplib.SMTPAuthenticationError):
        print("\nThis looks like an authentication error. Please check:")
        print("1. Your SENDGRID_MAIL_ACCESS API key is correct")
        print("2. Your domain (jobeas.com) is verified in SendGrid")
        print("3. The sender email (support@jobeas.com) is authorized")
    elif isinstance(e, smtplib.SMTPRecipientsRefused):
        print("\nRecipient email was refused. Please check:")
        print("1. The recipient email address is valid")
        print("2. Your SendGrid account is not in sandbox mode")
finally:
    try:
        server.quit()
        print("\nSMTP session closed.")
    except:
        pass 