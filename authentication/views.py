from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth import get_user_model
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .forms import LoginForm
from django.views import View
from django.shortcuts import render
from django.contrib.auth.models import User
from email_utility.services.notification_service import NotificationService
import logging
from django.conf import settings

User = get_user_model()
logger = logging.getLogger(__name__)

class CustomLoginView(View):
    template_name = 'authentication/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard:dashboard')
        
        # Check if user is coming from resume creation flow
        resume_data = request.GET.get('resume_data')
        if resume_data:
            # Set session flag to indicate resume creation flow
            request.session['pending_resume_creation'] = True
            request.session['resume_data'] = resume_data
        
        context = {
            'debug': settings.DEBUG,
            'resume_data': resume_data,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        username_or_email = request.POST.get('username_or_email', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me')
        next_url = request.POST.get('next')
        resume_data = request.POST.get('resume_data')

        # Log the attempt for debugging (without sensitive data)
        logger.info(f"Login attempt for username/email: {username_or_email[:3]}*** from IP: {request.META.get('REMOTE_ADDR')}")

        if not username_or_email or not password:
            messages.error(request, "Please provide both username/email and password.")
            return render(request, self.template_name)

        user = None
        
        # First try authenticating with username (case-insensitive)
        try:
            # Try exact username match first
            user = authenticate(username=username_or_email, password=password)
            
            # If that fails, try case-insensitive username lookup
            if user is None:
                try:
                    user_obj = User.objects.get(username__iexact=username_or_email)
                    user = authenticate(username=user_obj.username, password=password)
                    logger.info(f"Case-insensitive username match found for: {username_or_email}")
                except User.DoesNotExist:
                    pass
                    
        except Exception as e:
            logger.error(f"Error during username authentication: {str(e)}")
        
        # If username auth fails, try email (case-insensitive)
        if user is None:
            try:
                user_obj = User.objects.get(email__iexact=username_or_email)
                user = authenticate(username=user_obj.username, password=password)
                logger.info(f"Email authentication successful for: {username_or_email}")
            except User.DoesNotExist:
                logger.info(f"No user found with email: {username_or_email}")
            except Exception as e:
                logger.error(f"Error during email authentication: {str(e)}")

        if user is not None and user.is_active:
            login(request, user)
            
            # Handle remember me
            if not remember_me:
                request.session.set_expiry(0)
            
            logger.info(f"Successful login for user: {user.username}")
            
            # Conditional redirect logic
            if resume_data or request.session.get('pending_resume_creation'):
                # User is coming from resume creation flow
                logger.info("User logging in from resume creation flow, redirecting to resume creation")
                # Clear the session flag after using it
                request.session.pop('pending_resume_creation', None)
                return redirect('resume_builder:create_resume_after_auth')
            elif next_url and next_url.startswith('/'):
                # User was redirected to login from a protected page
                logger.info(f"Redirecting to requested page: {next_url}")
                return redirect(next_url)
            else:
                # Regular login - use Django's default redirect
                logger.info("Regular login, redirecting to dashboard")
                return redirect('dashboard:dashboard')
        else:
            if user is not None and not user.is_active:
                messages.error(request, "This account has been deactivated.")
            else:
                messages.error(request, "Invalid username/email or password.")
            
            logger.warning(f"Failed login attempt for: {username_or_email}")
        
        return render(request, self.template_name)

class RegisterView(CreateView):
    template_name = 'authentication/register.html'
    form_class = CustomUserCreationForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.get_success_url())
        
        # Check if user is coming from resume creation flow
        resume_data = request.GET.get('resume_data')
        if resume_data:
            # Set session flag to indicate resume creation flow
            request.session['pending_resume_creation'] = True
            request.session['resume_data'] = resume_data
        
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        # First save the form normally
        response = super().form_valid(form)
        # Get the username and password from the form
        username = form.cleaned_data['username']
        password = form.cleaned_data['password1']
        # Authenticate and login the user
        user = authenticate(username=username, password=password)
        login(self.request, user)
        
        # Send welcome email
        try:
            NotificationService.send_welcome_email(user)
        except Exception as e:
            # Log the error but don't fail the registration
            print(f"Failed to send welcome email: {str(e)}")
        
        messages.success(self.request, f"Welcome {username}! Your account has been created successfully.")
        return response

    def get_success_url(self):
        # Conditional redirect logic for registration
        resume_data = self.request.POST.get('resume_data')
        next_url = self.request.POST.get('next')
        
        if resume_data or self.request.session.get('pending_resume_creation'):
            # User is registering from resume creation flow
            logger.info("User registering from resume creation flow, redirecting to resume creation")
            # Clear the session flag after using it
            self.request.session.pop('pending_resume_creation', None)
            return reverse_lazy('resume_builder:create_resume_after_auth')
        elif next_url and next_url.startswith('/'):
            # User was redirected to registration from a protected page
            logger.info(f"Redirecting to requested page: {next_url}")
            return next_url
        else:
            # Regular registration - use Django's default redirect
            logger.info("Regular registration, redirecting to dashboard")
            return reverse_lazy('dashboard:dashboard')
        
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home:index')

def debug_auth_view(request):
    """Debug view to help identify authentication issues"""
    # Only allow in development mode
    if not settings.DEBUG:
        return redirect('authentication:login')
        
    if request.method == 'POST':
        username_or_email = request.POST.get('username_or_email', '').strip()
        password = request.POST.get('password', '')
        
        debug_info = {
            'raw_username_or_email': request.POST.get('username_or_email'),
            'stripped_username_or_email': username_or_email,
            'username_or_email_length': len(username_or_email),
            'password_length': len(password),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'remote_addr': request.META.get('REMOTE_ADDR', ''),
            'content_type': request.META.get('CONTENT_TYPE', ''),
            'encoding': request.encoding,
        }
        
        # Try to find user
        try:
            user_by_username = User.objects.filter(username__iexact=username_or_email).first()
            user_by_email = User.objects.filter(email__iexact=username_or_email).first()
            
            debug_info.update({
                'user_found_by_username': user_by_username.username if user_by_username else None,
                'user_found_by_email': user_by_email.username if user_by_email else None,
                'exact_username_match': User.objects.filter(username=username_or_email).exists(),
                'exact_email_match': User.objects.filter(email=username_or_email).exists(),
            })
            
            # Try authentication
            if user_by_username:
                auth_result = authenticate(username=user_by_username.username, password=password)
                debug_info['auth_with_username'] = auth_result.username if auth_result else None
                
            if user_by_email:
                auth_result = authenticate(username=user_by_email.username, password=password)
                debug_info['auth_with_email'] = auth_result.username if auth_result else None
                
        except Exception as e:
            debug_info['error'] = str(e)
        
        return render(request, 'authentication/debug_auth.html', {'debug_info': debug_info})
    
    return render(request, 'authentication/debug_auth.html')