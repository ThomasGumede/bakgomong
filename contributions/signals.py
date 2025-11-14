from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from accounts.models import Account# Adjust path to your Account model
from accounts.utils.abstracts import Role
from .models import ContributionType, MemberContribution
from datetime import timedelta, date
from contributions.models import SCOPE_CHOICES
from dateutil.relativedelta import relativedelta

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
    from accounts.utils.abstracts import Role
    """
    Automatically create MemberContribution entries for each active member
    when a new ContributionType is added.
    """
    if not created:
        return

    # Determine who should receive the contribution
    if instance.scope == SCOPE_CHOICES.CLAN:
        members = Account.objects.filter(is_active=True, is_approved=True)
    elif instance.scope == SCOPE_CHOICES.FAMILY and instance.family:
        members = Account.objects.filter(is_active=True, is_approved=True, family=instance.family)
    elif instance.scope == SCOPE_CHOICES.FAMILY_LEADERS:
        members = Account.objects.filter(is_active=True, is_approved=True, role__in=[Role.FAMILY_LEADER])
    elif instance.scope == SCOPE_CHOICES.EXECUTIVES:
        members = Account.objects.filter(is_active=True, is_approved=True, role__in=[Role.CLAN_CHAIRPERSON, Role.DEP_CHAIRPERSON, Role.DEP_SECRETARY, Role.KGOSANA, Role.SECRETARY, Role.TREASURER, Role.FAMILY_LEADER])
    else:
        members = []

    
    due_date = calculate_due_date(instance.recurrence)
    contributions = [
        MemberContribution(
            account=member,
            contribution_type=instance,
            amount_due=instance.amount,
            due_date=instance.due_date or due_date,
            is_paid='NOT PAID',
        )
        for member in members
    ]

    # Bulk create for performance
    MemberContribution.objects.bulk_create(contributions)

    print(f"✅ Created {len(contributions)} member contributions for {instance.name}.")
