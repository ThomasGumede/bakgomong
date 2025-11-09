from accounts.forms import FamilyForm
from accounts.models import Family
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.conf import settings
from django.db.models import Sum
from contributions.models import Payment, MemberContribution
from dashboard.models import ClanDocument
import logging

logger = logging.getLogger("accounts")

@login_required
def get_families(request):
    families = Family.objects.all()
    return render(request, 'family/families.html', {"families": families})


@login_required
def get_family(request, family_slug):
    """
    Show a family's profile, members, total contributions, unpaid balances, and uploaded documents.
    """
    family = get_object_or_404(Family, slug=family_slug)
    contributions = MemberContribution.objects.filter(account__family=family).select_related('account', 'contribution_type')[:5]

    # 1️⃣ Get all members in the family
    members = family.members.select_related("family").all()

    # 2️⃣ Calculate total contributed and unpaid
    total_contributed = (
        Payment.objects.filter(account__family=family)
        .aggregate(total=Sum("amount"))
        .get("total")
        or 0
    )

    total_unpaid = (
        MemberContribution.objects.filter(account__family=family, is_paid='NOT PAID')
        .aggregate(total=Sum("amount_due"))
        .get("total")
        or 0
    )

    total_due = (
        MemberContribution.objects.filter(account__family=family)
        .aggregate(total=Sum("amount_due"))
        .get("total")
        or 0
    )

    # 3️⃣ Fetch related family documents
    documents = ClanDocument.objects.filter(family=family).order_by("-created")

    context = {
        "family": family,
        "members": members,
        "documents": documents,
        "total_contributed": total_contributed,
        "total_unpaid": total_unpaid,
        "contributions": contributions,
    }

    return render(request, "family/family.html", context)


@login_required
def add_family(request):
    form = FamilyForm()
    if request.method == 'POST':
        form = FamilyForm(request.POST)
        if form.is_valid():
            family = form.save()
            messages.success(request, "Family added successfully")
            return redirect('accounts:get-families')
        else:
            messages.error(request, 'Something went wrong while adding family')
            
    return render(request, 'family/add-family.html', {"form": form})

@login_required
def update_family(request, family_slug):
    family = get_object_or_404(Family, slug=family_slug)
    form = FamilyForm(instance=family)
    if request.method == 'POST':
        form = FamilyForm(request.POST, instance=family)
        if form.is_valid():
            family = form.save()
            messages.success(request, "Family updated successfully")
            return redirect('accounts:get-families')
        else:
            messages.error(request, 'Something went wrong while updating family')
            
    return render(request, 'family/add-family.html', {"form": form})

@login_required
def delete_family(request, family_slug):
    family = get_object_or_404(Family, slug=family_slug)
    family.delete()
    messages.success(request, "Family deleted successfully")    
    return redirect('accounts:get-families')

