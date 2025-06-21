import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Print current working directory
print(f"Current working directory: {os.getcwd()}")

# Load environment variables
print("\nLoading .env file...")
load_dotenv()

# Print all environment variables (safely)
print("\nEnvironment variables:")
for key in ['EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD', 'DEFAULT_FROM_EMAIL']:
    value = os.getenv(key)
    if key == 'EMAIL_HOST_PASSWORD' and value:
        print(f"{key}: [HIDDEN]")
    else:
        print(f"{key}: {value}")

# Email settings
sender_email = os.getenv('EMAIL_HOST_USER')
password = os.getenv('EMAIL_HOST_PASSWORD')
receiver_email = "engrjoelivon@yahoo.com"  # The email you want to send to

print(f"\nEmail configuration:")
print(f"Sender email: {sender_email}")
print(f"Password is set: {'Yes' if password else 'No'}")
print(f"Receiver email: {receiver_email}")

try:
    # Create the email message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Test Email from Python"

    # Add body to email
    body = """
    This is a test email sent from Python using SMTP.
    If you receive this, the email configuration is working!
    """
    message.attach(MIMEText(body, "plain"))

    # Create SMTP session
    print("\nCreating SMTP session...")
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.set_debuglevel(1)  # Add debug information
    server.starttls()  # Enable TLS
    
    # Login to the server
    print("\nAttempting to log in...")
    server.login(sender_email, password)
    print("Login successful!")

    # Send email
    print("\nSending email...")
    text = message.as_string()
    server.sendmail(sender_email, receiver_email, text)
    print("Email sent successfully!")

except Exception as e:
    print(f"\nAn error occurred: {str(e)}")
    if isinstance(e, smtplib.SMTPAuthenticationError):
        print("\nThis looks like an authentication error. Please check:")
        print("1. Your EMAIL_HOST_USER is correct")
        print("2. If you have 2FA enabled, make sure you're using an App Password")
        print("3. If not using 2FA, make sure 'Less secure app access' is enabled")
        print("\nTo generate an App Password:")
        print("1. Go to Google Account settings")
        print("2. Search for 'App Passwords'")
        print("3. Generate a new App Password for 'Mail'")
finally:
    try:
        server.quit()
        print("\nSMTP session closed.")
    except:
        pass 