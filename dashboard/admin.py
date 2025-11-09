from django.contrib import admin
from dashboard.models import ClanDocument, Meeting
from django.db import models
from accounts.utils.abstracts import Role

# Register your models here.
@admin.register(ClanDocument)
class ClanDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "visibility", "family", "uploaded_by", "created")
    list_filter = ("visibility", "category", "family")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user

        # Admins see all documents
        if user.is_superuser or getattr(user, "role", "") == Role.CLAN_CHAIRPERSON:
            return qs

        # Family leaders see their family's documents
        if getattr(user, "role", "") == Role.FAMILY_LEADER:
            return qs.filter(models.Q(visibility="clan") | models.Q(family=user.family))

        # Regular members see only clan-wide and their family’s documents
        return qs.filter(
            models.Q(visibility="clan") |
            models.Q(family=user.family, visibility="family")
        )

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("title", "meeting_type", "audience", "meeting_date", "created_by", "family")
    list_filter = ("meeting_type", "audience", "meeting_date", "family")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    ordering = ("-meeting_date",)
