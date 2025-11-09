from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm, SetPasswordForm
from django.shortcuts import render, redirect
from accounts.utils.tokens import account_activation_token
import logging

from accounts.utils.custom_mail import send_password_reset_email, send_verification_email
from accounts.utils.decorators import user_not_authenticated

email_logger = logging.getLogger("emails")
account_logger = logging.getLogger("accounts")

@login_required
def password_change(request):
    user = request.user
    template = 'accounts/password/change_password.html'
    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()

            messages.success(request, "Your password has been changed")
            return redirect('accounts:profile-update')
        else:
            messages.error(request, "Your password was not changed. Fix errors below")
            return render(request, template, {'form': form})

    form = PasswordChangeForm(user)
    return render(request, template, {'form': form})

@user_not_authenticated
def password_reset_request(request):
    try:
        if request.method == 'POST':
            form = PasswordResetForm(request.POST)
            if form.is_valid():
                user_email = form.cleaned_data['email']
                user = get_user_model().objects.get(email=user_email)
                if not user.is_active:
                    messages.error(request, f"Sorry your account is not active. We have sent account activation email to your email {user.email}")
                    sent = send_verification_email(user, request)
                    if sent:
                        return redirect("accounts:login")

                # sent = send_password_reset_email(user, request)
                # if not sent:
                #     email_logger.error(f"Password reset email to {user.get_full_name()} was not sent")

                messages.success(request, "Password reset email was successfully sent")
                return redirect("accounts:password-reset-sent")
            else:
                return render(request, "accounts/password/pwd_reset_form.html", {"form": form})
            
    except get_user_model().DoesNotExist as ex:
        account_logger.error(f"User not found - trying to request email reset - {ex}")
        messages.success(request, "Password reset email was successfully sent")
        return redirect("accounts:password-reset-sent")

    except Exception as ex:
        account_logger.error(ex)
        messages.success(request, "Password reset email was successfully sent")
        return redirect("accounts:password-reset-sent")
    
    form = PasswordResetForm()
    return render(
        request=request, 
        template_name="accounts/password/pwd_reset_form.html", 
        context={"form": form}
        )

def password_reset_sent(request):
    return render(request, "accounts/password/password_email_sent.html")

def passwordResetConfirm(request, uidb64, token):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Your password has been set. You may go ahead and <b>log in </b> now.")
                return redirect('accounts:login')
            else:
                return render(request, 'accounts/password/pwd_reset_confirm.html', {'form': form})

        form = SetPasswordForm(user)
        return render(request, 'accounts/password/pwd_reset_confirm.html', {'form': form})
    else:
        messages.error(request, "Link is expired")
        return redirect("accounts:reset-password")
