# contributions/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import Family
from accounts.utils.abstracts import Role
from ..models import MemberContribution
from ..forms import MemberContributionForm
from django.db.models import Sum, Q


@login_required
def member_contributions_list(request, family_slug=None):
    """
    Display a list of member contributions.
    - If `family_slug` is provided, show only that family’s contributions.
    - If user is a family leader, show their family’s contributions.
    - If user is a normal member, show only their own contributions.
    - If user is admin/staff, show all contributions.
    """

    # 1️⃣ Filter by role
    if family_slug:
        # If a specific family was passed in the URL
        family = get_object_or_404(Family, slug=family_slug)
        
        contributions = MemberContribution.objects.filter(account__family=family).select_related('account', 'contribution_type')

    else:
        # Regular member - only their own contributions
        family = None
        contributions = MemberContribution.objects.all().select_related('account', 'contribution_type')

    # 2️⃣ Optional: Summary Totals
    total_contributed = contributions.filter(is_paid='PAID').aggregate(total=Sum('amount_due'))["total"] or 0
    total_due = contributions.filter(is_paid='NOT PAID').aggregate(total=Sum('amount_due'))["total"] or 0
    grand_total = contributions.aggregate(total=Sum('amount_due'))["total"] or 0

    # 3️⃣ Prepare context
    context = {
        "contributions": contributions.order_by('-created'),
        "family": family,
        "total_contributed": total_contributed,
        "total_due": total_due,
        "grand_total": grand_total,
    }

    return render(request, "member_inv/index.html", context)


@login_required
def my_member_contributions_list(request, username):
    contributions = MemberContribution.objects.select_related('account', 'contribution_type').filter(account__username=request.user.username)
    return render(request, 'member_inv/index.html', {'contributions': contributions, 'user': request.user})


@login_required
def member_contribution(request, id):
    contributions = MemberContribution.objects.select_related('account', 'contribution_type')
    contribution = get_object_or_404(contributions, id=id)
    return render(request, 'member_inv/invoice.html', {'contribution': contribution})

# Add new member contribution
@login_required
def add_member_contribution(request):
    if request.method == 'POST':
        form = MemberContributionForm(request.POST)
        if form.is_valid():
            contribution = form.save()
            messages.success(request, 'Member contribution added successfully.')
            return redirect('contributions:member-contributions-list')
        else:
            messages.error(request, 'Error creating member contribution.')
    else:
        form = MemberContributionForm()
    
    return render(request, 'member_inv/member_contribution_form.html', {'form': form})


# Update member contribution
@login_required
def update_member_contribution(request, id):
    contribution = get_object_or_404(MemberContribution, id=id)
    if request.method == 'POST':
        form = MemberContributionForm(request.POST, instance=contribution)
        if form.is_valid():
            form.save()
            messages.success(request, 'Member contribution updated successfully.')
            return redirect('contributions:member-contributions-list')
        else:
            messages.error(request, 'Error updating member contribution.')
    else:
        form = MemberContributionForm(instance=contribution)
    
    return render(request, 'member_inv/member_contribution_form.html', {'form': form, 'contribution': contribution})


# Delete member contribution
@login_required
def delete_member_contribution(request, id):
    contribution = get_object_or_404(MemberContribution, id=id)
    if request.method == 'POST':
        contribution.delete()
        messages.success(request, 'Member contribution deleted successfully.')
        return redirect('contributions:member-contributions-list')
    
    return render(request, 'member_inv/member_contribution_confirm_delete.html', {'contribution': contribution})
