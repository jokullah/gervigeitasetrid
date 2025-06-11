from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.models import User, Group
from django.db import IntegrityError
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from core.models import EmailVerification  # Import from your core app
import uuid
from core.models import EmailVerification, PasswordReset  # Update this line to include PasswordReset


def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Basic validation
        if not email:
            return render(request, 'login.html', {'error': 'Vinsamlegast sláðu inn netfang'})
            
        if not password:
            return render(request, 'login.html', {'error': 'Vinsamlegast sláðu inn lykilorð'})
            
        if email[-6:] != "@hi.is":
            return render(request, 'login.html', {'error': 'Vinsamlegast notaðu @hi.is tölvupóstfang'})
            
        try:
            user = User.objects.get(email=email)
            
            if user.check_password(password):
                # Check if user is verified
                try:
                    verification = EmailVerification.objects.get(user=user)
                    if not verification.is_verified:
                        return render(request, 'login.html', {
                            'error': 'Vinsamlegast staðfestu netfangið þitt áður en þú skráir þig inn. Athugaðu tölvupóstinn þinn.',
                            'show_resend': True,
                            'user_email': email
                        })
                except EmailVerification.DoesNotExist:
                    # User exists but no verification record - assume verified for existing users
                    pass
                
                auth_login(request, user)
                return redirect('/')
            else:
                return render(request, 'login.html', {'error': 'Rangt lykilorð'})
        except User.DoesNotExist:
            return render(request, 'login.html', {'error': 'Netfang er ekki skráð'})
    
    return render(request, 'login.html')


def signup(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Basic validation
        if password1 != password2:
            return render(request, 'signup.html', {'error': 'Lykilorðin eru ekki eins'})
        
        if len(password1) < 8:
            return render(request, 'signup.html', {'error': 'Lykilorðið þarf að vera að minnsta kosti 8 stafir'})
        
        if email[-6:] != "@hi.is":
            return render(request, 'signup.html', {'error': 'Vinsamlegast notaðu @hi.is tölvupóstfang'})
            
        try:
            # Check if email already exists
            existing_user = User.objects.filter(email=email).first()
            if existing_user:
                # Check if user is verified
                try:
                    verification = EmailVerification.objects.get(user=existing_user)
                    if not verification.is_verified:
                        # User exists but not verified - resend verification
                        verification.verification_code = uuid.uuid4()
                        verification.created_at = timezone.now()
                        verification.save()
                        
                        send_verification_email(existing_user, verification.verification_code)
                        messages.info(request, 'Nýr hlekkur hefur verið sendur á netfangið þitt.')
                        return redirect(reverse('auth'))
                    else:
                        # User exists and is verified
                        return render(request, 'signup.html', {'error': 'Netfang er nú þegar skráð. Vinsamlegast skráðu þig inn.'})
                except EmailVerification.DoesNotExist:
                    # User exists but no verification record - assume verified
                    return render(request, 'signup.html', {'error': 'Netfang er nú þegar skráð en hefur ekki verið staðfest.'})
                
            # Create new user with email as username
            username = email.split('@')[0]  # Use part before @ as username
            user = User.objects.create_user(username=username, email=email, password=password1)
            
            # Set user as inactive until email is verified
            user.is_active = False
            user.save()
            
            # Add user to "Nemandi" group
            nemandi_group = Group.objects.get(name='Nemandi')
            user.groups.add(nemandi_group)
            
            # Create email verification record
            verification = EmailVerification.objects.create(user=user)
            
            # Send verification email
            send_verification_email(user, verification.verification_code)
            
            # Redirect to verification page
            return redirect(reverse('auth'))
            
        except IntegrityError:
            # If username already exists, add a number to it
            base_username = username
            counter = 1
            while True:
                try:
                    username = f"{base_username}{counter}"
                    user = User.objects.create_user(username=username, email=email, password=password1)
                    
                    # Set user as inactive until email is verified
                    user.is_active = False
                    user.save()
                    
                    # Add user to "Nemandi" group
                    nemandi_group = Group.objects.get(name='Nemandi')
                    user.groups.add(nemandi_group)
                    
                    # Create email verification record
                    verification = EmailVerification.objects.create(user=user)
                    
                    # Send verification email
                    send_verification_email(user, verification.verification_code)
                    
                    return redirect(reverse('auth'))
                except IntegrityError:
                    counter += 1
                    
    return render(request, 'signup.html')


def logout(request):
    auth_logout(request)
    return redirect('/')


def send_verification_email(user, verification_code):
    """Send verification email to user"""
    subject = 'Staðfestu netfangið þitt'
    
    # Create verification link
    verification_url = f"{settings.SITE_URL}/verify-email/{verification_code}/"
    
    message = f"""
Halló!

Takk fyrir að búa til aðgang. Vinsamlegast staðfestu netfangið þitt með því að smella á tengilinn hér að neðan:

{verification_url}

Þessi hlekkur rennur út eftir 24 klukkustundir.

Ef þú bjóst ekki til þennan aðgang geturðu hunsað þennan tölvupóst.

Bestu kveðjur,
Þitt teymi
"""
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
    
    try:
        send_mail(
            subject,
            message,
            from_email,
            [user.email],
            fail_silently=False,
        )
        print(f"Verification email sent to {user.email}")  # For debugging
    except Exception as e:
        print(f"Failed to send email: {e}")  # For debugging


def verify_email(request, verification_code):
    """Handle email verification when user clicks the link"""
    try:
        verification = EmailVerification.objects.get(verification_code=verification_code)
        
        if verification.is_expired():
            return render(request, 'verification_expired.html', {
                'user_email': verification.user.email
            })
        
        if verification.is_verified:
            return render(request, 'already_verified.html')
        
        # Mark as verified and activate user
        verification.is_verified = True
        verification.save()
        
        verification.user.is_active = True
        verification.user.save()
        
        # Auto-login the user
        auth_login(request, verification.user)
        
        messages.success(request, 'Netfangið þitt hefur verið staðfest! Þú ert nú skráð/ur inn.')
        return redirect('/')
        
    except EmailVerification.DoesNotExist:
        return render(request, 'verification_invalid.html')
    

def resend_verification(request):
    """Resend verification email"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, 'Vinsamlegast sláðu inn netfang.')
            return redirect('auth')
        
        try:
            user = User.objects.get(email=email)
            verification = EmailVerification.objects.get(user=user)
            
            if verification.is_verified:
                messages.info(request, 'Þetta netfang er nú þegar staðfest. Þú getur skráð þig inn.')
                return redirect('login')
            
            # Generate new verification code
            verification.verification_code = uuid.uuid4()
            verification.created_at = timezone.now()
            verification.save()
            
            # Send new verification email
            send_verification_email(user, verification.verification_code)
            
            messages.success(request, 'Nýr hlekkur hefur verið sendur á netfangið þitt.')
            return redirect('auth')
            
        except (User.DoesNotExist, EmailVerification.DoesNotExist):
            messages.error(request, 'Netfang fannst ekki eða er þegar staðfest.')
            return redirect('auth')
    
    return redirect('auth')


def send_password_reset_email(user, reset_code):
    """Send password reset email to user"""
    subject = 'Endurstilla lykilorð'
    
    # Create reset link
    reset_url = f"{settings.SITE_URL}/reset-password/{reset_code}/"
    
    message = f"""
Halló!

Þú hefur beðið um að endurstilla lykilorðið þitt. Smelltu á tengilinn hér að neðan til að búa til nýtt lykilorð:

{reset_url}

Þessi hlekkur rennur út eftir 1 klukkustund.

Ef þú baðst ekki um þessa endurstillingu geturðu hunsað þennan tölvupóst.

Bestu kveðjur,
Þitt teymi
"""
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
    
    try:
        send_mail(
            subject,
            message,
            from_email,
            [user.email],
            fail_silently=False,
        )
        print(f"Password reset email sent to {user.email}")  # For debugging
    except Exception as e:
        print(f"Failed to send password reset email: {e}")  # For debugging


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            return render(request, 'forgot_password.html', {
                'error': 'Vinsamlegast sláðu inn netfang'
            })
        
        if email[-6:] != "@hi.is":
            return render(request, 'forgot_password.html', {
                'error': 'Vinsamlegast notaðu @hi.is tölvupóstfang'
            })
        
        try:
            user = User.objects.get(email=email)
            
            # Check if user is verified
            try:
                verification = EmailVerification.objects.get(user=user)
                if not verification.is_verified:
                    return render(request, 'forgot_password.html', {
                        'error': 'Þú þarft að staðfesta netfangið þitt áður en þú getur endurstillt lykilorðið.'
                    })
            except EmailVerification.DoesNotExist:
                # User exists but no verification record - assume verified for existing users
                pass
            
            # Create password reset record
            from core.models import PasswordReset
            reset_record = PasswordReset.objects.create(user=user)
            
            # Send reset email
            send_password_reset_email(user, reset_record.reset_code)
            
            return render(request, 'password_reset_sent.html', {'email': email})
            
        except User.DoesNotExist:
            # Don't reveal that the email doesn't exist - security best practice
            return render(request, 'password_reset_sent.html', {'email': email})
    
    return render(request, 'forgot_password.html')


def reset_password(request, reset_code):
    """Handle password reset when user clicks the link"""
    try:
        from core.models import PasswordReset
        reset_record = PasswordReset.objects.get(reset_code=reset_code)
        
        if reset_record.is_expired():
            return render(request, 'password_reset_expired.html')
        
        if reset_record.used:
            return render(request, 'password_reset_used.html')
        
        if request.method == 'POST':
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            # Validation
            if password1 != password2:
                return render(request, 'reset_password_form.html', {
                    'error': 'Lykilorðin eru ekki eins',
                    'reset_code': reset_code
                })
            
            if len(password1) < 8:
                return render(request, 'reset_password_form.html', {
                    'error': 'Lykilorðið þarf að vera að minnsta kosti 8 stafir',
                    'reset_code': reset_code
                })
            
            # Update password
            user = reset_record.user
            user.set_password(password1)
            user.save()
            
            # Mark reset as used
            reset_record.used = True
            reset_record.save()
            
            # Auto-login the user
            auth_login(request, user)
            
            messages.success(request, 'Lykilorðið þitt hefur verið endurstillt! Þú ert nú skráð/ur inn.')
            return redirect('/')
        
        # Show password reset form
        return render(request, 'reset_password_form.html', {
            'reset_code': reset_code,
            'user_email': reset_record.user.email
        })
        
    except PasswordReset.DoesNotExist:
        return render(request, 'password_reset_invalid.html')
    
    
def send_form_verification_email(contact_email, verification_code, company_name, title):
    """Send verification email for project advertisement form"""
    subject = 'Staðfestu verkefnaauglýsingu þína'
    
    # Create verification link
    verification_url = f"{settings.SITE_URL}/verify-project-ad/{verification_code}/"
    
    message = f"""
Halló!

Takk fyrir að senda inn verkefnaauglýsingu fyrir "{title}" frá {company_name}.

Til að ljúka við sendingu auglýsingarinnar, vinsamlegast staðfestu netfangið þitt með því að smella á tengilinn hér að neðan:

{verification_url}

Þessi tengill rennur út eftir 24 klukkustundir.

Ef þú sendir ekki inn þessa auglýsingu geturðu hunsað þennan tölvupóst.

Bestu kveðjur,
Háskóli Íslands
"""
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hi.is')
    
    try:
        send_mail(
            subject,
            message,
            from_email,
            [contact_email],
            fail_silently=False,
        )
        print(f"Form verification email sent to {contact_email}")  # For debugging
    except Exception as e:
        print(f"Failed to send form verification email: {e}")  # For debugging