import random
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import string
from django.db import IntegrityError
from .models import ShopOwnerProfile, Register  

from django.contrib.admin.views.decorators import staff_member_required


from .models import ShopOwnerProfile, UserProfile, Coupon, Prize, CustomerWinner, PaymentRequest


def index(request):
    return render(request, 'index.html')


def about(request):
    return render(request, 'about.html')


def services(request):
    return render(request, 'services.html')


def customer(request):
    winners = CustomerWinner.objects.select_related('coupon', 'prize').order_by('-redeemed_at')
    return render(request, 'customer.html', {'redemptions': winners})




def register(request):
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        image = request.FILES.get('image')

        # Password and uniqueness check...
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return redirect('register')
        if User.objects.filter(username__iexact=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')
        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('register')

        try:
            user = User.objects.create_user(username=username, email=email, password=password1)
            ShopOwnerProfile.objects.create(user=user, image=image)
            Register.objects.create(user=user)
            messages.success(request, "Registration successful.")
            return redirect('login')
        except IntegrityError:
            messages.error(request, "Username already exists. Please choose a different username.")
            return redirect('register')

    return render(request, 'register.html')


def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, "Please fill in both email and password.")
            return redirect('login')
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return redirect('login')

        user = authenticate(request, username=user_obj.username, password=password)
        if user:
            login(request, user)
            messages.success(request, "Login successful!")
            return redirect('dash')
        else:
            messages.error(request, "Invalid email or password.")
            return redirect('login')
    return render(request, 'login.html')


@login_required
def payment(request):
    if request.method == 'POST':
        upi_name = request.POST.get('upi_name')
        upi_id = request.POST.get('upi_id')
        if not upi_name or not upi_id:
            return render(request, 'payment.html', {'error': 'Please provide both UPI name and UPI ID.'})

        PaymentRequest.objects.create(
            user=request.user,
            upi_name=upi_name,
            upi_id=upi_id,
            is_confirmed=False
        )
        return render(request, 'payment_success.html')
    return render(request, 'payment.html')


@login_required
def dash(request):
    try:
        user_data = ShopOwnerProfile.objects.get(user=request.user)
    except ShopOwnerProfile.DoesNotExist:
        user_data = None

    coupons_created = Coupon.objects.filter(owner=user_data).count()
    plan_expiration_date = None
    try:
        user_package = UserProfile.objects.get(user=request.user)
        plan_expiration_date = user_package.plan_expiration_date
    except UserProfile.DoesNotExist:
        pass

    free_codes_limit = 10
    used_free_codes = Coupon.objects.filter(owner=user_data, status='Used').count()
    has_free_codes_remaining = (free_codes_limit - used_free_codes) > 0

    context = {
        'user_data': user_data,
        'coupons_created': coupons_created,
        'plan_expiration_date': plan_expiration_date,
        'has_free_codes_remaining': has_free_codes_remaining,
    }
    return render(request, 'dash.html', context)


def generate_unique_coupon_code(length=8):
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if not Coupon.objects.filter(code=code).exists():
            return code


@login_required
def gen(request):
    try:
        user_profile = ShopOwnerProfile.objects.get(user=request.user)
    except ShopOwnerProfile.DoesNotExist:
        messages.error(request, "User profile not found.")
        return redirect('gen')

    FREE_COUPONS_LIMIT = 10
    MONTHLY_PACKAGE_COUPONS_LIMIT = 1000

    try:
        user_package = UserProfile.objects.get(user=request.user)
        package_active = user_package.is_package_active()
        plan_expiration_date = user_package.plan_expiration_date
    except UserProfile.DoesNotExist:
        package_active = False
        plan_expiration_date = None

    coupons_queryset = Coupon.objects.filter(owner=user_profile)
    coupons_created = coupons_queryset.count()
    coupons_used = coupons_queryset.filter(status='Used').count()
    prizes_redeemed = CustomerWinner.objects.filter(coupon__owner=user_profile).count()

    allowed_coupons = (MONTHLY_PACKAGE_COUPONS_LIMIT if package_active else FREE_COUPONS_LIMIT) - coupons_created
    coupons_remaining = max(0, allowed_coupons)
    has_free_codes_remaining = coupons_remaining > 0

    show_purchase_message = False
    if (not package_active and coupons_created >= FREE_COUPONS_LIMIT) or \
            (package_active and coupons_created >= MONTHLY_PACKAGE_COUPONS_LIMIT):
        show_purchase_message = True

    if request.method == 'POST':
        if 'delete_all_coupons' in request.POST:
            coupons_queryset.delete()
            messages.success(request, "All coupons deleted successfully!")
            return redirect('gen')

        coupon_quantity = int(request.POST.get('coupon_quantity', 0))
        expiry_date = request.POST.get('expiry_date')
        prize_type = request.POST.get('prize_type')

        coupons_created = Coupon.objects.filter(owner=user_profile).count()
        allowed_coupons = (MONTHLY_PACKAGE_COUPONS_LIMIT if package_active else FREE_COUPONS_LIMIT) - coupons_created

        if allowed_coupons <= 0:
            messages.error(request, "Coupon limit reached. Please purchase another package to continue.")
            return redirect('purchase_package')

        if coupon_quantity > allowed_coupons:
            messages.error(request, f"You can only create {allowed_coupons} more coupons.")
            return redirect('gen')

        for _ in range(coupon_quantity):
            code = generate_unique_coupon_code()
            Coupon.objects.create(
                code=code,
                prize_type=prize_type,
                expiry_date=expiry_date,
                owner=user_profile
            )
        user_profile.total_coupons_created += coupon_quantity
        user_profile.save()
        messages.success(request, f"{coupon_quantity} coupon(s) created successfully!")
        return redirect('gen')

    context = {
        'user_data': user_profile,
        'coupons': coupons_queryset.order_by('-id'),
        'coupons_created': coupons_created,
        'user_coupons_used': coupons_used,
        'user_coupons_remaining': coupons_remaining,
        'user_prizes_redeemed': prizes_redeemed,
        'has_free_codes_remaining': has_free_codes_remaining,
        'package_active': package_active,
        'show_purchase_message': show_purchase_message,
        'plan_expiration_date': plan_expiration_date,
        'total_coupons_created': user_profile.total_coupons_created,
    }
    return render(request, 'gen.html', context)


@staff_member_required
def delete_all_coupons(request, user_id):
    """
    Staff-only view: delete all coupons for any user's ShopOwnerProfile by user_id.
    """
    if request.method == "POST":
        try:
            user_profile = ShopOwnerProfile.objects.get(user__id=user_id)
            Coupon.objects.filter(owner=user_profile).delete()
            messages.success(request, f"All coupons for user ID {user_id} deleted successfully!")
        except ShopOwnerProfile.DoesNotExist:
            messages.error(request, "User profile not found. Cannot delete coupons.")
    return redirect('gen')


@login_required
def download(request):
    user_profile = ShopOwnerProfile.objects.get(user=request.user)
    coupons = Coupon.objects.filter(owner=user_profile)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="coupons.csv"'
    writer = csv.writer(response)
    writer.writerow(['Code', 'Prize', 'Expiry Date', 'Status', 'Created At'])
    for coupon in coupons:
        writer.writerow([coupon.code, coupon.prize_type, coupon.expiry_date, coupon.status, coupon.created_at])
    return response


@login_required
def manage_prizes(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')
        if not name or not image:
            messages.error(request, "Both name and image are required to add a prize.")
            return redirect('prize')

        Prize.objects.create(name=name, image=image)
        messages.success(request, f'Prize "{name}" added successfully.')
        return redirect('prize')

    prizes = Prize.objects.all().order_by('-id')
    return render(request, 'prize.html', {'prizes': prizes})

@login_required
@require_http_methods(['POST'])
def delete_prize(request, prize_id):
    prize = get_object_or_404(Prize, pk=prize_id)
    prize.delete()
    messages.success(request, f'Prize "{prize.name}" deleted successfully.')
    return redirect('prize')

def qr(request):
    prizes = Prize.objects.all()
    return render(request, 'qr.html', {'prizes': prizes})


def validate_coupon(request):
    code = request.GET.get('coupon', '').strip()
    if not code:
        return JsonResponse({'valid': False, 'message': 'Coupon code is required.'})
    try:
        coupon_obj = Coupon.objects.get(code=code, status='Active')
        if coupon_obj.expiry_date and coupon_obj.expiry_date < timezone.now().date():
            return JsonResponse({'valid': False, 'message': 'Coupon expired.'})
        return JsonResponse({'valid': True, 'message': 'Coupon is valid.'})
    except Coupon.DoesNotExist:
        return JsonResponse({'valid': False, 'message': 'Coupon invalid or used.'})


@login_required
def spin_and_win(request):
    user_profile = ShopOwnerProfile.objects.filter(user=request.user).first()
    prizes = list(Prize.objects.all())
    context = {
        'prizes': prizes,
        'user_profile': user_profile,
        'name': '',
        'contact': '',
        'coupon': '',
        'show_modal': False,
    }

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        contact = request.POST.get('contact', '').strip()
        coupon_code = request.POST.get('coupon', '').strip()

        context.update({'name': name, 'contact': contact, 'coupon': coupon_code})

        if not (name and contact and coupon_code):
            messages.error(request, "All fields are required.")
            return render(request, 'spin_and_win.html', context)

        # Validate coupon
        try:
            coupon_obj = Coupon.objects.get(code=coupon_code, status='Active')
            if coupon_obj.expiry_date and coupon_obj.expiry_date < timezone.now().date():
                messages.error(request, "Coupon expired.")
                return render(request, 'spin_and_win.html', context)
        except Coupon.DoesNotExist:
            messages.error(request, "Coupon is invalid or already used.")
            return render(request, 'spin_and_win.html', context)

        if not prizes:
            messages.error(request, "No prizes available currently.")
            return render(request, 'spin_and_win.html', context)

        # Select prize at random
        prize_won = random.choice(prizes)
        winning_index = prizes.index(prize_won)

        # Mark coupon as used
        coupon_obj.status = 'Used'
        coupon_obj.save()

        # Record the winner
        CustomerWinner.objects.create(
            customer_name=name,
            mobile_number=contact,
            coupon=coupon_obj,
            prize=prize_won
        )

        # Update context for UI
        context.update({
            'show_modal': True,
            'prize_won': prize_won,
            'winning_index': winning_index,
        })

    return render(request, 'spin_and_win.html', context)


@csrf_exempt
def redeem_coupon(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})

    code = request.POST.get('coupon')
    name = request.POST.get('name')
    contact = request.POST.get('contact')
    prize_id = request.POST.get('prize_id')

    if not all([code, name, contact, prize_id]):
        return JsonResponse({'success': False, 'message': 'All fields are required.'})

    try:
        coupon_obj = Coupon.objects.get(code=code, status='Active')
    except Coupon.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Coupon invalid or used.'})

    try:
        prize_obj = Prize.objects.get(pk=prize_id)
    except Prize.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Selected prize does not exist.'})

    try:
        coupon_obj.status = 'Used'
        coupon_obj.save()

        CustomerWinner.objects.create(
            customer_name=name,
            mobile_number=contact,
            coupon=coupon_obj,
            prize=prize_obj
        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Redemption failed: {str(e)}'})


@login_required
def validate_coupon(request):
    code = request.GET.get('coupon', '').strip()
    if not code:
        return JsonResponse({'valid': False, 'message': 'Coupon code is required.'})

    try:
        coupon_obj = Coupon.objects.get(code=code, status='Active')
        if coupon_obj.expiry_date and coupon_obj.expiry_date < timezone.now().date():
            return JsonResponse({'valid': False, 'message': 'Coupon expired.'})
        return JsonResponse({'valid': True, 'message': 'Coupon is valid.'})
    except Coupon.DoesNotExist:
        return JsonResponse({'valid': False, 'message': 'Coupon invalid or used.'})


# Prize management views

@login_required
def manage_prizes(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')

        if not (name and image):
            messages.error(request, "Both Prize name and image are required.")
            return redirect('prize')

        Prize.objects.create(name=name, image=image)
        messages.success(request, f'Prize "{name}" added successfully.')
        return redirect('prize')

    prizes = Prize.objects.all().order_by('-id')
    return render(request, 'prize.html', {'prizes': prizes})


@login_required
def update_prize(request, prize_id):
    prize = get_object_or_404(Prize, pk=prize_id)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        image = request.FILES.get('image')

        if not name:
            messages.error(request, "Prize name is required.")
            return redirect('prize')

        prize.name = name

        if image:
            prize.image = image

        prize.save()
        messages.success(request, f'Prize "{prize.name}" updated successfully.')

    return redirect('prize')


@login_required
def delete_prize(request, prize_id):
    prize = get_object_or_404(Prize, pk=prize_id)
    prize.delete()
    messages.success(request, f'Prize "{prize.name}" deleted successfully.')
    return redirect('manage_prizes')  # Use the actual URL pattern name here
