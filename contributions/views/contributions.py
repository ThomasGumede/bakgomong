from django.shortcuts import render, redirect, get_object_or_404
from contributions.models import ContributionType, MemberContribution, Payment
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from contributions.forms import ContributionTypeForm
from django.contrib import messages
from accounts.utils.abstracts import PaymentStatus

@login_required
def get_contributions(request):
    contributions = ContributionType.objects.all()
    return render(request, 'contributions/index.html', {'contributions': contributions})

@login_required
def get_contribution(request, contribution_slug):
   
    contribution = get_object_or_404(ContributionType, slug=contribution_slug)

    # 💰 2. Fetch all payments related to this contribution
    payments = (
        Payment.objects
        .filter(contribution_type=contribution)
        .select_related("account", "account__family")
        .order_by("-payment_date")
    )
    
    outstandings = MemberContribution.objects.filter(
        contribution_type=contribution,
        is_paid=PaymentStatus.NOT_PAID  # or status='unpaid'
    )
    
    unpaid_amount = MemberContribution.objects.filter(
        contribution_type=contribution,
        is_paid=PaymentStatus.NOT_PAID  # or status='unpaid'
    ).aggregate(total=Sum('amount_due'))['total'] or 0

    # 🧮 3. Calculate totals
    total_collected = payments.aggregate(total=Sum("amount"))["total"] or 0

    # 🧩 4. Optional: Group totals by family (for admin dashboards)
    totals_by_family = (
        payments.values("account__family__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    context = {
        "contribution": contribution,
        "payments": payments,
        "total_collected": total_collected,
        "totals_by_family": totals_by_family,
        "unpaid_amount": unpaid_amount,
        'outstandings': outstandings,
    }

    return render(request, "contributions/contribution.html", context)


@login_required
def add_contribution(request):
    if request.method == 'POST':
        form = ContributionTypeForm(request.POST)
        if form.is_valid():
            contribution = form.save(commit=False)
            contribution.created_by = request.user
            contribution.save()
            messages.success(request, 'Contribution added successfully.')
            return redirect('contributions:get-contributions')
        else:
            messages.error(request, 'Something went wrong while creating your contribution type.')
    else:
        form = ContributionTypeForm()
    
    return render(request, 'contributions/add-contribution.html', {"form": form})


@login_required
def update_contribution(request, contribution_slug):
    contribution = get_object_or_404(ContributionType, slug=contribution_slug)
    
    if request.method == 'POST':
        form = ContributionTypeForm(request.POST, instance=contribution)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contribution updated successfully.')
            return redirect('contributions:get-contribution', contribution.slug)
        else:
            messages.error(request, 'Something went wrong while updating your contribution type.')
    else:
        form = ContributionTypeForm(instance=contribution)
    
    return render(request, 'contributions/add-contribution.html', {'form': form, 'contr': contribution})


@login_required
def delete_contribution(request, contribution_slug):
    contribution = get_object_or_404(ContributionType, slug=contribution_slug)
    
    if request.method == 'POST':
        contribution.delete()
        messages.success(request, 'Contribution deleted successfully.')
        return redirect('contributions:get-contributions')
    
    return render(request, 'contributions/delete-contribution.html', {'contribution': contribution})
