from rest_framework import serializers
from .models import FAQ, Testimonial, NewsletterSignup, ContactMessage

class FAQSerializer(serializers.ModelSerializer):
    language = serializers.CharField(default='en')
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'order', 'language']

class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ['id', 'name', 'quote', 'avatar']

class NewsletterSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsletterSignup
        fields = ['id', 'email', 'date']

class ContactMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'message', 'date'] 