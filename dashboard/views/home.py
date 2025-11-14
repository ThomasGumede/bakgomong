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

logger = logging.getLogger("events")


@login_required
def index(request):
    user = request.user
    context = {}

    context["upcoming_meeting"] = Meeting.objects.filter(
            meeting_date__gte=timezone.now()
        ).order_by("meeting_date").first()
    context["total_members"] = Account.objects.count()
    context["total_families"] = Family.objects.count()
    context["family"] = user.family
    
    if user.is_staff or user.role.lower() in ["CLAN CHAIRPERSORN", "FAMILY LEADER"]:
        
        context["total_contributions"] = ContributionType.objects.count()

    
        payments = Payment.objects.aggregate(total_paid=Sum("amount"))
        unpaid = MemberContribution.objects.filter(is_paid='NOT PAID').aggregate(total_due=Sum("amount_due"))

        context["total_paid"] = payments["total_paid"] or 0
        context["total_unpaid"] = unpaid["total_due"] or 0
        context["payments"] = MemberContribution.objects.order_by('created')[:5]
        context["recent_docs"] = ClanDocument.objects.order_by("-created")[:5]

    else:
        
        
        context["member_contributions"] = MemberContribution.objects.filter(account=user)
        context["member_payments"] = Payment.objects.filter(account=user)
        context["total_paid"] = context["member_payments"].aggregate(total=Sum("amount"))["total"] or 0
        context["payments"] = MemberContribution.objects.filter(account=user).order_by('created')[:5]
        context["total_unpaid"] = context["member_contributions"].filter(is_paid=False).aggregate(total=Sum("amount_due"))["total"] or 0
        
        documents = ClanDocument.objects.all()
        context["recent_docs"] = [doc for doc in documents if doc.user_has_access(user)][:5]


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
        logger.error("Missing Media file")
        messages.error(request, "Media file not aploaded yet, send us an email if you have questions")
        return redirect("dashboard:clan-documents")