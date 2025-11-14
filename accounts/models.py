from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.dispatch import receiver
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import pre_delete, post_save
from accounts.utils.abstracts import AbstractCreate, AbstractProfile, Gender, Title, Role, PaymentStatus
from accounts.utils.file_handlers import handle_profile_upload
from django.db.models import Sum

class Family(AbstractCreate):
    name = models.CharField(max_length=300, help_text=_('Enter family name e.g Dladla Family'), unique=True)
    slug = models.SlugField(max_length=400, unique=True, db_index=True)
    leader = models.OneToOneField('Account', related_name='family_leader', on_delete=models.SET_NULL, null=True, blank=True)
    is_approved = models.BooleanField(default=False, help_text=_("Should be approved by executives"))
    
    class Meta:
        verbose_name = _("Family")
        verbose_name_plural = _("Families")
        ordering = ["-created"]
        
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Family, self).save(*args, **kwargs)
        
    @property
    def total_unpaid(self):
        from contributions.models import MemberContribution
        result = MemberContribution.objects.filter(account__family=self, is_paid=PaymentStatus.NOT_PAID).aggregate(total=Sum("amount_due"))
        return result["total"] or 0
    
    @property
    def total_paid(self):
        from contributions.models import MemberContribution
        result = MemberContribution.objects.filter(account__family=self, is_paid=PaymentStatus.PAID).aggregate(total=Sum("amount_due"))
        return result["total"] or 0

class Account(AbstractUser, AbstractProfile):
    profile_image = models.ImageField(help_text=_("Upload profile image"), upload_to=handle_profile_upload, null=True, blank=True)
    title = models.CharField(max_length=30, choices=Title)
    gender = models.CharField(max_length=30, choices=Gender)
    maiden_name = models.CharField(help_text=_("Enter your maiden name"), max_length=300, blank=True, null=True)
    biography = models.TextField(blank=True)
    role = models.CharField(max_length=100, choices=Role.choices, default=Role.MEMBER)
    family = models.ForeignKey(Family, related_name='members', on_delete=models.SET_NULL, null=True, blank=True)
    is_approved = models.BooleanField(default=False, help_text=_("Should be approved by executives"))
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Account")
        verbose_name_plural = _("Accounts")
        ordering = ["-created"]
        
    def __str__(self):
        return self.get_full_name()
    
    @property
    def total_unpaid(self):
        from contributions.models import MemberContribution
        result = MemberContribution.objects.filter(account=self, is_paid=PaymentStatus.NOT_PAID).aggregate(total=Sum("amount_due"))
        return result["total"] or 0
    
    @property
    def total_paid(self):
        from contributions.models import MemberContribution
        result = MemberContribution.objects.filter(account=self, is_paid=PaymentStatus.PAID).aggregate(total=Sum("amount_due"))
        return result["total"] or 0


