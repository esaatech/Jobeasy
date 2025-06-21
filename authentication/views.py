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

User = get_user_model()

class CustomLoginView(View):
    template_name = 'authentication/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home:index')
        return render(request, self.template_name)

    def post(self, request):
        username_or_email = request.POST.get('username_or_email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')

        # First try authenticating with username
        user = authenticate(username=username_or_email, password=password)
        
        # If username auth fails, try email
        if user is None:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            
            # Handle remember me
            if not remember_me:
                request.session.set_expiry(0)
            
            return redirect('home:index')
        else:
            messages.error(request, "Invalid username/email or password.")
        
        return render(request, self.template_name)

class RegisterView(CreateView):
    success_url = reverse_lazy('home:index')
    template_name = 'authentication/register.html'
    form_class = CustomUserCreationForm
    
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
        return reverse_lazy('home:index')
        
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.get_success_url())
        return super().dispatch(request, *args, **kwargs)

def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home:index')