"""
Configuration settings for email providers and their specific requirements
"""

PROVIDERS = [
    {
        'id': 'gmail',
        'name': 'Gmail',
        'icon': 'gmail-icon',
        'host': 'imap.gmail.com',
        'port': 993,
        'requires_app_password': True,
        'app_password_url': 'https://myaccount.google.com/apppasswords',
        'setup_instructions': [
            'Enable 2-Factor Authentication in your Google Account',
            'Generate an App Password from Google Account Settings',
            'Use your email and the generated App Password here'
        ]
    },
    {
        'id': 'outlook',
        'name': 'Outlook',
        'icon': 'outlook-icon',
        'host': 'outlook.office365.com',
        'port': 993,
        'requires_app_password': False,
        'setup_instructions': [
            'Use your Outlook email address',
            'Use your regular Outlook password'
        ]
    },
    {
        'id': 'yahoo',
        'name': 'Yahoo Mail',
        'icon': 'yahoo-icon',
        'host': 'imap.mail.yahoo.com',
        'port': 993,
        'requires_app_password': True,
        'app_password_url': 'https://login.yahoo.com/account/security',
        'setup_instructions': [
            'Enable 2-Factor Authentication in Yahoo Account Security',
            'Generate an App Password from Account Security',
            'Use your email and the generated App Password here'
        ]
    },
    {
        'id': 'other',
        'name': 'Other IMAP Provider',
        'icon': 'email-icon',
        'requires_app_password': False,
        'setup_instructions': [
            'Enter your email address',
            'Enter your email password',
            'You may need to provide IMAP server details'
        ]
    }
]