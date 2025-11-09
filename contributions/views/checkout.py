import uuid
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum

from contributions.forms import PaymentCheckoutForm
from ..models import ContributionType, MemberContribution, Payment


@login_required
def checkout(request, id):
    user = request.user
    
    member_contribution = get_object_or_404(MemberContribution, id=id)
    contribution_type = member_contribution.contribution_type
    if member_contribution.account != request.user:
        user = member_contribution.account
        
    if request.method == "POST":
        form = PaymentCheckoutForm(request.POST)

        if form.is_valid():
            from accounts.utils.abstracts import PaymentStatus
            method = request.POST.get("payment_method")
            payment = form.save(commit=False)
            payment.account = user
            payment.recorded_by = request.user
            payment.save()
            payment.update_member_contribution_status(PaymentStatus.PENDING)
            
            messages.success(
                request,
                f"Payment of R{member_contribution.amount_due:.2f} for {contribution_type.name} has been recorded successfully!"
            )
            messages.info(request, f"You chose {method} as your payment method, We have emailed you banking details where you can make payment. We Will Verify Payment once you've uplaoded payment confirmation")
            return redirect("contributions:member-contribution", id=member_contribution.id)
        
    else:
        form = PaymentCheckoutForm(user=user, initial={
            "contribution_type": contribution_type,
            "member_contribution": member_contribution,
            "amount": contribution_type.amount,
        })
        
    context = {
        "contribution_type": contribution_type,
        "member_contribution": member_contribution,
        "form": form,
        "user": user,
       
    }
    return render(request, "payments/checkout.html", context)
