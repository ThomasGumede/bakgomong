from accounts.forms import FamilyForm
from accounts.models import Family
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.conf import settings
from django.db.models import Sum
from accounts.utils.abstracts import Role
from contributions.models import Payment, MemberContribution
from dashboard.models import ClanDocument
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger("accounts")

@login_required
def get_families(request):
    user  = request.user
    if user.role == Role.MEMBER and not user.is_staff:
        families = Family.objects.filter(is_approved=True, id=user.family.id)
    else:
        families = Family.objects.filter(is_approved=True)
    return render(request, 'family/families.html', {"families": families})


@login_required
def get_family(request, family_slug=None):
    """
    Show a family's profile, members, total contributions, unpaid balances, and uploaded documents.
    """
    user  = request.user
    
    # Ensure only approved families are viewable
    if user.role == Role.MEMBER and not user.is_staff:
        families = Family.objects.filter(is_approved=True, id=user.family.id)
        
        family = get_object_or_404(families, slug=family_slug)
        contributions = (
            MemberContribution.objects.filter(account__family=family, account=user)
            .select_related("account", "contribution_type")
            .order_by("-created")[:5]
        )
        total_contributed = (
            Payment.objects.filter(account=user, account__family=family)
            .aggregate(total=Sum("amount"))
            .get("total")
            or 0
        )
        total_unpaid = (
            MemberContribution.objects.filter(account__family=family, is_paid='NOT PAID', account=user)
            .aggregate(total=Sum("amount_due"))
            .get("total")
            or 0
        )
    else:
        families = Family.objects.filter(is_approved=True)
        family = get_object_or_404(families, slug=family_slug)
    
        # Show most recent 5 contributions
        contributions = (
            MemberContribution.objects.filter(account__family=family)
            .select_related("account", "contribution_type")
            .order_by("-created")[:5]
        )
        
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

    # 1️⃣ Get all members in the family
    members = family.members.select_related("family").all()

    

    

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
        "total_due": total_due,
    }

    return render(request, "family/family.html", context)


EXECUTIVE_ROLES = [
    Role.CLAN_CHAIRPERSON,
    Role.DEP_CHAIRPERSON,
    Role.SECRETARY,
    Role.DEP_SECRETARY,
    Role.TREASURER,
    Role.KGOSANA,
    Role.FAMILY_LEADER,
]


@login_required
def add_family(request):

    # Restrict access to executives only
    if request.user.role not in EXECUTIVE_ROLES:
        return HttpResponseForbidden("You do not have permission to perform this action.")

    form = FamilyForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            try:
                with transaction.atomic():
                    family = form.save(commit=False)

                    # Mark for approval depending on creator role
                    if request.user.role == Role.FAMILY_LEADER:
                        family.is_approved = False
                    else:
                        family.is_approved = True

                    # family.created_by = request.user
                    family.save()

                    # Link leader → family
                    leader = family.leader
                    leader.family = family
                    leader.save(update_fields=["family"])

                messages.success(request, "Family added successfully.")
                return redirect("accounts:get-families")

            except Exception as e:
                logger.exception(f"Failed to create family: {e}")
                messages.error(request, "Something went wrong while adding the family.")

        else:
            messages.error(request, "Please fix the errors below.")

    return render(request, "family/add-family.html", {"form": form})

@login_required
def update_family(request, family_slug):
    family = get_object_or_404(Family, slug=family_slug)
    if not request.user.is_staff:
        return HttpResponseForbidden()
    form = FamilyForm(instance=family)
    if request.method == 'POST':
        form = FamilyForm(request.POST, instance=family)
        if form.is_valid():
            try:
                with transaction.atomic():
                    family = form.save()
                messages.success(request, "Family updated successfully")
                return redirect('accounts:get-families')
            except Exception:
                logger.exception("Failed to update family %s", family_slug)
                messages.error(request, 'Something went wrong while updating family')
        else:
            messages.error(request, 'Please fix the errors below.')
            
    return render(request, 'family/add-family.html', {"form": form})

@login_required
def delete_family(request, family_slug):
    if not request.user.is_staff:
        return HttpResponseForbidden()
    family = get_object_or_404(Family, slug=family_slug)
    # Only allow delete via POST (avoid accidental deletes via GET)
    if request.method == "POST":
        family.delete()
        messages.success(request, "Family deleted successfully")
        return redirect('accounts:get-families')
    # Render a simple confirmation template (create template if needed)
    return render(request, "family/confirm_delete.html", {"family": family})

