# Views for the utils app
# This file can contain utility-related views if needed in the future 

from django.shortcuts import render

def alert_demo(request):
    """View to demonstrate the alert system functionality"""
    return render(request, 'utils/alert_demo.html') 