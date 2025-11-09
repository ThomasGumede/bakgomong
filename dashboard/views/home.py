from django.shortcuts import render, get_object_or_404, redirect
from dashboard.models import ClanDocument, Meeting
from django.core import serializers
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import logging, mimetypes

logger = logging.getLogger("events")

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