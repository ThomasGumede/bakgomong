from django.urls import path
from accounts.views.account import (
    account_update,
    activate,
    activation_sent,
    add_social_links,
    confirm_email,
    custom_login,
    custom_logout,
    general,
    register,
    user_details,
)
from accounts.views.password import (
    password_change,
    password_reset_request,
    password_reset_sent,
    password_reset_confirm,
)
from accounts.views.family import delete_family, get_families, add_family, get_family, update_family
from accounts.views.members import get_members, add_member, update_member, delete_member

app_name = "accounts"
urlpatterns = [
    path("login", custom_login, name="login"),
    path('logout', custom_logout, name='logout'),
    path("register", register, name="register"),
    path('profile/@<str:username>', user_details, name="user-details"),
    path('register/success', activation_sent, name='success'),
    path('activate/<uidb64>/<token>', activate, name='activate'),
    path('confirm/email/<uidb64>/<token>', confirm_email, name='confirm-email'),
    path("password/reset", password_reset_request, name="password-reset"),
    path('password/success', password_reset_sent, name='password-reset-sent'),
    path('password/reset/<uidb64>/<token>', password_reset_confirm, name='password-reset-confirm'),

    path('dashboard/update/profile', account_update, name="profile-update"),
    path('dashboard/update/password', password_change, name="password-update"),
    
    path('dashboard/families', get_families, name="get-families"),
    path('dashboard/add-family', add_family, name="add-family"),
    path('dashboard/family/<family_slug>', get_family, name="get-family"),
    path('dashboard/update-family/<family_slug>', update_family, name="update-family"),
    path('dashboard/delete-family/<family_slug>', delete_family, name="delete-family"),
    
    path('dashboard/<family_slug>/members', get_members, name="get-members"),
    path('dashboard/<family_slug>/add-member', add_member, name="add-member"),
    # member management
    path('dashboard/<str:family_slug>/members/<str:username>/edit', update_member, name="update-member"),
    path('dashboard/<str:family_slug>/members/<str:username>/delete', delete_member, name="delete-member"),
]
