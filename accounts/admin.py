from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from accounts.models import Account, Family


# ------------------------------------------------------------
# Inline display: show all members under a family
# ------------------------------------------------------------
class AccountInline(admin.TabularInline):
    model = Account
    fields = ("first_name", "email", "phone", "role", "is_active")
    extra = 0
    readonly_fields = ("first_name", "email", "phone", "role")
    can_delete = False
    show_change_link = True


# ------------------------------------------------------------
# Family Admin
# ------------------------------------------------------------
@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    def leader_display(self, obj):
        return obj.leader.first_name if obj.leader else "—"
    leader_display.short_description = _("Leader")

    def member_count(self, obj):
        return obj.members.count() if hasattr(obj, 'members') else obj.families.count()
    member_count.short_description = _("Members")
    
    list_display = ("name", "leader_display", "member_count", "created")
    search_fields = ("name", "leader__first_name")
    list_filter = ("created",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [AccountInline]
    ordering = ("-created",)


# ------------------------------------------------------------
# Account Admin
# ------------------------------------------------------------
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    def profile_image_preview(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:50%;" />', obj.profile_image.url)
        return "—"
    profile_image_preview.short_description = _("Profile Image Preview")
    
    list_display = ("profile_image_preview", "first_name", "email", "family", "role", "is_active", "created")
    list_filter = ("role", "is_active", "gender", "family")
    search_fields = ("first_name", "email", "phone")
    ordering = ("-created",)
    readonly_fields = ("created", "updated", "profile_image_preview")

    fieldsets = (
        (_("Personal Information"), {
            "fields": (
                "profile_image",
                "profile_image_preview",
                "title",
                "first_name",
                "email",
                "phone",
                "gender",
                "maiden_name",
                "biography",
            )
        }),
        (_("Clan Information"), {
            "fields": ("role", "family")
        }),
        (_("Permissions & Status"), {
            "fields": ("is_active", "is_staff", "is_superuser")
        }),
        (_("Timestamps"), {
            "fields": ("created", "updated")
        }),
    )

    
