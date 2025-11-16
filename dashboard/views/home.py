import logging
import mimetypes
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.db.models import Sum, Count, Q
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.core import serializers
from dashboard.models import ClanDocument, Meeting
from contributions.models import ContributionType, MemberContribution, Payment
from accounts.models import Account, Family
from accounts.utils.abstracts import PaymentStatus

logger = logging.getLogger("events")


@login_required
def index(request):
    user = request.user
    context = {}

    # Common overview
    context["upcoming_meeting"] = Meeting.objects.filter(
        meeting_date__gte=timezone.now()
    ).order_by("meeting_date").first()
    context["total_members"] = Account.objects.count()
    context["total_families"] = Family.objects.count()
    context["family"] = getattr(user, "family", None)

    # Clan-wide aggregates (safe to compute for everyone)
    # Use MemberContribution totals as source of truth
    clan_paid_agg = MemberContribution.objects.filter(
        is_paid__in=[PaymentStatus.PAID, 'PAID']
    ).aggregate(total_paid=Sum("amount_due"))
    clan_total_paid = clan_paid_agg.get("total_paid") or 0
    member_contribs_qs = MemberContribution.objects.select_related(
            "contribution_type"
        ).filter(account=user).order_by("-created")

    # Everyone can see a simple clan balance (paid amount). Detailed unpaid shown only to staff.
    context["clan_total_paid"] = clan_total_paid
    if user.is_staff:
        clan_unpaid_agg = MemberContribution.objects.filter(
        ~Q(is_paid__in=[PaymentStatus.NOT_PAID, 'NOT PAID', PaymentStatus.PENDING, 'PENDING'])
        )
        clan_total_unpaid = clan_unpaid_agg.aggregate(total_unpaid=Sum("amount_due")).get("total_unpaid") or 0
        context["clan_total_unpaid"] = clan_total_unpaid
        context["clan_total_unpaid_count"] = clan_unpaid_agg.count()
        context["payments"] = MemberContribution.objects.select_related(
            "account", "contribution_type", "account__family"
        ).order_by("-created")[:20]
        
    else:
        # Member view: only personal contributions/payments (MemberContribution)
        
        context["payments"] = member_contribs_qs[:10]

        
    member_paid_agg = member_contribs_qs.filter(is_paid=PaymentStatus.PAID).aggregate(total=Sum("amount_due"))
    member_unpaid_agg = member_contribs_qs.filter(is_paid__in=[PaymentStatus.NOT_PAID, 'NOT PAID', PaymentStatus.PENDING, 'PENDING'])

    context["member_total_paid"] = member_paid_agg.get("total") or 0
    context["member_total_unpaid"] = member_unpaid_agg.aggregate(total=Sum("amount_due")).get("total") or 0
    context["member_total_unpaid_count"] = member_unpaid_agg.count()
    
    return render(request, "home/index.html", context)


@login_required
def clan_documents(request):
    documents = ClanDocument.objects.all()
    docs = [doc for doc in documents if doc.user_has_access(request.user)]
    return render(request, 'home/documents.html', {'docs': docs})


@login_required
def clan_meetings(request):
    meetings = Meeting.objects.all()
    return render(request, 'home/meetings.html', {'meetings': meetings})


def get_clan_meetings_api(request):
    try:
        meetings = Meeting.objects.all()
        data = serializers.serialize("json", meetings)
        return JsonResponse({"success": True, "meetings": data}, status=200)
    except Exception as ex:
        return JsonResponse({"success": False, "message": f"Something went wrong: {ex}"}, status=200)


@login_required
def download_file(request, file_id):
    media = get_object_or_404(ClanDocument.objects.all(), id=file_id)

    try:
        file_path = media.file.path
        file_name = media.file.name
        if file_path and file_name:
            with open(file_path, 'rb') as file:
                file_data = file.read()
                mime_type, _ = mimetypes.guess_type(file_path)
                mime_type = mime_type or 'application/octet-stream'
                response = HttpResponse(file_data, content_type=mime_type)

            response['Content-Disposition'] = f'attachment; filename="{file_name.split("/")[-1]}"'

        return response
    except Exception as ex:
        logger.error("Missing Media file: %s", ex)
        messages.error(request, "Media file not uploaded yet, send us an email if you have questions")
        return redirect("dashboard:clan-documents")