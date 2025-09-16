from django.urls import path
from django.utils.html import format_html
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib import admin
from django.utils import timezone
from datetime import timedelta
from .models import PaymentRequest, UserProfile, ShopOwnerProfile, Coupon
from .models import Register

@admin.register(Register)
class RegisterAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_registered')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'package_active', 'plan_expiration_date', 'delete_coupons_button')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'delete-coupons/<int:user_id>/',
                self.admin_site.admin_view(self.delete_coupons_view),
                name='delete_coupons',
            ),
        ]
        return custom_urls + urls

    def delete_coupons_button(self, obj):
        return format_html(
            '<a class="button" href="{}">Delete All Coupons</a>',
            f'./delete-coupons/{obj.user.id}/'
        )
    delete_coupons_button.short_description = 'Delete Coupons'
    delete_coupons_button.allow_tags = True

    def delete_coupons_view(self, request, user_id):
        if not request.user.is_staff:
            self.message_user(request, "You do not have permission.", level=messages.ERROR)
            return redirect('..')
        try:
            owner = ShopOwnerProfile.objects.get(user__id=user_id)
            count, _ = Coupon.objects.filter(owner=owner).delete()
            self.message_user(request, f"Deleted {count} coupons for user.", level=messages.SUCCESS)
        except ShopOwnerProfile.DoesNotExist:
            self.message_user(request, "ShopOwnerProfile not found.", level=messages.WARNING)
        return redirect('..')


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'upi_name', 'upi_id', 'is_confirmed', 'created_at', 'confirmed_at')
    list_filter = ('is_confirmed', 'created_at')
    search_fields = ('user__username', 'upi_name', 'upi_id')
    actions = ['mark_as_confirmed']

    def mark_as_confirmed(self, request, queryset):
        updated_count = 0
        today = timezone.now().date()
        for payment in queryset.filter(is_confirmed=False):
            payment.is_confirmed = True
            payment.confirmed_at = timezone.now()
            payment.save()
            profile = getattr(payment.user, 'userprofile', None)
            if profile:
                profile.package_active = True
                if not profile.plan_expiration_date or profile.plan_expiration_date < today:
                    profile.plan_expiration_date = today + timedelta(days=30)
                else:
                    profile.plan_expiration_date += timedelta(days=30)
                profile.save()
            updated_count += 1
        self.message_user(request, f"{updated_count} payment(s) confirmed and packages activated/extended.")
    mark_as_confirmed.short_description = "Mark selected payments as confirmed and activate/extend package"
