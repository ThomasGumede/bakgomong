from django.shortcuts import render
from dashboard.models import ClanDocument, Meeting
from django.core import serializers
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    return render(request, 'home/index.html')

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