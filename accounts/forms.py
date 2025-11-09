from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import (AuthenticationForm,  UserCreationForm)
from django.utils.translation import gettext_lazy as _
from accounts.models import Family

class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)
    
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username or Email', 'id': 'id_username'}), label="Username or Email*")
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'id': 'id_password'}))

class RegistrationForm(UserCreationForm):
    """Custom registration form for the Clan Contribution Tracker."""

    class Meta:
        model = get_user_model()
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')

        widgets = {
            'email': forms.EmailInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("Enter your email address"),
            }),
            'first_name': forms.TextInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("First name"),
            }),
            'last_name': forms.TextInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("Last name"),
            }),
            'password1': forms.PasswordInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("Enter password"),
            }),
            'password2': forms.PasswordInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("Confirm password"),
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs['autocomplete'] = 'off'
            if self.initial.get(field_name) is None:
                self.initial[field_name] = ''

    def clean_email(self):
        """Ensure email uniqueness across users."""
        email = self.cleaned_data.get("email")
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                _(f"This email ({email}) is already registered.")
            )
        return email

    def save(self, commit=True):
        """Save the user with email as username."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email'] 
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            if hasattr(self, "save_m2m"):
                self.save_m2m()
        return user


class MemberForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = ("username", "title", "role", "profile_image", "first_name", "last_name", 'maiden_name', "biography", "gender", "email", "phone", "address", 'password1', 'password2')

        widgets = {
            'email': forms.EmailInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("Enter your email address"),
            }),
            'first_name': forms.TextInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("First name"),
            }),
            'last_name': forms.TextInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("Last name"),
            }),
            'password1': forms.PasswordInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("Enter password"),
            }),
            'password2': forms.PasswordInput(attrs={
                "class": "w-full px-8 py-4 rounded-lg font-medium bg-gray-100 border border-gray-200 placeholder-gray-500 text-sm focus:outline-none focus:border-gray-400 focus:bg-white",
                "placeholder": _("Confirm password"),
            }),
            'gender': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
            'title': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
            'role': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs['autocomplete'] = 'off'
            if self.initial.get(field_name) is None:
                self.initial[field_name] = ''

    def clean_email(self):
        """Ensure email uniqueness across users."""
        email = self.cleaned_data.get("email")
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                _(f"This email ({email}) is already registered.")
            )
        return email

    def save(self, commit=True):
        """Save the user with email as username."""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            if hasattr(self, "save_m2m"):
                self.save_m2m()
        return user
    
class AccountUpdateForm(forms.ModelForm):
    
    class Meta:
        model = get_user_model()
        fields = ["username", "title", "profile_image", "first_name", "last_name", 'maiden_name', "biography", "gender", "email", "phone", "address"]

        widgets = {
            'username': forms.TextInput(attrs={"class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"}),
            'title': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
            'first_name': forms.TextInput(attrs={"class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"}),
            'maiden_name': forms.TextInput(attrs={"class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"}),
            'last_name': forms.TextInput(attrs={"class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"}),
            #'hobbies': forms.TextInput(attrs={"class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"}),
            'gender': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super(AccountUpdateForm, self).__init__(*args, **kwargs)
        for field_name, field_value in self.initial.items():
            if field_value is None:
                self.initial[field_name] = ''
     
class GeneralEditForm(forms.ModelForm):
    """
        Form to edit only username and email
    """
    class Meta:
        model = get_user_model()
        fields = ["username", "email", "phone", "address"]

        widgets = {
            'address_one': forms.TextInput(attrs={"class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"}),
            'address_two': forms.TextInput(attrs={"class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"}),
            'city': forms.TextInput(attrs={"class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"}),
            'country': forms.TextInput(attrs={"value": "South Africa", "class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"}),
            'province': forms.Select(attrs={"class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"}),
            'zipcode': forms.NumberInput(attrs={"class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"})
        }

    def __init__(self, *args, **kwargs):
        super(GeneralEditForm, self).__init__(*args, **kwargs)
        for field_name, field_value in self.initial.items():
            if field_value is None:
                self.initial[field_name] = ''

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        email = cleaned_data.get("email")
        if get_user_model().objects.exclude(pk=self.instance.pk).filter(username=username).exists():
            raise forms.ValidationError(f'This username: {username} is already in use.')
        
        if get_user_model().objects.exclude(pk=self.instance.pk).filter(email=email).exists():
            raise forms.ValidationError(f'This email: {email} is already in use.')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super(GeneralEditForm, self).save(commit=False)
        email = self.cleaned_data['email']
        if commit:
            user.save()
            
        return user

class SocialLinksForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ("facebook", "twitter", "instagram", "linkedIn")

class FamilyForm(forms.ModelForm):
    class Meta:
        model = Family
        fields = ('name', 'leader')
        
        widgets = {
            'name': forms.TextInput(attrs={"class": "text-custom-text pl-5 pr-[50px] outline-none border-2 border-[#e4ecf2] focus:border focus:border-custom-primary h-[65px] block w-full rounded-none focus:ring-0 focus:outline-none placeholder:text-custom-text placeholder:text-sm"}),
            'leader': forms.Select(attrs={"class": "form-control rounded-lg form-select"}),
            
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field_name, field in self.fields.items():
            field.widget.attrs['autocomplete'] = 'off'
            if self.initial.get(field_name) is None:
                self.initial[field_name] = ''
        