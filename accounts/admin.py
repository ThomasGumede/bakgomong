from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin
import logging
from django.db.models import Count

from accounts.models import Account, Family
from accounts.utils.abstracts import Role

logger = logging.getLogger("accounts")

@admin.action(description="Approve selected members/family")
def approve_members(modeladmin, request, queryset):
    if not request.user.role in [Role.CLAN_CHAIRPERSON, Role.DEP_CHAIRPERSON, Role.DEP_SECRETARY, Role.KGOSANA, Role.SECRETARY, Role.TREASURER, Role.FAMILY_LEADER]:
        messages.error(request, "Only executives are allowed to approve members.")
        return
    
    queryset.update(
        is_approved=True,
    )
    messages.success(request, f"{queryset.count()} member(s) or families approved successfully.")

# ------------------------------------------------------------
# Inline display: show all members under a family
# ------------------------------------------------------------
class AccountInline(admin.TabularInline):
    model = Account
    fields = ("first_name", "email", "phone", "role", "is_active", "is_approved")
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
        # use annotated value if present to avoid extra query
        return getattr(obj, "member_count", obj.members.count())
    member_count.short_description = _("Members")
    
    list_display = ("name", "leader_display", "member_count", "created", "is_approved")
    search_fields = ("name", "leader__first_name", "leader__email")
    list_filter = ("created", "is_approved",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [AccountInline]
    ordering = ("-created",)
    actions = [approve_members]
    raw_id_fields = ("leader",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # annotate member counts once
        return qs.annotate(member_count=Count("members"))


# ------------------------------------------------------------
# Account Admin
# ------------------------------------------------------------
@admin.register(Account)
class AccountAdmin(UserAdmin):
    def profile_image_preview(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" width="50" height="50" style="border-radius:50%;" />', obj.profile_image.url)
        return "—"
    profile_image_preview.short_description = _("Profile Image Preview")
    
    list_display = ("profile_image_preview", "username", "first_name", "email", "family", "role", "is_active", "is_approved")
    list_filter = ("role", "is_active", "gender",)
    search_fields = ("username", "first_name", "email", "phone", "family__name")
    list_select_related = ("family",)
    autocomplete_fields = ("family",)
    ordering = ("-created",)
    readonly_fields = ("created", "updated", "profile_image_preview")
    actions = [approve_members]
    add_fieldsets = (
        ("Personal Info", {
            "fields": (
                "profile_image_preview",
                "profile_image",
                "username",
                "first_name",
                "last_name",
                "email",
                "title",
                "gender",
                "password1",
                "password2",
                
            ),
        }),
        ("Member Info", {
            "fields": (
                "biography", 
            ),
        }),
        ("Contact & Socials", {
            "fields": (
                "phone",
                "address",
                "facebook",
                "twitter",
                "instagram",
                "linkedIn",
            ),
        }),
        
        ("Permissions", {
            "fields": (
                "role",
                "family",
                "is_active",
                "is_staff",
                "is_approved",
                "is_superuser",
                "groups",
                
            ),
        }),
        ("Important Dates", {
            "fields": ("last_login", "created", "updated"),
        }),
    )
    fieldsets = (
        (_("Personal Information"), {
            "fields": (
                "profile_image",
                "profile_image_preview",
                "title",
                "first_name",
                "last_name",
                "email",
                "phone",
                "gender",
                "maiden_name",
                "biography",
            )
        }),
        ("Contact & Socials", {
            "fields": (
                "facebook",
                "twitter",
                "instagram",
                "linkedIn",
            ),
        }),
        (_("Clan Information"), {
            "fields": ("role", "family")
        }),
        (_("Permissions & Status"), {
            "fields": ("is_active", "is_staff", "is_superuser", "is_approved", "groups",)
        }),
        (_("Timestamps"), {
            "fields": ("created", "updated")
        }),
    )


