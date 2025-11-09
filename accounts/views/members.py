from accounts.forms import FamilyForm, MemberForm, RegistrationForm
from accounts.models import Family
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.conf import settings
import logging

from accounts.utils.custom_mail import send_verification_email

logger = logging.getLogger("accounts")

@login_required
def get_members(request, family_slug):
    family = get_object_or_404(Family, slug=family_slug)
    members = get_user_model().objects.filter(family=family)
    return render(request, 'members/members.html', {'members': members})

@login_required
def add_member(request, family_slug):
    family = get_object_or_404(Family, slug=family_slug)
    
    template_name = "members/add-member.html"
    success_url = "accounts:get-members"
    
    
    if request.method == "POST":
        form = MemberForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = True
            user.family = family
            user.save()
            send_verification_email(user, request)
            
            messages.success(
                request,
                f"Thank For Adding Member to your family, we have sent an email to member for verification for executives to approve member addition",
            )
            return redirect(success_url, family.slug)
        else:
            messages.error(request, "Something went wrong while adding member")
            return render(
                request=request, template_name=template_name, context={"form": form}
            )
    else:
        form = MemberForm()
    return render(request=request, template_name=template_name, context={"form": form})