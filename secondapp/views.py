from django.shortcuts import render, redirect, get_object_or_404

from django.http import JsonResponse

from django.contrib.auth import login, logout

from django.contrib.auth.decorators import login_required

from django.views.decorators.csrf import csrf_protect

from django.contrib import messages

from django.core.mail import send_mail

from django.conf import settings

from django.utils import timezone

from datetime import timedelta

from django.db.models import Q

from .models import User, OTP

from .forms import LoginForm, OTPForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm

import random

import string

try:

    from twilio.rest import Client

except ImportError:

    Client = None





def send_otp_email(user, otp):

    subject = 'Your OTP for E-Learning Platform'

    message = f'Your OTP is: {otp.otp_code}. It is valid for 10 minutes.'

    from_email = settings.EMAIL_HOST_USER

    recipient_list = [user.email]

    send_mail(subject, message, from_email, recipient_list)





def send_otp_sms(user, otp):

    if Client:

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        message = client.messages.create(

            body=f'Your OTP is: {otp.otp_code}. It is valid for 10 minutes.',

            from_=settings.TWILIO_PHONE_NUMBER,

            to=user.phone_number

        )





def index(request):

    return render(request, 'index.html')





def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful. Please login.')
            return redirect('login')
    else:
        form = RegistrationForm()
    
    return render(request, 'register.html', {
        'form': form
    })



def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Check if account is locked - try to find user by username or email
            from django.utils import timezone
            user = User.objects.filter(Q(username=username) | Q(email=username)).first()
            
            if user and user.account_locked:
                if user.locked_until and user.locked_until > timezone.now():
                    messages.error(request, f'Account is locked. Please try again after {user.locked_until.strftime("%Y-%m-%d %H:%M:%S")}.')
                    return render(request, 'login.html', {'form': form})
                else:
                    # Lockout period has expired, unlock the account
                    user.account_locked = False
                    user.failed_login_attempts = 0
                    user.locked_until = None
                    user.save()

            # Authenticate user (backend handles both username and email)
            from django.contrib.auth import authenticate
            authenticated_user = authenticate(request, username=username, password=password)
            
            if authenticated_user is not None:
                # Regenerate session ID for security
                request.session.flush()
                
                login(request, authenticated_user)
                
                # Reset failed login attempts on successful login
                authenticated_user.failed_login_attempts = 0
                authenticated_user.account_locked = False
                authenticated_user.locked_until = None
                authenticated_user.save()

                messages.success(request, 'Login successful.')
                
                # Get the next URL or redirect based on user type
                next_url = request.POST.get('next') or request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                elif authenticated_user.user_type == 'admin':
                    return redirect('admin_dashboard')
                else:
                    return redirect('dashboard')

            else:
                # Increment failed login attempts
                if user:
                    user.failed_login_attempts += 1
                    
                    # Lock account after 5 failed attempts
                    if user.failed_login_attempts >= 5:
                        user.account_locked = True
                        user.locked_until = timezone.now() + timezone.timedelta(minutes=30)
                        messages.error(request, 'Account has been locked due to multiple failed login attempts. Please try again in 30 minutes.')
                    else:
                        remaining_attempts = 5 - user.failed_login_attempts
                        messages.error(request, f'Invalid username/email or password. {remaining_attempts} attempts remaining before account lockout.')
                    
                    user.save()
                else:
                    messages.error(request, 'Invalid username/email or password.')

                return render(request, 'login.html', {'form': form})

    else:
        form = LoginForm()
    
    next_url = request.GET.get('next', '')
    return render(request, 'login.html', {'form': form, 'next': next_url})





def verify_otp(request):

    user_id = request.session.get('user_id')

    otp_type = request.session.get('otp_type')

    

    if not user_id:

        return redirect('login')

    

    user = get_object_or_404(User, id=user_id)

    

    if request.method == 'POST':

        form = OTPForm(request.POST)

        if form.is_valid():

            otp_code = form.cleaned_data['otp']

            

            # Get the latest unused OTP

            otp = OTP.objects.filter(

                user=user,

                otp_type=otp_type,

                otp_code=otp_code,

                is_used=False

            ).order_by('-created_at').first()

            

            if otp and otp.is_valid():

                otp.is_used = True

                otp.save()

                

                if otp_type == 'email':

                    user.email_verified = True

                else:

                    user.phone_verified = True

                user.save()

                

                login(request, user)

                del request.session['user_id']

                del request.session['otp_type']

                

                messages.success(request, 'Login successful.')

                return redirect('dashboard')

            else:

                messages.error(request, 'Invalid or expired OTP.')

    else:

        form = OTPForm()

    

    return render(request, 'verify_otp.html', {'form': form})





@login_required

def dashboard(request):
    if request.user.user_type == 'admin':
        return redirect('admin_dashboard')
    
    # Calculate completed courses count
    completed_count = request.user.enrollments.filter(is_completed=True).count()
    
    return render(request, 'dashboard.html', {
        'completed_count': completed_count
    })


def forgot_password(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.filter(email=email).first()
            if user:
                # Generate and send OTP via email
                otp = OTP.objects.create(user=user, otp_type='email')
                otp.generate_otp()
                send_otp_email(user, otp)
                
                request.session['user_id'] = user.id
                request.session['otp_type'] = 'email'
                request.session['reset_password'] = True
                
                messages.success(request, 'OTP sent to your email for password reset.')
                return redirect('reset_password')
            else:
                messages.error(request, 'No account found with this email address.')
    else:
        form = ForgotPasswordForm()
    
    return render(request, 'forgot_password.html', {'form': form})


def reset_password(request):
    if 'user_id' not in request.session or 'reset_password' not in request.session:
        messages.error(request, 'Please request a password reset first.')
        return redirect('forgot_password')
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp']
            new_password = form.cleaned_data['new_password']
            
            try:
                user = User.objects.get(id=request.session['user_id'])
                otp = OTP.objects.filter(user=user, otp_code=otp_code, otp_type='email').first()
                
                if otp and otp.is_valid():
                    user.set_password(new_password)
                    user.save()
                    otp.delete()
                    
                    del request.session['user_id']
                    del request.session['otp_type']
                    del request.session['reset_password']
                    
                    messages.success(request, 'Password reset successfully. Please login with your new password.')
                    return redirect('login')
                else:
                    messages.error(request, 'Invalid or expired OTP.')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
    else:
        form = ResetPasswordForm()
    
    return render(request, 'reset_password.html', {'form': form})





@login_required

def admin_dashboard(request):
    if request.user.user_type != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    
    # Get statistics
    from learnapp.models import Course, Video
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    courses = Course.objects.all()
    users = User.objects.filter(user_type='user')
    videos = Video.objects.all()
    
    return render(request, 'admin_dashboard.html', {
        'courses': courses,
        'users': users,
        'videos': videos
    })


@login_required
def profile(request):
    # Users can only view their own profile
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        
        # Handle new fields
        date_of_birth = request.POST.get('date_of_birth')
        if date_of_birth:
            from datetime import datetime
            user.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        
        user.ambition = request.POST.get('ambition', '')
        user.hobbies = request.POST.get('hobbies', '')
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    
    return render(request, 'profile.html', {'user': request.user})


@login_required
def upload_profile_photo(request):
    if request.method == 'POST':
        if 'profile_photo' in request.FILES:
            request.user.profile_picture = request.FILES['profile_photo']
            request.user.save()
            return JsonResponse({'success': True, 'message': 'Profile photo uploaded successfully.'})
        else:
            return JsonResponse({'success': False, 'message': 'No photo selected.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


@login_required
def remove_profile_photo(request):
    if request.method == 'POST':
        if request.user.profile_picture:
            # Delete the file from storage
            if request.user.profile_picture:
                request.user.profile_picture.delete(save=False)
            request.user.profile_picture = None
            request.user.save()
            return JsonResponse({'success': True, 'message': 'Your profile photo has been removed successfully.'})
        else:
            return JsonResponse({'success': False, 'message': 'No profile photo to remove.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})





@login_required

def logout_view(request):

    logout(request)

    messages.success(request, 'You have been logged out.')

    return redirect('index')



@login_required
@csrf_protect

def delete_account(request):
    # Only admin can delete accounts
    if request.user.user_type != 'admin':
        messages.error(request, 'Account deletion is only allowed for administrators.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        if user_id:
            try:
                user_to_delete = User.objects.get(id=user_id)
                
                # Prevent admin from deleting themselves
                if user_to_delete == request.user:
                    messages.error(request, 'You cannot delete your own account.')
                    return redirect('admin_dashboard')
                
                # Delete user's profile picture if exists
                if user_to_delete.profile_picture:
                    user_to_delete.profile_picture.delete(save=False)
                
                # Delete the user account
                user_to_delete.delete()
                
                messages.success(request, f'Account for {user_to_delete.username} has been deleted successfully.')
                return redirect('admin_dashboard')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
                return redirect('admin_dashboard')
        else:
            messages.error(request, 'User ID is required.')
            return redirect('admin_dashboard')
    
    # For GET request, show list of users to delete (admin only)
    users = User.objects.filter(user_type='user')
    return render(request, 'delete_account.html', {'users': users})





@login_required

def payment(request):
    messages.info(request, 'Payment feature has been disabled.')
    return redirect('dashboard')





@login_required

def payment_success(request):
    messages.info(request, 'Payment feature has been disabled.')
    return redirect('dashboard')





@login_required

def payment_failure(request):
    messages.info(request, 'Payment feature has been disabled.')
    return redirect('dashboard')

