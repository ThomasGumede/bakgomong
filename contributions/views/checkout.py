import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.urls import reverse
from django_q.tasks import async_task
from django.conf import settings
from contributions.forms import LogPaymentForm, PaymentCheckoutForm
from ..models import ContributionType, MemberContribution, Payment
from accounts.utils.abstracts import PaymentStatus, Role

logger = logging.getLogger("contributions")


@login_required
def checkout(request, id):
    user = request.user
    
    member_contribution = get_object_or_404(MemberContribution, id=id)
    contribution_type = member_contribution.contribution_type

    # Only allow users to pay their own contributions (or staff/admin)
    if member_contribution.account != request.user and not request.user.is_staff:
        messages.error(request, "You can only pay for your own contributions.")
        return redirect("contributions:member-contributions")

    # If staff is paying on behalf of member, use the member account
    if request.user.is_staff and member_contribution.account != request.user:
        user = member_contribution.account
         
    if request.method == "POST":
        form = PaymentCheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            payment_method = request.POST.get("payment_method", "").strip().lower()

            try:
                with transaction.atomic():
                    payment = form.save(commit=False)
                    payment.account = user
                    payment.recorded_by = request.user
                    payment.payment_method_type = payment_method
                    payment.is_approved = Payment.LogPaymentStatus.PENDING
                    payment.reference = member_contribution.reference
                    payment.save()
                    # update member contribution status (also atomic via Payment.save)
                    payment.update_member_contribution_status(PaymentStatus.PENDING)

                logger.info(
                    "Payment created: %s R%.2f for %s (method: %s)",
                    payment.id,
                    member_contribution.amount_due,
                    user.username,
                    payment_method,
                )

                # Route based on payment method
                if payment_method in ["cash", "bank"]:
                    # Queue email with banking details (non-blocking)
                    async_task("contributions.tasks.send_payment_details_task", member_contribution.pk)
                    messages.success(
                        request,
                        f"Payment of R{member_contribution.amount_due:.2f} for {contribution_type.name} has been recorded successfully!"
                    )
                    messages.info(
                        request,
                        f"You chose {payment_method.replace('_', ' ').title()} as your payment method. We have emailed you banking details. Please upload proof of payment once completed."
                    )
                    return redirect("contributions:member-contribution", id=member_contribution.id)

                elif payment_method == "mobile":
                    # Redirect to Yoco checkout
                    messages.info(request, "Redirecting to Yoco secure payment...")
                    return redirect("contributions:yoco-checkout", payment_id=payment.id)

                else:
                    logger.warning("Unknown payment method: %s", payment_method)
                    messages.error(request, "Invalid payment method selected.")
                    return redirect("contributions:checkout", id=member_contribution.id)
            
            except Exception as e:
                logger.exception("Failed to create payment for contribution %s", id)
                messages.error(request, "An error occurred while recording your payment. Please try again.")
        else:
            logger.warning("PaymentCheckoutForm validation failed for contribution %s", id)
            messages.error(request, "Please fix the errors below.")
      
    else:
        form = PaymentCheckoutForm(user=user, initial={
            "contribution_type": contribution_type,
            "member_contribution": member_contribution,
            "amount": member_contribution.amount_due,
        })
    
    context = {
        "contribution_type": contribution_type,
        "member_contribution": member_contribution,
        "form": form,
        "user": user,
    }
    return render(request, "payments/checkout.html", context)


@login_required
def yoco_checkout(request, payment_id):
    """
    Yoco payment page. Build checkout UI and handle Yoco API calls.
    Yoco will callback to yoco_callback on success/failure.
    """
    payment = get_object_or_404(Payment, id=payment_id, account=request.user)
    member_contribution = payment.member_contribution

    if not member_contribution:
        messages.error(request, "Invalid payment record.")
        return redirect("contributions:member-contributions")

    context = {
        "payment": payment,
        "member_contribution": member_contribution,
        "amount": member_contribution.amount_due,
        "yoco_public_key": getattr(settings, "YOCO_PUBLIC_KEY", ""),
        "reference": member_contribution.reference,
    }
    return render(request, "payments/yoco-checkout.html", context)


@login_required
def yoco_callback(request):
    """
    Yoco callback endpoint. Handle success/failure response from Yoco.
    Yoco will POST transactionId, status, etc. Verify and update Payment record.
    """
    import hmac
    import hashlib

    try:
        yoco_transaction_id = request.POST.get("transactionId")
        yoco_status = request.POST.get("status", "").lower()  # e.g., "success", "failed"
        yoco_signature = request.POST.get("signature")

        if not yoco_transaction_id or not yoco_status:
            logger.warning("Yoco callback missing transactionId or status")
            return render(request, "payments/yoco-callback-error.html", {"error": "Invalid callback data"}, status=400)

        # Verify Yoco signature (optional but recommended)
        secret = getattr(settings, "YOCO_SECRET_KEY", "")
        if secret and yoco_signature:
            expected_sig = hmac.new(
                secret.encode(),
                f"{yoco_transaction_id}{yoco_status}".encode(),
                hashlib.sha256
            ).hexdigest()
            if not hmac.compare_digest(yoco_signature, expected_sig):
                logger.error("Yoco callback signature mismatch for %s", yoco_transaction_id)
                return render(request, "payments/yoco-callback-error.html", {"error": "Signature verification failed"}, status=403)

        # Find payment by transaction reference (or query Yoco API to confirm)
        payment = Payment.objects.filter(payment_method_masked_card=yoco_transaction_id).first()
        if not payment:
            logger.warning("Yoco callback: no matching payment for transaction %s", yoco_transaction_id)
            return render(request, "payments/yoco-callback-error.html", {"error": "Payment not found"}, status=404)

        with transaction.atomic():
            if yoco_status == "success":
                payment.payment_method_masked_card = yoco_transaction_id
                payment.save()
                if payment.member_contribution:
                    payment.update_member_contribution_status(PaymentStatus.PAID)
                logger.info("Yoco payment successful for %s (txn: %s)", payment.account.username, yoco_transaction_id)
                messages.success(request, f"Payment of R{payment.member_contribution.amount_due:.2f} completed successfully!")
                return redirect("contributions:member-contribution", id=payment.member_contribution.id)
            else:
                payment.payment_method_masked_card = yoco_transaction_id
                if payment.member_contribution:
                    payment.update_member_contribution_status(PaymentStatus.NOT_PAID)
                payment.save()
                logger.warning("Yoco payment failed for %s (txn: %s, status: %s)", payment.account.username, yoco_transaction_id, yoco_status)
                messages.error(request, "Payment failed. Please try again or contact support.")
                return redirect("contributions:checkout", id=payment.member_contribution.id)

    except Exception as e:
        logger.exception("Yoco callback error")
        return render(request, "payments/yoco-callback-error.html", {"error": "An error occurred"}, status=500)


from ..forms import LogPaymentForm

@login_required
def log_payment(request, id):
    """
    Treasurer-only view to manually log/record a payment for a member contribution.
    Auto-sends confirmation email to member and marks contribution as PAID.
    """
    # Only treasurers can log payments
    if request.user.role != Role.TREASURER and not request.user.is_staff:
        messages.error(request, "Only treasurers can log payments.")
        return redirect("contributions:member-contributions")

    member_contribution = get_object_or_404(MemberContribution, id=id)
    contribution_type = member_contribution.contribution_type

    if request.method == "POST":
        form = LogPaymentForm(request.POST, request.FILES, treasurer=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    payment = form.save(commit=False)
                    payment.account = member_contribution.account
                    payment.recorded_by = request.user  # treasurer who logged it
                    payment.member_contribution = member_contribution
                    payment.reference = member_contribution.reference
                    payment.is_approved = Payment.LogPaymentStatus.PENDING  # Require approval
                    payment.save()

                    logger.info(
                        "Payment logged by treasurer %s for %s: R%.2f (%s)",
                        request.user.username,
                        member_contribution.account.username,
                        member_contribution.amount_due,
                        payment.payment_method,
                    )

                # Queue confirmation email to member (non-blocking)
                async_task(
                    "contributions.tasks.send_payment_confirmation_task",
                    member_contribution.pk,
                    request.user.get_full_name() or request.user.username,
                )

                messages.success(
                    request,
                    f"Payment of R{member_contribution.amount_due:.2f} for {contribution_type.name} "
                    f"has been recorded. Awaiting approval. Confirmation email sent to {member_contribution.account.email}."
                )
                return redirect("contributions:member-contribution", id=member_contribution.id)

            except Exception as e:
                logger.exception("Failed to log payment for contribution %s", id)
                messages.error(request, "An error occurred while logging payment. Please try again.")
        else:
            logger.warning("LogPaymentForm validation failed: %s", form.errors)
            messages.error(request, "Please fix the errors below.")

    else:
        form = LogPaymentForm(treasurer=request.user, initial={
            "contribution_type": contribution_type,
            "member_contribution": member_contribution,
            "amount": member_contribution.amount_due,
            "reference": member_contribution.reference
        })

    context = {
        "contribution_type": contribution_type,
        "member_contribution": member_contribution,
        "form": form,
        "is_log_payment": True,
    }
    return render(request, "payments/log-payment.html", context)
