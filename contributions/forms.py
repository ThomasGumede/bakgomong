from decimal import Decimal, InvalidOperation
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from .models import ContributionType, MemberContribution, Payment
from django.contrib.auth import get_user_model
from accounts.utils.abstracts import PaymentStatus

class MemberContributionForm(forms.ModelForm):
    class Meta:
        model = MemberContribution
        fields = [
            "account",
            "contribution_type",
            "amount_due",
            "reference",
            "due_date",
            "is_paid",
        ]
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        # Limit contribution types if you have family- or active-flag
        self.fields["contribution_type"].queryset = ContributionType.objects.all().order_by("name")
        # If creating/updating for a specific user, restrict account choices
        if user and not user.is_staff:
            self.fields["account"].queryset = get_user_model().objects.filter(pk=user.pk)
        else:
            self.fields["account"].queryset = get_user_model().objects.all()
        # reference is normally generated — keep readonly in form when present
        if not self.instance or not self.instance.pk:
            self.fields["reference"].widget.attrs["readonly"] = True


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
                account=user, is_paid=PaymentStatus.NOT_PAID
            ).select_related('contribution_type')
        else:
            # don't expose other users' contributions in the checkout
            self.fields['member_contribution'].queryset = MemberContribution.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        member_contribution = cleaned_data.get("member_contribution")
        contribution_type = cleaned_data.get("contribution_type")
        amount = cleaned_data.get("amount")

        if member_contribution and contribution_type:
            # Ensure the selected contribution matches the member_contribution type
            if member_contribution.contribution_type != contribution_type:
                raise ValidationError(_("The selected member contribution does not match the contribution type."))

            # Ensure amount is a valid Decimal and positive
            try:
                amt = Decimal(amount)
            except (InvalidOperation, TypeError):
                raise ValidationError(_("Enter a valid payment amount."))
            if amt <= 0:
                raise ValidationError(_("Payment amount must be greater than zero."))

            outstanding = Decimal(member_contribution.amount_due)
            # By default require exact payment to clear the contribution. If you support partials,
            # change this check to allow amt <= outstanding.
            if amt != outstanding:
                raise ValidationError(
                    _(f"Payment amount must equal outstanding balance: R{outstanding:.2f}.")
                )

            # Ensure the member contribution belongs to the current user (extra safety)
            request_user = getattr(self, "_current_user", None)
            # some callers set form._current_user after instantiation; if not available, skip strict check
            if request_user and member_contribution.account != request_user:
                raise ValidationError(_("You cannot pay for another member's contribution."))

        return cleaned_data

