from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model, authenticate
from django.test import RequestFactory
from authentication.views import CustomLoginView
import json

User = get_user_model()

class Command(BaseCommand):
    help = 'Test authentication with different input variations'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to test')
        parser.add_argument('password', type=str, help='Password to test')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        
        self.stdout.write(f"Testing authentication for username: {username}")
        
        # Test variations
        variations = [
            username,
            username.strip(),
            username.lower(),
            username.upper(),
            f" {username} ",  # With extra spaces
            username.replace(' ', ''),  # Remove spaces
        ]
        
        for variation in variations:
            self.stdout.write(f"\nTesting variation: '{variation}'")
            
            # Test direct authentication
            user = authenticate(username=variation, password=password)
            if user:
                self.stdout.write(f"  ✓ Direct auth successful: {user.username}")
            else:
                self.stdout.write(f"  ✗ Direct auth failed")
            
            # Test case-insensitive lookup
            try:
                user_obj = User.objects.get(username__iexact=variation)
                user = authenticate(username=user_obj.username, password=password)
                if user:
                    self.stdout.write(f"  ✓ Case-insensitive auth successful: {user.username}")
                else:
                    self.stdout.write(f"  ✗ Case-insensitive auth failed")
            except User.DoesNotExist:
                self.stdout.write(f"  ✗ User not found with case-insensitive lookup")
            
            # Test email lookup
            try:
                user_obj = User.objects.get(email__iexact=variation)
                user = authenticate(username=user_obj.username, password=password)
                if user:
                    self.stdout.write(f"  ✓ Email auth successful: {user.username}")
                else:
                    self.stdout.write(f"  ✗ Email auth failed")
            except User.DoesNotExist:
                self.stdout.write(f"  ✗ Email not found")
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write("Test completed!") 