from django.urls import path
from dashboard.views.home import index, clan_meetings, clan_documents, get_clan_meetings_api

app_name = 'dashboard'

urlpatterns = [
    path('', index, name='index'),
    path('meetings', clan_meetings, name='clan-meetings'),
    path('documents', clan_documents, name='clan-documents'),
    path('api/meetings', get_clan_meetings_api, name='get-meetings-api'),
]
