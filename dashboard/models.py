from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.core.exceptions import PermissionDenied
from accounts.utils.abstracts import Role, AbstractCreate
from accounts.models import Family
from django.contrib.auth import get_user_model
from django.utils import timezone


class ClanDocument(AbstractCreate):
    class Visibility(models.TextChoices):
        CLAN = "clan", _("Entire Clan")
        FAMILY = "family", _("Specific Family")
        PRIVATE = "private", _("Private (Admin Only)")

    class Category(models.TextChoices):
        MINUTES = "minutes", _("Meeting Minutes")
        REPORT = "report", _("Financial / Contribution Report")
        EVENT = "event", _("Event Notice or Program")
        POLICY = "policy", _("Policy / Constitution")
        OTHER = "other", _("Other")

    title = models.CharField(max_length=255, help_text=_("Enter the document title"))
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=30, choices=Category.choices, default=Category.OTHER)
    file = models.FileField(upload_to="clan_documents/%Y/%m/")
    uploaded_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_documents"
    )
    family = models.ForeignKey(
        Family,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documents",
        help_text=_("Optional: restrict this document to a specific family"),
    )
    visibility = models.CharField(
        max_length=20,
        choices=Visibility.choices,
        default=Visibility.CLAN,
        help_text=_("Who can access this document"),
    )

    class Meta:
        verbose_name = _("Clan Document")
        verbose_name_plural = _("Clan Documents")
        ordering = ["-created"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    # -----------------------------------------------
    # 🔐 ACCESS CONTROL LOGIC
    # -----------------------------------------------
    def user_has_access(self, user):
        """
        Determines if a given user can view/download this document.
        """
        # Unauthenticated users have no access
        if not user.is_authenticated:
            return False

        # Admins can access everything
        if getattr(user, "role", None) == Role.CLAN_CHAIRPERSON or user.is_superuser:
            return True

        # Clan-wide document
        if self.visibility == self.Visibility.CLAN:
            return True

        # Family-only document
        if self.visibility == self.Visibility.FAMILY:
            if self.family and user.family == self.family:
                return True
            return False

        # Private (Admin-only)
        if self.visibility == self.Visibility.PRIVATE:
            return False

        return False

    def ensure_user_has_access(self, user):
        """
        Raises PermissionDenied if user doesn't have access.
        Useful in views or API endpoints.
        """
        if not self.user_has_access(user):
            raise PermissionDenied(_("You do not have permission to access this document."))
        return True

    def file_name(self):
        return self.file.name.split('/')[-1]

class Meeting(AbstractCreate):
    class MeetingType(models.TextChoices):
        ONLINE = "online", _("Online Meeting")
        IN_PERSON = "in_person", _("Live / In-Person Meeting")

    class Audience(models.TextChoices):
        CLAN = "clan", _("Entire Clan")
        FAMILY_LEADERS = "family_leaders", _("Family Leaders")
        EXECUTIVES = "executives", _("Clan Executives")
        FAMILY = "family", _("Specific Family")

    title = models.CharField(max_length=150, help_text=_("Enter meeting title"))
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True, null=True)
    meeting_type = models.CharField(
        max_length=20,
        choices=MeetingType.choices,
        default=MeetingType.IN_PERSON,
        help_text=_("Specify whether this meeting is online or in-person."),
    )
    meeting_venue = models.CharField(max_length=150, help_text=_("Meeting Venue for in-person meetings"), blank=True, null=True)
    meeting_link = models.URLField(
        blank=True,
        null=True,
        help_text=_("Link for online meetings (e.g., Zoom, Google Meet)."),
    )
    audience = models.CharField(
        max_length=30,
        choices=Audience.choices,
        default=Audience.CLAN,
        help_text=_("Specify who this meeting is for."),
    )
    meeting_date = models.DateTimeField(help_text=_("Start date and time of the meeting"))
    meeting_end_date = models.DateTimeField(help_text=_("End date and time of the meeting"))
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        related_name="meetings_created",
        help_text=_("User who created this meeting"),
    )
    family = models.ForeignKey(
        Family,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="meetings",
        help_text=_("Optional: assign this meeting to a specific family if needed."),
    )
    

    class Meta:
        verbose_name = _("Meeting")
        verbose_name_plural = _("Meetings")
        ordering = ["-meeting_date"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.title}-{self.meeting_date.strftime('%Y%m%d%H%M')}")
        super().save(*args, **kwargs)
        
    @property
    def date_time_formatter(self):
        start_local = timezone.localtime(self.meeting_date)
        end_local = timezone.localtime(self.meeting_end_date)
        if start_local.date() == end_local.date():
            return f"{start_local.strftime('%a %d %b %Y')}, {start_local.strftime('%H:%M')} - {end_local.strftime('%H:%M')}"
        else:
            return f"{start_local.strftime('%a %d %b %Y, %H:%M')} - {end_local.strftime('%a %d %b %Y, %H:%M')}"

    # ---------------------------------------------
    # 🧠 Helper Methods
    # ---------------------------------------------
    def is_online(self):
        return self.meeting_type == self.MeetingType.ONLINE

    def is_for_clan(self):
        return self.audience == self.Audience.CLAN

    def is_for_family(self):
        return self.audience == self.Audience.FAMILY and self.family is not None

    def get_audience_display_name(self):
        """Human-readable version of who the meeting is for."""
        if self.audience == self.Audience.CLAN:
            return "Entire Clan"
        elif self.audience == self.Audience.EXECUTIVES:
            return "Clan Executives"
        elif self.audience == self.Audience.FAMILY_LEADERS:
            return "Family Leaders"
        elif self.audience == self.Audience.FAMILY and self.family:
            return f"{self.family.name} Family"
        return "—"
