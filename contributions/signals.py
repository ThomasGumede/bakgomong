from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from accounts.models import Account# Adjust path to your Account model
from accounts.utils.abstracts import Role
from .models import ContributionType, MemberContribution
from datetime import timedelta


@receiver(post_save, sender=ContributionType)
def create_member_contributions(sender, instance, created, **kwargs):
    """
    Automatically create MemberContribution entries for each active member
    when a new ContributionType is added.
    """
    if not created:
        return  # Only run on creation, not updates

    active_members = Account.objects.filter(is_active=True, role__in=[Role.FAMILY_LEADER, Role.MEMBER, Role.CLAN_CHAIRPERSON])
    
    contributions = [
        MemberContribution(
            account=member,
            contribution_type=instance,
            amount_due=instance.amount,
            due_date=instance.due_date or timezone.now().date(),
            is_paid=False,
        )
        for member in active_members
    ]

    # Bulk create for performance
    MemberContribution.objects.bulk_create(contributions)

    print(f"✅ Created {len(contributions)} member contributions for {instance.name}.")
