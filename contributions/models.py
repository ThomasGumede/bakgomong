from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from accounts.utils.abstracts import AbstractCreate, AbstractPayment
from django.contrib.auth import get_user_model

from django.db.models import Sum
import random

from accounts.utils.validators import verify_rsa_phone

PHONE_VALIDATOR = verify_rsa_phone()

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
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
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
    is_paid = models.CharField(max_length=100, choices=PaymentStatus.choices, default=PaymentStatus.NOT_PAID)
    

    class Meta:
        verbose_name = _("Member Contribution")
        verbose_name_plural = _("Member Contributions")
        unique_together = ('account', 'contribution_type', 'due_date')
        ordering = ["-created"]

    def __str__(self):
        return f"{self.account.get_full_name()} - {self.contribution_type.name}"

    @property
    def balance(self):
        total_paid = sum(payment.amount for payment in self.payments.all())
        return self.amount_due - total_paid
    
    def generate_reference(self):
        while True:
            ref = f"CLN-{random.randint(100000, 999999)}"
            if not MemberContribution.objects.filter(reference=ref).exists():
                return ref
            
    def save(self, *args, **kwargs):
        # Automatically generate reference if not set
        if not self.reference:
            self.reference = self.generate_reference()
        super().save(*args, **kwargs)
        
    def get_absolute_url(self):
        return reverse("contributions:member-contribution", kwargs={"id": self.id}) 


class Payment(AbstractCreate, AbstractPayment):
    
    
    class PaymentMethod(models.TextChoices):
        CASH = 'cash', _('Cash')
        BANK = 'bank', _('Bank Deposit')
        MOBILE = 'mobile', _('Mobile Payment')
        OTHER = 'other', _('Other')
    
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
        return f"{self.account.get_full_name()} - {self.amount} ({self.contribution_type.name})"

    def update_member_contribution_status(self, status):
        
        """Automatically update member contribution payment status."""
        if not self.member_contribution:
            return

        self.member_contribution.is_paid = status
        self.member_contribution.save()
    
    def save(self, *args, **kwargs):
        from accounts.utils.abstracts import PaymentStatus
        super().save(*args, **kwargs)
        # ✅ Automatically update member contribution status
        # if self.member_contribution:
        #     total_paid = sum(p.amount for p in self.member_contribution.payments.all())
        #     if total_paid >= self.member_contribution.amount_due:
        #         self.member_contribution.is_paid = PaymentStatus.PAID
        #         self.member_contribution.save()


