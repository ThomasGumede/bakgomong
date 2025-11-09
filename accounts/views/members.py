from accounts.forms import FamilyForm
from accounts.models import Family
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.conf import settings
import logging

logger = logging.getLogger("accounts")

@login_required
def get_members(request, family_slug):
    family = get_object_or_404(Family, slug=family_slug)
    members = get_user_model().objects.filter(family=family)
    return render(request, 'members/members.html', {'members': members})