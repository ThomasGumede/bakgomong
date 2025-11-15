from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from accounts.models import Account
from accounts.utils.abstracts import Role
from .models import ContributionType, MemberContribution
from contributions.models import SCOPE_CHOICES
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from contributions.tasks import send_contribution_created_notification
import logging

logger = logging.getLogger('infos')


def calculate_due_date(occurrence):
    today = timezone.now().date()

    if occurrence == "monthly":
        return today + relativedelta(months=1)
    if occurrence == "annual":
        return today + relativedelta(years=1)
    if occurrence == "once_off":
        return today + timedelta(days=7)

    return today


@receiver(post_save, sender=ContributionType)
def create_member_contributions(sender, instance, created, **kwargs):
    """
    Automatically creates MemberContribution records for all eligible members
    whenever a new ContributionType is created.
    """

    if not created:
        return

    # Determine target members based on scope
    if instance.scope == SCOPE_CHOICES.CLAN:
        members = Account.objects.filter(is_active=True, is_approved=True)

    elif instance.scope == SCOPE_CHOICES.FAMILY and instance.family:
        members = Account.objects.filter(
            is_active=True,
            is_approved=True,
            family=instance.family
        )

    elif instance.scope == SCOPE_CHOICES.FAMILY_LEADERS:
        members = Account.objects.filter(
            is_active=True,
            is_approved=True,
            role=Role.FAMILY_LEADER
        )

    elif instance.scope == SCOPE_CHOICES.EXECUTIVES:
        members = Account.objects.filter(
            is_active=True,
            is_approved=True,
            role__in=[
                Role.CLAN_CHAIRPERSON,
                Role.DEP_CHAIRPERSON,
                Role.DEP_SECRETARY,
                Role.KGOSANA,
                Role.SECRETARY,
                Role.TREASURER,
                Role.FAMILY_LEADER,
            ]
        )

    else:
        members = []

    if not members:
        print("⚠ No matching members to assign contribution.")
        return

    # Calculate due date
    due_date = calculate_due_date(instance.recurrence)

    # Bulk create contributions
    contributions = []
    for member in members:
        mc = MemberContribution(
            account=member,
            contribution_type=instance,
            amount_due=instance.amount,
            due_date=instance.due_date or due_date,  # or instance.due_date if that field exists
            is_paid="NOT PAID",  # use correct field name
        )
        contributions.append(mc)

    MemberContribution.objects.bulk_create(contributions)

    # Trigger notifications for each entry
    for mc in MemberContribution.objects.filter(contribution_type=instance):
        send_contribution_created_notification(mc.id)

    logger.info(f"✅ Created {len(contributions)} member contributions for: {instance.name}")

