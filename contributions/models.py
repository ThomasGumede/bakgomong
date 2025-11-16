from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from accounts.models import Family
from accounts.utils.abstracts import AbstractCreate, AbstractPayment
from django.contrib.auth import get_user_model

from django.db.models import Sum
import random
import uuid
from django.utils.crypto import get_random_string
from django.db import transaction

from accounts.utils.validators import verify_rsa_phone

PHONE_VALIDATOR = verify_rsa_phone()

class PaymentMethod(models.TextChoices):
        CASH = 'cash', _('Cash')
        BANK = 'bank', _('Bank Deposit')
        MOBILE = 'mobile', _('Yoco Mobile Payment')
        OTHER = 'other', _('Other')

class SCOPE_CHOICES(models.TextChoices):
        CLAN = "clan", _("Entire Clan")
        FAMILY_LEADERS = "family_leaders", _("Family Leaders")
        FAMILY = "family", _("Specific Family")
        EXECUTIVES = "executives", _("Executives")

class ContributionType(AbstractCreate):
    class Recurrence(models.TextChoices):
        ONCE_OFF = 'once_off', _('Once Off')
        MONTHLY = 'monthly', _('Monthly')
        ANNUAL = 'annual', _('Annual')

    # 🧱 StokFella-style contribution categories
    class Category(models.TextChoices):
        EVENT = 'event', _('Event / Celebration')
        BURIAL = 'burial', _('Burial / Funeral Fund')
        SAVINGS = 'savings', _('Savings / Stokvel')
        INVESTMENT = 'investment', _('Investment Fund')
        BUSINESS = 'business', _('Business or Income Project')
        HOLIDAY = 'holiday', _('Holiday / Travel Fund')
        GROCERY = 'grocery', _('Grocery / Monthly Food Club')
        EMERGENCY = 'emergency', _('Emergency Support')
        EDUCATION = 'education', _('Education or Skills Fund')
        OTHER = 'other', _('Other')
        

    name = models.CharField(
        max_length=100,
        help_text=_("Enter contribution name (e.g. Monthly Clan Fee or Funeral Fund)"),
    )
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(
        max_length=50,
        choices=Category.choices,
        default=Category.OTHER,
        help_text=_("Select the contribution category (e.g. Burial, Savings, Event)"),
    )
    family = models.ForeignKey(Family, on_delete=models.SET_NULL, null=True, blank=True, related_name='family_contribution_types')
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text=_("Default amount to be contributed for this type"),
    )
    recurrence = models.CharField(
        max_length=20,
        choices=Recurrence.choices,
        default=Recurrence.ONCE_OFF,
        help_text=_("Specify if this contribution is once-off, monthly, or annual"),
    )
    scope = models.CharField(max_length=20, choices=SCOPE_CHOICES, default=SCOPE_CHOICES.CLAN)
    due_date = models.DateField(blank=True, null=True, help_text=_("For Annual and Once-off contributions"))
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_contributions",
    )
    

    class Meta:
        verbose_name = _("Contribution Type")
        verbose_name_plural = _("Contribution Types")
        ordering = ["-created"]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def save(self, *args, **kwargs):
        # ensure unique slug (append counter when needed)
        base = slugify(self.name) or "contribution"
        if not self.slug or slugify(self.slug) != base:
            slug = base
            counter = 1
            while ContributionType.objects.filter(slug=slug).exclude(pk=getattr(self, "pk", None)).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
        
    def clean(self):
        """
        Enforce family selection when scope is 'family',
        and ensure family is None for other scopes.
        """
        from django.core.exceptions import ValidationError

        if self.scope == SCOPE_CHOICES.FAMILY and not self.family:
            raise ValidationError("A family must be selected when scope is 'Specific Family'.")

        if self.scope != SCOPE_CHOICES.FAMILY and self.family is not None:
            raise ValidationError("Family should only be set for 'Specific Family' scope.")
            
    @property
    def total_collected(self):
        from .models import Payment 
        result = Payment.objects.filter(contribution_type=self).aggregate(total=Sum("amount"))
        return result["total"] or 0
    
    def get_absolute_url(self):
        return reverse("contributions:get-contribution", kwargs={"contribution_slug": self.slug})
    
    def get_update_url(self):
        return reverse("contributions:update-contribution", kwargs={"contribution_slug": self.slug})
    

class MemberContribution(AbstractCreate):
    from accounts.utils.abstracts import PaymentStatus
    
    account = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="member_contributions")
    contribution_type = models.ForeignKey(ContributionType, on_delete=models.CASCADE, related_name="member_contributions")
    amount_due = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True, null=True, help_text=_("Receipt or transaction reference"), unique=True)
    due_date = models.DateField(blank=True, null=True)
    is_paid = models.CharField(max_length=100, choices=PaymentStatus.choices, default=PaymentStatus.NOT_PAID, db_index=True)
    

    class Meta:
        verbose_name = _("Member Contribution")
        verbose_name_plural = _("Member Contributions")
        unique_together = ('account', 'contribution_type', 'due_date')
        ordering = ["-created"]

    def __str__(self):
        return f"{self.account.get_full_name()} - {self.contribution_type.name}"

    @property
    def balance(self):
        # consistent calculation using DB aggregation
        result = self.payments.aggregate(total=Sum("amount"))
        total_paid = result.get("total") or 0
        return self.amount_due - total_paid
    
    def save(self, *args, **kwargs):
        # reference has default UUID; ensure not overwritten on update
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        return reverse("contributions:member-contribution", kwargs={"id": self.id}) 


class Payment(AbstractCreate, AbstractPayment):
    
    
    
    
    checkout_id = models.CharField(max_length=200, unique=True, null=True, blank=True, db_index=True)
    
    account = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="payments")
    contribution_type = models.ForeignKey(ContributionType, on_delete=models.SET_NULL, null=True, related_name="payments")
    member_contribution = models.ForeignKey(MemberContribution, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True, null=True, help_text=_("Receipt or transaction reference"))
    payment_date = models.DateField(auto_now_add=True)
    recorded_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, related_name="recorded_payments")
    

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        ordering = ["-payment_date"]

    def __str__(self):
        return f"{self.account.get_full_name()} - {self.amount} "

    def update_member_contribution_status(self, status):
        
        """Automatically update member contribution payment status."""
        if not self.member_contribution:
            return

        self.member_contribution.is_paid = status
        self.member_contribution.save()
    
    def save(self, *args, **kwargs):
        from accounts.utils.abstracts import PaymentStatus
        # save payment and then atomically update related member_contribution status
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.member_contribution:
                # recalc total paid for the member contribution
                total_paid = self.member_contribution.payments.aggregate(total=Sum("amount")).get("total") or 0
                if total_paid >= self.member_contribution.amount_due:
                    new_status = PaymentStatus.PAID
                else:
                    new_status = PaymentStatus.PARTIALLY_PAID if total_paid > 0 else PaymentStatus.NOT_PAID
                # only save when status changes
                if self.member_contribution.is_paid != new_status:
                    self.member_contribution.is_paid = new_status
                    self.member_contribution.save()


