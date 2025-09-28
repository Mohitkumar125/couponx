from django.contrib.auth.models import User
from django.db import models
from datetime import date

class Register(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="registration")
    date_registered = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.user.username

class ShopOwnerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='shop_owners/', blank=True, null=True)
    total_coupons_created = models.PositiveIntegerField(default=0)  # Tracks total coupons created
    def __str__(self):
        return self.user.username

class Prize(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='prize_images/', blank=True, null=True)
    owner = models.ForeignKey(ShopOwnerProfile, on_delete=models.CASCADE, related_name="prizes")  # NEW FIELD
    def __str__(self):
        return f"{self.name} ({self.owner.user.username})"  # Shows ownership

class Coupon(models.Model):
    STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Used', 'Used'),
        ('Expired', 'Expired'),
    )
    code = models.CharField(max_length=20, unique=True)
    prize = models.ForeignKey(Prize, on_delete=models.CASCADE, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    created_at = models.DateTimeField(auto_now_add=True)
    prize_type = models.CharField(max_length=50, blank=True, null=True)
    owner = models.ForeignKey(ShopOwnerProfile, on_delete=models.CASCADE, related_name='coupons')
    def __str__(self):
        return f"{self.code} ({self.status})"

class CustomerWinner(models.Model):
    customer_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=20)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    prize = models.ForeignKey(Prize, on_delete=models.SET_NULL, null=True)
    redeemed_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(ShopOwnerProfile, on_delete=models.CASCADE, related_name="winners")  # NEW FIELD
    def __str__(self):
        prize_name = self.prize.name if self.prize else 'No Prize'
        return f"{self.customer_name} - {prize_name} ({self.owner.user.username})"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    package_active = models.BooleanField(default=False)  # Indicates if package is activated by admin
    plan_expiration_date = models.DateField(null=True, blank=True)
    def is_package_active(self):
        today = date.today()
        return self.package_active and self.plan_expiration_date and self.plan_expiration_date >= today
    def __str__(self):
        return f"{self.user.username} Profile"

class PaymentRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_requests')
    upi_name = models.CharField(max_length=255)
    upi_id = models.CharField(max_length=100)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return f"PaymentRequest by {self.user.username} - {self.upi_id} - Confirmed: {self.is_confirmed}"
