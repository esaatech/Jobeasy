import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Hardcoded email settings
sender_email = "esaatechnology@gmail.com"  # Your Gmail address
password = "sfqp oapb lagw rmin"  # Your App Password
receiver_email = "engrjoelivon@yahoo.com"

print(f"\nEmail configuration:")
print(f"Sender email: {sender_email}")
print(f"Password is set: {'Yes' if password else 'No'}")
print(f"Receiver email: {receiver_email}")

try:
    print("\nCreating SMTP session...")
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.set_debuglevel(1)  # Show SMTP conversation
    server.starttls()
    
    print("\nAttempting to log in...")
    server.login(sender_email, password)
    print("Login successful!")

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = "Test Email from Python"

    body = "This is a test email sent from Python using SMTP."
    message.attach(MIMEText(body, "plain"))

    print("\nSending email...")
    text = message.as_string()
    server.sendmail(sender_email, receiver_email, text)
    print("Email sent successfully!")

except Exception as e:
    print(f"\nAn error occurred: {str(e)}")
    if isinstance(e, smtplib.SMTPAuthenticationError):
        print("\nThis looks like an authentication error. Please check:")
        print("1. Your Gmail address is correct")
        print("2. If you have 2FA enabled (recommended):")
        print("   - Go to Google Account settings")
        print("   - Search for 'App Passwords'")
        print("   - Generate a new App Password for 'Mail'")
        print("3. If not using 2FA (not recommended):")
        print("   - Enable 'Less secure app access' in Google Account settings")
finally:
    try:
        server.quit()
        print("\nSMTP session closed.")
    except:
        pass 