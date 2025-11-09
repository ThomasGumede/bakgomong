# contributions/forms.py
from django import forms
from .models import ContributionType, MemberContribution, Payment
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum

class MemberContributionForm(forms.ModelForm):
    class Meta:
        model = MemberContribution
        fields = [
            'account', 'contribution_type', 'amount_due', 
            'reference', 'due_date', 'is_paid'
        ]
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: filter contribution_type to active contributions only
        self.fields['contribution_type'].queryset = ContributionType.objects.all()
        # Optional: filter account to active members only
        self.fields['account'].queryset = get_user_model().objects.all()


class ContributionTypeForm(forms.ModelForm):
    class Meta:
        model = ContributionType
        fields = [
            'name', 'description', 'category', 'amount', 
            'recurrence', 'due_date'
        ]
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'category': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
            'recurrence': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs['autocomplete'] = 'off'
            if self.initial.get(field_name) is None:
                self.initial[field_name] = ''


class MemberContributionForm(forms.ModelForm):
    class Meta:
        model = MemberContribution
        fields = [
            'account', 'contribution_type', 'amount_due', 
            'reference', 'due_date', 'is_paid'
        ]
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }
        
class PaymentCheckoutForm(forms.ModelForm):

    class Meta:
        model = Payment
        fields = ('contribution_type', 'member_contribution', 'amount', 'payment_method')

        widgets = {
            'contribution_type': forms.Select(attrs={
                "class": "form-control rounded-lg form-select",
                "placeholder": "Select Contribution Type"
            }),
            'member_contribution': forms.Select(attrs={
                "class": "form-control rounded-lg form-select",
                "placeholder": "Select Member Contribution"
            }),
            'amount': forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter Contribution Amount e.g R100",
                "step": "0.01"
            }),
            'payment_method': forms.Select(attrs={
                "class": "form-control rounded-lg form-select",
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Filter active contribution types
        self.fields['contribution_type'].queryset = ContributionType.objects.all().order_by('name')

        # Limit member_contribution to current user
        if user:
            self.fields['member_contribution'].queryset = MemberContribution.objects.filter(
                account=user, is_paid='NOT PAID'
            ).select_related('contribution_type')

    def clean(self):
        cleaned_data = super().clean()
        member_contribution = cleaned_data.get("member_contribution")
        contribution_type = cleaned_data.get("contribution_type")
        amount = cleaned_data.get("amount")

        if member_contribution and contribution_type:
            # Ensure the selected contribution matches the member_contribution type
            if member_contribution.contribution_type != contribution_type:
                raise ValidationError(_("The selected member contribution does not match the contribution type."))

            # Validate payment amount
            # total_paid = member_contribution.payments.aggregate(total=Sum('amount'))['total'] or 0
            # total_unpaid = MemberContribution.objects.filter(account=member_contribution.account, contribution_type=contribution_type).aggregate(total=Sum('amount_due'))['total'] or 0
            # remaining = total_unpaid - total_paid
            if member_contribution.amount_due > amount:
                raise ValidationError(_(f"Payment exceeds outstanding balance (Required: R{amount:.2f})."))
            
            if member_contribution.amount_due < amount:
                raise ValidationError(_(f"Payment below outstanding balance (Required: R{amount:.2f})."))

        return cleaned_data

