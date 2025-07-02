from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model

User = get_user_model()

class BaseModel(models.Model):
    """
    Abstract base model providing common fields and functionality.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class FeatureCatalog(BaseModel):
    """
    Catalog of all available tools and services that can be included in subscriptions.
    
    Attributes:
        name (str): Display name of the feature
        identifier (str): Unique identifier used in code
        type (str): Type of feature (tool or service)
        description (str): Detailed description of the feature
    """
    FEATURE_TYPES = (
        ('TOOL', 'Tool'),
        ('SERVICE', 'Service'),
    )

    name = models.CharField(max_length=255)
    identifier = models.SlugField(
        max_length=100, 
        unique=True,
        help_text="Unique identifier used in code to reference this feature"
    )
    type = models.CharField(
        max_length=10,
        choices=FEATURE_TYPES,
        help_text="Whether this is a tool or service"
    )
    description = models.TextField(
        help_text="Detailed description of what this feature provides"
    )

    class Meta:
        verbose_name = "Feature"
        verbose_name_plural = "Features"
        ordering = ['type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class SubscriptionPlan(BaseModel):
    """
    Defines subscription plans available for purchase.
    
    A plan can either grant access to specific features or have full access to everything.
    """
    name = models.CharField(max_length=255)
    description = models.TextField()
    has_full_access = models.BooleanField(
        default=False,
        help_text="If True, this plan has access to all features regardless of selection"
    )
    features = models.ManyToManyField(
        FeatureCatalog,
        blank=True,
        help_text="Features included in this plan (ignored if has_full_access is True)"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"
        ordering = ['name']

    def __str__(self):
        return self.name

    def clean(self):
        """Validate the subscription plan."""
        pass

    def save(self, *args, **kwargs):
        """
        Override save to handle validation after the object exists
        """
        super().save(*args, **kwargs)
        # Only validate features if not full access and this isn't a new object
        if not self.has_full_access and not self.pk:
            if not self.features.exists():
                raise ValidationError(
                    "Plan must either have full access or select specific features."
                )


class PlanDuration(BaseModel):
    """
    Defines available durations and prices for subscription plans.
    """
    DURATION_TYPES = (
        ('ONE_TIME', 'One Time'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('SEMI_ANNUAL', 'Semi-Annual'),
        ('YEARLY', 'Yearly'),
    )

    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.CASCADE,
        related_name='durations'
    )
    duration_type = models.CharField(
        max_length=20,
        choices=DURATION_TYPES
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Price in USD"
    )
    stripe_price_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Stripe Price ID for this duration"
    )

    class Meta:
        verbose_name = "Plan Duration"
        verbose_name_plural = "Plan Durations"
        ordering = ['plan', 'duration_type']
        unique_together = ['plan', 'duration_type']

    def __str__(self):
        """Generic string representation of duration and price."""
        return f"{self.get_duration_type_display()} (${self.price})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='stripe_profile')
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)


class UserSubscription(BaseModel):
    """
    Tracks user subscriptions and their status.
    """
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
        ('PENDING', 'Pending'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan = models.ForeignKey('SubscriptionPlan', on_delete=models.PROTECT)
    plan_duration = models.ForeignKey('PlanDuration', on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_payment_intent = models.CharField(max_length=255, blank=True, null=True)
    stripe_invoice_id = models.CharField(max_length=255, null=True, blank=True)
    invoice_url = models.URLField(max_length=500, null=True, blank=True)

    class Meta:
        verbose_name = "User Subscription"
        verbose_name_plural = "User Subscriptions"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.status})"

    @property
    def is_active(self):
        """Check if subscription is currently active."""
        now = timezone.now()
        return (
            self.status == 'ACTIVE' and
            self.start_date <= now and
            (self.end_date is None or self.end_date > now)
        )

    def has_access_to_feature(self, feature_identifier):
        """
        Check if this subscription grants access to a specific feature.
        """
        if not self.is_active:
            return False
            
        if self.plan.has_full_access:
            return True
            
        return self.plan.features.filter(
            identifier=feature_identifier,
            is_active=True
        ).exists()