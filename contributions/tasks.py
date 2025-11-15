from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from contributions.utils.sms import send_sms_via_smsportal, send_sms_via_twilio, send_email_notification
from contributions.models import MemberContribution
import logging

logger = logging.getLogger('tasks')


@shared_task
def send_contribution_created_notification(member_contribution_id):
    """
    Notify member immediately when a new MemberContribution is created.
    """
    try:
        mc = MemberContribution.objects.get(id=member_contribution_id)
    except MemberContribution.DoesNotExist:
        return

    contribution = mc.contribution_type
    member = mc.account

    payment_url = f"{settings.SITE_URL}/payments/{mc.id}/pay/"

    message = (
        f"New Contribution Assigned:\n"
        f"{contribution.name}\n"
        f"Amount: R{contribution.amount}\n"
        f"Due: {mc.due_date}\n"
        f"Pay here: {payment_url}"
    )

    # Send SMS
    # if member.phone:
    #     send_sms_via_smsportal(member.phone, message)
    #     send_sms_via_twilio(member.phone, message)

    # Email
    if member.email:
        send_email_notification(
            settings.SITE_URL,
            mc
        )


@shared_task
def send_payment_reminder():
    """
    Daily task: Remind members 10 days before + on due date + 10 days after.
    """
    today = timezone.now().date()

    # 10 days before deadline
    upcoming = MemberContribution.objects.filter(
        due_date=today + timedelta(days=10),
        is_paid=False
    )

    # On the due date
    due_today = MemberContribution.objects.filter(
        due_date=today,
        is_paid=False
    )

    # 10 days after overdue
    overdue = MemberContribution.objects.filter(
        due_date=today - timedelta(days=10),
        is_paid=False
    )

    for mc in list(upcoming) + list(due_today) + list(overdue):
        contribution = mc.contribution_type
        member = mc.member

        payment_url = f"{settings.SITE_URL}/payments/{mc.id}/pay/"

        message = (
            f"Payment Reminder:\n"
            f"Contribution: {contribution.name}\n"
            f"Amount: R{contribution.amount}\n"
            f"Due: {mc.due_date}\n"
            f"Pay here: {payment_url}"
        )

        # SMS
        if member.phone:
            send_sms_via_smsportal(member.phone, message)
            send_sms_via_twilio(member.phone, message)

        # Email
        if member.email:
            send_email_notification(
                to=member.email,
                subject="Contribution Payment Reminder",
                message=message
            )
