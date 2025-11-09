from contributions.models import ContributionType, MemberContribution, Payment
from django.contrib import admin
from django.contrib import messages

@admin.register(ContributionType)
class ContributionTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "amount", "recurrence", "due_date", "created_by", "created")
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("recurrence",)
    search_fields = ("name", "description")
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            messages.success(
                request,
                f"Automatically created contributions for all members under '{obj.name}'."
            )

@admin.register(MemberContribution)
class MemberContributionAdmin(admin.ModelAdmin):
    list_display = ("account", "contribution_type", "amount_due", "due_date", "is_paid")
    list_filter = ("is_paid", "due_date", "contribution_type")
    search_fields = ("account__full_name",)
    readonly_fields = ("created", "updated")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("account", "contribution_type", "amount", "payment_method", "payment_date", "recorded_by")
    list_filter = ("payment_method", "payment_date", "contribution_type")
    search_fields = ("account__full_name", "reference")
