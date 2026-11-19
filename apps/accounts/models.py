"""
User Accounts & Subscription Models.

Subscription Tiers:
- FREE: 5 photos/month (demo)
- BASIC: $2/month - 5,000 photos/month
- PRO: $5/month - 20,000 photos/month
- ENTERPRISE: $15/month - 100,000 photos/month
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class SubscriptionPlan(models.Model):
    """Subscription plan tiers."""
    TIER_CHOICES = [
        ("free", "Free (Demo)"),
        ("basic", "Basic"),
        ("pro", "Pro"),
        ("enterprise", "Enterprise"),
    ]

    BILLING_CYCLE_CHOICES = [
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    tier = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    price_monthly = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    price_yearly = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    monthly_photo_limit = models.PositiveIntegerField(default=5)
    yearly_photo_limit = models.PositiveIntegerField(default=5)
    features = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    stripe_price_id_monthly = models.CharField(max_length=100, blank=True)
    stripe_price_id_yearly = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["price_monthly"]

    def __str__(self):
        return f"{self.name} (${self.price_monthly}/mo)"

    def get_limit(self, billing_cycle="monthly"):
        return self.monthly_photo_limit if billing_cycle == "monthly" else self.yearly_photo_limit


class User(AbstractUser):
    """Extended user model with subscription info."""
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email


class UserSubscription(models.Model):
    """User's active subscription."""
    STATUS_CHOICES = [
        ("active", "Active"),
        ("past_due", "Past Due"),
        ("canceled", "Canceled"),
        ("expired", "Expired"),
        ("trialing", "Trialing"),
    ]

    BILLING_CYCLE_CHOICES = [
        ("monthly", "Monthly"),
        ("yearly", "Yearly"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription"
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CYCLE_CHOICES, default="monthly")
    current_period_start = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField()
    photos_used_this_period = models.PositiveIntegerField(default=0)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.plan.name} ({self.status})"

    @property
    def is_active(self):
        return self.status in ("active", "trialing") and self.current_period_end > timezone.now()

    @property
    def photo_limit(self):
        return self.plan.get_limit(self.billing_cycle)

    @property
    def photos_remaining(self):
        return max(0, self.photo_limit - self.photos_used_this_period)

    @property
    def usage_percentage(self):
        if self.photo_limit == 0:
            return 100
        return min(100, (self.photos_used_this_period / self.photo_limit) * 100)

    def can_process(self, count=1):
        """Check if user can process `count` more photos."""
        if not self.is_active:
            return False
        return (self.photos_used_this_period + count) <= self.photo_limit

    def increment_usage(self, count=1):
        """Increment photo usage counter."""
        self.photos_used_this_period += count
        self.save(update_fields=["photos_used_this_period", "updated_at"])

    def reset_usage_if_new_period(self):
        """Reset usage counter if we're in a new billing period."""
        if timezone.now() >= self.current_period_end:
            self.photos_used_this_period = 0
            self.current_period_start = self.current_period_end
            if self.billing_cycle == "monthly":
                self.current_period_end += timedelta(days=30)
            else:
                self.current_period_end += timedelta(days=365)
            self.save(update_fields=["photos_used_this_period", "current_period_start", "current_period_end", "updated_at"])
            return True
        return False


class PhotoUsageLog(models.Model):
    """Log of photo processing for analytics."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="usage_logs"
    )
    subscription = models.ForeignKey(
        UserSubscription,
        on_delete=models.SET_NULL,
        null=True,
        related_name="usage_logs"
    )
    photos_count = models.PositiveIntegerField(default=1)
    action = models.CharField(max_length=50)  # upload, analyze, clean, download
    batch_job_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["batch_job_id"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.photos_count} photos - {self.action}"